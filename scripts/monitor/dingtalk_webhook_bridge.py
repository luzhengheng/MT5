#!/usr/bin/env python3
"""
钉钉告警 Webhook 桥接服务
接收 Prometheus Alertmanager 告警,转发到钉钉群
"""

import json
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 钉钉 Webhook URL
DINGTALK_WEBHOOK = 'https://oapi.dingtalk.com/robot/send?access_token=3df74b9dd5f916bed39020e318f415cc5617f59041ba26aa50a8e823cd54a1fb'

# 告警级别对应的emoji
SEVERITY_EMOJI = {
    'critical': '🔴',
    'warning': '🟡',
    'info': '🔵'
}

def format_alert_message(data):
    """将 Alertmanager 告警格式化为钉钉消息"""
    alerts = data.get('alerts', [])

    if not alerts:
        return None

    # 获取告警状态
    status = data.get('status', 'firing')

    # 构建消息
    message_lines = []
    message_lines.append(f"# {'🔔 告警触发' if status == 'firing' else '✅ 告警恢复'}")
    message_lines.append("")

    for alert in alerts:
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})

        # 获取关键信息
        alertname = labels.get('alertname', 'Unknown')
        severity = labels.get('severity', 'info')
        service = labels.get('service', 'N/A')
        instance = labels.get('instance', 'N/A')

        # 获取描述信息
        summary = annotations.get('summary', '')
        description = annotations.get('description', '')

        # 格式化单个告警
        emoji = SEVERITY_EMOJI.get(severity, '⚪')
        message_lines.append(f"## {emoji} {alertname}")
        message_lines.append("")
        message_lines.append(f"**告警级别**: {severity.upper()}")

        if service != 'N/A':
            message_lines.append(f"**服务**: {service}")

        if instance != 'N/A':
            message_lines.append(f"**实例**: {instance}")

        if summary:
            message_lines.append(f"**摘要**: {summary}")

        if description:
            message_lines.append(f"**详情**: {description}")

        # 添加告警时间
        starts_at = alert.get('startsAt', '')
        if starts_at:
            try:
                dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                message_lines.append(f"**触发时间**: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                pass

        message_lines.append("")
        message_lines.append("---")
        message_lines.append("")

    # 添加footer
    message_lines.append(f"🤖 MT5 Hub 监控系统")
    message_lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(message_lines)

def send_to_dingtalk(message):
    """发送消息到钉钉"""
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "MT5 Hub 监控告警",
            "text": message
        },
        "at": {
            "isAtAll": False
        }
    }

    try:
        response = requests.post(
            DINGTALK_WEBHOOK,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()

        result = response.json()
        if result.get('errcode') == 0:
            logger.info("消息发送成功")
            return True
        else:
            logger.error(f"钉钉返回错误: {result}")
            return False
    except Exception as e:
        logger.error(f"发送到钉钉失败: {e}")
        return False

@app.route('/alert', methods=['POST'])
def receive_alert():
    """接收 Alertmanager webhook"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        logger.info(f"收到告警: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # 格式化消息
        message = format_alert_message(data)

        if not message:
            logger.warning("没有告警需要发送")
            return jsonify({"status": "no alerts"}), 200

        # 发送到钉钉
        if send_to_dingtalk(message):
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed"}), 500

    except Exception as e:
        logger.error(f"处理告警失败: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "healthy"}), 200

@app.route('/test', methods=['POST'])
def test():
    """测试接口"""
    test_message = """# 🧪 钉钉告警测试

## ✅ 测试消息

**状态**: 正常
**时间**: {}

---

🤖 MT5 Hub 监控系统
⏰ 测试成功
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if send_to_dingtalk(test_message):
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failed"}), 500

if __name__ == '__main__':
    logger.info("🚀 启动钉钉告警 Webhook 桥接服务...")
    logger.info(f"📡 监听端口: 5001")
    logger.info(f"📮 钉钉 Webhook: {DINGTALK_WEBHOOK[:50]}...")

    app.run(host='0.0.0.0', port=5001, debug=False)
