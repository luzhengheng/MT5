#!/usr/bin/env python3
"""
[审计脚本标准模版] - Reference Only
用于指导 Claude CLI 生成 audit_current_task.py。
所有的审计脚本都必须参考此结构。
"""
import sys
import os

# --- 辅助函数：让输出带颜色，方便 CLI 识别 ---
def log_success(msg):
    print(f"\033[92m✅ {msg}\033[0m")

def log_fail(msg):
    print(f"\033[91m❌ {msg}\033[0m")

def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        log_fail(f"文件缺失: {filepath}")
        sys.exit(1)
    log_success(f"文件存在: {filepath}")

def check_keywords_in_file(filepath, keywords):
    """检查文件中是否包含核心业务逻辑关键字"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing = []
        for kw in keywords:
            if kw not in content:
                missing.append(kw)
        
        if missing:
            log_fail(f"完整性校验失败: {filepath}")
            log_fail(f"    -> 缺失关键字: {missing}")
            sys.exit(1)
        
        log_success(f"内容校验通过 (包含: {keywords})")
        
    except Exception as e:
        log_fail(f"读取文件出错: {e}")
        sys.exit(1)

def main():
    print("🕵️‍♂️ 启动任务审计程序 (Audit Task)...")
    
    # ---------------------------------------------------------
    # 1. 定义本次任务的目标文件 (由 Claude 根据实际任务修改)
    # ---------------------------------------------------------
    # [示例] TARGET_FILE = "src/gateway/mt5_service.py"
    TARGET_FILE = "YOUR_TARGET_FILE_HERE.py" 
    
    # ---------------------------------------------------------
    # 2. 执行基础检查
    # ---------------------------------------------------------
    check_file_exists(TARGET_FILE)
    
    # ---------------------------------------------------------
    # 3. 执行业务逻辑检查 (Keyword Smell Test)
    # ---------------------------------------------------------
    # 这里必须包含能够证明任务“真正完成”的硬核特征
    # [示例] REQUIRED_KEYWORDS = ["class MT5Service", "def connect", "ZeroMQ"]
    REQUIRED_KEYWORDS = [
        "KEYWORD_1", 
        "KEYWORD_2"
    ]
    check_keywords_in_file(TARGET_FILE, REQUIRED_KEYWORDS)
    
    # ---------------------------------------------------------
    # 4. 最终放行
    # ---------------------------------------------------------
    print("-" * 30)
    log_success("审计通过！允许 Gemini Review Bridge 提交代码。")
    sys.exit(0) # 只有 Exit 0 才会触发 Git Commit

if __name__ == "__main__":
    main()
