---
title: "认识 kbdiag"
description: "面向 KingbaseES 的只读命令行诊断：给结论、给证据、给下一步。"
weight: 10
---

## 解决什么问题？ {#purpose}

数据库感觉不对劲时，最先要问的往往是同几件事：谁连着、谁在等锁又被谁挡住、哪个事务开了太久、备库的槽是不是在堆 WAL。回答它们要记住一堆系统视图，再手工关联起来。

kbdiag 把这些问题做成命令。每条命令对运行中的实例做一次只读查询，输出结论、结论依据的证据，以及下一步该跑的命令。

## 适合谁？ {#audience}

| 读者 | 从哪开始 | 得到什么 |
|---|---|---|
| 运维 | `status`、`sessions` | 实例事实、连接压力、停在 idle in transaction 的会话 |
| DBA | `locks`、`session <pid>`、`txn` | 谁挡住谁、一个会话持有什么、老事务和两阶段事务 |
| 监控脚本 | 任意命令，`--json` | 退出码里的结论和字段稳定的 JSON 报告 |

## 看、查、断 {#layers}

1. **看**：一条命令给一个事实，比如实例的角色、连接占用（`status`）。
2. **查**：单个维度深查，比如锁等待（`locks`）或某一个会话（`session <pid>`）。
3. **断**：把多个维度关联到根因，留给后续版本。当前版本只做看和查；每条 finding 的 `verify` 行会告诉你下一步查什么。

## 运行环境 {#requirements}

- KingbaseES V8R6（在 V008R006C009B0014 上测试），单机或 repmgr 主备。
- 单个 Linux 静态二进制（amd64 或 arm64）。它自己实现线协议：不需要 `ksql`、运行时或常驻服务。
- 在数据库主机上以 `kingbase` OS 用户走本地 socket 运行，能看到全部信息。其他账号和 TCP 也能用；看不到的部分会明说，不会藏起来。
- repmgr 可选。

## 操作边界 {#boundaries}

- **只读。** 每个连接都是只读事务并设了 `lock_timeout`。`ROLLBACK PREPARED` 之类的处理建议只打印出来让你判断，从不执行。
- **不假装 OK。** 判定要用的数据没采到或看不到、看得到的部分又没有 WARN 或 FAIL 时，结论是 UNKNOWN（退出码 3），不是 OK。
- **一次查看，不是监控。** 每次运行只是一个采样。这一次干净，不代表刚才或待会儿也干净。

kbdiag 2.0 是 Go 重写版。shell 版（`v1.x`）已冻结，它的其他命令（健康检查、报告、性能和建议类）在 [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0) 里。

## 下一步 {#next}

[第一次检查](../get-started/) · [功能概览](../features/) · [查看源码](https://github.com/Kevin-wenyu/kbdiag)
