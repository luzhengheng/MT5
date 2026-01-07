# #017 - Market Data Service (ZMQ Pub/Sub)

**Status**: 进行中
**Page ID**: 2d3c8858-2b4e-8139-a7a3-f7c8693cb1a6
**URL**: https://www.notion.so/017-Market-Data-Service-ZMQ-Pub-Sub-2d3c88582b4e8139a7a3f7c8693cb1a6
**Created**: 2025-12-24T15:00:00.000Z
**Last Edited**: 2026-01-02T18:10:00.000Z

---

## Properties

- **类型**: Feature
- **状态**: 进行中
- **标题**: #017 - Market Data Service (ZMQ Pub/Sub)

---

## Content

---

## 🎯 目标

搭建高吞吐量的实时行情分发服务。

## ✅ 交付内容

* MarketDataService: 订阅 MT5 `OnTick` 事件。
* ZMQ Publisher: 通过 TCP 5556 端口广播行情更新数据。
