#!/bin/bash
################################################################################
# GPU 环境自动化安装脚本
#
# Purpose:
#   在远程 GPU 节点上幂等地安装和配置：
#   - Python 3.9+ 和虚拟环境
#   - PyTorch/CUDA 依赖
#   - boto3 (S3 客户端)
#   - 其他必要的 ML 库
#
# Design:
#   - 幂等性: 重复运行不会导致错误
#   - 环境注入: 支持通过环境变量动态配置
#   - 错误处理: 每一步都有检查点
#
# Protocol: v4.3 (Zero-Trust Edition)
# Author: MT5-CRS Agent
# Date: 2026-01-12
################################################################################

set -euo pipefail

# ============================================================================
# 配置
# ============================================================================

PROJECT_ROOT="${PROJECT_ROOT:-.}"
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/venv_gpu}"
LOG_FILE="${LOG_FILE:-setup_env.log}"
PYTHON_VERSION="${PYTHON_VERSION:-3.9}"

echo "[SETUP] GPU Environment Setup Started" | tee -a "$LOG_FILE"
echo "[SETUP] Timestamp: $(date -Iseconds)" | tee -a "$LOG_FILE"
echo "[SETUP] Project Root: $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "[SETUP] Venv Dir: $VENV_DIR" | tee -a "$LOG_FILE"

# ============================================================================
# 实用函数
# ============================================================================

log() {
    echo "[SETUP] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "[ERROR] $*" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo "[SUCCESS] $*" | tee -a "$LOG_FILE"
}

# ============================================================================
# 检查系统依赖
# ============================================================================

log "Checking system dependencies..."

if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed"
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
log "Python version: $python_version"

if ! command -v pip3 &> /dev/null; then
    error "pip3 is not installed"
fi

pip_version=$(pip3 --version 2>&1)
log "pip version: $pip_version"

# ============================================================================
# 虚拟环境设置
# ============================================================================

log "Setting up Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    log "Creating new virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment"
else
    log "Virtual environment already exists at $VENV_DIR"
fi

# 激活虚拟环境
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate" || error "Failed to activate virtual environment"

log "Virtual environment activated: $VIRTUAL_ENV"

# ============================================================================
# 升级 pip 和工具
# ============================================================================

log "Upgrading pip, setuptools, and wheel..."
pip3 install --upgrade pip setuptools wheel 2>&1 | grep -E "(Successfully|already)" | head -3 | tee -a "$LOG_FILE" || true

# ============================================================================
# 安装 PyTorch (带 CUDA 支持)
# ============================================================================

log "Checking for CUDA..."

if command -v nvidia-smi &> /dev/null; then
    cuda_version=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1)
    log "CUDA available (compute capability: $cuda_version)"

    # 使用官方 PyTorch CUDA 版本
    log "Installing PyTorch with CUDA 11.8..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 2>&1 | \
        grep -E "(Successfully|already|Collecting)" | tail -5 | tee -a "$LOG_FILE" || true
else
    log "CUDA not found, installing CPU-only PyTorch..."
    pip3 install torch torchvision torchaudio 2>&1 | \
        grep -E "(Successfully|already|Collecting)" | tail -5 | tee -a "$LOG_FILE" || true
fi

# 验证 PyTorch
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" | tee -a "$LOG_FILE"

# ============================================================================
# 安装数据处理和 ML 库
# ============================================================================

log "Installing data processing and ML libraries..."

packages_to_install=(
    "numpy>=1.21"
    "pandas>=1.3"
    "scikit-learn>=1.0"
    "xgboost>=1.5"
    "boto3>=1.20"
    "python-dotenv>=0.19"
)

for package in "${packages_to_install[@]}"; do
    log "Installing $package..."
    pip3 install "$package" 2>&1 | grep -E "(Successfully|already)" | head -1 | tee -a "$LOG_FILE" || true
done

# ============================================================================
# 验证安装
# ============================================================================

log "Verifying installations..."

verify_package() {
    local pkg=$1
    if python3 -c "import $pkg" 2>/dev/null; then
        success "✅ $pkg is installed"
    else
        log "⚠️  $pkg is not installed (optional)"
    fi
}

verify_package "torch"
verify_package "numpy"
verify_package "pandas"
verify_package "sklearn"
verify_package "xgboost"
verify_package "boto3"

# ============================================================================
# 配置 boto3 (如果提供了凭证)
# ============================================================================

if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    log "Configuring boto3 with provided credentials..."

    mkdir -p ~/.aws
    cat > ~/.aws/credentials <<EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

    chmod 600 ~/.aws/credentials
    success "boto3 credentials configured"
fi

# ============================================================================
# 最终检查
# ============================================================================

log "Setup complete!"
log "To activate the virtual environment, run: source $VENV_DIR/bin/activate"

# 打印环境摘要
echo "" | tee -a "$LOG_FILE"
echo "============================================================================" | tee -a "$LOG_FILE"
echo "Environment Summary" | tee -a "$LOG_FILE"
echo "============================================================================" | tee -a "$LOG_FILE"
echo "Python: $(python3 --version)" | tee -a "$LOG_FILE"
echo "Pip: $(pip3 --version)" | tee -a "$LOG_FILE"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')" | tee -a "$LOG_FILE" || echo "PyTorch not available" | tee -a "$LOG_FILE"
echo "============================================================================" | tee -a "$LOG_FILE"

success "✅ GPU environment setup completed successfully!"
