---
title: "功能概览"
description: "按要回答的问题选命令：实例、会话、锁、事务、等待、复制槽。"
weight: 20
---

从你要回答的问题出发。示例假设二进制放在 `~/kbdiag`；全部参数和输出字段见[使用手册](../reference/)。

## 实例概况 {#instance}

**这是个什么实例，基本面正常吗？**

```bash
~/kbdiag status
```

版本、角色（主 / 备）、运行时长、连接数、给哪些备库发 WAL（备库则是从哪里收 WAL）、各库大小，以及数据目录所在的磁盘。普通用户可用的连接（`max_connections` 减去 `superuser_reserved_connections`）全部占满时 FAIL；备库没在收 WAL 时 WARN。

→ [status]({{< relref "/docs/reference/status" >}})

## 会话 {#sessions}

**连接是谁占的，哪些会话在干活，某个会话在干什么？**

```bash
~/kbdiag sessions
~/kbdiag session <pid>
```

`sessions` 按用户、库、应用、客户端给连接计数，再列出不是 idle 的客户端会话，事务最久的排前面；idle in transaction 超过 300 秒报 WARN。`session <pid>` 看单个会话的全貌：它是谁、完整 SQL、在等什么锁、被谁挡住、挡住了谁、持有什么。

→ [sessions]({{< relref "/docs/reference/sessions" >}}) · [session]({{< relref "/docs/reference/session" >}})

## 锁 {#locks}

**谁在等锁，被哪个会话挡住？**

```bash
~/kbdiag locks
```

先列挡路者，挡住会话最多的在最上面；再列每个等锁的会话，等得最久的在前。等超过 10 秒的各报一条 WARN，写明直接挡路者，`verify` 行指向挡路者的 `session`。挡路链有好几层时，一跳一跳往上找。

→ [locks]({{< relref "/docs/reference/locks" >}}) · [场景：锁等待]({{< relref "/docs/scenarios/lock-waits" >}})

## 事务 {#txn}

**哪个事务开得太久，有没有被遗忘的两阶段事务？**

```bash
~/kbdiag txn
```

先给最老的事务号，以及持有它的会话或两阶段事务，再列开着的事务和两阶段事务。开着的事务 300 秒报 WARN，两阶段事务 900 秒报 WARN，并打印 `ROLLBACK PREPARED` / `COMMIT PREPARED` 建议供你决定。两阶段事务只在主库上查得到；备库上报告为不适用。

→ [txn]({{< relref "/docs/reference/txn" >}})

## 等待事件 {#waits}

**会话现在都在等什么？**

```bash
~/kbdiag waits
```

把在干活的会话按等待事件和状态分组，附带 PID，扎堆最多的在前；idle 的会话和在主循环里空闲的后台进程只计数。只汇总、不设阈值；等了多久、被谁挡住，用 `locks` 看。

→ [waits]({{< relref "/docs/reference/waits" >}}) · [场景：长时间运行的 SQL]({{< relref "/docs/scenarios/slow-sql" >}})

## 复制槽 {#slots}

**有没有槽在为一个已经不在的备库保留 WAL？**

```bash
~/kbdiag slots
```

列出每个槽的消费者、保留的 WAL 和 `xmin`。未激活的槽会一直保留 WAL，带 `xmin` 的还会压着清理视界，所以直接报 WARN。`verify` 行让你到这个槽的下游节点上跑 `status`，确认它还在不在收 WAL。kbdiag 从不删槽。

→ [slots]({{< relref "/docs/reference/slots" >}})

## 脚本集成 {#automation}

每条命令都按结论设置退出码，并支持 `--json`：

```bash
~/kbdiag --json locks
echo $?   # 0 OK，1 WARN，2 FAIL，3 UNKNOWN，64 参数错误，69 连不上
```

UNKNOWN 表示有东西没采到或看不到，所以 kbdiag 不说 OK。69 只表示连接失败；连上了但答不上来的库是 UNKNOWN。见[退出码](../get-started/#exit-codes)。

## 当前版本还没有的 {#not-yet}

复制延迟、repmgr 集群检查、慢 SQL 历史、vacuum 与膨胀、死锁历史以及关联诊断，kbdiag 2.0 还没有。需要健康检查和报告的话，冻结的 shell 版 [`v1.0.0`](https://github.com/Kevin-wenyu/kbdiag/releases/tag/v1.0.0) 仍然可用。
