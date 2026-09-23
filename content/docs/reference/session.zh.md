---
title: "session：看一个会话"
description: "看一个会话在跑什么、等什么、持有哪些锁、被谁挡住或挡住了谁。"
weight: 20
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `0a4d61e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的锁等待是故障注入脚本造出来的：367208 拿着表 `kbdiag_inj_lock` 的排他锁不提交，367217 等它。PID、计数与时间只属于本次采样。

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

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 看等锁的会话

```bash
~/kbdiag session 367217
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:41:05+08:00)

[WARN] lock.waiting  会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住
  verify: kbdiag session 367208  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype    relation                mode             granted  wait_s  blocked_by
367217  virtualxid  -                       ExclusiveLock    true     -       []
367217  relation    public.kbdiag_inj_lock  AccessShareLock  false    12.9    [367208]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
367217  system   test     kbdiag_inj_lock_waiter  -            client backend  active  -            6022          12.9        12.9         12.9         Lock             relation    select count(*) from kbdiag_inj_lock;
EXIT_CODE=1
```

- `lock.list` 是这个会话自己的锁；`granted=false` 那行就是它在等的锁，`blocked_by` 是直接挡住它的会话。
- `session.activity` 是这个会话的一行活动信息，列和 `sessions` 一样。
- 等锁 13 秒超过默认的 10 秒，所以 WARN，退出码 1。`verify` 行给出下一步：去看挡路的 367208。
- `wait_s` 是近似值：用会话最近一次状态变化到现在的时间估算。

## 看挡路的会话

```bash
~/kbdiag session 367208
echo EXIT_CODE=$?
```

```text
session  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:41:05+08:00)

[WARN] lock.waiting  会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住
  verify: kbdiag session 367208  # 看挡路的会话在干什么

lock.list: 4 rows
pid     locktype       relation                mode                 granted  wait_s  blocked_by
367208  relation       public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
367208  transactionid  -                       ExclusiveLock        true     -       []
367208  virtualxid     -                       ExclusiveLock        true     -       []
367217  relation       public.kbdiag_inj_lock  AccessShareLock      false    13      [367208]

session.activity: 1 rows
pid     usename  datname  application_name        client_addr  backend_type    state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
367208  system   test     kbdiag_inj_lock_holder  -            client backend  idle in transaction  6022         -             13.1        13.1         13.1         Client           ClientRead  lock table kbdiag_inj_lock in access exclusive mode;
EXIT_CODE=1
```

- 对挡路的会话，`lock.list` 除了它自己的锁，还列出被它挡住的会话在等的锁（最后一行 367217）。
- 它自己处于 idle in transaction：拿着锁、事务没结束、又不在执行。这是常见的"应用忘了提交"的样子。
- 它只在 idle in transaction 满 300 秒时才会报 `session.idle_in_txn`；这里的 WARN 来自它挡住的 367217。

`--json` 输出同样的内容。`lock.waiting` 的 `evidence` 带 `waiter_pid`、`blocker_pids`、`relation`、`lock_mode`、`wait_s`，便于脚本处理：

```json
{
  "id": "lock.waiting",
  "level": "WARN",
  "symptom": "会话 367217 等 public.kbdiag_inj_lock 的 AccessShareLock 已 13 秒，被 367208 挡住",
  "evidence": [
    {
      "probe_id": "lock.list",
      "fields": {
        "blocker_pids": [367208],
        "lock_mode": "AccessShareLock",
        "relation": "public.kbdiag_inj_lock",
        "wait_s": 13.1,
        "waiter_pid": 367217
      }
    }
  ],
  "cause": null,
  "next": [{"kind": "verify", "command": "kbdiag session 367208", "note": "看挡路的会话在干什么"}]
}
```

## 会话不存在

```bash
~/kbdiag session 999999
echo EXIT_CODE=$?
```

```text
kbdiag: no session with pid 999999 (it may have ended)
session  UNKNOWN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:55+08:00)

lock.list: 0 rows
pid  locktype  relation  mode  granted  wait_s  blocked_by

session.activity: 0 rows
pid  usename  datname  application_name  client_addr  backend_type  state  backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
EXIT_CODE=3
```

- 找不到这个 PID（可能已经结束）时，提示写到标准错误，结论是 UNKNOWN，退出码 3。
- 不带 PID 是参数错误，退出码 64。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 2 | FAIL |
| 3 | UNKNOWN：会话不存在，或有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
