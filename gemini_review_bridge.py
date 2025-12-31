#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Review Bridge v3.3 (Insightful Edition)
架构目标: 
1. 穿透 Cloudflare (Titanium Shield).
2. 精准提取 JSON 用于控制脚本流程 (Pass/Fail).
3. 保留并展示 AI 的架构点评，供 Claude 学习改进.
"""
import os
import sys
import subprocess
import json
import datetime
import re
from dotenv import load_dotenv

# --- 核心配置 ---
AUDIT_SCRIPT = "scripts/audit_current_task.py"
ENABLE_AI_REVIEW = True # 开启云端大脑

# --- 尝试导入核武器 (curl_cffi) ---
try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    CURL_AVAILABLE = False
    print("⚠️  [WARN] 缺少 curl_cffi，建议运行: pip install curl_cffi")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# --- UI 颜色配置 ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"  # AI 点评专用色
RESET = "\033[0m"

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    colors = {"SUCCESS": GREEN, "ERROR": RED, "WARN": YELLOW, "PHASE": CYAN, "INFO": RESET}
    prefix = {'SUCCESS': '✅ ', 'ERROR': '⛔ ', 'WARN': '⚠️  ', 'PHASE': '🔹 '}.get(level, '')
    print(f"[{timestamp}] {colors.get(level, RESET)}{prefix}{msg}{RESET}")

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def extract_json_and_comments(text):
    """
    智能分离器：从 AI 的回复中拆分出 JSON (给机器看) 和 点评 (给 Claude 看)
    返回: (json_obj, comment_text)
    """
    json_obj = None
    comment_text = ""

    # 1. 使用栈平衡法寻找第一个完整的 JSON 对象 {...}
    stack = 0
    start_index = -1
    end_index = -1
    
    for i, char in enumerate(text):
        if char == '{':
            if stack == 0: start_index = i
            stack += 1
        elif char == '}':
            stack -= 1
            if stack == 0 and start_index != -1:
                end_index = i + 1
                # 尝试解析找到的这一段
                try:
                    candidate = text[start_index : end_index]
                    json_obj = json.loads(candidate)
                    # 提取成功！剩下的全是评论
                    if end_index < len(text):
                        comment_text = text[end_index:].strip()
                    return json_obj, comment_text
                except:
                    continue # 解析失败，可能是个假括号，继续找
    
    # 2. 兜底：如果没找到复杂的，尝试把整段当 JSON
    if not json_obj:
        try:
            json_obj = json.loads(text)
        except:
            pass
            
    return json_obj, comment_text

# ==============================================================================
# 🧠 Phase 1: 本地审计 (硬性门槛)
# ==============================================================================
def phase_local_audit():
    if not os.path.exists(AUDIT_SCRIPT):
        log(f"未找到本地审计脚本，跳过。", "WARN")
        return True
    
    log(f"执行本地审计: {AUDIT_SCRIPT}", "INFO")
    code, out, err = run_cmd(f"python3 {AUDIT_SCRIPT}")
    
    if code == 0:
        log("本地审计通过。", "SUCCESS")
        return True
    else:
        log("本地审计失败！阻止提交。", "ERROR")
        print(f"{YELLOW}--- AUDIT LOG ---\n{out}\n{err}{RESET}")
        return False

# ==============================================================================
# 🧠 Phase 2: 外部 AI 深度审查 (核心逻辑)
# ==============================================================================
def external_ai_review(diff_content):
    if not CURL_AVAILABLE or not GEMINI_API_KEY:
        log("跳过 AI 审查 (缺少配置或依赖)", "WARN")
        return None

    log("启动 curl_cffi 引擎，请求架构师审查...", "PHASE")
    
    # Prompt: 明确要求 JSON 在前，评论在后
    prompt = f"""
    你是一位严厉的 Python 架构师。请审查以下 Git Diff:
    {diff_content[:15000]}
    
    **输出格式要求 (严格遵守)**:
    1. 第一部分：必须是一个标准的 JSON 对象。
    2. 第二部分（可选）：JSON 结束后，你可以用 Markdown 写出详细的改进建议、风险警告或重构思路。
    
    JSON 结构：
    {{
        "status": "PASS" | "FAIL",
        "reason": "一句话总结",
        "commit_message_suggestion": "feat(scope): ..."
    }}
    """
    
    try:
        resp = requests.post(
            f"{GEMINI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GEMINI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3 
            },
            timeout=60,
            impersonate="chrome110" 
        )
        
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            
            # 使用分离器处理
            result, comments = extract_json_and_comments(content)
            
            if result:
                status = result.get("status", "FAIL")
                
                # --- 🔥 关键：展示 AI 的“话痨”部分给 Claude 看 ---
                if comments:
                    print(f"\n{BLUE}================ 🧠 架构师点评 (AI Feedback) ================{RESET}")
                    print(f"{CYAN}{comments}{RESET}")
                    print(f"{BLUE}============================================================={RESET}\n")
                else:
                    print(f"\n{BLUE}ℹ️  架构师没有提供额外评论。{RESET}\n")
                # ----------------------------------------------------

                if status == "PASS":
                    log(f"AI 审查通过: {result.get('reason')}", "SUCCESS")
                    return result.get("commit_message_suggestion")
                else:
                    log(f"AI 拒绝提交: {result.get('reason')}", "ERROR")
                    return "FAIL" 
            else:
                log("无法解析 AI 响应格式，降级通过。", "WARN")
                return None
        else:
            log(f"API 请求失败: {resp.status_code}", "ERROR")
            return None

    except requests.ConnectTimeout:
        log(f"连接超时: 无法连接API服务器 (timeout=60s)", "ERROR")
        log(f"请检查网络连接和API地址: {GEMINI_BASE_URL}", "ERROR")
        return None

    except requests.ReadTimeout:
        log(f"读取超时: API服务器响应过慢 (timeout=60s)", "ERROR")
        log(f"请检查网络连接或稍后重试", "ERROR")
        return None

    except requests.RequestException as e:
        log(f"网络错误: {e}", "ERROR")
        log(f"API地址: {GEMINI_BASE_URL}", "ERROR")
        log(f"请检查网络连接并重试", "ERROR")
        return None

    except Exception as e:
        log(f"AI审查失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None

# ==============================================================================
# 🚀 主流程
# ==============================================================================
def main():
    print(f"{CYAN}🛡️ Gemini Review Bridge v3.3 (Insightful Edition){RESET}")
    
    # 0. 自动暂存
    run_cmd("git add .")
    _, diff, _ = run_cmd("git diff --cached")
    
    if not diff:
        log("工作区干净，无代码变更。", "WARN")
        sys.exit(0)

    # 1. 本地审计 (Claude 自测)
    if not phase_local_audit():
        sys.exit(1)

    # 2. 外部 AI 审查 (架构师把关)
    ai_commit_msg = None
    if ENABLE_AI_REVIEW:
        log("=" * 80, "INFO")
        log("启动外部AI审查...", "PHASE")
        log("=" * 80, "INFO")
        print()

        review_result = external_ai_review(diff)

        if review_result == "FAIL":
            print()
            print(f"{RED}{'=' * 80}{RESET}")
            log("AI审查拒绝提交", "ERROR")
            print(f"{RED}{'=' * 80}{RESET}")
            log("修复上述问题后重新运行finish命令", "ERROR")
            sys.exit(1)  # AI 明确拒绝，阻断提交

        elif review_result is None:
            print()
            print(f"{YELLOW}{'=' * 80}{RESET}")
            log("AI审查服务不可用", "WARN")
            print(f"{YELLOW}{'=' * 80}{RESET}")
            log("可能原因:", "WARN")
            log("  - 网络连接失败", "WARN")
            log("  - API密钥无效或未设置", "WARN")
            log("  - API服务器无响应", "WARN")
            print()
            log("将继续使用本地提交信息", "WARN")
            print(f"{YELLOW}{'=' * 80}{RESET}")
            print()

        ai_commit_msg = review_result

    # 3. 决定提交信息
    if ai_commit_msg:
        commit_msg = ai_commit_msg
    else:
        # 降级或 AI 故障时的默认信息
        _, files, _ = run_cmd("git diff --cached --name-only")
        cnt = len([f for f in files.splitlines() if f])
        commit_msg = f"feat(auto): update {cnt} files (local audit passed)"

    # 4. 执行提交
    log(f"执行提交: {commit_msg}", "INFO")
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    
    if code == 0:
        log("代码已成功提交！", "SUCCESS")
        sys.exit(0)
    else:
        log(f"提交失败: {err}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
