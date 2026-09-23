---
title: "txn：事务"
description: "列出开着的事务和两阶段提交（prepare 后未结束）的事务，标出过长的。"
weight: 40
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `0a4d61e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的事务是故障注入脚本造出来的：365547 开了事务后停在 idle in transaction，`kbdiag_inj_2pc` 是一个 prepare 后没有提交也没有回滚的两阶段事务。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag txn [--limit N] [--xact-warn 秒] [--xact-fail 秒] [--prepared-fail 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 个会话，默认 50，`0` 表示全部 |
| `--xact-warn 秒` | 事务开了多少秒报 WARN，默认 300 |
| `--xact-fail 秒` | 事务开了多少秒报 FAIL，默认 1800 |
| `--prepared-fail 秒` | 两阶段事务 prepare 后多少秒报 FAIL，默认 900 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只影响显示，判定始终覆盖全部会话。

## 默认输出

```bash
~/kbdiag txn --limit 5
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:03+08:00)

session.activity: 1 rows
pid     usename  datname  application_name     client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
365547  system   test     kbdiag_inj_idle_txn  -            client backend  idle in transaction  6019         -             5.7         4.7          3.7          Client           ClientRead  select txid_current() as kbdiag_last, pg_sleep(1);

txn.prepared: 1 rows
gid             owner   database  prepared_at                age_s  transaction
kbdiag_inj_2pc  system  test      2026-09-24T04:38:56+08:00  7.4    6018
EXIT_CODE=0
```

- `session.activity` 只列在事务里的会话：有事务开始时间、事务号（`backend_xid`）或快照（`backend_xmin`）的会话。看不到状态的会话（权限不足、关了 track_activities）也列出来。列和 `sessions` 一样。
- `txn.prepared` 列出所有两阶段事务。它们不属于任何会话，所以 `sessions` 看不到。
- 两者都没到默认阈值，结论 OK。

## 出现 WARN 和 FAIL

把阈值调低：

```bash
~/kbdiag txn --xact-warn 2 --prepared-fail 2 --limit 5
echo EXIT_CODE=$?
```

```text
txn  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:04+08:00)

[WARN] txn.long  会话 365547 的事务已开了 6 秒，当前 idle in transaction
  verify: kbdiag session 365547  # 看它在跑什么、持有哪些锁、有没有挡住别人

[FAIL] txn.prepared  两阶段事务 kbdiag_inj_2pc 已 prepare 8 秒未结束，压着视界
  fix: ROLLBACK PREPARED 'kbdiag_inj_2pc'  # 先和应用确认它该提交还是回滚（提交用 COMMIT PREPARED）；要连到库 test 执行，且不能放在事务块里

session.activity: 1 rows
pid     usename  datname  application_name     client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
365547  system   test     kbdiag_inj_idle_txn  -            client backend  idle in transaction  6019         -             6.2         5.2          4.2          Client           ClientRead  select txid_current() as kbdiag_last, pg_sleep(1);

txn.prepared: 1 rows
gid             owner   database  prepared_at                age_s  transaction
kbdiag_inj_2pc  system  test      2026-09-24T04:38:56+08:00  7.9    6018
EXIT_CODE=2
```

- 365547 超过 `--xact-warn`，但没到 `--xact-fail`（默认 1800 秒），所以是 WARN。
- 两阶段事务只有 FAIL 一级：它会一直压着 VACUUM 的清理视界、一直拿着锁，直到有人提交或回滚。
- `fix` 行给出处理语句。kbdiag 只打印，不执行；要先和应用确认该提交还是回滚。
- 有 FAIL 时退出码 2。

## 在备库上

```bash
~/kbdiag txn --limit 3
echo EXIT_CODE=$?
```

```text
txn  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-24T04:39:05+08:00)

session.activity: 0 rows
pid  usename  datname  application_name  client_addr  backend_type  state  backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query

txn.prepared: not_applicable  备库看不到主库的两阶段提交事务，请在主库上运行 kbdiag txn
EXIT_CODE=0
```

- 主库上的两阶段事务在备库上查不到，所以备库上 `txn.prepared` 是 `not_applicable`，不算"没有"，也不影响结论。
- 两阶段事务要在主库上看。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
