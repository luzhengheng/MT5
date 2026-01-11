import os
import shutil
from pathlib import Path

# Define categorization rules
guides = [
    'QUICK_START.md', 'QUICK_START_CHECKLIST.md', 'QUICKSTART_ML.md',
    'DEPLOYMENT.md', 'DEPLOYMENT_GTW_SSH_SETUP.md', 'DEPLOYMENT_CHECKLIST.md',
    'ML_TRAINING_GUIDE.md', 'ML_ADVANCED_GUIDE.md', 'BACKTEST_GUIDE.md',
    'NOTION_SETUP_CN.md', 'NOTION_SETUP_GUIDE.md', 'EXTERNAL_AI_QUICK_START.md',
    'MANUAL_WINDOWS_SSH_SETUP.md', 'RISK_CONTROL_INTEGRATION_GUIDE.md'
]

references = [
    'SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md',
    '[System Instruction MT5-CRS Development Protocol v4.3].md',
    '📄 MT5-CRS 基础设施资产全景档案.md.md',
    'AI_RULES.md', 'DATA_FORMAT_SPEC.md', 'WORKFLOW_PROTOCOL.md',
    'AI_SYNC_PROMPT.md', 'AI_COLLABORATION_GEMINI_REVIEW_REQUEST.md',
    'THRESHOLD_CALIBRATION.md', 'task.md'
]

# Organize files
for guide in guides:
    src = f'/opt/mt5-crs/docs/{guide}'
    if os.path.exists(src):
        dst = f'/opt/mt5-crs/docs/guides/{guide}'
        shutil.move(src, dst)
        print(f'Moved {guide} -> guides/')

for ref in references:
    src = f'/opt/mt5-crs/docs/{ref}'
    if os.path.exists(src):
        dst = f'/opt/mt5-crs/docs/references/{ref}'
        shutil.move(src, dst)
        print(f'Moved {ref} -> references/')

# Move old task completion reports to archive
for f in os.listdir('/opt/mt5-crs/docs'):
    if f.startswith('TASK_') and f.endswith('_COMPLETION_REPORT.md'):
        src = f'/opt/mt5-crs/docs/{f}'
        task_num = f.split('_')[1]
        task_dir = f'/opt/mt5-crs/docs/archive/tasks/TASK_{task_num}'
        os.makedirs(task_dir, exist_ok=True)
        dst = f'{task_dir}/{f}'
        if not os.path.exists(dst):
            shutil.move(src, dst)
            print(f'Archived {f}')

print("✅ Organization complete")
