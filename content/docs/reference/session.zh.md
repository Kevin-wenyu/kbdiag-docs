---
title: "session：单个会话"
description: "一个会话的完整 SQL、在等什么、挡住了谁、持有哪些锁。"
weight: 20
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的会话是故障注入脚本造出来的：1045715 在 idle in transaction 状态下持有表 `kbdiag_inj_lock` 的排他锁，1045724 在等它，1045809 是另一个 idle in transaction 的会话。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag session <pid> [--lock-wait-warn 秒] [--idle-in-txn-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `<pid>` | 要看的会话 PID，必填 |
| `--lock-wait-warn 秒` | 等锁超过多少秒报 WARN，默认 10 |
| `--idle-in-txn-warn 秒` | idle in transaction 超过多少秒报 WARN，默认 300 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。阈值和 finding 与 `sessions`、[`locks`]({{< relref "/docs/reference/locks" >}}) 相同。

## 在等锁的会话

```bash
~/kbdiag session 1045724
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:22+08:00)

[WARN] lock.waiting  session 1045724 has waited 35s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715
  verify: kbdiag session 1045715  # what the blocking session is doing

session 1045724
  user         system
  database     test
  application  kbdiag_inj_lock_waiter
  client       local
  type         client backend
  state        active  (for 35s)
  xact         35s
  query        35s
  wait         Lock:relation
  xid / xmin   - / 6343

sql
  select count(*) from kbdiag_inj_lock;

waiting for: 1
  object                  wants            waited  blocked by
  public.kbdiag_inj_lock  AccessShareLock  35s     1045715

blocking: 0

holds: 0
EXIT_CODE=1
```

- 最上面的键值块说明这个会话是谁（用户、库、应用、客户端、类型）、在干什么：状态和处于这个状态多久、事务和语句时长、等待事件、事务号和快照 xmin。
- `sql` 是完整的语句，保留原来的换行。这是唯一能看到完整 SQL 的命令。idle 的会话标题写 `last sql`，因为那条语句已经结束了。
- `waiting for` 是它想要的锁、等了多久、被谁直接挡住。
- 它等了 35 秒，超过默认的 10 秒，所以有一条 `lock.waiting` WARN，退出码 1。`verify` 行指向挡路的会话。
- `waited` 从会话上一次状态变化算起，只会多报一点，不会少报。

## 挡路的会话

```bash
~/kbdiag session 1045715
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:21+08:00)

[WARN] lock.waiting  session 1045724 has waited 34s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715

session 1045715
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       local
  type         client backend
  state        idle in transaction  (for 34s)
  xact         34s
  query        34s
  wait         -
  xid / xmin   6343 / -

last sql
  lock table kbdiag_inj_lock in access exclusive mode;

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1045724  public.kbdiag_inj_lock  AccessShareLock  34s

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
EXIT_CODE=1
```

- `blocking` 列出在等这个会话所持有的锁的会话，`holds` 列出它持有的锁。
- 每个事务都持有自己的 `virtualxid` 和 `transactionid` 锁，除非有人在等这类锁，否则 `holds` 里不列；事务号在上面的键值块里。
- 行锁会写明类型，例如 `public.t (tuple)`，免得被读成表锁。
- 这条 WARN 是等待者的 `lock.waiting`：它说的是这个会话已经挡住别人 34 秒，这是这个会话自己的问题。它没有 `verify` 行，因为会指回这里。
- 这个会话 idle in transaction 已 34 秒：拿了锁一直没提交。它自己的 `session.idle_in_txn` 要到 300 秒才报。

## idle in transaction

把阈值降到 10 秒：

```bash
~/kbdiag session 1045809 --idle-in-txn-warn 10
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:23+08:00)

[WARN] session.idle_in_txn  session 1045809 has been idle in transaction for 32s

session 1045809
  user         system
  database     test
  application  kbdiag_inj_idle_txn
  client       local
  type         client backend
  state        idle in transaction  (for 33s)
  xact         35s
  query        34s
  wait         -
  xid / xmin   6344 / -

last sql
  select txid_current() as kbdiag_last, pg_sleep(1);

waiting for: 0

blocking: 0

holds: 0
EXIT_CODE=1
```

这个会话有事务号，但没持有别人想要的锁，所以 `holds` 是空的。它压着的是 vacuum 视界，见 [`txn`]({{< relref "/docs/reference/txn" >}})。

## 权限不足

用没有监控角色的 `kbdiag_ro` 连接，看挡路的会话：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro session 1045715
echo EXIT_CODE=$?
```

```text
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:28+08:00)

session 1045715
  user         system
  database     test
  application  kbdiag_inj_lock_holder
  client       ?
  type         ?
  state        ?
  xact         ?
  query        ?
  wait         ?
  xid / xmin   6343 / -

sql
  ?

waiting for: 0

blocking: 1
  pid      object                  wants            waited
  1045724  public.kbdiag_inj_lock  AccessShareLock  ?

holds: 1
  object                  mode
  public.kbdiag_inj_lock  AccessExclusiveLock
redacted: 1 row of session.activity hides state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
redacted: 1 row of lock.list hides wait (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- 用户、库、应用看得到，事务号和 xmin 也看得到；状态、时长、客户端、类型、等待事件和 SQL 显示 `?`。
- 锁和谁挡谁看得到，别的会话等了多久看不到。
- 这个会话判不了，所以结论是 UNKNOWN、退出码 3。授予 `sys_monitor` 后可以看全。

## 会话不存在

```bash
~/kbdiag session 999999
echo EXIT_CODE=$?
```

```text
kbdiag: no session with pid 999999 (it may have ended)
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:46+08:00)

session 999999: not found (it may have ended)
EXIT_CODE=3
```

找不到这个 PID 时（可能已经结束），标准错误输出一行说明，结论是 UNKNOWN，退出码 3。不给 PID 是用法错误，退出码 64。

## JSON

`--json` 带文本所依据的活动行和锁行，值是原始值：时长以秒计，锁行一行不省，包括 `virtualxid`。下面是上面那个等待者的 `lock.waiting` finding，字段可供脚本使用：

```json
{
  "id": "lock.waiting",
  "level": "WARN",
  "symptom": "session 1045724 has waited 37s for AccessShareLock on public.kbdiag_inj_lock, blocked by 1045715",
  "evidence": [
    {
      "probe_id": "lock.list",
      "fields": {
        "blocker_pids": [
          1045715
        ],
        "lock_mode": "AccessShareLock",
        "relation": "public.kbdiag_inj_lock",
        "wait_s": 37.3,
        "waiter_pid": 1045724
      }
    }
  ],
  "cause": null,
  "next": [
    {
      "kind": "verify",
      "command": "kbdiag session 1045715",
      "note": "what the blocking session is doing"
    }
  ]
}
```

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：等锁或 idle in transaction 超过阈值 |
| 3 | UNKNOWN：会话不存在，或数据没采到、看不到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
