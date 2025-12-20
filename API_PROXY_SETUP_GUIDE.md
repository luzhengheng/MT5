# 🌐 API 中转服务设置指南

## 🎯 解决 Gemini API 配额问题

由于您的 Gemini API 配额已用完，这里有几种解决方案：

## 🚀 方案 1: 使用免费中转服务 (推荐)

### 选项 1A: OpenAI-SB (免费额度)
```bash
# 注册获取免费 API Key
# 网站: https://openai-sb.com/

# 配置到 .env 文件
PROXY_API_KEY=sk-your-free-api-key-here
```

### 选项 1B: AI Proxy (免费试用)
```bash
# 注册获取免费 API Key
# 网站: https://aiproxy.io/

# 配置到 .env 文件
PROXY_API_KEY=sk-your-aiproxy-key-here
```

### 选项 1C: DeepSeek (国产免费)
```bash
# 注册获取免费 API Key
# 网站: https://platform.deepseek.com/

# 配置到 .env 文件
PROXY_API_KEY=sk-your-deepseek-key-here
```

## 🔧 方案 2: 使用 Cloudflare Workers (自建)

### 步骤 1: 创建 Cloudflare Workers
1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 "Workers & Pages"
3. 点击 "Create application"
4. 选择 "Create Worker"

### 步骤 2: 部署中转代码
```javascript
// worker.js
export default {
    async fetch(request, env) {
        if (request.method !== 'POST') {
            return new Response('Method not allowed', { status: 405 });
        }

        try {
            const body = await request.json();
            const model = body.model || 'gemini-2.0-flash-exp';

            // 使用 DeepSeek 作为后端 (免费)
            const deepseekResponse = await fetch('https://api.deepseek.com/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: 'deepseek-chat',
                    messages: body.messages,
                    temperature: body.temperature || 0.7,
                    max_tokens: body.max_tokens || 4000,
                }),
            });

            if (deepseekResponse.ok) {
                const result = await deepseekResponse.json();
                return new Response(JSON.stringify(result), {
                    headers: { 'Content-Type': 'application/json' },
                });
            }

            return new Response('Backend error', { status: 500 });
        } catch (error) {
            return new Response(error.message, { status: 500 });
        }
    }
};
```

### 步骤 3: 配置环境变量
在 Cloudflare Workers 设置中添加：
- `DEEPSEEK_API_KEY`: 您的 DeepSeek API Key

### 步骤 4: 部署并配置
1. 部署 Worker
2. 复制 Workers URL
3. 配置到 .env 文件：
   ```env
   PROXY_API_URL=https://your-worker.your-subdomain.workers.dev
   PROXY_API_KEY=dummy-key
   ```

## 🛠️ 方案 3: 使用本地模型 (高级)

### 安装 Ollama
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull qwen2.5-coder:7b
```

### 创建本地 API 服务
```python
# local_api_server.py
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    messages = data.get('messages', [])

    # 转换为 Ollama 格式
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    # 调用本地 Ollama
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'qwen2.5-coder:7b',
        'prompt': prompt,
        'stream': False
    })

    if response.ok:
        result = response.json()
        return jsonify({
            'choices': [{
                'message': {
                    'content': result['response']
                }
            }]
        })

    return jsonify({'error': 'Request failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## ⚡ 快速设置 (推荐 DeepSeek)

### 1. 注册 DeepSeek
```bash
# 访问: https://platform.deepseek.com/
# 免费注册，送 $10 额度
```

### 2. 获取 API Key
```bash
# 在控制台获取 API Key
# 格式: sk-xxxxxxxxxxxxxxxx
```

### 3. 配置环境
```bash
# 编辑 .env 文件
nano /opt/mt5-crs/.env

# 替换这行：
PROXY_API_KEY=your_proxy_api_key_here
# 改为：
PROXY_API_KEY=sk-your-deepseek-api-key
```

### 4. 测试中转服务
```bash
# 停止当前运行的 nexus_simple.py
# 启动支持中转的版本
python3 /opt/mt5-crs/nexus_with_proxy.py
```

## 🧪 测试 API 连接

### 测试脚本
```bash
python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('PROXY_API_KEY')

if api_key and not api_key.startswith('your_'):
    print('✅ 代理 API Key 已配置')

    # 测试 DeepSeek
    try:
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10
            },
            timeout=10
        )
        if response.status_code == 200:
            print('✅ DeepSeek API 连接成功')
        else:
            print(f'❌ DeepSeek API 连接失败: {response.status_code}')
    except Exception as e:
        print(f'❌ 测试失败: {e}')
else:
    print('❌ 代理 API Key 未配置')
"
```

## 🔄 切换不同方案

### 使用本地模型
```env
PROXY_API_KEY=dummy
PROXY_API_URL=http://localhost:8080
```

### 使用 Cloudflare Workers
```env
PROXY_API_KEY=dummy
PROXY_API_URL=https://your-worker.workers.dev
```

### 使用 DeepSeek
```env
PROXY_API_KEY=sk-your-deepseek-key
PROXY_API_URL=
```

## 📋 推荐配置优先级

1. **DeepSeek** (推荐) - 免费，高质量，中文好
2. **OpenAI-SB** - 免费额度，稳定
3. **Cloudflare Workers** - 自由控制，技术门槛高
4. **本地模型** - 完全免费，需要好的硬件

---

**选择最适合您的方案，配置后即可继续使用 Notion Nexus！** 🚀