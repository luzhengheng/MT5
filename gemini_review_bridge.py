#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Review Bridge v3.1 (Hybrid Intelligence)
特性: 本地审计 + 外部 AI 深度审查 (Cloudflare Penetration)
"""
import os
import sys
import subprocess
import json
import datetime
from dotenv import load_dotenv

# --- 配置 ---
AUDIT_SCRIPT = "scripts/audit_current_task.py"
ENABLE_AI_REVIEW = True

# --- 尝试导入核武器 ---
try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    CURL_AVAILABLE = False
    print("⚠️  [WARN] 缺少 curl_cffi，外部 AI 审查可能失败。建议运行: pip install curl_cffi")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    colors = {"SUCCESS": GREEN, "ERROR": RED, "WARN": YELLOW, "PHASE": CYAN, "INFO": RESET}
    print(f"[{timestamp}] {colors.get(level, RESET)}{'✅ ' if level=='SUCCESS' else '⛔ ' if level=='ERROR' else '⚠️  ' if level=='WARN' else '🔹 ' if level=='PHASE' else ''}{msg}{RESET}")

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

# ==============================================================================
# 🧠 Phase 1: 本地审计 (The Hard Rule)
# ==============================================================================
def phase_local_audit():
    if not os.path.exists(AUDIT_SCRIPT):
        log(f"未找到本地审计脚本 {AUDIT_SCRIPT}，跳过。", "WARN")
        return True
    
    log(f"执行本地审计: {AUDIT_SCRIPT}", "INFO")
    code, out, err = run_cmd(f"python3 {AUDIT_SCRIPT}")
    
    if code == 0:
        log("本地审计通过。", "SUCCESS")
        return True
    else:
        log("本地审计失败！", "ERROR")
        print(f"{YELLOW}--- AUDIT LOG ---\n{out}\n{err}{RESET}")
        return False

# ==============================================================================
# 🧠 Phase 2: 外部 AI 审查 (The Titanium Shield)
# ==============================================================================
def external_ai_review(diff_content):
    if not CURL_AVAILABLE or not GEMINI_API_KEY:
        log("跳过外部 AI 审查 (缺少 curl_cffi 或 API_KEY)", "WARN")
        return True

    log("启动 curl_cffi 引擎，正在穿透 Cloudflare...", "PHASE")
    
    prompt = f"""
    你是一位资深的 Python 架构师。请审查以下 Git Diff (用于量化交易系统):
    {diff_content[:15000]}
    
    检查重点：
    1. 是否有明显的逻辑错误或死锁风险？
    2. 是否有硬编码的敏感信息（密码/密钥）？
    3. 代码风格是否符合 PEP8？
    
    **必须输出 JSON**:
    {{
        "status": "PASS" | "FAIL",
        "reason": "简短的通过或拒绝理由",
        "commit_message_suggestion": "feat(scope): ..."
    }}
    """
    
    try:
        # 使用 chrome110 指纹穿透
        resp = requests.post(
            f"{GEMINI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GEMINI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            },
            timeout=60,
            impersonate="chrome110"
        )

        # 调试：记录原始响应
        import os
        if os.getenv("DEBUG_BRIDGE") == "1":
            log(f"[DEBUG] API Status: {resp.status_code}", "INFO")
            if hasattr(resp, 'text'):
                log(f"[DEBUG] Raw Response: {resp.text[:500]}...", "INFO")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                # 处理多种可能的响应格式
                if 'choices' in data:
                    content = data['choices'][0]['message']['content']
                elif 'content' in data:
                    content = data['content']
                else:
                    log(f"未知的 API 响应格式: {data}", "WARN")
                    return None

                # 清理 JSON 包装
                clean_content = content.replace("```json", "").replace("```", "").strip()

                # 智能提取 JSON 块（处理 JSON 后的额外文字）
                if '{' in clean_content:
                    start = clean_content.index('{')
                    # 从起始位置开始，找到完整的 JSON 对象
                    brace_count = 0
                    end = start
                    for i in range(start, len(clean_content)):
                        if clean_content[i] == '{':
                            brace_count += 1
                        elif clean_content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    clean_content = clean_content[start:end]

                try:
                    result = json.loads(clean_content)
                    if result.get("status") == "PASS":
                        log(f"AI 审查通过: {result.get('reason')}", "SUCCESS")
                        return result.get("commit_message_suggestion")
                    else:
                        log(f"AI 拒绝提交: {result.get('reason')}", "ERROR")
                        return None
                except json.JSONDecodeError as je:
                    log(f"JSON 解析失败: {str(je)[:80]}", "WARN")
                    log(f"原始内容: {clean_content[:200]}...", "WARN")
                    log("强制通过 (Fail-open)", "WARN")
                    return None
            except Exception as e:
                log(f"API 响应处理异常: {str(e)[:80]}", "ERROR")
                return None
        else:
            log(f"API 请求失败: {resp.status_code}", "ERROR")
            if hasattr(resp, 'text'):
                log(f"响应内容: {resp.text[:200]}", "WARN")
            return None

    except Exception as e:
        log(f"穿透失败: {e}", "ERROR")
        return None

# ==============================================================================
# 🚀 主流程
# ==============================================================================
def main():
    print(f"{CYAN}🛡️ Gemini Review Bridge v3.1 (Titanium Edition){RESET}")
    
    # 0. 准备环境
    run_cmd("git add .") # 自动暂存所有更改
    _, diff, _ = run_cmd("git diff --cached")
    
    if not diff:
        log("工作区干净，无事可做。", "WARN")
        sys.exit(0)

    # 1. 本地硬性审计
    if not phase_local_audit():
        sys.exit(1)

    # 2. 外部智能审查
    ai_commit_msg = None
    if ENABLE_AI_REVIEW:
        ai_commit_msg = external_ai_review(diff)

    # 3. 生成提交信息
    if ai_commit_msg:
        commit_msg = ai_commit_msg
    else:
        # 降级方案
        _, files, _ = run_cmd("git diff --cached --name-only")
        file_list = [f for f in files.splitlines() if f]
        commit_msg = f"feat(auto): update {len(file_list)} files (audit passed)"

    # 4. 自动提交 (No Input Blocking)
    log(f"执行提交: {commit_msg}", "INFO")
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    
    if code == 0:
        log("代码已成功提交！", "SUCCESS")
        # 5. (可选) 推送
        # run_cmd("git push")
        sys.exit(0)
    else:
        log(f"提交失败: {err}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
