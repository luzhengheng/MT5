#!/bin/bash
# ========================================
# MT5-CRS 基础设施互联互通测试脚本
# ========================================
# 用途: 在 INF (Linux) 上验证全网连通性
# 运行方式: bash verify_network.sh
#
# 测试项目:
#   ✅ VPC 内网连通性 (ping GTW, HUB)
#   ✅ ZeroMQ 端口可达性 (nc GTW:5555, GTW:5556)
#   ✅ 公网连通性 (ping GPU)
#   ✅ SSH 端口可用性 (nc GPU:22, HUB:22)
#   ✅ 本机环境检测 (IP 地址判断)
# ========================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 资产定义 (基于工单 #011 资产清单)
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

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ========================================
# 工具函数
# ========================================

print_header() {
    echo ""
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
    echo ""
}

test_result() {
    local test_name="$1"
    local result=$2
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ $result -eq 0 ]; then
        echo -e "   ${GREEN}✅ PASS${NC} - $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌ FAIL${NC} - $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}错误: 缺少必需工具 '$cmd'${NC}"
        echo -e "${YELLOW}请安装: sudo apt-get install -y $cmd${NC}"
        exit 1
    fi
}

# ========================================
# 主测试逻辑
# ========================================

main() {
    print_header "MT5-CRS 基础设施互联互通测试"

    # 环境检查
    print_section "环境检查"

    echo -e "   检查必需工具..."
    check_command "ping"
    check_command "nc"
    check_command "curl"
    echo -e "   ${GREEN}✅ 所有必需工具已安装${NC}"

    # 获取本机 IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo -e "   本机 IP: ${CYAN}${LOCAL_IP}${NC}"

    # 判断运行环境
    if [[ $LOCAL_IP == 172.19.* ]]; then
        ENVIRONMENT="🟢 生产环境 (新加坡 VPC)"
        IN_PROD_VPC=true
    elif [[ $LOCAL_IP == 172.23.* ]]; then
        ENVIRONMENT="🟡 训练环境 (广州 VPC)"
        IN_PROD_VPC=false
    else
        ENVIRONMENT="🔵 本地开发环境"
        IN_PROD_VPC=false
    fi

    echo -e "   环境识别: ${CYAN}${ENVIRONMENT}${NC}"

    # ========================================
    # 测试 1: VPC 内网连通性 (仅在生产 VPC 内测试)
    # ========================================

    if [ "$IN_PROD_VPC" = true ]; then
        print_section "测试 1: VPC 内网连通性 (172.19.0.0/16)"

        echo -e "   测试 GTW (网关) 内网连通性..."
        ping -c 3 -W 2 $GTW_PRIVATE_IP > /dev/null 2>&1
        test_result "ping $GTW_PRIVATE_IP (GTW 内网 IP)" $?

        echo -e "   测试 HUB (仓库) 内网连通性..."
        ping -c 3 -W 2 $HUB_PRIVATE_IP > /dev/null 2>&1
        test_result "ping $HUB_PRIVATE_IP (HUB 内网 IP)" $?

        echo -e "   测试自身连通性..."
        ping -c 3 -W 2 $INF_PRIVATE_IP > /dev/null 2>&1
        test_result "ping $INF_PRIVATE_IP (INF 内网 IP)" $?

    else
        print_section "测试 1: VPC 内网连通性 (跳过)"
        echo -e "   ${YELLOW}⚠️  当前不在新加坡 VPC 内，跳过内网测试${NC}"
    fi

    # ========================================
    # 测试 2: ZeroMQ 端口可达性 (仅在生产 VPC 内测试)
    # ========================================

    if [ "$IN_PROD_VPC" = true ]; then
        print_section "测试 2: ZeroMQ 端口可达性"

        echo -e "   测试 GTW ZMQ REQ 端口 (5555)..."
        nc -z -w 3 $GTW_PRIVATE_IP $ZMQ_REQ_PORT > /dev/null 2>&1
        test_result "nc -z $GTW_PRIVATE_IP:$ZMQ_REQ_PORT (交易指令通道)" $?

        echo -e "   测试 GTW ZMQ PUB 端口 (5556)..."
        nc -z -w 3 $GTW_PRIVATE_IP $ZMQ_PUB_PORT > /dev/null 2>&1
        test_result "nc -z $GTW_PRIVATE_IP:$ZMQ_PUB_PORT (行情推送通道)" $?

        # 额外检查: ZMQ 端口不应该对公网开放
        echo ""
        echo -e "   ${CYAN}安全检查: ZMQ 端口应仅对内网开放${NC}"
        echo -e "   测试 GTW 公网 IP 的 ZMQ 端口 (应超时)..."
        timeout 5 nc -z -w 3 $GTW_PUBLIC_IP $ZMQ_REQ_PORT > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "   ${GREEN}✅ 安全验证通过 - ZMQ 端口未对公网开放${NC}"
        else
            echo -e "   ${RED}⚠️  安全警告 - ZMQ 端口对公网开放！${NC}"
        fi

    else
        print_section "测试 2: ZeroMQ 端口可达性 (跳过)"
        echo -e "   ${YELLOW}⚠️  当前不在新加坡 VPC 内，跳过 ZMQ 端口测试${NC}"
        echo -e "   ${CYAN}提示: 本地开发需配置 SSH 隧道访问 ZMQ 端口${NC}"
        echo -e "   ${CYAN}命令: ssh -L 5555:172.19.141.255:5555 inf${NC}"
    fi

    # ========================================
    # 测试 3: 公网连通性
    # ========================================

    print_section "测试 3: 公网连通性"

    echo -e "   测试 GPU (训练节点) 公网连通性..."
    ping -c 3 -W 2 $GPU_PUBLIC_IP > /dev/null 2>&1
    test_result "ping $GPU_PUBLIC_IP (GPU 公网 IP)" $?

    echo -e "   测试 HUB (仓库) 公网连通性..."
    ping -c 3 -W 2 $HUB_PUBLIC_IP > /dev/null 2>&1
    test_result "ping $HUB_PUBLIC_IP (HUB 公网 IP)" $?

    echo -e "   测试 GTW (网关) 公网连通性..."
    ping -c 3 -W 2 $GTW_PUBLIC_IP > /dev/null 2>&1
    test_result "ping $GTW_PUBLIC_IP (GTW 公网 IP)" $?

    # ========================================
    # 测试 4: SSH 端口可用性
    # ========================================

    print_section "测试 4: SSH 端口可用性"

    echo -e "   测试 GPU SSH 端口..."
    nc -z -w 3 $GPU_PUBLIC_IP $SSH_PORT > /dev/null 2>&1
    test_result "nc -z $GPU_PUBLIC_IP:$SSH_PORT (GPU SSH)" $?

    echo -e "   测试 HUB SSH 端口..."
    nc -z -w 3 $HUB_PUBLIC_IP $SSH_PORT > /dev/null 2>&1
    test_result "nc -z $HUB_PUBLIC_IP:$SSH_PORT (HUB SSH)" $?

    echo -e "   测试 GTW SSH 端口..."
    nc -z -w 3 $GTW_PUBLIC_IP $SSH_PORT > /dev/null 2>&1
    test_result "nc -z $GTW_PUBLIC_IP:$SSH_PORT (GTW SSH)" $?

    echo -e "   测试 INF SSH 端口..."
    nc -z -w 3 $INF_PUBLIC_IP $SSH_PORT > /dev/null 2>&1
    test_result "nc -z $INF_PUBLIC_IP:$SSH_PORT (INF SSH)" $?

    # ========================================
    # 测试 5: DNS 解析
    # ========================================

    print_section "测试 5: DNS 解析"

    echo -e "   测试 GTW 域名解析..."
    RESOLVED_IP=$(dig +short $GTW_FQDN | tail -n1)
    if [ "$RESOLVED_IP" == "$GTW_PUBLIC_IP" ]; then
        test_result "DNS $GTW_FQDN -> $GTW_PUBLIC_IP" 0
    else
        test_result "DNS $GTW_FQDN (解析为: $RESOLVED_IP, 预期: $GTW_PUBLIC_IP)" 1
    fi

    echo -e "   测试 HUB 域名解析..."
    RESOLVED_IP=$(dig +short $HUB_FQDN | tail -n1)
    if [ "$RESOLVED_IP" == "$HUB_PUBLIC_IP" ]; then
        test_result "DNS $HUB_FQDN -> $HUB_PUBLIC_IP" 0
    else
        test_result "DNS $HUB_FQDN (解析为: $RESOLVED_IP, 预期: $HUB_PUBLIC_IP)" 1
    fi

    echo -e "   测试 INF 域名解析..."
    RESOLVED_IP=$(dig +short $INF_FQDN | tail -n1)
    if [ "$RESOLVED_IP" == "$INF_PUBLIC_IP" ]; then
        test_result "DNS $INF_FQDN -> $INF_PUBLIC_IP" 0
    else
        test_result "DNS $INF_FQDN (解析为: $RESOLVED_IP, 预期: $INF_PUBLIC_IP)" 1
    fi

    echo -e "   测试 GPU 域名解析..."
    RESOLVED_IP=$(dig +short $GPU_FQDN | tail -n1)
    if [ "$RESOLVED_IP" == "$GPU_PUBLIC_IP" ]; then
        test_result "DNS $GPU_FQDN -> $GPU_PUBLIC_IP" 0
    else
        test_result "DNS $GPU_FQDN (解析为: $RESOLVED_IP, 预期: $GPU_PUBLIC_IP)" 1
    fi

    # ========================================
    # 测试总结
    # ========================================

    print_header "测试总结"

    echo -e "   总测试数: ${CYAN}$TOTAL_TESTS${NC}"
    echo -e "   通过数:   ${GREEN}$PASSED_TESTS${NC}"
    echo -e "   失败数:   ${RED}$FAILED_TESTS${NC}"

    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo -e "   ${GREEN}🎉 所有测试通过！网络配置正常。${NC}"
        echo ""
        exit 0
    else
        echo ""
        echo -e "   ${YELLOW}⚠️  部分测试失败，请检查网络配置。${NC}"
        echo ""

        # 提供故障排查建议
        print_section "故障排查建议"

        if [ "$IN_PROD_VPC" != true ]; then
            echo -e "   ${YELLOW}1. 当前不在生产 VPC 内，某些测试被跳过${NC}"
            echo -e "      请在 INF (172.19.141.250) 上运行此脚本以获得完整测试"
        fi

        echo -e "   ${YELLOW}2. 检查阿里云安全组规则${NC}"
        echo -e "      新加坡安全组 ID: sg-t4n0dtkxxy1sxnbjsgk6"
        echo -e "      广州安全组 ID: sg-7xvffzmphblpy15x141f"

        echo -e "   ${YELLOW}3. 检查服务器防火墙 (iptables/firewalld)${NC}"
        echo -e "      确保端口 5555, 5556, 22 未被本地防火墙阻止"

        echo -e "   ${YELLOW}4. 检查 Windows 防火墙 (GTW)${NC}"
        echo -e "      确保 OpenSSH Server 和 ZMQ 端口允许通过"

        echo ""
        exit 1
    fi
}

# ========================================
# 执行主函数
# ========================================

main
