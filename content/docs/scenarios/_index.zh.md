---
title: "按场景排查"
description: "从现象到证据，再确认处置结果。"
weight: 40
---

先确认连接的是目标实例，再按现象选择入口。以下示例来自隔离测试会话；不需要在生产环境复现测试负载。

- [正在运行的慢 SQL](slow-sql/)：找到 PID，区分主动等待与执行问题。
- [锁等待](lock-waits/)：核对等待方与阻塞方，再决定如何处理事务。
- [真实巡检输出]({{< relref "/docs/get-started/reading-results" >}})：理解 WARN 和退出码。
