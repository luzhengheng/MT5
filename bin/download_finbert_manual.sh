#!/bin/bash
# 手动下载 FinBERT 模型文件
# 由于服务器网络或 transformers 版本问题,使用直接下载方式

set -e

MODEL_CACHE="/opt/mt5-crs/var/cache/models"
MODEL_NAME="ProsusAI--finbert"
MODEL_DIR="${MODEL_CACHE}/${MODEL_NAME}"

echo "创建模型目录: ${MODEL_DIR}"
mkdir -p "${MODEL_DIR}"

cd "${MODEL_DIR}"

echo "开始下载 FinBERT 模型文件..."
echo ""

# 下载模型配置文件
echo "[1/5] 下载 config.json..."
curl -L -o config.json "https://huggingface.co/ProsusAI/finbert/resolve/main/config.json"

# 下载词汇表
echo "[2/5] 下载 vocab.txt..."
curl -L -o vocab.txt "https://huggingface.co/ProsusAI/finbert/resolve/main/vocab.txt"

# 下载tokenizer配置
echo "[3/5] 下载 tokenizer_config.json..."
curl -L -o tokenizer_config.json "https://huggingface.co/ProsusAI/finbert/resolve/main/tokenizer_config.json"

# 下载模型权重 (最大的文件)
echo "[4/5] 下载 pytorch_model.bin (约 440MB, 可能需要几分钟)..."
curl -L -o pytorch_model.bin "https://huggingface.co/ProsusAI/finbert/resolve/main/pytorch_model.bin"

# 下载special tokens map
echo "[5/5] 下载 special_tokens_map.json..."
curl -L -o special_tokens_map.json "https://huggingface.co/ProsusAI/finbert/resolve/main/special_tokens_map.json"

echo ""
echo "✓ 所有文件下载完成!"
echo ""
echo "模型位置: ${MODEL_DIR}"
echo "文件清单:"
ls -lh "${MODEL_DIR}"
echo ""

# 计算总大小
TOTAL_SIZE=$(du -sh "${MODEL_DIR}" | awk '{print $1}')
echo "总大小: ${TOTAL_SIZE}"
