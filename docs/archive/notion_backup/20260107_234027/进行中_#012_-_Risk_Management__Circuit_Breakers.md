# #012 - Risk Management & Circuit Breakers

**Status**: 进行中
**Page ID**: 2d2c8858-2b4e-818f-a9f5-cd0ddfe8d1cf
**URL**: https://www.notion.so/012-Risk-Management-Circuit-Breakers-2d2c88582b4e818fa9f5cd0ddfe8d1cf
**Created**: 2025-12-23T08:30:00.000Z
**Last Edited**: 2026-01-01T22:47:00.000Z

---

## Properties

- **类型**: 核心
- **优先级**: P0
- **状态**: 进行中
- **标题**: #012 - Risk Management & Circuit Breakers

---

## Content

---

## 📋 技术详情

### 交易网关通信架构

放弃了高延迟的 HTTP 轮询，采用 ZeroMQ (ZMQ) 实现毫秒级通讯。

* PUB 模式: MT5 终端广播实时 Tick 数据。
* REP 模式: 接收 Python 端的交易指令并返回结果。
### 💻 核心代码

```python
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
```

---

## 📋 技术详情

### 交易网关通信架构

放弃了高延迟的 HTTP 轮询，采用 ZeroMQ (ZMQ) 实现毫秒级通讯。

* PUB 模式: MT5 终端广播实时 Tick 数据。
* REP 模式: 接收 Python 端的交易指令并返回结果。
### 💻 核心代码

```python
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
```

---

## 📋 技术详情

### 交易网关通信架构

放弃了高延迟的 HTTP 轮询，采用 ZeroMQ (ZMQ) 实现毫秒级通讯。

* PUB 模式: MT5 终端广播实时 Tick 数据。
* REP 模式: 接收 Python 端的交易指令并返回结果。
### 💻 核心代码

```python
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
```

