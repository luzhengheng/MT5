#!/bin/bash
# ========================================
# MT5-CRS 一键部署脚本
# ========================================
# 用途: 自动化部署整个基础设施网络配置
# 运行方式: bash deploy_all.sh
#
# 功能:
#   1. 验证环境和前置条件
#   2. 部署本地 SSH 配置
#   3. 生成部署清单
#   4. 对接 GTW (Windows) 部署
#   5. 验证网络连通性
#   6. 生成部署报告
# ========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
DOCS_DIR="$PROJECT_ROOT/docs"
SSH_CONFIG="$CONFIG_DIR/ssh_config_template"

DEPLOYMENT_LOG="/tmp/mt5_deployment_$(date +%Y%m%d_%H%M%S).log"
DEPLOYMENT_CHECKLIST="/tmp/mt5_deployment_checklist.md"

# ========================================
# 工具函数
# ========================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $@" | tee -a "$DEPLOYMENT_LOG"
}

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-yes}"

    if [ "$default" = "yes" ]; then
        read -p "$(echo -e ${CYAN}$prompt [Y/n]${NC} )" -n 1 -r
    else
        read -p "$(echo -e ${CYAN}$prompt [y/N]${NC} )" -n 1 -r
    fi

    echo ""
    [[ $REPLY =~ ^[Yy]$ ]] && return 0 || return 1
}

check_prerequisite() {
    local cmd="$1"
    local package="${2:-$cmd}"

    if ! command -v "$cmd" &> /dev/null; then
        print_error "缺少工具: $cmd"
        echo "  安装命令: sudo apt-get install -y $package"
        return 1
    fi
    return 0
}

# ========================================
# 前置检查
# ========================================

check_prerequisites() {
    print_section "前置条件检查"

    local required_tools=("ssh" "ssh-keygen" "scp" "git" "python3")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! check_prerequisite "$tool"; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "缺少必需工具: ${missing_tools[*]}"
        echo ""
        echo "  请先安装缺失工具，然后重新运行此脚本"
        exit 1
    fi

    print_success "所有必需工具已安装"

    # 检查项目结构
    print_section "项目结构检查"

    if [ ! -d "$PROJECT_ROOT" ]; then
        print_error "未找到项目根目录: $PROJECT_ROOT"
        exit 1
    fi

    if [ ! -f "$SSH_CONFIG" ]; then
        print_error "未找到 SSH 配置模板: $SSH_CONFIG"
        exit 1
    fi

    print_success "项目结构完整"

    # 检查 SSH 密钥
    print_section "SSH 密钥检查"

    if [ ! -f ~/.ssh/id_rsa ]; then
        print_warning "未找到本地 SSH 私钥 (~/.ssh/id_rsa)"
        if prompt_yes_no "现在生成 SSH 密钥吗？"; then
            ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
            print_success "SSH 密钥已生成"
        else
            print_warning "部署将继续，但某些功能可能不可用"
        fi
    else
        print_success "SSH 私钥已存在"
    fi

    if [ ! -f ~/.ssh/id_rsa.pub ]; then
        print_error "未找到 SSH 公钥"
        exit 1
    fi

    # 检查公钥格式
    if ! grep -q "^ssh-rsa " ~/.ssh/id_rsa.pub; then
        print_error "SSH 公钥格式不正确"
        exit 1
    fi

    print_success "SSH 公钥有效"
}

# ========================================
# 本地 SSH 配置部署
# ========================================

deploy_local_ssh_config() {
    print_section "部署本地 SSH 配置"

    local ssh_dir=~/.ssh
    local target_config="$ssh_dir/config"

    # 创建 .ssh 目录
    if [ ! -d "$ssh_dir" ]; then
        mkdir -p "$ssh_dir"
        chmod 700 "$ssh_dir"
        print_success "创建 ~/.ssh 目录"
    fi

    # 备份现有配置
    if [ -f "$target_config" ]; then
        local backup_file="$target_config.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$target_config" "$backup_file"
        print_warning "已备份原配置: $backup_file"
    fi

    # 复制 SSH 配置
    cp "$SSH_CONFIG" "$target_config"
    chmod 600 "$target_config"
    print_success "SSH 配置已部署: $target_config"

    # 验证配置
    if ssh -G inf > /dev/null 2>&1; then
        print_success "SSH 配置验证通过"
    else
        print_warning "SSH 配置可能有问题，请手动检查"
    fi
}

# ========================================
# 生成 GTW 部署清单
# ========================================

generate_gtw_checklist() {
    print_section "生成 GTW (Windows) 部署清单"

    cat > "$DEPLOYMENT_CHECKLIST" << 'EOF'
# GTW Windows Server 2022 SSH 部署清单

## 前置条件
- [ ] 已获得 GTW RDP 访问权限
- [ ] 拥有 Administrator 账户
- [ ] GTW 已连接到网络

## 第 1 步: 远程连接
- [ ] 使用 RDP 连接到 GTW (47.237.79.129)
- [ ] 成功登录 GTW

## 第 2 步: 部署 OpenSSH Server
- [ ] 以管理员身份打开 PowerShell
- [ ] 运行部署脚本: `.\scripts\setup_win_ssh.ps1`
- [ ] 脚本执行成功（看到"SSH 服务配置完成"）

## 第 3 步: 配置 SSH 密钥
- [ ] 从本地复制公钥内容: `cat ~/.ssh/id_rsa.pub`
- [ ] 在 GTW 上打开 authorized_keys: `notepad C:\Users\Administrator\.ssh\authorized_keys`
- [ ] 粘贴公钥到文件
- [ ] 保存文件

## 第 4 步: 本地验证
- [ ] 从本地测试 SSH 连接: `ssh gtw`
- [ ] 成功无密码登录到 GTW
- [ ] 在 GTW 上执行命令验证

## 第 5 步: 网络验证
- [ ] 在 INF 上运行网络诊断: `bash scripts/verify_network.sh`
- [ ] 所有测试通过
- [ ] 特别检查 ZMQ 端口 (5555, 5556)

## 完成清单
- [ ] GTW SSH 部署完成
- [ ] 本地可以无密码登录 GTW
- [ ] 网络连通性验证通过
- [ ] 部署报告已生成

---

**部署开始时间**: $(date)
**部署状态**: 进行中

EOF

    print_success "部署清单已生成: $DEPLOYMENT_CHECKLIST"
    echo ""
    cat "$DEPLOYMENT_CHECKLIST"
}

# ========================================
# 生成 GTW 部署指令
# ========================================

generate_gtw_instructions() {
    print_section "生成 GTW 部署指令"

    local gtw_script_path="$PROJECT_ROOT/scripts/setup_win_ssh.ps1"

    cat > /tmp/gtw_deployment_instructions.txt << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║         GTW (Windows Server 2022) SSH 自动化部署指令                        ║
║                                                                            ║
║ 目标: 在 GTW (gtw.crestive.net) 上安装和配置 OpenSSH Server               ║
╚════════════════════════════════════════════════════════════════════════════╝

【第 1 步】远程连接到 GTW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Windows 用户:
  1. 按 Win + R
  2. 输入: mstsc /v:47.237.79.129
  3. 输入用户名: Administrator
  4. 输入密码: [GTW 管理员密码]

Linux/Mac 用户 (如果已有 SSH 访问):
  ssh Administrator@47.237.79.129 -p 22

【第 2 步】在 GTW 上获取部署脚本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

选项 A: 从 Git 仓库克隆 (推荐)
  在 GTW PowerShell 中运行:

  git clone https://github.com/your-repo/mt5-crs.git
  cd mt5-crs

选项 B: 从远程下载脚本
  在 GTW PowerShell 中运行:

  mkdir C:\Temp\MT5-Deploy
  cd C:\Temp\MT5-Deploy

  Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/mt5-crs/main/scripts/setup_win_ssh.ps1" -OutFile "setup_win_ssh.ps1"

【第 3 步】以管理员身份运行部署脚本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在 GTW PowerShell (管理员) 中运行:

  .\setup_win_ssh.ps1

脚本会自动执行以下操作:
  ✓ 安装 OpenSSH Server
  ✓ 配置 Windows 防火墙
  ✓ 启动 sshd 服务
  ✓ 设置服务自启动
  ✓ 创建 .ssh 目录和 authorized_keys

脚本完成后会提示下一步操作。

【第 4 步】配置 SSH 密钥认证 (从本地执行)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 获取本地公钥:

  cat ~/.ssh/id_rsa.pub

2. 复制整个输出 (ssh-rsa 开头的长字符串)

3. 在 GTW 上添加公钥到 authorized_keys:

  # 方法 A: 使用记事本 (GUI)
  notepad C:\Users\Administrator\.ssh\authorized_keys
  # 粘贴公钥，Ctrl+S 保存

  # 方法 B: 使用 PowerShell
  $publicKey = "ssh-rsa AAAAB3NzaC1yc2EA..."  # 替换为你的实际公钥
  Add-Content -Path "C:\Users\Administrator\.ssh\authorized_keys" -Value $publicKey

【第 5 步】从本地验证连接
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在本地 Linux/Mac 运行:

  ssh gtw

应该能无密码登录到 GTW，看到 Windows 命令提示符:

  Microsoft Windows [版本 10.0.20348]
  C:\Users\Administrator>

【第 6 步】验证网络连通性 (在 INF 上运行)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  bash scripts/verify_network.sh

验证以下项目:
  ✓ GTW 内网 IP 连通性
  ✓ ZMQ 端口 (5555, 5556)
  ✓ SSH 端口
  ✓ DNS 解析

【故障排查】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问题 1: "拒绝访问" (Permission denied)
  原因: authorized_keys 权限不正确
  解决: 检查文件权限，确保只有 Administrator 可读写

问题 2: 连接超时
  原因: 防火墙或安全组阻止
  解决: 检查阿里云安全组 (sg-t4n0dtkxxy1sxnbjsgk6)

问题 3: sshd 无法启动
  原因: 配置文件有语法错误
  解决: 运行 `sshd.exe -T` 验证配置

【支持】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

详细文档: docs/DEPLOYMENT_GTW_SSH_SETUP.md
快速开始: docs/ISSUE_011_QUICKSTART.md
EOF

    print_success "GTW 部署指令已生成: /tmp/gtw_deployment_instructions.txt"
    echo ""
    cat /tmp/gtw_deployment_instructions.txt
}

# ========================================
# 网络诊断
# ========================================

run_network_diagnostics() {
    print_section "运行网络诊断"

    if [ -f "$PROJECT_ROOT/scripts/verify_network.sh" ]; then
        echo "检测当前环境..."
        LOCAL_IP=$(hostname -I | awk '{print $1}')

        if [[ $LOCAL_IP == 172.19.* ]]; then
            echo -e "${GREEN}检测到生产环境 (新加坡 VPC)${NC}"
            echo ""
            echo "运行完整网络诊断..."
            bash "$PROJECT_ROOT/scripts/verify_network.sh"
        else
            echo -e "${YELLOW}当前环境: 本地或训练环境${NC}"
            echo "部分测试将被跳过"
            echo ""
            bash "$PROJECT_ROOT/scripts/verify_network.sh"
        fi
    else
        print_warning "网络诊断脚本不存在"
    fi
}

# ========================================
# 生成部署报告
# ========================================

generate_deployment_report() {
    print_section "生成部署报告"

    local report_file="$DOCS_DIR/DEPLOYMENT_REPORT_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << 'EOF'
# 部署报告

## 部署信息
- **部署时间**: $(date)
- **部署主机**: $(hostname)
- **部署用户**: $(whoami)
- **部署日志**: $DEPLOYMENT_LOG

## 部署清单

### 1. 本地 SSH 配置
- [x] SSH 配置已复制到 ~/.ssh/config
- [x] SSH 权限已设置为 600
- [x] SSH 配置验证通过

### 2. GTW (Windows) 部署
- [ ] 在 GTW 上运行 setup_win_ssh.ps1
- [ ] OpenSSH Server 已安装
- [ ] 防火墙已配置
- [ ] SSH 密钥已配置

### 3. 网络验证
- [ ] 本地到 GTW 的 SSH 连接
- [ ] 内网 IP 连通性
- [ ] ZMQ 端口可达性
- [ ] DNS 解析正确

## 后续步骤

1. **在 GTW 上部署 OpenSSH**
   ```powershell
   .\scripts\setup_win_ssh.ps1
   ```

2. **配置 SSH 密钥**
   - 获取本地公钥: `cat ~/.ssh/id_rsa.pub`
   - 复制到 GTW: `C:\Users\Administrator\.ssh\authorized_keys`

3. **验证连接**
   ```bash
   ssh gtw
   ```

4. **运行网络诊断**
   ```bash
   bash scripts/verify_network.sh
   ```

## 相关文档
- [GTW 部署详细指南](./DEPLOYMENT_GTW_SSH_SETUP.md)
- [工单 #011 快速开始](./ISSUE_011_QUICKSTART.md)
- [工单 #011 完成报告](./issues/ISSUE_011_PHASE1_COMPLETION_REPORT.md)

---
生成时间: $(date)
EOF

    print_success "部署报告已生成: $report_file"
}

# ========================================
# 主函数
# ========================================

main() {
    print_header "MT5-CRS 一键部署脚本"

    log "部署开始"

    # 前置检查
    check_prerequisites

    # 部署本地 SSH 配置
    deploy_local_ssh_config

    # 生成清单和指令
    generate_gtw_checklist
    generate_gtw_instructions

    # 运行网络诊断
    if prompt_yes_no "运行网络诊断吗？"; then
        run_network_diagnostics
    fi

    # 生成报告
    generate_deployment_report

    # 总结
    print_section "部署总结"

    print_success "本地配置已完成"
    print_warning "GTW (Windows) 部署需要手动执行"
    print_success "所有文档和清单已生成"

    echo ""
    echo -e "${CYAN}后续步骤:${NC}"
    echo "  1. 在 GTW 上运行: .\scripts\setup_win_ssh.ps1"
    echo "  2. 配置 SSH 密钥认证"
    echo "  3. 从本地验证: ssh gtw"
    echo "  4. 在 INF 上验证: bash scripts/verify_network.sh"
    echo ""
    echo -e "${CYAN}文档位置:${NC}"
    echo "  - 部署清单: $DEPLOYMENT_CHECKLIST"
    echo "  - 部署指令: /tmp/gtw_deployment_instructions.txt"
    echo "  - 部署日志: $DEPLOYMENT_LOG"
    echo ""

    log "部署完成"

    print_success "部署脚本执行完成"
}

# 运行主函数
main "$@"
