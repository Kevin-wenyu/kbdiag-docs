---
title: "按场景排查"
description: "从症状走到证据，再确认结果。"
weight: 40
---

照场景走之前，先确认连的是目标实例。示例来自测试集群上的故障注入脚本，不需要在生产环境复现。

- [长时间运行的 SQL](slow-sql/)：找到跑了一阵的语句，看它在等什么。
- [锁等待](lock-waits/)：找到谁在等，顺着 verify 行找到挡路者，再确认等待消失。
- [读懂一个真实结果]({{< relref "/docs/get-started/reading-results" >}})：逐行解读一个 WARN 的文本和 JSON 输出。
