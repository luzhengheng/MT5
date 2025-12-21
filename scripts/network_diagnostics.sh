#!/bin/bash
# ========================================
# MT5-CRS 网络诊断工具包
# ========================================
# 用途: 全面的网络诊断和故障排查工具
# 运行方式: bash network_diagnostics.sh [mode]
#
# 模式:
#   quick    - 快速诊断 (2分钟)
#   full     - 完整诊断 (5分钟)
#   deep     - 深度诊断 (10分钟，包含性能测试)
#   zmq      - ZMQ 专项诊断
#   ssh      - SSH 专项诊断
#   dns      - DNS 专项诊断
# ========================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 资产定义
GTW_PRIVATE_IP="172.19.141.255"
GTW_PUBLIC_IP="47.237.79.129"
GTW_FQDN="gtw.crestive.net"

HUB_PRIVATE_IP="172.19.141.254"
HUB_PUBLIC_IP="47.84.1.161"
HUB_FQDN="www.crestive-code.com"

INF_PRIVATE_IP="172.19.141.250"
INF_PUBLIC_IP="47.84.111.158"
INF_FQDN="www.crestive.net"

GPU_PRIVATE_IP="172.23.135.141"
GPU_PUBLIC_IP="8.138.100.136"
GPU_FQDN="www.guangzhoupeak.com"

ZMQ_REQ_PORT=5555
ZMQ_PUB_PORT=5556
SSH_PORT=22

# 诊断模式
MODE=${1:-quick}

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# 性能指标
declare -A LATENCY_DATA
declare -A BANDWIDTH_DATA

# ========================================
# 工具函数
# ========================================

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

test_result() {
    local test_name="$1"
    local result=$2
    local level=${3:-"critical"}  # critical, warning, info

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ $result -eq 0 ]; then
        echo -e "   ${GREEN}✅ PASS${NC} - $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [ "$level" == "warning" ]; then
        echo -e "   ${YELLOW}⚠️  WARN${NC} - $test_name"
        WARNING_TESTS=$((WARNING_TESTS + 1))
    else
        echo -e "   ${RED}❌ FAIL${NC} - $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

info_output() {
    echo -e "   ${CYAN}ℹ️  INFO${NC} - $1"
}

check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}错误: 缺少必需工具 '$cmd'${NC}"
        return 1
    fi
    return 0
}

# ========================================
# 环境检测
# ========================================

detect_environment() {
    print_section "环境检测"

    LOCAL_IP=$(hostname -I | awk '{print $1}')
    HOSTNAME=$(hostname)
    OS_INFO=$(uname -a)

    info_output "主机名: $HOSTNAME"
    info_output "本机 IP: $LOCAL_IP"
    info_output "系统: $OS_INFO"

    # 判断运行环境
    if [[ $LOCAL_IP == 172.19.* ]]; then
        ENVIRONMENT="production"
        ENV_NAME="🟢 生产环境 (新加坡 VPC)"
        IN_PROD_VPC=true
    elif [[ $LOCAL_IP == 172.23.* ]]; then
        ENVIRONMENT="training"
        ENV_NAME="🟡 训练环境 (广州 VPC)"
        IN_PROD_VPC=false
    else
        ENVIRONMENT="local"
        ENV_NAME="🔵 本地开发环境"
        IN_PROD_VPC=false
    fi

    info_output "环境识别: $ENV_NAME"
    echo ""
}

# ========================================
# 工具检查
# ========================================

check_tools() {
    print_section "工具检查"

    local required_tools=("ping" "nc" "curl" "dig")
    local optional_tools=("iperf3" "mtr" "tcpdump" "nmap")
    local missing_required=()
    local missing_optional=()

    echo "   检查必需工具:"
    for tool in "${required_tools[@]}"; do
        if check_command "$tool"; then
            echo -e "   ${GREEN}✓${NC} $tool"
        else
            echo -e "   ${RED}✗${NC} $tool (必需)"
            missing_required+=("$tool")
        fi
    done

    echo ""
    echo "   检查可选工具:"
    for tool in "${optional_tools[@]}"; do
        if check_command "$tool"; then
            echo -e "   ${GREEN}✓${NC} $tool"
        else
            echo -e "   ${YELLOW}✗${NC} $tool (可选)"
            missing_optional+=("$tool")
        fi
    done

    if [ ${#missing_required[@]} -gt 0 ]; then
        echo ""
        echo -e "${RED}错误: 缺少必需工具: ${missing_required[*]}${NC}"
        echo -e "${YELLOW}安装命令:${NC}"
        echo -e "  Ubuntu/Debian: ${CYAN}sudo apt-get install -y ${missing_required[*]}${NC}"
        echo -e "  CentOS/RHEL:   ${CYAN}sudo yum install -y ${missing_required[*]}${NC}"
        exit 1
    fi

    if [ ${#missing_optional[@]} -gt 0 ] && [[ "$MODE" == "deep" ]]; then
        echo ""
        echo -e "${YELLOW}提示: 深度诊断建议安装可选工具: ${missing_optional[*]}${NC}"
    fi

    echo ""
}

# ========================================
# ICMP 连通性测试
# ========================================

test_icmp() {
    print_section "ICMP 连通性测试 (Ping)"

    local targets=(
        "$INF_PRIVATE_IP:INF 内网"
        "$GTW_PRIVATE_IP:GTW 内网"
        "$HUB_PRIVATE_IP:HUB 内网"
        "$GTW_PUBLIC_IP:GTW 公网"
        "$HUB_PUBLIC_IP:HUB 公网"
        "$GPU_PUBLIC_IP:GPU 公网"
        "8.8.8.8:Google DNS"
        "1.1.1.1:Cloudflare DNS"
    )

    for target_pair in "${targets[@]}"; do
        IFS=':' read -r ip name <<< "$target_pair"

        # 跳过内网 IP（如果不在生产 VPC 内）
        if [[ $ip == 172.19.* ]] && [ "$IN_PROD_VPC" != true ]; then
            info_output "跳过 $name ($ip) - 不在生产 VPC 内"
            continue
        fi

        echo -n "   测试 $name ($ip)... "

        # Ping 测试，获取延迟
        ping_output=$(ping -c 3 -W 2 $ip 2>&1)
        result=$?

        if [ $result -eq 0 ]; then
            # 提取平均延迟
            avg_latency=$(echo "$ping_output" | grep -oP 'avg = \K[0-9.]+' || echo "$ping_output" | grep -oP 'min/avg/max/mdev = [0-9.]+/\K[0-9.]+')
            LATENCY_DATA["$name"]=$avg_latency
            echo -e "${GREEN}✓${NC} (${avg_latency}ms)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi

        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    done

    echo ""
}

# ========================================
# TCP 端口测试
# ========================================

test_tcp_ports() {
    print_section "TCP 端口连通性测试"

    local port_tests=(
        "$GTW_PRIVATE_IP:$ZMQ_REQ_PORT:GTW ZMQ REQ (内网)"
        "$GTW_PRIVATE_IP:$ZMQ_PUB_PORT:GTW ZMQ PUB (内网)"
        "$GTW_PUBLIC_IP:$SSH_PORT:GTW SSH (公网)"
        "$HUB_PUBLIC_IP:$SSH_PORT:HUB SSH (公网)"
        "$INF_PUBLIC_IP:$SSH_PORT:INF SSH (公网)"
        "$GPU_PUBLIC_IP:$SSH_PORT:GPU SSH (公网)"
    )

    for port_test in "${port_tests[@]}"; do
        IFS=':' read -r ip port name <<< "$port_test"

        # 跳过内网测试（如果不在生产 VPC）
        if [[ $ip == 172.19.* ]] && [ "$IN_PROD_VPC" != true ]; then
            info_output "跳过 $name - 不在生产 VPC 内"
            continue
        fi

        echo -n "   测试 $name ($ip:$port)... "
        nc -z -w 3 $ip $port > /dev/null 2>&1
        result=$?

        if [ $result -eq 0 ]; then
            echo -e "${GREEN}✓${NC} 端口开放"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗${NC} 端口关闭或不可达"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi

        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    done

    echo ""
}

# ========================================
# DNS 解析测试
# ========================================

test_dns() {
    print_section "DNS 解析测试"

    local dns_tests=(
        "$INF_FQDN:$INF_PUBLIC_IP:INF"
        "$GTW_FQDN:$GTW_PUBLIC_IP:GTW"
        "$HUB_FQDN:$HUB_PUBLIC_IP:HUB"
        "$GPU_FQDN:$GPU_PUBLIC_IP:GPU"
    )

    for dns_test in "${dns_tests[@]}"; do
        IFS=':' read -r fqdn expected_ip name <<< "$dns_test"

        echo -n "   解析 $fqdn ($name)... "

        resolved_ip=$(dig +short $fqdn | tail -n1)

        if [ "$resolved_ip" == "$expected_ip" ]; then
            echo -e "${GREEN}✓${NC} $resolved_ip"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗${NC} 解析为 $resolved_ip (预期: $expected_ip)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi

        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    done

    echo ""
}

# ========================================
# ZMQ 专项诊断
# ========================================

test_zmq_detailed() {
    print_section "ZeroMQ 专项诊断"

    if [ "$IN_PROD_VPC" != true ]; then
        echo -e "   ${YELLOW}⚠️  当前不在生产 VPC 内，ZMQ 端口无法直接访问${NC}"
        echo -e "   ${CYAN}提示: 使用 SSH 隧道转发 ZMQ 端口${NC}"
        echo -e "   ${CYAN}命令: ssh -L 5555:$GTW_PRIVATE_IP:5555 -L 5556:$GTW_PRIVATE_IP:5556 inf${NC}"
        return
    fi

    echo "   ZMQ 服务器: $GTW_PRIVATE_IP"
    echo "   REQ 端口: $ZMQ_REQ_PORT"
    echo "   PUB 端口: $ZMQ_PUB_PORT"
    echo ""

    # 测试 REQ 端口
    echo -n "   测试 REQ 端口 ($ZMQ_REQ_PORT)... "
    if nc -z -w 3 $GTW_PRIVATE_IP $ZMQ_REQ_PORT; then
        echo -e "${GREEN}✓${NC} 端口开放"
    else
        echo -e "${RED}✗${NC} 端口关闭"
    fi

    # 测试 PUB 端口
    echo -n "   测试 PUB 端口 ($ZMQ_PUB_PORT)... "
    if nc -z -w 3 $GTW_PRIVATE_IP $ZMQ_PUB_PORT; then
        echo -e "${GREEN}✓${NC} 端口开放"
    else
        echo -e "${RED}✗${NC} 端口关闭"
    fi

    # 安全检查：验证 ZMQ 端口不对公网开放
    echo ""
    echo "   安全检查: 验证 ZMQ 端口不对公网开放..."
    echo -n "   测试公网 IP ($GTW_PUBLIC_IP:$ZMQ_REQ_PORT)... "

    if timeout 5 nc -z -w 3 $GTW_PUBLIC_IP $ZMQ_REQ_PORT 2>/dev/null; then
        echo -e "${RED}⚠️  警告: ZMQ 端口对公网开放！${NC}"
    else
        echo -e "${GREEN}✓${NC} 安全 - ZMQ 端口未对公网开放"
    fi

    echo ""
}

# ========================================
# SSH 专项诊断
# ========================================

test_ssh_detailed() {
    print_section "SSH 专项诊断"

    local ssh_targets=(
        "inf:$INF_FQDN:$INF_PUBLIC_IP"
        "gtw:$GTW_FQDN:$GTW_PUBLIC_IP"
        "hub:$HUB_FQDN:$HUB_PUBLIC_IP"
        "gpu:$GPU_FQDN:$GPU_PUBLIC_IP"
    )

    for target in "${ssh_targets[@]}"; do
        IFS=':' read -r alias fqdn ip <<< "$target"

        echo "   测试 $alias ($fqdn, $ip)..."

        # 端口开放检查
        echo -n "     [1] 端口开放... "
        if nc -z -w 3 $ip $SSH_PORT; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            continue
        fi

        # SSH 服务响应检查
        echo -n "     [2] SSH 服务响应... "
        ssh_banner=$(timeout 5 nc $ip $SSH_PORT < /dev/null 2>&1 | head -n1)
        if [[ $ssh_banner == SSH-* ]]; then
            echo -e "${GREEN}✓${NC} $ssh_banner"
        else
            echo -e "${YELLOW}⚠${NC}  无响应或非 SSH 服务"
        fi

        # 密钥认证测试 (仅测试，不实际登录)
        echo -n "     [3] SSH 密钥认证... "
        if [ -f ~/.ssh/id_rsa ]; then
            # 尝试连接但不执行命令
            ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no $alias exit 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓${NC} 可以无密码登录"
            else
                echo -e "${YELLOW}⚠${NC}  需要密码或密钥未配置"
            fi
        else
            echo -e "${YELLOW}⚠${NC}  本地无 SSH 私钥"
        fi

        echo ""
    done
}

# ========================================
# 性能测试 (仅 deep 模式)
# ========================================

test_performance() {
    print_section "网络性能测试"

    if ! check_command "iperf3"; then
        echo -e "   ${YELLOW}⚠️  iperf3 未安装，跳过带宽测试${NC}"
        return
    fi

    echo "   测试网络带宽和延迟..."
    echo ""

    # MTR 追踪路由
    if check_command "mtr"; then
        echo "   路由追踪 (到 GTW):"
        mtr -r -c 10 $GTW_PUBLIC_IP | tail -n +2
        echo ""
    fi
}

# ========================================
# Python 配置验证
# ========================================

test_python_config() {
    print_section "Python 配置验证"

    echo -n "   检查 Python 环境... "
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗${NC} Python3 未安装"
        return
    fi
    echo -e "${GREEN}✓${NC}"

    echo -n "   检查 mt5_bridge 模块... "
    if python3 -c "import src.mt5_bridge" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC}  模块未找到或有错误"
        return
    fi

    echo ""
    echo "   运行网络配置验证..."
    python3 -c "from src.mt5_bridge import print_network_status; print_network_status()" 2>/dev/null || echo -e "   ${RED}执行失败${NC}"
    echo ""
}

# ========================================
# 生成诊断报告
# ========================================

generate_report() {
    print_header "诊断报告"

    echo -e "${CYAN}环境信息:${NC}"
    echo "  主机名: $HOSTNAME"
    echo "  本机 IP: $LOCAL_IP"
    echo "  环境: $ENV_NAME"
    echo ""

    echo -e "${CYAN}测试统计:${NC}"
    echo "  总测试数: $TOTAL_TESTS"
    echo -e "  通过数:   ${GREEN}$PASSED_TESTS${NC}"
    echo -e "  失败数:   ${RED}$FAILED_TESTS${NC}"
    echo -e "  警告数:   ${YELLOW}$WARNING_TESTS${NC}"

    local success_rate=$((PASSED_TESTS * 100 / (TOTAL_TESTS == 0 ? 1 : TOTAL_TESTS)))
    echo "  成功率: ${success_rate}%"
    echo ""

    if [ ${#LATENCY_DATA[@]} -gt 0 ]; then
        echo -e "${CYAN}延迟统计:${NC}"
        for key in "${!LATENCY_DATA[@]}"; do
            echo "  $key: ${LATENCY_DATA[$key]}ms"
        done
        echo ""
    fi

    echo -e "${CYAN}结论:${NC}"
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "  ${GREEN}✅ 所有测试通过，网络配置正常${NC}"
    elif [ $FAILED_TESTS -le 2 ]; then
        echo -e "  ${YELLOW}⚠️  部分测试失败，建议检查配置${NC}"
    else
        echo -e "  ${RED}❌ 多项测试失败，网络存在严重问题${NC}"
    fi

    echo ""
    echo -e "${CYAN}建议操作:${NC}"
    if [ "$IN_PROD_VPC" != true ]; then
        echo "  1. 在生产环境 (INF) 上运行完整诊断获得更准确结果"
        echo "  2. 配置 SSH 隧道以访问 ZMQ 端口"
    fi
    if [ $FAILED_TESTS -gt 0 ]; then
        echo "  3. 检查阿里云安全组规则"
        echo "  4. 验证防火墙配置"
        echo "  5. 查看详细的网络日志"
    fi

    echo ""
}

# ========================================
# 主函数
# ========================================

main() {
    print_header "MT5-CRS 网络诊断工具 - $MODE 模式"

    detect_environment
    check_tools

    case $MODE in
        quick)
            test_icmp
            test_tcp_ports
            ;;
        full)
            test_icmp
            test_tcp_ports
            test_dns
            test_python_config
            ;;
        deep)
            test_icmp
            test_tcp_ports
            test_dns
            test_zmq_detailed
            test_ssh_detailed
            test_python_config
            test_performance
            ;;
        zmq)
            test_zmq_detailed
            ;;
        ssh)
            test_ssh_detailed
            ;;
        dns)
            test_dns
            ;;
        *)
            echo "未知模式: $MODE"
            echo "可用模式: quick, full, deep, zmq, ssh, dns"
            exit 1
            ;;
    esac

    generate_report
}

# 执行主函数
main
