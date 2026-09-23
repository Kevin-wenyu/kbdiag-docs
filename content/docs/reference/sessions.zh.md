---
title: "sessions：列会话"
description: "列出会话，标出长时间 idle in transaction 的会话。"
weight: 10
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `84c883e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的两个业务会话是故障注入脚本造出来的；PID、计数与时间只属于本次采样。

Go 版正式发布（`v2.0.0-alpha.1`）之前，`sessions` 是唯一可用的命令。

## 用法

```text
kbdiag sessions [--active] [--limit N] [--idle-in-txn-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--active` | 只显示正在执行查询的会话；看不到状态的行（权限不足、会话关了 track_activities）也照样显示 |
| `--limit N` | 最多显示 N 行，默认 50，`0` 表示全部 |
| `--idle-in-txn-warn 秒` | idle in transaction 超过多少秒报 WARN，默认 300 |
| `--json` | 输出 JSON |

连接参数 `--host`、`-p`、`-d`、`-U`、`--timeout` 是全局参数，默认 `/tmp` 本地 socket、端口 54321、库 `test`、用户 `system`；密码从 `PGPASSWORD` 或 `~/.pgpass` 取。连接是只读事务，并设了 `lock_timeout`。

`--active` 和 `--limit` 只影响显示：判定始终覆盖全部会话，被隐藏的会话也会报 WARN。

## 默认输出

```bash
~/kbdiag sessions --limit 6
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T00:09:11+08:00)

session.activity: 6 rows
pid     usename  datname  application_name       client_addr  backend_type         state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event         query
320047  system   test     kbdiag_inj_idle_txn    -            client backend       idle in transaction  5898         -             11.8        10.8         9.8          Client           ClientRead         select txid_current() as kbdiag_last, pg_sleep(1);
320211  system   test     kbdiag_inj_long_query  -            client backend       active               -            5898          9           9            9            Timeout          PgSleep            select pg_sleep(3600);
3271    -        -        check pointer          -            checkpointer         -                    -            -             -           -            -            Activity         CheckpointerMain   
3272    -        -        background flush       -            background writer    -                    -            -             -           -            -            Activity         BgWriterHibernate  
3273    -        -        wal flush              -            walwriter            -                    -            -             -           -            -            Activity         WalWriterMain      
3274    -        -        auto vacuum            -            autovacuum launcher  -                    -            -             -           -            -            Activity         AutoVacuumMain     
... 7 more rows not shown (use --limit 0 to show all)
EXIT_CODE=0
```

- 第一行是结论和上下文：OK、版本、角色（primary）、连接身份和采集时间。
- 按事务年龄（`xact_age_s`）从大到小排，没有事务的排后面，再按 PID 排。后台进程也列出来。
- `*_age_s` 都是秒。`-` 表示空值。
- 320047 已经 idle in transaction 9.8 秒，但没超过默认的 300 秒，所以是 OK。

## 出现 WARN

把阈值调到 5 秒，同时只看活动会话：

```bash
~/kbdiag sessions --active --idle-in-txn-warn 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T00:09:12+08:00)

[WARN] session.idle_in_txn  会话 320047 处于 idle in transaction 已 10 秒
  verify: kbdiag session 320047  # 看它持有哪些锁、有没有挡住别人

session.activity: 2 rows
pid     usename  datname  application_name       client_addr     backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event     query
320211  system   test     kbdiag_inj_long_query  -               client backend  active  -            5898          9.5         9.5          9.5          Timeout          PgSleep        select pg_sleep(3600);
261437  esrep    -        node2                  192.168.105.11  walsender       active  -            -             -           -            10392.7      Activity         WalSenderMain  
EXIT_CODE=1
```

- 320047 因为 `--active` 没有显示，但 WARN 照报：判定不受显示过滤影响。
- `verify` 行给出下一步要跑的命令。`kbdiag session` 在后续版本提供，当前还不能用。
- 退出码 1 表示有 WARN。

`--json` 输出同样的内容：`verdict`、`context`、`data`（每个探针的 `status`、`columns`、`rows`、`truncated`）、`findings`（每条带 `evidence` 和 `next`）以及 `redacted`。

## 权限不足时

用没有监控角色的账号 `kbdiag_ro` 远程连接：

```bash
PGPASSWORD=... ~/kbdiag sessions --host 127.0.0.1 -U kbdiag_ro --active
echo EXIT_CODE=$?
```

```text
sessions  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-24T00:09:13+08:00)

session.activity: 13 rows
pid     usename  datname   application_name       client_addr     backend_type  state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event     query
3271    -        -         check pointer          -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3272    -        -         background flush       -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3273    -        -         wal flush              -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3274    -        -         auto vacuum            -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3279    system   kingbase  -                      -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3280    system   -         sys_ksh collector      -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3281    system   -         logical replication    -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
3294    esrep    esrep     internal_rwcmgr        -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
179417  esrep    esrep     internal_rwcmgr        -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
222736  esrep    esrep     internal_rwcmgr        -               -             -       -            -             -           -            -            -                -              <insufficient privilege>
261437  esrep    -         node2                  192.168.105.11  walsender     active  -            -             -           -            10393.9      Activity         WalSenderMain  
320047  system   test      kbdiag_inj_idle_txn    -               -             -       5898         -             -           -            -            -                -              <insufficient privilege>
320211  system   test      kbdiag_inj_long_query  -               -             -       -            5898          -           -            -            -                -              <insufficient privilege>

redacted: session.activity.client_addr in 12 rows (insufficient_privilege)
redacted: session.activity.backend_type in 12 rows (insufficient_privilege)
redacted: session.activity.state in 12 rows (insufficient_privilege)
redacted: session.activity.xact_age_s in 12 rows (insufficient_privilege)
redacted: session.activity.query_age_s in 12 rows (insufficient_privilege)
redacted: session.activity.state_age_s in 12 rows (insufficient_privilege)
redacted: session.activity.wait_event_type in 12 rows (insufficient_privilege)
redacted: session.activity.wait_event in 12 rows (insufficient_privilege)
redacted: session.activity.query in 12 rows (insufficient_privilege)
EXIT_CODE=3
```

- 看不到状态的 12 行无法判定，所以结论是 UNKNOWN，退出码 3，而不是 OK。同一个 idle in transaction 的会话还在，只是这个账号看不见它的状态。
- `redacted` 逐列列出哪些字段被遮住、涉及多少行。`backend_xid`、`backend_xmin` 仍然可见。
- 授予 `sys_monitor` 角色后可以看到完整信息。
- 如果某个会话自己关掉了 `track_activities`（`SET` 或 `ALTER ROLE ... SET`），它的 `state` 显示为 `disabled`。这种行同样按 UNKNOWN 处理，`redacted` 的原因写 `track_activities_off`。

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
