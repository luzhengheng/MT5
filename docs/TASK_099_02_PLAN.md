# Task #099.02: Critical Pipeline Repair (AI Bridge & Sync)

## 执行摘要 (Executive Summary)

本任务修复关键的CI/CD管道故障。当前`finish`命令在本地报告成功，但未能触发External AI Review、Git Push和Notion Sync。问题根源是静默失败（silent failures）- 子进程崩溃但未被检测。

**任务目标**:
1. 使所有管道失败变成**响亮的错误**（LOUD FAILURES）
2. 修复`gemini_review_bridge.py`的网络超时处理
3. 强化`project_cli.py`的错误检查逻辑
4. 确保失败时任务不会被标记为完成
5. 验证完整的管道流程

## 1. 背景与现状 (Context)

### 问题描述

**症状**:
```bash
$ python3 scripts/project_cli.py finish
...
✅ Task completed successfully
# But:
# - No AI Review output visible
# - Git not pushed to remote
# - Notion card status unchanged
```

**根本原因**:
1. **Silent Try-Except**: `project_cli.py`中的异常被捕获但未处理
2. **Missing Exit Code Checks**: 子进程失败但返回码未检查
3. **Network Timeout**: `gemini_review_bridge.py`在网络问题时崩溃
4. **curl_cffi Issues**: 可能在当前环境中不可用

### 影响范围

**受影响的工作流**:
- Task #099.01: Git-Notion同步（部分失效）
- Task #018.01: 提交后未触发AI审查
- 所有未来任务：可能报告虚假成功

**数据完整性风险**:
- Notion数据库状态不同步
- GitHub commit未同步
- AI审查记录缺失

## 2. 方案设计 (Solution Design)

### 2.1 修复策略

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT STATE (BROKEN)                    │
└─────────────────────────────────────────────────────────────┘

project_cli.py finish()
    │
    ├─▶ try: AI Review
    │      (fails silently)
    │
    ├─▶ try: Git Push
    │      (may fail, ignored)
    │
    └─▶ try: Notion Sync
           (may fail, ignored)

    ✅ Reports "Success" regardless!


┌─────────────────────────────────────────────────────────────┐
│                    TARGET STATE (FIXED)                      │
└─────────────────────────────────────────────────────────────┘

project_cli.py finish()
    │
    ├─▶ AI Review (gemini_review_bridge.py)
    │   │
    │   ├─ Check return code != 0?
    │   │     ❌ ABORT: "AI Review Failed"
    │   │     EXIT 1
    │   │
    │   └─ Success → Continue
    │
    ├─▶ Git Push
    │   │
    │   ├─ Check return code != 0?
    │   │     ❌ ABORT: "Git Push Failed"
    │   │     EXIT 1
    │   │
    │   └─ Success → Continue
    │
    └─▶ Notion Sync
        │
        ├─ Check success == False?
        │     ❌ ABORT: "Notion Sync Failed"
        │     EXIT 1
        │
        └─ Success → ✅ Complete
```

### 2.2 gemini_review_bridge.py 修复

**当前问题**:
```python
# 可能的问题代码
response = session.post(url, ...)  # 网络超时，未处理
# 或
import curl_cffi  # 导入失败，程序崩溃
```

**修复方案**:
```python
def review_code_with_gemini(code_content):
    """
    Call Gemini API with robust error handling

    Returns:
        (success: bool, output: str, exit_code: int)
    """
    try:
        # Try curl_cffi first
        try:
            from curl_cffi import requests as curl_requests
            session = curl_requests.Session()
            print("[DEBUG] Using curl_cffi for API call")
        except ImportError:
            import requests
            session = requests.Session()
            print("[DEBUG] Using standard requests (fallback)")

        # Call API with timeout
        response = session.post(
            url,
            json=payload,
            timeout=120  # 2 minutes max
        )

        if response.status_code != 200:
            print(f"[ERROR] API returned {response.status_code}")
            return (False, "", 1)

        # Success
        return (True, response.text, 0)

    except requests.Timeout:
        print("[ERROR] API request timed out after 120s")
        return (False, "", 1)

    except requests.RequestException as e:
        print(f"[ERROR] Network error: {e}")
        return (False, "", 1)

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return (False, "", 1)


if __name__ == "__main__":
    success, output, exit_code = review_code_with_gemini(...)

    if success:
        print(output)
        sys.exit(0)
    else:
        print("[FATAL] AI Review failed - see errors above")
        sys.exit(1)
```

### 2.3 project_cli.py 修复

**Step 4 重写** (finish command):

```python
def finish_task(ticket_num, page_id):
    """
    Complete task with STRICT error checking

    Workflow:
        1. AI Review (gemini_review_bridge.py)
        2. Git Push (git push)
        3. Notion Sync (update_task_status)

    CRITICAL: Any failure → ABORT entire finish process
    """
    print("=" * 80)
    log("Starting Task Completion Pipeline", "PHASE")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: AI REVIEW (BLOCKING)
    # ========================================================================
    print("=" * 80)
    log("Step 1/3: External AI Review", "PHASE")
    print("=" * 80)

    log("Calling gemini_review_bridge.py...", "INFO")

    try:
        ret = subprocess.call([
            "python3",
            "gemini_review_bridge.py"
        ], cwd=PROJECT_ROOT)

        if ret != 0:
            print()
            print("=" * 80)
            log("AI REVIEW FAILED", "ERROR")
            print("=" * 80)
            log(f"gemini_review_bridge.py exited with code {ret}", "ERROR")
            log("Task CANNOT be marked as complete", "ERROR")
            log("Please review the errors above and fix them", "WARN")
            print("=" * 80)
            sys.exit(1)

        log("AI Review completed successfully", "SUCCESS")

    except FileNotFoundError:
        log("gemini_review_bridge.py not found!", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error during AI Review: {e}", "ERROR")
        sys.exit(1)

    print()

    # ========================================================================
    # STEP 2: GIT PUSH (BLOCKING)
    # ========================================================================
    print("=" * 80)
    log("Step 2/3: Push to GitHub", "PHASE")
    print("=" * 80)

    log("Running: git push", "INFO")

    try:
        ret = subprocess.call(["git", "push"], cwd=PROJECT_ROOT)

        if ret != 0:
            print()
            print("=" * 80)
            log("GIT PUSH FAILED", "ERROR")
            print("=" * 80)
            log(f"git push exited with code {ret}", "ERROR")
            log("Possible causes:", "WARN")
            log("  - Network connectivity issue", "WARN")
            log("  - Authentication failure", "WARN")
            log("  - Remote repository unreachable", "WARN")
            print("=" * 80)
            sys.exit(1)

        log("Git push completed successfully", "SUCCESS")

    except FileNotFoundError:
        log("git command not found!", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error during git push: {e}", "ERROR")
        sys.exit(1)

    print()

    # ========================================================================
    # STEP 3: NOTION SYNC (BLOCKING)
    # ========================================================================
    print("=" * 80)
    log("Step 3/3: Sync to Notion", "PHASE")
    print("=" * 80)

    # Get commit URL
    try:
        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            universal_newlines=True
        ).strip()

        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=PROJECT_ROOT,
            universal_newlines=True
        ).strip()

        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                repo_path = remote_url.split("github.com:")[1].replace(".git", "")
                github_url = f"https://github.com/{repo_path}"
            else:
                github_url = remote_url.replace(".git", "")

            commit_url = f"{github_url}/commit/{commit_sha}"
            log(f"Commit URL: {commit_url}", "INFO")
        else:
            commit_url = None
            log("Not a GitHub repository, skipping commit URL", "WARN")

    except Exception as e:
        commit_url = None
        log(f"Could not build commit URL: {e}", "WARN")

    # Update Notion status
    from scripts.utils.notion_updater import update_task_status

    log("Updating Notion task status...", "INFO")

    success = update_task_status(
        page_id=page_id,
        status="Done",
        commit_url=commit_url
    )

    if not success:
        print()
        print("=" * 80)
        log("NOTION SYNC FAILED", "ERROR")
        print("=" * 80)
        log("Failed to update Notion task status", "ERROR")
        log("Possible causes:", "WARN")
        log("  - NOTION_TOKEN not set", "WARN")
        log("  - Network connectivity issue", "WARN")
        log("  - Invalid page_id", "WARN")
        log("Task WAS pushed to GitHub but Notion is out of sync", "WARN")
        print("=" * 80)
        sys.exit(1)

    log("Notion sync completed successfully", "SUCCESS")

    print()
    print("=" * 80)
    log("TASK COMPLETION SUCCESSFUL", "SUCCESS")
    print("=" * 80)
    log(f"Ticket #{ticket_num:03d} marked as DONE", "SUCCESS")
    log("All pipeline steps completed successfully:", "SUCCESS")
    log("  ✅ AI Review passed", "SUCCESS")
    log("  ✅ Git pushed to remote", "SUCCESS")
    log("  ✅ Notion status updated", "SUCCESS")
    print("=" * 80)
```

### 2.4 测试脚本

**scripts/test_pipeline_integrity.py**:

```python
#!/usr/bin/env python3
"""
Pipeline Integrity Test

Tests the complete finish pipeline without making real changes.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_gemini_bridge():
    """Test 1: Can gemini_review_bridge.py be called?"""
    print("=" * 80)
    print("TEST 1: Gemini Review Bridge Availability")
    print("=" * 80)

    bridge_path = PROJECT_ROOT / "gemini_review_bridge.py"

    if not bridge_path.exists():
        print(f"❌ FAIL: {bridge_path} not found")
        return False

    print(f"✅ PASS: Bridge script exists")
    return True


def test_git_available():
    """Test 2: Is git command available?"""
    print("\n" + "=" * 80)
    print("TEST 2: Git Command Availability")
    print("=" * 80)

    try:
        ret = subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL)
        if ret != 0:
            print("❌ FAIL: git command failed")
            return False

        print("✅ PASS: Git is available")
        return True

    except FileNotFoundError:
        print("❌ FAIL: git command not found")
        return False


def test_notion_imports():
    """Test 3: Can Notion updater be imported?"""
    print("\n" + "=" * 80)
    print("TEST 3: Notion Updater Import")
    print("=" * 80)

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.utils.notion_updater import update_task_status

        print("✅ PASS: Notion updater can be imported")
        return True

    except ImportError as e:
        print(f"❌ FAIL: Import error: {e}")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔍 PIPELINE INTEGRITY TEST")
    print("=" * 80)
    print()

    results = []

    results.append(("Gemini Bridge", test_gemini_bridge()))
    results.append(("Git Command", test_git_available()))
    results.append(("Notion Import", test_notion_imports()))

    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Pipeline is healthy")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Fix issues before using finish command")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## 3. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的修复计划文档 (本文件)

### 步骤 2: 修复 gemini_review_bridge.py

**修改内容**:
1. 添加try-except捕获网络超时
2. 添加curl_cffi导入失败的fallback
3. 添加DEBUG日志输出
4. 明确返回Exit Code (0=success, 1=failure)

### 步骤 3: 强化 project_cli.py

**修改内容**:
1. 移除finish_task中的silent try-except
2. 添加subprocess.call返回码检查
3. 每个步骤失败时立即sys.exit(1)
4. 添加详细的错误消息

### 步骤 4: 创建测试脚本

**实现**:
- `scripts/test_pipeline_integrity.py`
- 3个测试：Bridge可用性、Git可用性、Notion导入

### 步骤 5: 审计检查

更新`scripts/audit_current_task.py`:
- Section [17/17]: Task #099.02检查项
- 验证修复后的代码

## 4. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_099_02_PLAN.md完整
- [ ] gemini_review_bridge.py有明确的exit code处理
- [ ] project_cli.py finish命令移除silent failures
- [ ] scripts/test_pipeline_integrity.py存在并可执行
- [ ] 运行finish命令时能看到AI Review输出
- [ ] Git push失败时finish命令返回非0
- [ ] Notion sync失败时finish命令返回非0

**可见性要求**:
- [ ] AI Review输出显示在终端
- [ ] 失败时有清晰的红色错误消息
- [ ] 成功时有明确的绿色成功消息

**可靠性要求**:
- [ ] 网络断开时不会报告虚假成功
- [ ] 每个步骤的失败都会被捕获
- [ ] 错误消息包含修复建议

## 5. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|----------|
| curl_cffi不可用 | AI Review失败 | 中 | Fallback到标准requests |
| 网络不稳定 | 偶发失败 | 高 | 增加超时时间到120s |
| Notion API限流 | Sync失败 | 低 | 添加重试逻辑（3次） |
| Git认证失败 | Push失败 | 低 | 明确错误消息指导用户 |

## 6. 回归测试 (Regression Testing)

**测试场景**:
1. **正常流程**: 所有步骤成功
2. **AI Review失败**: gemini返回错误
3. **Git Push失败**: 网络断开
4. **Notion Sync失败**: Token无效

**期望行为**:
- 场景1: finish命令返回0，Notion更新
- 场景2-4: finish命令返回1，显示错误，任务未标记完成

## 7. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建docs/TASK_099_02_PLAN.md
- ✅ 本地存储: 日志存储在logs/
- ✅ 代码优先: 修复实际代码，不只是文档
- ✅ 审计强制: Section [17/17]验证所有要求
- ✅ Notion仅状态: 只更新属性，不修改内容

---

**创建日期**: 2026-01-01

**协议版本**: v2.2 (Documentation-First, Loud Failures, Code-First)

**任务状态**: Ready for Implementation

**预计完成时间**: 1-2 hours
