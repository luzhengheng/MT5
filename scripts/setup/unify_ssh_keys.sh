#!/bin/bash
# SSH 密钥统一脚本
# 目标: 用 HenryLu.pem 替换所有旧密钥,统一所有服务器的 SSH 配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSH 密钥统一脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 配置
PROJECT_ROOT="/root/M t 5-CRS"
NEW_KEY="${PROJECT_ROOT}/secrets/HenryLu.pem"
NEW_KEY_PUB="${PROJECT_ROOT}/secrets/HenryLu.pem.pub"
OLD_KEY="${PROJECT_ROOT}/secrets/Henry.pem"

# 服务器列表(从CONTEXT.md中提取)
SERVERS=(
    "root@47.84.1.161:CRS"          # 中文股 / 策略研究服务器
    "root@47.84.111.158:PTS"        # 多品种 / 训练服务器
    "root@8.138.100.136:TRS"        # A股 / 推理服务器
)

echo -e "${YELLOW}检查密钥文件...${NC}"

# 检查新密钥
if [ ! -f "$NEW_KEY" ]; then
    echo -e "${RED}错误: 新密钥不存在: $NEW_KEY${NC}"
    exit 1
fi

# 检查权限
if [ $(stat -c %a "$NEW_KEY") != "600" ]; then
    echo -e "${YELLOW}修正密钥权限为 600${NC}"
    chmod 600 "$NEW_KEY"
fi

# 确保公钥存在
if [ ! -f "$NEW_KEY_PUB" ]; then
    echo -e "${YELLOW}从私钥生成公钥...${NC}"
    ssh-keygen -y -f "$NEW_KEY" > "$NEW_KEY_PUB"
fi

echo -e "${GREEN}✅ 新密钥文件检查通过${NC}"
echo -e "私钥: $NEW_KEY"
echo -e "公钥: $NEW_KEY_PUB"
echo ""

# 显示密钥信息
echo -e "${YELLOW}密钥指纹:${NC}"
ssh-keygen -l -f "$NEW_KEY"
echo ""

# 函数: 测试 SSH 连接
test_ssh_connection() {
    local host=$1
    local key=$2
    local name=$3

    echo -n "测试 $name 连接 ($host)... "

    if timeout 10 ssh -i "$key" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "$host" "echo '连接成功'" &>/dev/null; then
        echo -e "${GREEN}✅ 成功${NC}"
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        return 1
    fi
}

# 函数: 分发公钥到服务器
distribute_key() {
    local server_info=$1
    local host=$(echo $server_info | cut -d: -f1)
    local name=$(echo $server_info | cut -d: -f2)

    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}处理服务器: $name ($host)${NC}"
    echo -e "${YELLOW}========================================${NC}"

    # 先测试旧密钥能否连接
    echo -n "测试旧密钥连接... "
    if test_ssh_connection "$host" "$OLD_KEY" "$name"; then
        USE_KEY="$OLD_KEY"
    else
        echo -e "${YELLOW}旧密钥无法连接,尝试新密钥...${NC}"
        if test_ssh_connection "$host" "$NEW_KEY" "$name"; then
            echo -e "${GREEN}新密钥已经配置!${NC}"
            return 0
        else
            echo -e "${RED}无法连接到服务器: $host${NC}"
            echo -e "${YELLOW}可能需要手动配置或使用密码登录${NC}"
            return 1
        fi
    fi

    # 读取公钥内容
    PUB_KEY_CONTENT=$(cat "$NEW_KEY_PUB")

    # 分发公钥
    echo "分发新公钥到服务器..."
    ssh -i "$USE_KEY" -o StrictHostKeyChecking=no "$host" "bash -s" <<EOF
# 确保 .ssh 目录存在
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 备份现有的 authorized_keys
if [ -f ~/.ssh/authorized_keys ]; then
    cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.backup.\$(date +%Y%m%d_%H%M%S)
fi

# 添加新公钥(如果不存在)
if ! grep -q "$PUB_KEY_CONTENT" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$PUB_KEY_CONTENT" >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    echo "✅ 公钥已添加"
else
    echo "ℹ️  公钥已存在"
fi

# 显示 authorized_keys 状态
echo "当前授权密钥数量: \$(wc -l < ~/.ssh/authorized_keys)"
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 公钥分发成功${NC}"

        # 测试新密钥
        echo "测试新密钥连接..."
        if test_ssh_connection "$host" "$NEW_KEY" "$name"; then
            echo -e "${GREEN}✅ 新密钥连接成功!${NC}"
            return 0
        else
            echo -e "${RED}❌ 新密钥连接失败${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ 公钥分发失败${NC}"
        return 1
    fi
}

# 函数: 配置 SSH 安全设置
configure_ssh_security() {
    local server_info=$1
    local host=$(echo $server_info | cut -d: -f1)
    local name=$(echo $server_info | cut -d: -f2)

    echo ""
    echo -e "${YELLOW}配置 $name SSH 安全设置...${NC}"

    ssh -i "$NEW_KEY" -o StrictHostKeyChecking=no "$host" "bash -s" <<'EOF'
# 备份 sshd_config
if [ ! -f /etc/ssh/sshd_config.backup ]; then
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    echo "✅ 已备份 sshd_config"
fi

# 读取当前配置
CURRENT_CONFIG=$(cat /etc/ssh/sshd_config)

# 检查并更新配置
update_sshd_config() {
    local key=$1
    local value=$2

    if grep -q "^$key" /etc/ssh/sshd_config; then
        # 配置已存在,更新它
        sed -i "s/^$key.*/$key $value/" /etc/ssh/sshd_config
        echo "✅ 已更新: $key $value"
    elif grep -q "^#$key" /etc/ssh/sshd_config; then
        # 配置被注释,取消注释并更新
        sed -i "s/^#$key.*/$key $value/" /etc/ssh/sshd_config
        echo "✅ 已启用: $key $value"
    else
        # 配置不存在,添加它
        echo "$key $value" >> /etc/ssh/sshd_config
        echo "✅ 已添加: $key $value"
    fi
}

# 推荐的安全设置
echo "应用 SSH 安全配置..."
update_sshd_config "PermitRootLogin" "prohibit-password"
update_sshd_config "PubkeyAuthentication" "yes"
update_sshd_config "PasswordAuthentication" "no"
update_sshd_config "ChallengeResponseAuthentication" "no"
update_sshd_config "UsePAM" "yes"
update_sshd_config "X11Forwarding" "no"

# 验证配置
echo ""
echo "验证 SSHD 配置..."
if sshd -t; then
    echo "✅ SSHD 配置有效"
    echo ""
    echo "⚠️  注意: 需要重启 SSHD 服务才能生效"
    echo "执行命令: systemctl restart sshd"
    echo "建议先在另一个 SSH 会话中测试,以防锁定"
else
    echo "❌ SSHD 配置无效,请检查"
    exit 1
fi
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $name SSH 安全设置配置完成${NC}"
        return 0
    else
        echo -e "${RED}❌ $name SSH 安全设置配置失败${NC}"
        return 1
    fi
}

# 主流程
SUCCESS_COUNT=0
FAIL_COUNT=0

echo -e "${YELLOW}开始分发密钥到所有服务器...${NC}"
echo ""

for server in "${SERVERS[@]}"; do
    if distribute_key "$server"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done

# 总结
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}密钥分发完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "成功: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "失败: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ 所有服务器密钥分发成功!${NC}"
    echo ""

    # 询问是否配置安全设置
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}SSH 安全配置(可选)${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "现在可以配置 SSH 安全设置:"
    echo "- 禁用密码登录"
    echo "- 仅允许公钥认证"
    echo "- 其他安全增强"
    echo ""
    read -p "是否配置 SSH 安全设置? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for server in "${SERVERS[@]}"; do
            configure_ssh_security "$server"
        done

        echo ""
        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}重要提醒${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo ""
        echo "SSH 安全配置已应用,但尚未生效"
        echo "需要在每台服务器上重启 SSHD 服务:"
        echo ""
        for server in "${SERVERS[@]}"; do
            host=$(echo $server | cut -d: -f1)
            name=$(echo $server | cut -d: -f2)
            echo "  ssh -i $NEW_KEY $host 'systemctl restart sshd'"
        done
        echo ""
        echo -e "${RED}警告: 重启前请确保至少有一个 SSH 会话保持打开!${NC}"
    fi
else
    echo -e "${RED}部分服务器配置失败,请检查日志${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}测试连接${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

for server in "${SERVERS[@]}"; do
    host=$(echo $server | cut -d: -f1)
    name=$(echo $server | cut -d: -f2)
    test_ssh_connection "$host" "$NEW_KEY" "$name"
done

echo ""
echo -e "${GREEN}密钥统一完成!${NC}"
echo ""
