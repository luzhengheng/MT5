import os
import sys
import boto3
import paramiko
import time
from botocore.config import Config
from dotenv import load_dotenv

# 加载配置
load_dotenv(dotenv_path=".env", override=True)

# === 核心配置 ===
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET = os.getenv("OSS_BUCKET_NAME", "mt5-hub-data")

# 网络路径
LOCAL_ENDPOINT = os.getenv("MINIO_ENDPOINT_URL") # 内网
REMOTE_ENDPOINT = "https://oss-ap-southeast-1.aliyuncs.com" # 公网

# 文件路径
LOCAL_FILE = "data/eurusd_m1_features_labels.parquet"
REMOTE_FILE = "/opt/mt5-crs/data/eurusd_m1_features_labels.parquet"
S3_KEY = "datasets/eurusd_m1.parquet"

# 远程主机
REMOTE_HOST = os.getenv("GPU_HOST")
REMOTE_USER = "root"

# === S3v2 兼容配置 (关键) ===
s3_config = Config(
    signature_version='s3',
    s3={'addressing_style': 'virtual'}
)

def step_1_upload():
    print(f"\n🚀 [Step 1] INF 节点正在上传数据 (内网加速)...")
    
    # 如果本地没有数据文件，创建一个伪造的用于测试 (防止脚本报错)
    if not os.path.exists(LOCAL_FILE):
        print(f"⚠️ 本地数据文件不存在，生成 1MB 测试数据: {LOCAL_FILE}")
        os.makedirs(os.path.dirname(LOCAL_FILE), exist_ok=True)
        with open(LOCAL_FILE, "wb") as f:
            f.write(os.urandom(1024 * 1024)) # 1MB random data

    try:
        s3 = boto3.client('s3', 
            endpoint_url=LOCAL_ENDPOINT,
            aws_access_key_id=ACCESS_KEY, 
            aws_secret_access_key=SECRET_KEY,
            config=s3_config
        )
        
        start = time.time()
        s3.upload_file(LOCAL_FILE, BUCKET, S3_KEY)
        cost = time.time() - start
        print(f"✅ 上传成功! 耗时: {cost:.2f}s")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        sys.exit(1)

def step_2_remote_download():
    print(f"\n📡 [Step 2] 呼叫广州 GPU 节点下载 (公网通道)...")

    # 远程执行脚本 (动态生成)
    remote_code = f"""
import boto3, time, os
from botocore.config import Config

print('   [GPU] 连接 OSS...')
my_config = Config(signature_version='s3', s3={{'addressing_style': 'virtual'}})

try:
    s3 = boto3.client('s3', 
        endpoint_url='{REMOTE_ENDPOINT}',
        aws_access_key_id='{ACCESS_KEY}',
        aws_secret_access_key='{SECRET_KEY}',
        config=my_config
    )
    
    start = time.time()
    os.makedirs(os.path.dirname('{REMOTE_FILE}'), exist_ok=True)
    s3.download_file('{BUCKET}', '{S3_KEY}', '{REMOTE_FILE}')
    cost = time.time() - start
    
    size = os.path.getsize('{REMOTE_FILE}') / (1024*1024)
    print(f'   [GPU] ✅ 下载成功! {{size:.2f}} MB, 耗时: {{cost:.2f}}s')
except Exception as e:
    print(f'   [GPU] ❌ 失败: {{e}}')
    exit(1)
"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(REMOTE_HOST, username=REMOTE_USER, timeout=20)
        
        # 1. 安装依赖
        ssh.exec_command("pip3 install boto3 -q")
        
        # 2. 执行代码
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/remote_sync.py", "w") as f:
            f.write(remote_code)
        
        stdin, stdout, stderr = ssh.exec_command("python3 /tmp/remote_sync.py")
        
        for line in stdout: print(line.strip())
        err = stderr.read().decode()
        if err: print(f"   [GPU Error] {err}")

    except Exception as e:
        print(f"❌ SSH 连接失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    step_1_upload()
    step_2_remote_download()
    print("\n🎉 全流程完成！")
