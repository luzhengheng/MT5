# #016 - Basic Order Execution Logic

**Status**: 进行中
**Page ID**: 2d3c8858-2b4e-81ba-8be8-c810d0eec363
**URL**: https://www.notion.so/016-Basic-Order-Execution-Logic-2d3c88582b4e81ba8be8c810d0eec363
**Created**: 2025-12-24T13:37:00.000Z
**Last Edited**: 2026-01-02T18:28:00.000Z

---

## Properties

- **类型**: Feature
- **状态**: 进行中
- **标题**: #016 - Basic Order Execution Logic

---

## Content

---

## 🎯 目标

实现基础订单执行逻辑，将策略信号转换为 MT5 订单。

## ✅ 交付内容

* OrderExecutor: 封装 `order_send` 函数。
* TradeRequest: 标准化交易请求结构体。
* Error Handling: 处理重新报价 (Requote) 和滑点异常。
