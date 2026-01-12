#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO/S3 数据传输工具

Purpose:
  提供统一的 S3/MinIO 对象存储接口，支持文件上传/下载、
  MD5 校验、进度条展示，兼容本地 (INF) 和远程 (GPU) 环境。

Design:
  - S3TransferClient: 核心客户端类，基于 boto3
  - upload_file(): 上传文件并返回 metadata
  - download_file(): 下载文件并验证 MD5
  - list_objects(): 列出 bucket 中的对象

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-12
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("❌ boto3 is not installed. Please run: pip install boto3")
    sys.exit(1)


# ============================================================================
# 日志配置
# ============================================================================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# S3 传输客户端
# ============================================================================

class S3TransferClient:
    """
    MinIO/S3 对象存储客户端。

    支持：
    - 文件上传/下载
    - MD5 校验
    - 元数据管理
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
        use_ssl: bool = True,
    ):
        """
        初始化 S3 客户端。

        Args:
            endpoint_url: S3 服务地址 (e.g., "https://minio.example.com:9000")
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region_name: AWS 区域
            use_ssl: 是否使用 SSL
        """
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region_name = region_name
        self.use_ssl = use_ssl

        # 初始化 boto3 客户端
        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name,
                use_ssl=use_ssl,
            )
            logger.info(f"✅ S3 client initialized: {endpoint_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            raise

    @staticmethod
    def compute_md5(file_path: str) -> str:
        """
        计算文件 MD5 哈希。

        Args:
            file_path: 文件路径

        Returns:
            MD5 哈希字符串
        """
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def upload_file(
        self,
        file_path: str,
        bucket: str,
        key: str,
        compute_hash: bool = True,
    ) -> Dict[str, Any]:
        """
        上传文件到 S3/MinIO。

        Args:
            file_path: 本地文件路径
            bucket: 目标 bucket 名称
            key: 对象 key (路径)
            compute_hash: 是否计算 MD5 哈希

        Returns:
            元数据字典，包含：
            - file_path: 本地文件路径
            - bucket: bucket 名称
            - key: 对象 key
            - size: 文件大小 (bytes)
            - md5: 文件 MD5 (若 compute_hash=True)
            - etag: S3 返回的 ETag
            - status: "success" 或 "failed"
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return {
                "file_path": str(file_path),
                "bucket": bucket,
                "key": key,
                "status": "failed",
                "error": "File not found",
            }

        file_size = file_path.stat().st_size
        logger.info(f"📤 Uploading {file_path} ({file_size} bytes) to s3://{bucket}/{key}")

        try:
            # 计算 MD5
            md5_hash = self.compute_md5(str(file_path)) if compute_hash else None

            # 上传文件
            with open(file_path, "rb") as f:
                response = self.client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=f,
                )

            etag = response.get("ETag", "").strip('"')
            logger.info(f"✅ Upload complete: {bucket}/{key} (ETag: {etag})")

            return {
                "file_path": str(file_path),
                "bucket": bucket,
                "key": key,
                "size": file_size,
                "md5": md5_hash,
                "etag": etag,
                "status": "success",
            }

        except ClientError as e:
            logger.error(f"❌ Upload failed: {e}")
            return {
                "file_path": str(file_path),
                "bucket": bucket,
                "key": key,
                "status": "failed",
                "error": str(e),
            }

    def download_file(
        self,
        bucket: str,
        key: str,
        file_path: str,
        verify_hash: bool = True,
        expected_md5: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从 S3/MinIO 下载文件。

        Args:
            bucket: 源 bucket 名称
            key: 对象 key (路径)
            file_path: 本地保存路径
            verify_hash: 是否验证 MD5
            expected_md5: 期望的 MD5 值 (用于验证)

        Returns:
            元数据字典，包含：
            - bucket: bucket 名称
            - key: 对象 key
            - file_path: 本地文件路径
            - size: 文件大小 (bytes)
            - md5: 下载文件的 MD5
            - md5_match: MD5 是否匹配 (若 verify_hash=True)
            - status: "success" 或 "failed"
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 Downloading s3://{bucket}/{key} to {file_path}")

        try:
            # 下载文件
            response = self.client.get_object(Bucket=bucket, Key=key)
            file_size = response.get("ContentLength", 0)

            with open(file_path, "wb") as f:
                for chunk in response["Body"].iter_chunks(chunk_size=1024 * 1024):
                    f.write(chunk)

            # 计算 MD5
            md5_hash = self.compute_md5(str(file_path)) if verify_hash else None
            md5_match = True

            if verify_hash and expected_md5:
                md5_match = md5_hash == expected_md5
                status_str = "✅" if md5_match else "❌"
                logger.info(f"{status_str} MD5 verification: {md5_hash} vs {expected_md5}")

                if not md5_match:
                    logger.error(f"❌ MD5 mismatch for {file_path}")
                    return {
                        "bucket": bucket,
                        "key": key,
                        "file_path": str(file_path),
                        "size": file_size,
                        "md5": md5_hash,
                        "md5_match": False,
                        "status": "failed",
                        "error": "MD5 mismatch",
                    }

            logger.info(f"✅ Download complete: {file_path} ({file_size} bytes)")

            return {
                "bucket": bucket,
                "key": key,
                "file_path": str(file_path),
                "size": file_size,
                "md5": md5_hash,
                "md5_match": md5_match,
                "status": "success",
            }

        except ClientError as e:
            logger.error(f"❌ Download failed: {e}")
            return {
                "bucket": bucket,
                "key": key,
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e),
            }

    def list_objects(self, bucket: str, prefix: str = "") -> Dict[str, Any]:
        """
        列出 bucket 中的对象。

        Args:
            bucket: bucket 名称
            prefix: 对象 key 前缀

        Returns:
            对象列表
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
            )

            objects = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    objects.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    })

            logger.info(f"✅ Listed {len(objects)} objects in {bucket}/{prefix}")
            return {
                "bucket": bucket,
                "prefix": prefix,
                "count": len(objects),
                "objects": objects,
                "status": "success",
            }

        except ClientError as e:
            logger.error(f"❌ List failed: {e}")
            return {
                "bucket": bucket,
                "prefix": prefix,
                "status": "failed",
                "error": str(e),
            }


# ============================================================================
# CLI 接口 (用于脚本调用)
# ============================================================================

def main():
    """命令行接口 (仅供本地测试)"""
    import argparse

    parser = argparse.ArgumentParser(description="S3/MinIO 数据传输工具")
    parser.add_argument("--action", choices=["upload", "download", "list"], required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--file", required=False)
    parser.add_argument("--endpoint", default=os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000"))
    parser.add_argument("--access-key", default=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"))
    parser.add_argument("--secret-key", default=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"))

    args = parser.parse_args()

    client = S3TransferClient(
        endpoint_url=args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
    )

    if args.action == "upload":
        result = client.upload_file(args.file, args.bucket, args.key)
        print(json.dumps(result, indent=2, default=str))

    elif args.action == "download":
        result = client.download_file(args.bucket, args.key, args.file)
        print(json.dumps(result, indent=2, default=str))

    elif args.action == "list":
        result = client.list_objects(args.bucket, args.key)
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
