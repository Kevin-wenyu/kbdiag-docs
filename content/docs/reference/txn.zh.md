---
title: "txn：事务"
description: "谁压着 vacuum 视界：开着的事务、两阶段（prepared）事务，以及其中最老的那个。"
weight: 40
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的事务是故障注入脚本造出来的：两个 idle in transaction 的会话（其中一个持有表锁）、几个在等锁的会话、一个 `pg_sleep(3600)`，还有 `kbdiag_inj_2pc`，一个既没提交也没回滚的两阶段事务。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag txn [--limit N] [--xact-warn 秒] [--prepared-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 个事务，默认 50，`0` 表示全部 |
| `--xact-warn 秒` | 事务开了超过多少秒报 WARN，默认 300 |
| `--prepared-warn 秒` | 两阶段事务挂了超过多少秒报 WARN，默认 900 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只影响显示，判定始终覆盖全部事务。

## 默认输出

```bash
~/kbdiag txn
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:18+08:00)

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5
  pid      user    database  application                 state                xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      idle in transaction  31s   6343  -     lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      active               30s   -     6343  select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         idle in transaction  29s   6344  -     select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  active               25s   6347  6343  lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       active               25s   -     6343  select pg_sleep(3600);

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      26s  6346
EXIT_CODE=0
```

- `oldest xid` 是所有会话和两阶段事务里最老的事务号，以及谁持有它。这里 1045715 的事务号是 6343，另外三个会话的快照（`xmin`）是在 6343 还没结束时拿的。VACUUM 不能清理比它新的行版本，所以这一行回答"谁压着 vacuum 视界"。事务号按 2^32 取模比较，和服务器一样。
- `open transactions` 列出在事务里的会话：有事务开始时间、事务号或快照 xmin 的。事务最老的在前。`xid` 在第一次写的时候才分配，只读事务只有 `xmin`。
- `prepared` 列出所有两阶段事务：gid、属主、库、挂了多久、事务号。它们不属于任何会话，所以 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 看不到。
- 都没到默认阈值，所以结论是 OK。

## 报 WARN

把两个阈值都降到 10 秒：

```bash
~/kbdiag txn --xact-warn 10 --prepared-warn 10
echo EXIT_CODE=$?
```

```text
txn  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:21+08:00)

[WARN] txn.long  session 1045715 has had a transaction open for 34s, now idle in transaction
  verify: kbdiag session 1045715  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1045724 has had a transaction open for 34s, now active
  verify: kbdiag session 1045724  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1045809 has had a transaction open for 32s, now idle in transaction
  verify: kbdiag session 1045809  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1046007 has had a transaction open for 28s, now active
  verify: kbdiag session 1046007  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.long  session 1046088 has had a transaction open for 28s, now active
  verify: kbdiag session 1046088  # what it is running, which locks it holds, whether it blocks anyone

[WARN] txn.prepared  two-phase transaction kbdiag_inj_2pc prepared 29s ago and not finished, holding back the vacuum horizon
  fix: ROLLBACK PREPARED 'kbdiag_inj_2pc'  # check with the application whether to commit (COMMIT PREPARED) or roll back; run it connected to database test, outside a transaction block

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5
  pid      user    database  application                 state                xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      idle in transaction  34s   6343  -     lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      active               34s   -     6343  select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         idle in transaction  32s   6344  -     select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  active               28s   6347  6343  lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       active               28s   -     6343  select pg_sleep(3600);

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      29s  6346
EXIT_CODE=1
```

- `txn.long`：每个开了超过 `--xact-warn` 的事务一条，`verify` 行指向对应的会话。
- `txn.prepared`：挂了超过 `--prepared-warn` 的两阶段事务。在有人提交或回滚之前，它一直持有锁、压着 vacuum 视界。`fix` 行给出语句，kbdiag 只打印，不执行。注释写明：先和应用确认是提交（`COMMIT PREPARED`）还是回滚，连到这个事务所在的库，在事务块外执行。
- gid 含控制字符时，终端上显示的是转义后的文本，照抄执行匹配不到。这时不给 `fix` 行，`verify` 行提示从 `--json` 取原始 gid。
- 两条都只报 WARN，不报 FAIL：它们的危害（表膨胀、锁长期不放）是以后的事；它们眼下挡住的会话由 [`locks`]({{< relref "/docs/reference/locks" >}}) 报。
- 300 秒和 900 秒在服务器端没有对应的客观线。300 秒会碰上正常的批处理，批处理库可以调高。
- 默认阈值下，idle in transaction 超过 300 秒的会话也会被 `sessions` 报成 `session.idle_in_txn`。两条回答的问题不同。

## 在备库上

```bash
~/kbdiag txn
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:20+08:00)

oldest xid: 6354  (599825 xmin)

open transactions: 1
  pid     user    database  application             state   xact  xid  xmin  sql
  599825  system  test      kbdiag_inj_lock_waiter  active  14s   -    6354  select pg_advisory_lock(424242);

txn.prepared: not_applicable  (a standby cannot see the primary's two-phase transactions: run kbdiag txn on the primary)
EXIT_CODE=0
```

备库看不到主库的两阶段事务，所以 `txn.prepared` 是 `not_applicable`。它不表示"没有"，也不影响结论。到主库上跑 `txn`。

## 权限不足

用没有监控角色的 `kbdiag_ro` 连接：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro txn
echo EXIT_CODE=$?
```

```text
txn  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:27+08:00)

oldest xid: 6343  (1045715 xid, 1045724 xmin, 1046007 xmin, 1046088 xmin)

open transactions: 5, 10 sessions hidden
  pid      user    database  application                 state  xact  xid   xmin  sql
  1045715  system  test      kbdiag_inj_lock_holder      ?      ?     6343  -     ?
  1045724  system  test      kbdiag_inj_lock_waiter      ?      ?     -     6343  ?
  1045809  system  test      kbdiag_inj_idle_txn         ?      ?     6344  -     ?
  1046007  system  test      kbdiag_inj_prepared_waiter  ?      ?     6347  6343  ?
  1046088  system  test      kbdiag_inj_long_query       ?      ?     -     6343  ?

prepared: 1
  gid             owner   database  age  xid
  kbdiag_inj_2pc  system  test      35s  6346
redacted: 15 rows of session.activity hide state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- KingbaseES 对任何账号都显示别人会话的事务号和 xmin，所以 `oldest xid` 和开着的事务照样找得出来，只是状态、时长和 SQL 显示 `?`。
- 既没有 xid 也没有 xmin 的遮蔽会话只计数（`10 sessions hidden`）：它们多半是 idle，不能说成事务。
- 结论是 UNKNOWN，退出码 3。授予 `sys_monitor` 后可以看全。
- 会话活动或两阶段事务有一项没采到时，`oldest xid` 会注明可能有更老的；一个持有者都没找到时显示 `unknown`。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：有长事务，或两阶段事务挂得太久 |
| 3 | UNKNOWN：数据没采到或看不到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
