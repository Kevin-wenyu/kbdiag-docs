---
title: "排查锁等待"
description: "找到谁在等，顺着 verify 行找到挡路者，做决定，再确认等待消失。"
weight: 20
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数和时间只属于本次采样。故障注入脚本开了一个事务，对测试表加 `ACCESS EXCLUSIVE` 锁后停着不动；另一个会话去读这张表。

## 1. 谁在等？

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:33+08:00)

[WARN] lock.waiting  session 1048829 has waited 13s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1048819
  verify: kbdiag session 1048819  # what the blocking session is doing

blockers: 1
  pid      blocks  holds
  1048819  1       public.kbdiag_inj_lock AccessExclusiveLock

waiting: 1
  pid      object                  wants            waited  blocked by
  1048829  public.kbdiag_inj_lock  AccessShareLock  13s     1048819
EXIT_CODE=1
```

- 会话 1048829 等 `public.kbdiag_inj_lock` 的 `AccessShareLock` 已经 13 秒，直接挡路者是 1048819。等超过 10 秒报 WARN（用 `--lock-wait-warn` 调整）。
- `blockers` 排在前面，因为第一个问题是谁挡的：1048819 挡住了 1 个会话，持有这张表的 `AccessExclusiveLock`。一个挡路者挡住几十个会话时，它就是第一行。
- `waiting` 逐个列出等锁的会话，等得最久的在前。时长从等待者最后一次状态变化算起，可能略微多报，不会少报。

## 2. 挡路者在干什么？

照 `verify` 行跑：

```bash
~/kbdiag session 1048819
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:34+08:00)

[WARN] lock.waiting  session 1048829 has waited 14s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1048819

session 1048819
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       local
  type         client backend
  state        idle in transaction  (for 14s)
  xact         14s
  query        14s
  wait         -
  xid / xmin   6351 / -

last sql
  lock table kbdiag_inj_lock in access exclusive mode;

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1048829  public.kbdiag_inj_lock  AccessShareLock  14s

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
EXIT_CODE=1
```

- 挡路者是 `idle in transaction`：最后一条语句是 `lock table kbdiag_inj_lock in access exclusive mode;`，已经在等客户端 14 秒，事务还开着。它什么都没在跑，锁一直占着只是因为没人提交或回滚。
- `blocking` 是它挡住了谁，`holds` 是对方想要的那把锁。
- 如果 `waiting for` 不为空，说明挡路者自己也在等：对它的挡路者再跑 `session`，直到找到一个没在等的。kbdiag 一次只显示一跳。
- 如果挡路者显示为 `2PC`，挡路的是一个没有会话的两阶段事务；到主库跑 `kbdiag txn` 找它。

## 3. 决定并处理

kbdiag 不会结束会话。先和应用负责人确认这个事务是干什么的。通常应该由应用提交或回滚；应用做不到时，再自己断开连接，比如在 `ksql` 里执行 `select pg_terminate_backend(1048819);`，执行前确认这个 PID 仍然属于同一个用户和应用。断开挡路者会回滚它的事务。

这次测试里，注入脚本释放了持锁会话，事务随之结束。

## 4. 确认

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:36+08:00)

waiting: 0
EXIT_CODE=0
```

没有等待，OK，退出码 0。一次干净的采样只说明现在没有等待；如果反复出现，要去找应用里把事务开着不关的那段逻辑。

[回到排查场景]({{< relref "/docs/scenarios" >}}) · [locks 手册]({{< relref "/docs/reference/locks" >}})
