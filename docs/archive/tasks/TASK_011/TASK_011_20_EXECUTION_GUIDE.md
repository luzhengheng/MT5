# Task #011.20: Final SSH Mesh - Execution Guide
## Step-by-Step Instructions for Complete SSH Connectivity

**Date**: 2025-12-30
**Status**: 🟡 **READY FOR EXECUTION**
**Ticket**: #060

---

## Current Status

### What's Already Done ✅

- ✅ SSH key generation script created (`ops_universal_key_setup.py`)
- ✅ SSH mesh verification script created (`verify_ssh_mesh.py`)
- ✅ GTW retry deployment script created (`ops_retry_gtw_setup.py`)
- ✅ SSH topology documentation complete
- ✅ Windows OpenSSH setup guide provided
- ✅ All scripts installed and tested

### What's Missing 🔄

- 🔄 SSH keys generated on INF node
- 🔄 SSH keys distributed to HUB and GPU nodes
- 🔄 SSH keys deployed to GTW (Windows Gateway)
- 🔄 Final verification of all 3 remote nodes

### Blocker ⚠️

**User interaction required**: The setup scripts require passwords for remote servers, which only the DevOps engineer/operator with credentials can provide.

---

## Prerequisites Checklist

Before starting, verify you have:

```bash
# On INF node (Linux control node)
✅ Access to ~/.ssh directory (writable)
✅ Python 3.9+ installed
✅ SSH command available
✅ Paramiko library installed (pip install paramiko)
✅ Network connectivity to GTW, HUB, GPU

# For remote nodes:
✅ HUB credentials (root password or key)
✅ GTW credentials (Administrator password)
✅ GPU credentials (root password or key)
✅ OpenSSH enabled on GTW (Windows)
```

---

## Execution Steps

### STEP 1: Generate and Distribute SSH Keys

**Objective**: Create SSH key pair locally and deploy to HUB and GPU

**Command**:
```bash
python3 scripts/ops_universal_key_setup.py
```

**What Happens**:

1. Script checks if `~/.ssh/id_rsa` exists
2. If missing, generates new 4096-bit RSA key
3. Creates `~/.ssh/config` with host aliases (gtw, hub, gpu)
4. Prompts for credentials:
   ```
   Enter password for root@172.19.141.254 (HUB): [YOUR_HUB_PASSWORD]
   Enter password for root@www.guangzhoupeak.com (GPU): [YOUR_GPU_PASSWORD]
   ```
5. Deploys public key to each remote node
6. Outputs:
   ```
   ✅ GTW Key Installed
   ✅ HUB Key Installed
   ✅ GPU Key Installed
   ```

**Expected Time**: 3-5 minutes

**If Fails**:
- Verify network connectivity: `ping 172.19.141.254` (HUB)
- Check SSH service on remote: `ssh root@172.19.141.254 systemctl status ssh`
- Retry script after troubleshooting

### STEP 2: Deploy Key to Windows Gateway (GTW)

**Objective**: Connect Windows Gateway to the SSH mesh

**Prerequisites**:
- OpenSSH Server installed on GTW ✅
- SSH service running on GTW ✅
- Port 22 open ✅
- Administrator account accessible ✅

**Command**:
```bash
python3 scripts/ops_retry_gtw_setup.py
```

**What Happens**:

1. Script loads SSH public key generated in Step 1
2. Prompts for Windows credentials:
   ```
   Enter password for Administrator@172.19.141.255 (GTW): [YOUR_GTW_PASSWORD]
   ```
3. Connects via Paramiko SSH to Windows
4. Deploys key to `C:\Users\Administrator\.ssh\authorized_keys`
5. Sets proper Windows file permissions (icacls)
6. Tests password-less SSH connection
7. Outputs:
   ```
   ✅ SSH connection to GTW (Administrator@172.19.141.255)
   ✅ Key deployed to GTW
   ✅ GTW Key Installed
   ✅ Password-less SSH to GTW: Connection successful
   ```

**Expected Time**: 1-2 minutes

**If Fails**:
- Verify GTW OpenSSH: `ssh gtw Get-Service sshd` (if using password auth temporarily)
- Check GTW firewall: `ssh gtw netstat -ano | findstr :22`
- Verify .ssh directory: `ssh gtw dir C:\Users\Administrator\.ssh`

### STEP 3: Verify Complete Mesh Connectivity

**Objective**: Confirm all 3 remote nodes are accessible

**Command**:
```bash
python3 scripts/verify_ssh_mesh.py
```

**What Happens**:

1. Tests SSH connection to GTW (Windows)
2. Tests SSH connection to HUB (Linux)
3. Tests SSH connection to GPU (Remote Linux)
4. Measures latency to each node
5. Generates summary table:
   ```
   Host │ Description          │ Network    │ Status  │ Latency
   ─────┼─────────────────────┼───────────┼─────────┼─────────
   gtw  │ Gateway (Windows)    │ Local     │ ✅ PASS │  <1ms
   hub  │ Hub (Feature Store)  │ Local     │ ✅ PASS │  <1ms
   gpu  │ GPU (Compute Node)   │ Remote    │ ✅ PASS │ ~200ms

   🎯 SSH MESH FULLY OPERATIONAL
   All nodes accessible via password-less SSH
   ```

**Expected Time**: 1-2 minutes

**Success Criteria**: All 3 show ✅ PASS

**If Fails**:
- Check SSH config: `cat ~/.ssh/config`
- Test manually: `ssh -o BatchMode=yes gtw "echo OK"`
- Check public key: `cat ~/.ssh/id_rsa.pub`

### STEP 4: Manual Verification (Optional)

**Test each node directly**:

```bash
# Test Gateway (Windows)
ssh gtw
# Should open Windows CMD prompt
# Type: exit (to leave)

# Test Hub (Linux)
ssh hub
# Should open Linux bash prompt
# Type: exit (to leave)

# Test GPU (Remote Linux)
ssh gpu
# Should open Linux bash prompt
# Type: exit (to leave)

# Test commands on each node
ssh gtw "powershell Get-Date"
ssh hub "systemctl status postgresql"
ssh gpu "nvidia-smi"
```

**Expected**: All commands execute without password prompts

---

## Complete Execution Sequence (Copy-Paste)

```bash
# Set up color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}  Task #011.20: Finalize SSH Mesh${NC}"
echo -e "${YELLOW}======================================${NC}\n"

# Step 1: Generate and distribute keys
echo -e "${YELLOW}[Step 1/3] Generate SSH Keys & Distribute to HUB/GPU${NC}"
echo "This will prompt for:"
echo "  • root password for HUB (172.19.141.254)"
echo "  • root password for GPU (www.guangzhoupeak.com)"
echo ""
python3 scripts/ops_universal_key_setup.py
STEP1_RESULT=$?

if [ $STEP1_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Step 1 complete: Keys distributed to HUB and GPU${NC}\n"
else
    echo -e "${RED}❌ Step 1 failed: Check error messages above${NC}\n"
    exit 1
fi

# Step 2: Deploy to Gateway
echo -e "${YELLOW}[Step 2/3] Deploy Key to Windows Gateway (GTW)${NC}"
echo "This will prompt for:"
echo "  • Administrator password for GTW (172.19.141.255)"
echo ""
python3 scripts/ops_retry_gtw_setup.py
STEP2_RESULT=$?

if [ $STEP2_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Step 2 complete: Key deployed to GTW${NC}\n"
else
    echo -e "${RED}❌ Step 2 failed: Check error messages above${NC}\n"
    exit 1
fi

# Step 3: Verify all nodes
echo -e "${YELLOW}[Step 3/3] Verify SSH Mesh - All 3 Nodes${NC}"
python3 scripts/verify_ssh_mesh.py
STEP3_RESULT=$?

if [ $STEP3_RESULT -eq 0 ]; then
    echo -e "${GREEN}\n✅ ALL STEPS COMPLETE: SSH MESH FULLY OPERATIONAL${NC}"
    echo -e "${GREEN}You can now access all nodes:${NC}"
    echo -e "  ${GREEN}ssh gtw${NC}  # Windows Gateway"
    echo -e "  ${GREEN}ssh hub${NC}  # Linux Hub"
    echo -e "  ${GREEN}ssh gpu${NC}  # Remote GPU Node"
else
    echo -e "${RED}❌ Step 3 failed: Some nodes unreachable${NC}\n"
    exit 1
fi
```

---

## Credential Requirements

### What Passwords You'll Need

| Node | IP | User | Password Type | Status |
|------|----|----|---|---|
| HUB | 172.19.141.254 | root | Linux login | 🔄 Needed |
| GPU | www.guangzhoupeak.com | root | Linux login | 🔄 Needed |
| GTW | 172.19.141.255 | Administrator | Windows login | 🔄 Needed |

### Credential Sources

```bash
# Check HUB credentials (if you manage it)
ssh-keyscan -H 172.19.141.254

# Check GPU credentials (if you manage it)
ssh-keyscan -H www.guangzhoupeak.com

# Check GTW (Windows) - should have been provided during setup
# Administrator account on the Windows Gateway machine
```

---

## Troubleshooting Common Issues

### Issue 1: "SSH connection refused"

**Cause**: Remote SSH service not running

**Fix**:
```bash
# On HUB (Linux)
ssh root@172.19.141.254 systemctl status ssh
ssh root@172.19.141.254 systemctl start ssh

# On GPU (Linux)
ssh root@www.guangzhoupeak.com systemctl status ssh
ssh root@www.guangzhoupeak.com systemctl start ssh

# On GTW (Windows)
# Verify OpenSSH is running:
ssh Administrator@172.19.141.255 Get-Service sshd
```

### Issue 2: "Authentication failed"

**Cause**: Wrong password or wrong credentials

**Fix**:
- Double-check username and password
- Verify you're connecting to the right IP address
- For GTW, make sure it's using Administrator account (not Domain\Administrator)

### Issue 3: "Key permissions denied"

**Cause**: authorized_keys file has wrong permissions

**Fix** (on remote node):
```bash
# Linux (HUB/GPU)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Windows (GTW) - from PowerShell (as Administrator)
icacls "C:\Users\Administrator\.ssh" /inheritance:r /grant:r "Administrator:(F)"
icacls "C:\Users\Administrator\.ssh\authorized_keys" /inheritance:r /grant:r "Administrator:(F)"
```

### Issue 4: "File not found: ops_universal_key_setup.py"

**Cause**: Script doesn't exist or wrong path

**Fix**:
```bash
# Verify scripts exist
ls -la scripts/ops_universal_key_setup.py
ls -la scripts/ops_retry_gtw_setup.py
ls -la scripts/verify_ssh_mesh.py

# If missing, they should be in the repo - update it:
git pull origin main
```

---

## Success Indicators

### After Step 1 (HUB & GPU keys deployed):
```
✅ Keys Deployed
  ✅ Key deployed to hub (172.19.141.254)
  ✅ Key deployed to gpu (www.guangzhoupeak.com)
```

### After Step 2 (GTW key deployed):
```
✅ Key deployed to gtw
✅ GTW Key Installed
✅ Password-less SSH to GTW: Connection successful
```

### After Step 3 (Full verification):
```
gtw  │ Gateway (Windows)    │ Local     │ ✅ PASS  │  <1ms
hub  │ Hub (Feature Store)  │ Local     │ ✅ PASS  │  <1ms
gpu  │ GPU (Compute Node)   │ Remote    │ ✅ PASS  │ ~200ms

🎯 SSH MESH FULLY OPERATIONAL
```

---

## Next Steps After Completion

Once all 3 nodes pass verification:

1. **You can access all nodes without passwords**:
   ```bash
   ssh gtw "powershell dir"
   ssh hub "systemctl status postgresql"
   ssh gpu "nvidia-smi"
   ```

2. **The infrastructure is ready for**:
   - Code deployment to all nodes
   - Service monitoring and management
   - Centralized control and automation
   - Feature store activation (Feast on HUB)
   - GPU training jobs (GPU node)
   - ZMQ gateway activation (GTW)

3. **Proceed with next tasks**:
   - Activate nexus_with_proxy.py daemon
   - Start feature store services
   - Initialize ZMQ message broker
   - Deploy trading bot to GPU

---

## Quick Reference

### SSH Aliases (from ~/.ssh/config)

```bash
ssh gtw               # Windows Gateway
ssh hub               # Linux Hub (Feature Store)
ssh gpu               # Remote GPU Node
```

### SSH Commands

```bash
# Shell access
ssh gtw

# Command execution
ssh gtw "powershell Get-Process"

# File copy
scp local_file.txt gtw:/remote/path/
scp gpu:/remote/file.txt local_path/

# Port forwarding
ssh -L 5432:localhost:5432 hub  # Forward HUB PostgreSQL

# Bulk operations
for node in gtw hub gpu; do ssh $node "uptime"; done
```

### Verification Commands

```bash
# Test all nodes
python3 scripts/verify_ssh_mesh.py

# Test individual node
ssh -o BatchMode=yes gtw "echo OK"

# Check SSH key
cat ~/.ssh/id_rsa.pub

# Check SSH config
cat ~/.ssh/config
```

---

## Safety Notes

⚠️ **Security Considerations**:

1. **SSH Keys**:
   - `~/.ssh/id_rsa` is your private key - keep it secret
   - Never share `id_rsa` with anyone
   - Keep `id_rsa` permissions at 0600 (read-only)

2. **Passwords**:
   - Don't store passwords in files or scripts
   - Scripts prompt for passwords interactively
   - Each password is used only for initial key deployment

3. **SSH Config**:
   - `~/.ssh/config` specifies trusted hosts
   - `StrictHostKeyChecking no` (in scripts) speeds up batch operations
   - For production, consider `StrictHostKeyChecking=yes`

4. **Post-Deployment**:
   - After keys are deployed, you can disable password auth on remote nodes
   - This improves security (keys only, no passwords)

---

## Support & Debugging

### Enable verbose SSH for debugging:

```bash
# Verbose connection test
ssh -vvv gtw "echo OK"

# Check SSH key availability
ssh -vvv gtw ls

# This shows what's happening step-by-step
```

### Check logs on remote nodes:

```bash
# HUB/GPU Linux logs
ssh hub tail -50 /var/log/auth.log

# GTW Windows logs
ssh gtw Get-EventLog -LogName System -Newest 20 | Where Source -eq sshd
```

---

**Ready to Execute**: Task #011.20 is fully prepared. Follow the steps above to complete SSH mesh connectivity.

**Estimated Time**: 8-12 minutes (depending on network and password entry speed)

**Expected Outcome**: ✅ All 3 remote nodes accessible via password-less SSH

🎯 **PROCEED WITH STEP 1 ABOVE TO BEGIN**
