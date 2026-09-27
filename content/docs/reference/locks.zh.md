---
title: "locks：锁等待"
description: "谁挡住了谁：先列挡路者，再列每个在等锁的会话、等了多久、被谁挡住。"
weight: 30
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。锁等待是故障注入脚本造出来的。主库上，1045715 在 idle in transaction 状态下持有表 `kbdiag_inj_lock` 的排他锁，1045724 在等它；一个两阶段（prepared）事务持有 `kbdiag_inj_2pc` 上的锁，1046007 在等它。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag locks [--limit N] [--lock-wait-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 个等锁的会话，默认 50，`0` 表示全部 |
| `--lock-wait-warn 秒` | 等锁超过多少秒报 WARN，默认 10 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只裁 `waiting` 列表，判定始终覆盖所有等待。

## 有会话在等锁

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:17+08:00)

[WARN] lock.waiting  session 1045724 has waited 30s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715
  verify: kbdiag session 1045715  # what the blocking session is doing

[WARN] lock.waiting  session 1046007 has waited 25s for AccessExclusiveLock on public.kbdiag_inj_2pc, blocked by an uncommitted two-phase transaction
  verify: kbdiag txn  # the blocker is an uncommitted two-phase transaction: its gid and how long it has been pending

blockers: 2
  pid      blocks  holds
  2PC      1       public.kbdiag_inj_2pc RowExclusiveLock
  1045715  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 2
  pid      object                  wants                waited  blocked by
  1045724  public.kbdiag_inj_lock  AccessShareLock      30s     1045715
  1046007  public.kbdiag_inj_2pc   AccessExclusiveLock  25s     2PC
EXIT_CODE=1
```

- 先列 `blockers`，因为出事时第一问是"谁挡的"。一个挡路者常常挡住几十个会话，所以按挡住的会话数排。`holds` 是挡路者在等待者想要的对象上持有的锁。
- 两阶段事务不属于任何会话，所以写成 `2PC`。它的 finding 会说明这一点，并指向 [`kbdiag txn`]({{< relref "/docs/reference/txn" >}})，在那里能看到 gid 和挂了多久。
- 挡路者自己也在排队时会标出 `(queued ahead for ...)`：服务器会把排在前面、锁模式冲突的等待者也算作挡路者。
- `waiting` 列出每个在等锁的会话，等得最久的在前。`blocked by` 只写直接挡路的会话；链条更长时，对挡路者依次跑 [`session`]({{< relref "/docs/reference/session" >}})。
- 每个等锁超过 `--lock-wait-warn` 的会话一条 `lock.waiting`；等得更短的照样列出，但不报。
- `waited` 从等待者上一次状态变化算起：V8R6 没有记录开始等锁的时间。只会多报一点，不会少报。

等锁 10 秒对 OLTP 来说已经是事故，对批处理可能是正常的，所以报 WARN 而不是 FAIL。10 秒是滤掉行锁瞬时争用的下限；批处理库可以调高。

没有等待时：

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:43+08:00)

waiting: 0
EXIT_CODE=0
```

## 在备库上

在备库上拿一个会话级的 advisory 锁：

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:19+08:00)

[WARN] lock.waiting  session 599825 has waited 14s for advisory lock, blocked by 599816
  verify: kbdiag session 599816  # what the blocking session is doing

blockers: 1
  pid     blocks  holds
  599816  1       advisory ExclusiveLock

waiting: 1
  pid     object    wants          waited  blocked by
  599825  advisory  ExclusiveLock  14s     599816
EXIT_CODE=1
```

没有表的锁（比如 advisory 锁）用锁类型当对象名。

## 权限不足

用没有监控角色的 `kbdiag_ro` 连接，主库上的等待还在：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro locks
echo EXIT_CODE=$?
```

```text
locks  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:26+08:00)

blockers: 2
  pid      blocks  holds
  2PC      1       public.kbdiag_inj_2pc RowExclusiveLock
  1045715  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 2
  pid      object                  wants                waited  blocked by
  1045724  public.kbdiag_inj_lock  AccessShareLock      ?       1045715
  1046007  public.kbdiag_inj_2pc   AccessExclusiveLock  ?       2PC
redacted: 2 rows of lock.list hide wait (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- 锁和谁挡谁看得到。这个账号看不到别的会话的时间戳，所以等待时长显示 `?`，阈值没法判。结论是 UNKNOWN，退出码 3。
- 授予 `sys_monitor` 后可以看全。

## JSON

`--json` 列出等锁会话的锁行，加上挡路者在同一对象上的锁：`pid`、`locktype`、`relation`、`mode`、`granted`、`wait_s`、`blocked_by`。`blocked_by` 保留服务器给的原样列表，两阶段事务写成 `0`。

## 已知限制

- 并行查询的 worker 有自己的 PID 和锁行，所以一条等锁的并行查询可能被算成几个被挡住的会话。
- 同一个挡路者的几个 advisory 锁会一起列在它的 `holds` 里，因为只按锁类型比对。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：有会话等锁太久 |
| 3 | UNKNOWN：数据没采到或看不到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
