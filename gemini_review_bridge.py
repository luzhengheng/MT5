#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime

# --- 核心配置 ---
# 这是唯一的验收标准入口
AUDIT_SCRIPT = "scripts/audit_current_task.py"

# --- ANSI 颜色配置 (让 CLI 日志更清晰) ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if level == "SUCCESS":
        print(f"[{timestamp}] {GREEN}✅ {msg}{RESET}")
    elif level == "ERROR":
        print(f"[{timestamp}] {RED}⛔ {msg}{RESET}")
    elif level == "WARN":
        print(f"[{timestamp}] {YELLOW}⚠️  {msg}{RESET}")
    elif level == "PHASE":
        print(f"\n[{timestamp}] {CYAN}🔹 {msg}{RESET}")
    else:
        print(f"[{timestamp}] ℹ️  {msg}")

def run_cmd(cmd, shell=True):
    """
    运行系统命令并捕获所有输出。
    返回: (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def phase_audit():
    """
    第一阶段：审计 (Quality Gate)
    """
    log("启动审计程序...", "PHASE")
    
    if not os.path.exists(AUDIT_SCRIPT):
        log(f"未找到审计脚本: {AUDIT_SCRIPT}", "WARN")
        log("跳过逻辑验证 (仅在没有特定审计要求时允许)", "INFO")
        return True
    
    log(f"发现审计脚本，正在执行验收: {AUDIT_SCRIPT}", "INFO")
    code, out, err = run_cmd(f"python3 {AUDIT_SCRIPT}")
    
    if code == 0:
        log("审计通过！业务逻辑验证成功。", "SUCCESS")
        if out: 
            print(f"{GREEN}--- 审计日志 ---{RESET}")
            print(out)
            print(f"{GREEN}----------------{RESET}")
        return True
    else:
        log("审计失败！拦截提交。", "ERROR")
        print(f"\n{RED}================ 错误详情 (CLAUDE ATTENTION) ================{RESET}")
        print(f"{YELLOW}Exit Code:{RESET} {code}")
        if out: 
            print(f"{YELLOW}STDOUT:{RESET}\n{out}")
        if err: 
            print(f"{YELLOW}STDERR (Bug Location):{RESET}\n{err}")
        print(f"{RED}============================================================={RESET}")
        print(f"💡 指导: 请阅读上面的报错信息，修复 'src/' 代码或 'scripts/' 逻辑，然后重试。")
        return False

def phase_commit():
    """
    第二阶段：提交 (Auto Commit)
    """
    log("准备提交代码...", "PHASE")
    
    # 1. 获取变更文件列表用于 Commit Message
    _, out, _ = run_cmd("git diff --cached --name-only")
    files = [f.split('/')[-1] for f in out.splitlines() if f]
    
    if not files:
        # 如果缓存区为空，先 add . 再看一遍
        run_cmd("git add .")
        _, out, _ = run_cmd("git diff --cached --name-only")
        files = [f.split('/')[-1] for f in out.splitlines() if f]
    
    # 2. 生成 Commit Message
    timestamp = datetime.datetime.now().strftime("%H:%M")
    if not files:
        commit_msg = f"feat(auto): general update (audit passed at {timestamp})"
    else:
        file_str = ", ".join(files[:3])
        if len(files) > 3: file_str += f" (+{len(files)-3} files)"
        commit_msg = f"feat(auto): update {file_str} (audit passed)"

    # 3. 执行 Git Commit
    log(f"执行 Git Commit: '{commit_msg}'", "INFO")
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    
    if code == 0:
        log("代码提交成功！", "SUCCESS")
        print(out)
        return True
    else:
        log("Git 提交失败！", "ERROR")
        print(err)
        return False

def main():
    print(f"{CYAN}🚀 Gemini Review Bridge (Iron Judge Edition) 启动...{RESET}")
    
    # 0. 预检查
    code, out, _ = run_cmd("git status --porcelain")
    if not out:
        log("工作区干净，无事可做。", "WARN")
        sys.exit(0)

    # 1. 必须通过审计，否则直接死刑 (Exit 1)
    if not phase_audit():
        sys.exit(1)

    # 2. 只有审计通过，才执行提交
    # 确保所有变更都加入暂存区
    run_cmd("git add .")
    
    if not phase_commit():
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
