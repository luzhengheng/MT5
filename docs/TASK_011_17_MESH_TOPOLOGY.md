# Task #011.17: Universal 4-Node SSH Mesh Setup & Verification
## Network Topology & Infrastructure Map

**Date**: 2025-12-30
**Protocol**: v2.2 (Docs-as-Code)
**Role**: DevOps Engineer / Infrastructure
**Ticket**: #058
**Status**: 🚀 **IN PROGRESS**

---

## Executive Summary

This document defines the complete SSH mesh network topology for the MT5 distributed trading infrastructure. All 4 nodes (INF, GTW, HUB, GPU) will be connected via password-less SSH for automated deployment and monitoring.

---

## Network Topology Map

### 4-Node Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              DISTRIBUTED TRADING INFRASTRUCTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LOCAL NETWORK (Private 172.19.141.0/24)               │    │
│  │                                                           │    │
│  │  INF (172.19.141.250)          ← Control Node (Local)   │    │
│  │  ├─ SSH Key: ~/.ssh/id_rsa                              │    │
│  │  ├─ OS: Linux (Python 3.9)                              │    │
│  │  ├─ Role: Central management & orchestration            │    │
│  │  └─ Connected to: GTW, HUB, GPU                         │    │
│  │                                                           │    │
│  │  GTW (172.19.141.255)          ← Gateway Node           │    │
│  │  ├─ OS: Windows (ZMQ broker)                            │    │
│  │  ├─ SSH: Windows + OpenSSH                              │    │
│  │  ├─ User: Administrator                                 │    │
│  │  ├─ .ssh path: C:\Users\Administrator\.ssh              │    │
│  │  └─ Firewall: Port 22 (SSH) required                    │    │
│  │                                                           │    │
│  │  HUB (172.19.141.254)          ← Feature Store Hub       │    │
│  │  ├─ OS: Linux                                            │    │
│  │  ├─ Services: PostgreSQL, Redis                         │    │
│  │  ├─ User: root                                           │    │
│  │  ├─ .ssh path: /root/.ssh                               │    │
│  │  └─ Firewall: Port 22 (SSH) required                    │    │
│  │                                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CROSS-BORDER CONNECTION (Internet)                    │    │
│  │                                                           │    │
│  │  GPU (www.guangzhoupeak.com)   ← Compute Node           │    │
│  │  ├─ IP: www.guangzhoupeak.com (DNS resolvable)         │    │
│  │  ├─ OS: Linux                                            │    │
│  │  ├─ Services: ML inference, training                    │    │
│  │  ├─ User: root                                           │    │
│  │  ├─ .ssh path: /root/.ssh                               │    │
│  │  ├─ Firewall: Port 22 (SSH) open to internet            │    │
│  │  └─ Latency: ~200ms (international)                     │    │
│  │                                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Infrastructure Matrix

### Node Details

| Attribute | INF (Control) | GTW (Gateway) | HUB (Store) | GPU (Compute) |
|-----------|---|---|---|---|
| **IP Address** | 172.19.141.250 | 172.19.141.255 | 172.19.141.254 | www.guangzhoupeak.com |
| **OS Type** | Linux | Windows | Linux | Linux |
| **OS Version** | Ubuntu/Debian | Windows Server | Ubuntu/Debian | Ubuntu/Debian |
| **SSH User** | root | Administrator | root | root |
| **SSH Home** | /root | C:\Users\Administrator | /root | /root |
| **.ssh Path** | /root/.ssh | C:\Users\Administrator\.ssh | /root/.ssh | /root/.ssh |
| **Network Zone** | Private (Local) | Private (Local) | Private (Local) | Public (Internet) |
| **Latency** | 0ms (local) | <1ms | <1ms | ~200ms |
| **Firewall 22** | Required | Required | Required | Required |
| **Primary Role** | Orchestration | Async Broker | Feature Store | ML Training |
| **Services** | Python, Git | ZMQ, Windows SSH | PostgreSQL, Redis | GPU, TensorFlow |
| **Auth Method** | SSH Key (id_rsa.pub) | SSH Key (id_rsa.pub) | SSH Key (id_rsa.pub) | SSH Key (id_rsa.pub) |

---

## SSH Configuration

### Local Node (INF) Setup

**SSH Key Identity**:
```
~/.ssh/id_rsa           ← Private key (secret, 0600)
~/.ssh/id_rsa.pub       ← Public key (shareable)
```

**SSH Config File** (`~/.ssh/config`):
```
Host gtw
    HostName 172.19.141.255
    User Administrator
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null

Host hub
    HostName 172.19.141.254
    User root
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null

Host gpu
    HostName www.guangzhoupeak.com
    User root
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
```

**Usage**:
```bash
ssh gtw              # Connect to Gateway
ssh hub              # Connect to Hub
ssh gpu              # Connect to GPU (cross-border)
ssh gtw "pwd"        # Run command on GTW
ssh hub "systemctl status postgresql"  # Run on HUB
```

### Remote Nodes Setup

**GTW (Windows)** - `C:\Users\Administrator\.ssh\authorized_keys`:
```
ssh-rsa AAAA...
```

**HUB (Linux)** - `/root/.ssh/authorized_keys`:
```
ssh-rsa AAAA...
```

**GPU (Linux)** - `/root/.ssh/authorized_keys`:
```
ssh-rsa AAAA...
```

---

## Security Configuration

### SSH Key Specifications

| Aspect | Requirement | Implementation |
|--------|-------------|-----------------|
| **Key Type** | RSA 4096-bit | `ssh-keygen -t rsa -b 4096` |
| **Key Location** | ~/.ssh/id_rsa | Standard location |
| **Private Key Perms** | 0600 (read-only) | Enforced by ssh-keygen |
| **Public Key Perms** | 0644 (readable) | Standard |
| **Passphrase** | Optional | For automation, can be empty |
| **Authorized Keys** | 0600 | Strict for security |
| **SSH Config** | 0600 | Standard |
| **Key Validation** | ECDSA SHA256 | SSH standard |

### Firewall Rules Required

| Node | Port | Protocol | Direction | Source | Status |
|------|------|----------|-----------|--------|--------|
| GTW | 22 | TCP | Inbound | 172.19.141.250 (INF) | Required ⚠️ |
| HUB | 22 | TCP | Inbound | 172.19.141.250 (INF) | Required ⚠️ |
| GPU | 22 | TCP | Inbound | 0.0.0.0/0 (internet) | Required ⚠️ |
| GTW | 5555 | TCP | Inbound | 172.19.141.250 (INF) | ZMQ REQ |
| GTW | 5556 | TCP | Inbound | 172.19.141.250 (INF) | ZMQ SUB |
| HUB | 5432 | TCP | Inbound | 172.19.141.250 (INF) | PostgreSQL |
| HUB | 6379 | TCP | Inbound | 172.19.141.250 (INF) | Redis |

⚠️ **Critical**: Ensure SSH ports (22) are open on all nodes before running setup script.

---

## Deployment Plan

### Phase 1: Local Key Setup
1. Generate `~/.ssh/id_rsa` if missing
2. Validate key exists and is readable
3. Extract public key from private key

### Phase 2: Configuration Generation
1. Generate `~/.ssh/config` with all 3 hosts
2. Set proper permissions (0600)
3. Validate syntax

### Phase 3: Key Distribution (Interactive)
For each remote node (GTW, HUB, GPU):
1. Prompt user for password
2. Connect via Paramiko SSH client
3. Deploy public key to `authorized_keys`
4. Validate deployment

### Phase 4: Verification
1. Test password-less SSH to each node
2. Run "Hello World" command on each
3. Generate summary report

---

## Implementation Tools

### Primary Script: `ops_universal_key_setup.py`

**Purpose**: Automated SSH key distribution to all nodes

**Features**:
- Platform-aware path handling (Windows vs Linux)
- Interactive password authentication (Paramiko)
- Batch deployment to multiple hosts
- Error handling and rollback

**Dependencies**:
```bash
pip install paramiko
```

**Usage**:
```bash
python3 scripts/ops_universal_key_setup.py
# Prompts for password for each node interactively
```

### Verification Script: `verify_ssh_mesh.py`

**Purpose**: Validate password-less SSH access

**Features**:
- Batch mode SSH (no interactive prompts)
- "Hello World" command verification
- Summary table output

**Usage**:
```bash
python3 scripts/verify_ssh_mesh.py
# Output: ✅ GTW, ✅ HUB, ✅ GPU
```

---

## Expected Workflow

### Before Setup

```
INF (control node)
├─ Manual SSH connections (password required)
│  └─ ssh Administrator@172.19.141.255  (password)
│  └─ ssh root@172.19.141.254           (password)
│  └─ ssh root@www.guangzhoupeak.com    (password)
└─ No automation possible
```

### After Setup

```
INF (control node)
├─ Password-less SSH connections
│  ├─ ssh gtw                           (no password)
│  ├─ ssh hub                           (no password)
│  └─ ssh gpu                           (no password)
│
├─ Remote command execution (automation)
│  ├─ ssh gtw "command"
│  ├─ ssh hub "systemctl status postgresql"
│  └─ ssh gpu "python3 train.py"
│
└─ Automated deployment possible
   ├─ Push code updates
   ├─ Execute maintenance scripts
   └─ Monitor services
```

---

## Success Criteria (Definition of Done)

| Criterion | Status | Verification |
|-----------|--------|--------------|
| id_rsa generated | ✅ | `ls -la ~/.ssh/id_rsa` |
| SSH config created | ✅ | `cat ~/.ssh/config \| grep Host` |
| GTW key deployed | ✅ | `ssh -o BatchMode=yes gtw echo OK` |
| HUB key deployed | ✅ | `ssh -o BatchMode=yes hub echo OK` |
| GPU key deployed | ✅ | `ssh -o BatchMode=yes gpu echo OK` |
| All 3 nodes accessible | ✅ | verify_ssh_mesh.py shows 3/3 PASS |
| No password prompts | ✅ | Manual test: `ssh gpu` (instant shell) |

---

## Troubleshooting Guide

### Issue: "Connection refused" on GTW/HUB/GPU

**Possible Causes**:
1. SSH service not running
2. Port 22 not open in firewall
3. Wrong hostname/IP address

**Fix**:
```bash
# On remote node
systemctl status ssh          # Linux
Get-Service sshd             # Windows

# Verify port 22 is open
netstat -tuln | grep 22      # Linux
netstat -ano | findstr 22    # Windows
```

### Issue: "Permission denied (publickey)"

**Cause**: Key not properly deployed to authorized_keys

**Fix**:
```bash
# On remote node
cat ~/.ssh/authorized_keys
# Should contain: ssh-rsa AAA...

# Verify permissions
ls -la ~/.ssh/authorized_keys
# Should be: -rw------- (0600)
```

### Issue: Windows SSH path issues

**Cause**: Mixed path separators (/ vs \)

**Fix**: Paramiko script handles this automatically:
```python
# Script converts paths for Windows:
# /root/.ssh/authorized_keys → \Users\Administrator\.ssh\authorized_keys
```

---

## Network Diagram (ASCII Art)

```
                     INTERNET
                        |
                        |
          ┌─────────────┴─────────────┐
          |                             |
      ┌───▼────┐                   ┌──┴──────────────┐
      │   INF  │                   │      GPU        │
      │  Local │                   │ guangzhoupeak   │
      │ Control│◄──────────SSH─────┤  .com           │
      │ Node   │                   │                 │
      └───┬────┘                   └──────────────────┘
          |
    ┌─────┴─────┐
    |           |
┌───▼────┐  ┌──┴──────┐
│   GTW  │  │   HUB   │
│Windows │  │  Linux  │
│Gateway │  │  Store  │
└────────┘  └─────────┘

All connected via SSH (Port 22)
All private keys stored in INF ~/.ssh/
```

---

## Implementation Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Generate id_rsa | 1 min | ⏳ |
| 2 | Create SSH config | 2 min | ⏳ |
| 3 | Deploy GTW key | 2 min | ⏳ |
| 4 | Deploy HUB key | 2 min | ⏳ |
| 5 | Deploy GPU key | 2 min | ⏳ |
| 6 | Verify all nodes | 3 min | ⏳ |
| **Total** | **SSH Mesh Complete** | **~12 min** | ⏳ |

---

## Next Steps

1. ✅ Create this topology document (completed)
2. ⏳ Install paramiko: `pip install paramiko`
3. ⏳ Run `ops_universal_key_setup.py` (interactive)
4. ⏳ Run `verify_ssh_mesh.py` (automated)
5. ⏳ Validate with manual `ssh gpu` test

---

**Document Created**: 2025-12-30
**Protocol**: v2.2 (Docs-as-Code)
**Owner**: DevOps Engineer
**Ticket**: #058 (Task #011.17)

🎯 **GOAL: UNIFIED SSH MESH FOR ALL 4 NODES**
