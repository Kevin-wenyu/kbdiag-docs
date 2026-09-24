---
title: "排查锁等待"
description: "找到谁在等，顺着 verify 行找到挡路者，做决定，再确认等待消失。"
weight: 20
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `6803c61` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数和时间只属于本次采样。 故障注入脚本开了一个事务，对测试表加 `ACCESS EXCLUSIVE` 锁后停着不动；另一个会话去读这张表。

## 1. 谁在等？

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:02+08:00)

[WARN] lock.waiting  会话 435317 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 435308 挡住
  verify: kbdiag session 435308  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
435308  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
435317  relation  public.kbdiag_inj_lock  AccessShareLock      false    13.7    [435308]
EXIT_CODE=1
```

- 会话 435317 等 `public.kbdiag_inj_lock` 的 `AccessShareLock` 已经 14 秒，直接挡路者是 435308。等超过 10 秒报 WARN（用 `--lock-wait-warn` 调整）。
- `lock.list` 两边都列出来了：435308 持有 `AccessExclusiveLock`（`granted true`），435317 没拿到锁，`blocked_by` 写着 435308。
- `wait_s` 从等待者最后一次状态变化算起，可能略微多报，不会少报。

## 2. 挡路者在干什么？

照 `verify` 行跑：

```bash
~/kbdiag session 435308
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:02+08:00)

[WARN] lock.waiting  会话 435317 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 435308 挡住
  verify: kbdiag session 435308  # 看挡路的会话在干什么

lock.list: 4 rows
pid     locktype       relation                mode                 granted  wait_s  blocked_by
435308  relation       public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
435308  transactionid  -                       ExclusiveLock        true     -       []
435308  virtualxid     -                       ExclusiveLock        true     -       []
435317  relation       public.kbdiag_inj_lock  AccessShareLock      false    14.3    [435308]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
435308  system   test     kbdiag_inj_lock_holder  -            client backend  idle in transaction  6099         -             14.3        14.3         14.3         Client           ClientRead  lock table kbdiag_inj_lock in access exclusive mode;
EXIT_CODE=1
```

- 挡路者是 `idle in transaction`：最后一条语句是 `lock table kbdiag_inj_lock in access exclusive mode;`，已经在等客户端（`Client / ClientRead`）14 秒，事务还开着。它什么都没在跑，锁一直占着只是因为没人提交或回滚。
- 会话报告里重复出现了那条锁等待 finding，因为被它挡住的会话也属于这个会话的全貌。
- 如果挡路者自己也在等（它的 `blocked_by` 不为空），就对它的挡路者再跑 `session`，直到找到一个没在等的。kbdiag 一次只显示一跳。
- 如果 `blocked_by` 显示 `[0]`，挡路的是一个没有会话的两阶段事务；到主库跑 `kbdiag txn` 找它。

## 3. 决定并处理

kbdiag 不会结束会话。先和应用负责人确认这个事务是干什么的。通常应该由应用提交或回滚；应用做不到时，再自己断开连接，比如在 `ksql` 里执行 `select pg_terminate_backend(435308);`，执行前确认这个 PID 仍然属于同一个用户和应用。断开挡路者会回滚它的事务。

这次测试里，注入脚本释放了持锁会话，事务随之结束。

## 4. 确认

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:04+08:00)

lock.list: 0 rows
pid  locktype  relation  mode  granted  wait_s  blocked_by
EXIT_CODE=0
```

没有等待，OK，退出码 0。一次干净的采样只说明现在没有等待；如果反复出现，要去找应用里把事务开着不关的那段逻辑。

[回到排查场景]({{< relref "/docs/scenarios" >}}) · [locks 手册]({{< relref "/docs/reference/locks" >}})
