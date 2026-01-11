# 📢 PROTOCOL UPDATE: Ticket-First Workflow

**Effective Date**: 2025-12-24
**Applies To**: Task #015 and all future tasks
**Reason**: Incident in Task #014 - Notion ticket missing despite implementation complete

---

## 🎯 The Problem

**Task #014** was fully implemented:
- ✅ Code written and tested
- ✅ Features complete
- ✅ Committed to GitHub
- ✅ Released to production
- ❌ **But**: Notion ticket was **NEVER CREATED**

This created a data inconsistency:
- GitHub showed completed work
- Notion showed nothing
- Project visibility incomplete

---

## ✅ The Solution: Ticket-First Workflow

**MANDATORY**: Create Notion ticket BEFORE writing any code.

### Phase 1: CREATE TICKET (Before Coding)

```
┌─────────────────────────────────────────┐
│ 1. Prepare Ticket Details               │
├─────────────────────────────────────────┤
│ • Title: "#015 <Task Name>"             │
│ • Status: "未开始" (Not Started)         │
│ • Type: Feature/Bug/Enhancement         │
│ • Priority: P0/P1/P2/P3 (if applicable) │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ 2. Create in Notion Issues Database     │
├─────────────────────────────────────────┤
│ Manual: Create directly in Notion       │
│ Script: python3 scripts/create_task.py  │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ 3. VERIFY Ticket Created                │
├─────────────────────────────────────────┤
│ ✅ Appears in Issues database list      │
│ ✅ Correct title and status             │
│ ✅ Note the ticket ID/URL               │
└─────────────────────────────────────────┘
```

**Key Requirement**: Do NOT proceed to coding until ticket is verified in Notion.

### Phase 2: IMPLEMENT CODE (During Coding)

```
┌─────────────────────────────────────────┐
│ 1. Reference Ticket in Git              │
├─────────────────────────────────────────┤
│ Commit Format:                          │
│ "feat(component): implement #015 desc"  │
│                                         │
│ Example:                                │
│ "feat(order): implement #015 placement" │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ 2. Update Notion Status (Optional)      │
├─────────────────────────────────────────┤
│ When starting active work:              │
│ • Set status to "进行中" (In Progress)   │
└─────────────────────────────────────────┘
```

**Key Requirement**: Every commit message must reference the ticket number.

### Phase 3: COMPLETE & DOCUMENT (On Completion)

```
┌─────────────────────────────────────────┐
│ 1. Update Notion Status                 │
├─────────────────────────────────────────┤
│ • Set status to "完成" (Completed)      │
│ • Document implementation summary       │
│ • Link to release documentation         │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ 2. Create Release Documentation         │
├─────────────────────────────────────────┤
│ • Summary of what was implemented       │
│ • Key files and components              │
│ • Git commit references                 │
│ • Any learnings or gotchas               │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ 3. Final Verification                   │
├─────────────────────────────────────────┤
│ ✅ Notion status: "完成"                 │
│ ✅ Git commits reference #015            │
│ ✅ Release docs complete                 │
│ ✅ Task ready for review                 │
└─────────────────────────────────────────┘
```

---

## 📋 Task Completion Checklist

### For Project Manager
- [ ] Ticket created in Notion Issues database
- [ ] Ticket visible and searchable in database
- [ ] Ticket status is "未开始"
- [ ] Proceed with implementation approval

### For Developer
- [ ] Reference ticket number in all commits
- [ ] Update Notion status during active work
- [ ] Create release documentation on completion
- [ ] Set Notion status to "完成" when done

### For Release Manager
- [ ] All commits reference ticket number
- [ ] Notion status set to "完成"
- [ ] Release documentation exists
- [ ] Git pushed to remote

---

## 🔍 Verification Commands

### Check if Ticket Exists
```python
# Query Notion for ticket by number
python3 scripts/inspect_notion_db.py
# Look for "#015" in the list
```

### View Git Commit References
```bash
# Check commits reference the ticket
git log --grep="#015" --oneline
```

### List All Incomplete Tasks
```bash
# Show tasks not yet marked as "完成"
# (Requires Notion query script)
```

---

## 📝 Commit Message Format

**Required Format**:
```
<type>(<scope>): <message> #<ticket-number>
```

**Examples**:
```
feat(gateway): implement #015 order placement service
feat(risk): add #015 position limit checker
fix(order): resolve #015 execution timing bug
docs(api): update #015 order API documentation
```

**Valid Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `refactor` - Code restructuring
- `test` - Test additions
- `chore` - Build/config changes

---

## 🚨 Non-Compliance

Tasks that do NOT follow this protocol will be:
1. ❌ Not approved for merge
2. ❌ Not marked as complete in project management
3. ❌ Require rework and resubmission

**Why**: This ensures:
- ✅ Data consistency between Git and Notion
- ✅ Complete project visibility
- ✅ Proper change tracking
- ✅ Team awareness of progress

---

## 💾 Tools & Scripts

### Backfill Script (For Missing Tickets)
```bash
python3 scripts/sync_missing_ticket.py
```
*Used to retroactively add missing tickets (like Task #014)*

### Create New Ticket Script (Recommended)
```bash
# Script to be created for Task #015:
python3 scripts/create_task_015_ticket.py
```
*Will automatically create and verify Notion ticket*

---

## 📚 Reference: Task #014 Recovery

As of 2025-12-24, Task #014 was recovered using:
1. Backfill script: `scripts/sync_missing_ticket.py`
2. Manual verification with Notion API
3. Confirmed in Notion database
4. Documented in: `TICKET_014_BACKFILL_REPORT.md`

**Ticket #014 Notion URL**:
https://www.notion.so/014-MT5-Gateway-Core-Service-2d2c88582b4e81d9bcb7d3f0e3d63980

---

## 📊 Summary

| Before (Task #014) | After (Task #015+) |
|---|---|
| ❌ Code in Git | ✅ Ticket in Notion first |
| ❌ Notion missing | ✅ Code then implemented |
| ⚠️ Data inconsistent | ✅ Data always in sync |
| ❌ Visibility gap | ✅ Complete transparency |

---

**Policy Owner**: Project Management
**Implementation Date**: 2025-12-24
**Version**: 1.0

Status: ✅ ACTIVE & ENFORCED

