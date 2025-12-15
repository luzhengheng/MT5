#!/bin/bash

# MT5 Hub 告警测试脚本
# 用于触发测试告警，验证钉钉通知效果

set -e

echo "🧪 MT5 Hub 告警测试工具"
echo "========================"

# 检查Grafana状态
echo "📊 检查Grafana状态..."
if curl -s http://localhost:3000/api/healthz > /dev/null; then
    echo "✅ Grafana运行正常"
else
    echo "❌ Grafana未运行，请先启动Grafana"
    exit 1
fi

echo ""
echo "选择测试类型:"
echo "1) CPU压力测试 (触发CPU告警)"
echo "2) 内存压力测试 (触发内存告警)"
echo "3) 服务模拟宕机 (触发服务告警)"
echo "4) 发送测试钉钉消息"
echo "5) 查看当前告警状态"

read -p "请输入选择 (1-5): " choice

case $choice in
    1)
        echo "🔥 开始CPU压力测试..."
        echo "这将运行60秒的高CPU负载来触发告警"
        echo "请在另一个终端查看Grafana告警状态"
        echo "按Ctrl+C可以提前停止测试"
        echo ""

        # 创建CPU压力
        stress --cpu 2 --timeout 60

        echo "✅ CPU压力测试完成"
        echo "请检查:"
        echo "1. Grafana Alerting页面是否有告警触发"
        echo "2. 钉钉群是否收到告警消息"
        ;;

    2)
        echo "💾 开始内存压力测试..."
        echo "这将消耗大量内存来触发告警"
        echo "按Ctrl+C停止测试"
        echo ""

        # 创建内存压力 (消耗约1GB内存)
        stress --vm 1 --vm-bytes 1G --timeout 30

        echo "✅ 内存压力测试完成"
        ;;

    3)
        echo "🔌 模拟服务宕机测试..."
        echo "这将临时停止一个监控服务来触发告警"
        echo "注意: 这只是临时测试，不会影响实际服务"
        echo ""

        # 临时停止Grafana 10秒
        echo "临时停止Grafana 10秒..."
        docker stop grafana
        sleep 10
        docker start grafana

        echo "✅ 服务重启完成，请检查告警触发"
        ;;

    4)
        echo "📱 发送钉钉测试消息..."
        WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=3df74b9dd5f916bed39020e318f415cc5617f59041ba26aa50a8e823cd54a1fb"

        TEST_MESSAGE='{
          "msgtype": "markdown",
          "markdown": {
            "title": "告警测试消息",
            "text": "# 🧪 告警系统测试\n\n✅ 钉钉webhook连接正常\n\n⏰ 测试时间: '$(date)'\n\n📊 这是一条测试消息，验证告警通道是否畅通"
          },
          "at": {
            "isAtAll": false
          }
        }'

        if curl -s -X POST -H 'Content-type: application/json' --data "$TEST_MESSAGE" "$WEBHOOK_URL" > /dev/null; then
            echo "✅ 测试消息发送成功"
            echo "请检查钉钉群是否收到消息"
        else
            echo "❌ 测试消息发送失败"
            echo "请检查webhook URL和网络连接"
        fi
        ;;

    5)
        echo "📈 查看当前告警状态..."
        echo ""
        echo "Grafana Alerting状态: http://47.84.1.161:3000/alerting/list"
        echo ""
        echo "当前运行的告警规则:"

        # 检查Prometheus告警状态
        if curl -s http://localhost:9090/api/v1/alerts 2>/dev/null | grep -q "alertname"; then
            echo "📊 Prometheus告警状态:"
            curl -s http://localhost:9090/api/v1/alerts | jq '.data[] | {alertname: .labels.alertname, state: .state, severity: .labels.severity}' 2>/dev/null || echo "无法解析告警数据"
        else
            echo "📊 暂无活跃告警"
        fi

        echo ""
        echo "💡 提示: 在浏览器中访问Grafana查看详细状态"
        ;;

    *)
        echo "❌ 无效选择，请输入1-5之间的数字"
        exit 1
        ;;
esac

echo ""
echo "🎉 测试完成！"
echo "请检查Grafana和钉钉的告警状态"
echo "如有问题，请查看故障排除指南"
