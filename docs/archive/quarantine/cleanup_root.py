import os
import shutil
from pathlib import Path

# Files to move to docs/
temp_files = [
    'CALIBRATION_ANALYSIS.log',
    'check_sync_status.py',
    'create_work_orders_in_notion.py',
    'DEVOPS_PATCH_DEPLOYMENT_STATUS.txt',
    'DEVOPS_PATCH_PoE_IMPLEMENTATION.md',
    'DUAL_AI_COLLABORATION_PLAN.md',
    'ENVIRONMENT_SETUP_REMEDIATION.md',
    'export_context_for_ai.py',
    'export_context_output.log',
    'EXTERNAL_AI_QUICK_START.md',
    'FINAL_SESSION_SUMMARY.txt',
    'NEXT_STEPS_PLAN.md',
    'NEXUS_DEPLOYMENT_COMPLETE.md',
    'NOTION_NEXUS_ENV_EXAMPLE.md',
    'NOTION_SETUP_GUIDE.md',
    'NOTION_SYNC_DEPLOYMENT_COMPLETE.md',
    'PROTOCOL_UPDATE_TICKET_FIRST.md',
    'QUICK_START_CHECKLIST.md',
    'QUICK_START.md',
    'README_COMPLETION.md',
    'README_IMPLEMENTATION.md',
    'TASK_026_9_FINAL_SUMMARY.txt',
    'TASK_034_EXECUTION_READINESS.md',
    'TASK_034_FINAL_STATUS.md',
    'TASK_034_STATUS.md',
    'TASK_036_COMPLETION_STATUS.md',
    'TASK_038_COMPLETION_STATUS.md',
    'TASK_039_FINAL_AUDIT_REPORT.md',
    'TASK_064.5_EXECUTION_SUMMARY.md',
]

moved = 0
for f in temp_files:
    src = f'/opt/mt5-crs/{f}'
    if os.path.exists(src):
        dst = f'/opt/mt5-crs/docs/{f}'
        shutil.move(src, dst)
        moved += 1
        print(f'Moved {f}')

print(f"\n✅ Moved {moved} files from root to docs/")
