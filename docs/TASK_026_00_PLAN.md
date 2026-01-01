# Task #026.00: GPU Node Connectivity Setup (Cross-Region)

**Status**: Implementation Phase
**Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
**Objective**: Enable seamless SSH access to remote GPU node in Guangzhou from Singapore HUB

---

## Executive Summary

This task establishes secure, password-less SSH connectivity from the local development environment (Singapore HUB) to a remote GPU-accelerated compute node (Guangzhou) operated by Guangzhou Peak. This bridges the development and training infrastructure, enabling:

1. **Remote GPU Access**: `ssh gpu-node nvidia-smi` from local terminal
2. **Model Training**: Run XGBoost and deep learning workloads on remote GPU
3. **Automated Setup**: Python script configures SSH without manual intervention
4. **Cross-Region Connectivity**: Singapore ↔ Guangzhou secure channel

---

## Context

### Infrastructure Setup

**Source (Local HUB)**:
- Location: Singapore
- Role: Development and command center
- Goal: Control remote GPU node with simple `ssh gpu-node` command

**Target (Remote GPU Node)**:
- Hostname: `www.guangzhoupeak.com`
- User: `root`
- Location: Guangzhou, China
- Capabilities: GPU acceleration (Tesla/Ampere series)
- Purpose: Model training, inference acceleration

### Current State

- SSH keys may not exist or may not be configured
- `.ssh/config` may not have entry for GPU node
- Public key not yet copied to remote server

### Goal

Enable one-command GPU node access:
```bash
ssh gpu-node nvidia-smi
```

This should return GPU status without password prompt.

---

## Implementation Details

### 1. SSH Configuration (`~/.ssh/config`)

**Target Entry Format**:
```
Host gpu-node
    HostName www.guangzhoupeak.com
    User root
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    ConnectTimeout 10
```

**Purpose**:
- `Host gpu-node`: Alias for easy access
- `HostName`: Actual server address
- `User`: Remote login user
- `IdentityFile`: Path to private key
- `StrictHostKeyChecking no`: Skip known_hosts verification (optional, for automation)
- `ConnectTimeout`: 10-second timeout for slow networks

### 2. SSH Key Management

**Key Generation** (if needed):
```bash
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
```

**Key Distribution** (manual if automated fails):
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com
```

**Verification**:
```bash
ssh gpu-node nvidia-smi
```

### 3. Setup Script (`scripts/ops_establish_gpu_link.py`)

**Workflow**:

```python
1. Check if SSH key exists
   ├─ If no: Generate new key (id_rsa)
   └─ If yes: Use existing key

2. Check SSH config
   ├─ If no config: Create ~/.ssh/config
   └─ If no gpu-node entry: Append entry

3. Test connectivity
   ├─ Try: ssh gpu-node nvidia-smi
   ├─ If success: Report GPU info
   └─ If fail (Permission denied): Prompt for manual ssh-copy-id
```

**Error Handling**:
- SSH key missing → Generate automatically
- SSH config missing → Create and set permissions (600)
- SSH config exists but no gpu-node entry → Append safely
- Remote key not trusted → Provide manual step with clear instructions
- Connection timeout → Check network and firewall

**Output Examples**:

Success:
```
✅ SSH key exists at ~/.ssh/id_rsa
✅ Added gpu-node to SSH config
✅ GPU Node Connected!

GPU Status:
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.104.05    Driver Version: 535.104.05    CUDA Version: 12.2 |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| No  Type        Default   | 00000000:00:1E.0 Off |                  Off |
+-------------------------------+----------------------+----------------------+
| 0  Tesla A100       Off     | 00000000:00:1E.0 Off |                  Off |
```

Failure with guidance:
```
⚠️ Connection failed: Permission denied (publickey)

📝 MANUAL ACTION REQUIRED:
   Run this command on your local machine:
   ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com

   Then retry: python3 scripts/ops_establish_gpu_link.py
```

---

## Security Considerations

### Authentication Method

- **Mechanism**: Public key cryptography (RSA)
- **Key Type**: RSA 2048-bit or higher
- **Key Location**: `~/.ssh/id_rsa` (private), `~/.ssh/id_rsa.pub` (public)
- **Access Control**: Root access only (prod use should restrict)

### Security Best Practices

1. **Private Key Protection**:
   - File permissions: `600` (read-write owner only)
   - Never commit private keys to Git
   - Never share private keys

2. **SSH Config Permissions**:
   - File permissions: `600`
   - Directory permissions: `700` for `~/.ssh/`

3. **Remote Server Access**:
   - Use dedicated SSH user in production (not root)
   - Implement IP whitelisting if possible
   - Enable SSH server logging
   - Disable password authentication on remote server

4. **Audit Trail**:
   - Log all SSH connections
   - Monitor for unauthorized access attempts
   - Review logs periodically

### Recommended Production Changes

For production deployment:
1. Create non-root user (e.g., `mlops`)
2. Use SSH certificates instead of keys
3. Implement bastion host if in restricted network
4. Enable MFA if supported
5. Use VPN for cross-region traffic

---

## Technical Architecture

### Connection Flow

```
┌─────────────────────┐
│  Local HUB          │
│  (Singapore)        │
│                     │
│  ~$ ssh gpu-node    │
│  ↓                  │
│  ~/.ssh/config      │
│  reads: gpu-node    │
│  ↓                  │
│  Resolves to:       │
│  www.guangzhoupeak  │
│  ↓                  │
│  Loads key:         │
│  ~/.ssh/id_rsa      │
└────────┬────────────┘
         │ SSH Protocol (Port 22)
         │ RSA Public Key Auth
         ↓
┌─────────────────────┐
│  Remote GPU Node    │
│  (Guangzhou)        │
│                     │
│  www.guangzhoupeak  │
│  root@*             │
│                     │
│  ~/.ssh/authorized  │
│  _keys              │
│  (verifies pub key) │
│  ↓                  │
│  Grants access      │
│  ↓                  │
│  $ nvidia-smi       │
│  returns GPU info   │
└─────────────────────┘
```

### SSH Handshake Sequence

```
1. Client initiates connection to gpu-node
2. SSH config resolves alias → www.guangzhoupeak.com:22
3. Server presents host key
4. Client verifies host key (or skips if StrictHostKeyChecking=no)
5. Client sends public key
6. Server checks ~/.ssh/authorized_keys
7. Public key match → Authentication successful
8. Session established → Run nvidia-smi
9. Return GPU status
10. Close connection
```

---

## Audit Checklist

When task is complete, verify:

- [ ] **Documentation**
  - [ ] `docs/TASK_026_00_PLAN.md` exists (this file)
  - [ ] Plan covers all components

- [ ] **Script Implementation**
  - [ ] `scripts/ops_establish_gpu_link.py` exists
  - [ ] Script is executable
  - [ ] Handles all error cases

- [ ] **SSH Setup**
  - [ ] SSH key exists at `~/.ssh/id_rsa`
  - [ ] SSH config exists at `~/.ssh/config`
  - [ ] `gpu-node` entry present in config
  - [ ] File permissions correct (600 for files, 700 for dir)

- [ ] **Connectivity Test**
  - [ ] `ssh gpu-node nvidia-smi` works without password
  - [ ] Returns valid GPU information
  - [ ] Output shows card model (Tesla/Ampere/etc)

- [ ] **Audit Integration**
  - [ ] `scripts/audit_current_task.py` has Task #026.00 section
  - [ ] All audit checks pass

- [ ] **Pipeline Verification**
  - [ ] Script executes without critical errors
  - [ ] SSH connectivity verified
  - [ ] GPU access confirmed

---

## Success Criteria

**Minimum Requirements**:
1. ✅ `ops_establish_gpu_link.py` exists and is executable
2. ✅ Script successfully configures SSH access
3. ✅ `ssh gpu-node nvidia-smi` returns GPU information

**Extended Verification**:
1. ✅ SSH key generated or verified
2. ✅ `.ssh/config` properly formatted
3. ✅ Public key copied to remote server
4. ✅ No password prompts required
5. ✅ GPU model and CUDA version displayed

---

## Execution Steps

### Step 1: Create Documentation
- Write `docs/TASK_026_00_PLAN.md` (this file)
- Verify completeness

### Step 2: Implement Setup Script
- Write `scripts/ops_establish_gpu_link.py`
- Handle SSH key creation
- Configure SSH config entry
- Test connectivity
- Provide clear error messages

### Step 3: Update Audit
- Add Task #026.00 verification to `scripts/audit_current_task.py`
- Create 6-8 audit checks

### Step 4: Execute and Verify
- Run `python3 scripts/ops_establish_gpu_link.py`
- Handle "Permission denied" gracefully
- Prompt user for `ssh-copy-id` if needed
- Verify final connectivity

### Step 5: Commit and Finish
- Commit changes to Git
- Run finish command
- Verify AI review passes

---

## Troubleshooting

### Issue: "Permission denied (publickey)"

**Cause**: Public key not yet copied to remote server

**Solution**:
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com
# Then re-run: python3 scripts/ops_establish_gpu_link.py
```

### Issue: "Could not resolve hostname"

**Cause**: DNS resolution failing or network unreachable

**Solution**:
```bash
# Test DNS
nslookup www.guangzhoupeak.com

# Test network connectivity
ping www.guangzhoupeak.com

# Test SSH port
nc -zv www.guangzhoupeak.com 22
```

### Issue: "Connection timed out"

**Cause**: Firewall blocking SSH (port 22) or network latency

**Solution**:
1. Check firewall rules on local machine
2. Check firewall rules on remote server
3. Increase timeout in SSH config
4. Try VPN if available

### Issue: "~/.ssh: No such file or directory"

**Cause**: SSH directory doesn't exist

**Solution**:
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

---

## Benefits After Completion

Once this task is complete:

1. **Development Speed**: Run training jobs on GPU with one command
2. **Resource Optimization**: Use GPU for ML tasks without local hardware
3. **Automation**: Scripts can trigger GPU jobs without human intervention
4. **Monitoring**: Query GPU status anytime with `ssh gpu-node nvidia-smi`
5. **Scalability**: Easy to add more GPU nodes to `.ssh/config`

---

## Future Extensions

After this task is complete, future tasks could:

1. **Task #027.00**: Multi-GPU load balancing (distribute jobs across multiple GPU nodes)
2. **Task #028.00**: GPU monitoring and alerting (prometheus metrics from nvidia-smi)
3. **Task #029.00**: Distributed training orchestration (Ray Tune on GPU cluster)
4. **Task #030.00**: Cost optimization (schedule training during off-peak hours)

---

## Files Modified/Created

### New Files
- `docs/TASK_026_00_PLAN.md` - This documentation
- `scripts/ops_establish_gpu_link.py` - GPU node connection setup

### Modified Files
- `scripts/audit_current_task.py` - Added Task #026.00 audit section

### System Files (Modified by script)
- `~/.ssh/config` - Appended gpu-node entry
- `~/.ssh/id_rsa` - Generated if missing

---

## References

- SSH Protocol: RFC 4251-4256
- SSH Config Manual: `man ssh_config`
- NVIDIA CUDA Setup: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/
- Public Key Authentication: https://linux.die.net/man/1/ssh-keygen

---

## Appendix: SSH Config Example

```bash
# ~/.ssh/config

Host gpu-node
    HostName www.guangzhoupeak.com
    User root
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    ConnectTimeout 10
    ServerAliveInterval 60
    ServerAliveCountMax 5

# Other hosts can be added similarly:
# Host web-server
#     HostName api.example.com
#     User deploy
#     IdentityFile ~/.ssh/id_rsa
```

---

## Document Information

- **Created**: Task #026.00: GPU Node Connectivity Setup
- **Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
- **Status**: Complete
- **Version**: 1.0

---
