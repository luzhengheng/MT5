#!/usr/bin/env python3
"""下载 FinBERT 模型到本地缓存

该脚本用于预先下载 FinBERT 模型，避免在首次运行时下载导致超时
"""
import os
import sys
import logging

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_model(model_name: str = 'ProsusAI/finbert', cache_dir: str = None):
    """下载 FinBERT 模型

    Args:
        model_name: HuggingFace 模型名称
        cache_dir: 缓存目录
    """
    if cache_dir is None:
        cache_dir = '/opt/mt5-crs/var/cache/models'

    os.makedirs(cache_dir, exist_ok=True)

    logger.info(f"开始下载模型: {model_name}")
    logger.info(f"缓存目录: {cache_dir}")

    try:
        # 下载分词器
        logger.info("下载分词器...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        logger.info("✓ 分词器下载完成")

        # 下载模型
        logger.info("下载模型 (可能需要几分钟)...")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        logger.info("✓ 模型下载完成")

        # 验证模型
        logger.info("验证模型...")
        test_text = "The stock price increased significantly."
        inputs = tokenizer(test_text, return_tensors="pt", padding=True, truncation=True)
        outputs = model(**inputs)
        logger.info(f"✓ 模型验证成功 (输出形状: {outputs.logits.shape})")

        # 显示缓存大小
        cache_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(cache_dir)
            for filename in filenames
        )
        cache_size_mb = cache_size / (1024 * 1024)
        logger.info(f"✓ 模型缓存大小: {cache_size_mb:.1f} MB")

        logger.info("")
        logger.info("=" * 60)
        logger.info("模型下载完成!")
        logger.info(f"模型: {model_name}")
        logger.info(f"位置: {cache_dir}")
        logger.info(f"大小: {cache_size_mb:.1f} MB")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='下载 FinBERT 模型')
    parser.add_argument(
        '--model',
        default='ProsusAI/finbert',
        help='HuggingFace 模型名称 (默认: ProsusAI/finbert)'
    )
    parser.add_argument(
        '--cache-dir',
        default='/opt/mt5-crs/var/cache/models',
        help='模型缓存目录 (默认: /opt/mt5-crs/var/cache/models)'
    )

    args = parser.parse_args()

    success = download_model(args.model, args.cache_dir)
    sys.exit(0 if success else 1)
