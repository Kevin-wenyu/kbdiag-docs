---
title: "sessions：列会话"
description: "连接是谁占的、哪些会话在干活；标出长时间 idle in transaction 的会话。"
weight: 10
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。名为 `kbdiag_inj_*` 的业务会话是故障注入脚本造出来的。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag sessions [--all] [--limit N] [--idle-in-txn-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--all` | 列出全部会话，包括 idle 的会话和后台进程 |
| `--limit N` | 最多显示 N 行，默认 50，`0` 表示全部 |
| `--idle-in-txn-warn 秒` | idle in transaction 超过多少秒报 WARN，默认 300 |
| `--json` | 输出 JSON |

连接参数 `--host`、`-p`、`-d`、`-U`、`--timeout` 是全局参数，默认 `/tmp` 本地 socket、端口 54321、库 `test`、用户 `system`；密码从 `PGPASSWORD` 或 `~/.pgpass` 取。连接是只读事务，并设了 `lock_timeout`。

`--all` 和 `--limit` 只影响显示：汇总和判定始终覆盖全部会话，没显示出来的会话也会报 WARN。

## 默认输出

现场有几个注入的会话：一个 idle in transaction 的会话持有表锁、一个读这张表的会话在等它，另一个 idle in transaction 的会话，一个在等两阶段事务的会话，还有一个 `pg_sleep(3600)`。

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:17+08:00)

connected: 8 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application                 client
  2      esrep   esrep     internal_rwcmgr             192.168.105.10
  1      esrep   esrep     internal_rwcmgr             192.168.105.11
  1      system  test      kbdiag_inj_idle_txn         local
  1      system  test      kbdiag_inj_lock_holder      local
  1      system  test      kbdiag_inj_lock_waiter      local
  1      system  test      kbdiag_inj_long_query       local
  1      system  test      kbdiag_inj_prepared_waiter  local

not idle: 5
  pid      user    database  application                 client  state                xact  query  wait             sql
  1045715  system  test      kbdiag_inj_lock_holder      local   idle in transaction  30s   30s    -                lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter      local   active               30s   30s    Lock:relation    select count(*) from kbdiag_inj_lock;
  1045809  system  test      kbdiag_inj_idle_txn         local   idle in transaction  28s   27s    -                select txid_current() as kbdiag_last, pg_sleep(1);
  1046007  system  test      kbdiag_inj_prepared_waiter  local   active               25s   25s    Lock:relation    lock table kbdiag_inj_2pc in access exclusive mode;
  1046088  system  test      kbdiag_inj_long_query       local   active               24s   24s    Timeout:PgSleep  select pg_sleep(3600);
EXIT_CODE=0
```

- `connected:` 回答"连接是谁占的"：客户端会话按用户、库、应用、客户端分组计数，不算 kbdiag 自己的连接。walsender 和后台进程只在标题行里计数。`local` 是 Unix socket。
- `not idle:` 列出在干活或开着事务的客户端会话：`active`、`idle in transaction` 等。idle 的会话和后台进程不列，要看用 `--all`。
- 按事务时长从长到短排；没有事务的排后面，再按 PID 排。
- `xact` 是事务时长，`query` 是当前（或上一条）语句的时长，`wait` 是等待事件，写成 `类型:事件`。`sql` 截到 60 个字符，完整 SQL 用 [`session <pid>`]({{< relref "/docs/reference/session" >}}) 看。`-` 表示空值。
- 两个 idle in transaction 的会话都在 30 秒左右，没到默认的 300 秒，所以结论是 OK。

## 报 WARN

只留下 idle in transaction 的会话，把阈值降到 5 秒，免得例子要等 300 秒：

```bash
~/kbdiag sessions --idle-in-txn-warn 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:37:04+08:00)

[WARN] session.idle_in_txn  session 1049818 has been idle in transaction for 9s
  verify: kbdiag session 1049818  # which locks it holds, whether it blocks anyone

connected: 4 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application          client
  2      esrep   esrep     internal_rwcmgr      192.168.105.10
  1      esrep   esrep     internal_rwcmgr      192.168.105.11
  1      system  test      kbdiag_inj_idle_txn  local

not idle: 2
  pid      user    database  application          client          state                xact  query  wait  sql
  1049818  system  test      kbdiag_inj_idle_txn  local           idle in transaction  11s   10s    -     select txid_current() as kbdiag_last, pg_sleep(1);
  179417   esrep   esrep     internal_rwcmgr      192.168.105.10  active               0s    0s     -     SELECT n.node_id, n.type, n.upstream_node_id, n.node_name...
EXIT_CODE=1
```

- 每个超过阈值的会话一条 finding，`verify` 行给出下一步要跑的命令。
- `esrep` 那一行是 repmgr 自己的查询，采样时正好在跑。
- 退出码 1 表示至少有一条 WARN。

idle in transaction 放 5 分钟，不管应用怎么设计都是毛病：连接池泄漏，或者漏了 commit。300 秒是滤掉噪声的下限，不是容量线；如果 DBA 经常手工开着事务改数据，可以调高。默认阈值下 [`txn`]({{< relref "/docs/reference/txn" >}}) 也会把同一个会话报成长事务。两条回答的问题不同（"它闲着"和"事务太长"），所以都保留。

## 连接是谁占的

[`status`]({{< relref "/docs/reference/status" >}}) 报普通用户已经连不上时，`verify` 行指向这里。故障注入脚本占满了普通用户可用的全部连接：

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:38:17+08:00)

connected: 96 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user       database  application      client
  93     kbdiag_ro  test      kbdiag_inj_conn  127.0.0.1
  2      esrep      esrep     internal_rwcmgr  192.168.105.10
  1      esrep      esrep     internal_rwcmgr  192.168.105.11

not idle: 0
EXIT_CODE=0
```

汇总一眼就能看出扎堆：`kbdiag_ro` 从 `127.0.0.1` 连进来 93 个 idle 会话，应用是 `kbdiag_inj_conn`。它们都是 idle，所以 `not idle` 是空的。

## 少显示几行

```bash
~/kbdiag sessions --limit 2
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:20+08:00)

connected: 8 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application                 client
  2      esrep   esrep     internal_rwcmgr             192.168.105.10
  1      esrep   esrep     internal_rwcmgr             192.168.105.11
  1      system  test      kbdiag_inj_idle_txn         local
  1      system  test      kbdiag_inj_lock_holder      local
  1      system  test      kbdiag_inj_lock_waiter      local
  1      system  test      kbdiag_inj_long_query       local
  1      system  test      kbdiag_inj_prepared_waiter  local

not idle: 5
  pid      user    database  application             client  state                xact  query  wait           sql
  1045715  system  test      kbdiag_inj_lock_holder  local   idle in transaction  33s   33s    -              lock table kbdiag_inj_lock in access exclusive mode;
  1045724  system  test      kbdiag_inj_lock_waiter  local   active               33s   33s    Lock:relation  select count(*) from kbdiag_inj_lock;
... 3 more rows not shown (use --limit 0 to show all)
EXIT_CODE=0
```

`--limit` 裁的是 `not idle` 列表（和 `--json` 里的行），最后一行说明还有多少行没显示。汇总和判定仍然覆盖全部会话。

## 全部会话

```bash
~/kbdiag sessions --all
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:46+08:00)

connected: 3 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user   database  application      client
  2      esrep  esrep     internal_rwcmgr  192.168.105.10
  1      esrep  esrep     internal_rwcmgr  192.168.105.11

all: 11
  pid     user    database  application          client          type                          state   xact  query  wait                    sql
  3271    -       -         check pointer        -               checkpointer                  -       -     -      -                       -
  3272    -       -         background flush     -               background writer             -       -     -      -                       -
  3273    -       -         wal flush            -               walwriter                     -       -     -      -                       -
  3274    -       -         auto vacuum          -               autovacuum launcher           -       -     -      -                       -
  3279    system  kingbase  ksh writer           -               ksh writer                    idle    -     2s     -                       select pg_catalog.metric_update_timer();
  3280    system  -         sys_ksh collector    -               ksh collector                 idle    -     -      -                       -
  3281    system  -         logical replication  -               logical replication launcher  -       -     -      -                       -
  3294    esrep   esrep     internal_rwcmgr      192.168.105.10  client backend                idle    -     2s     -                       SELECT n.node_id as nodeId, n.type as nodeType, n.upstrea...
  179417  esrep   esrep     internal_rwcmgr      192.168.105.10  client backend                idle    -     2s     -                       SELECT pg_catalog.pg_is_in_recovery()
  759699  esrep   esrep     internal_rwcmgr      192.168.105.11  client backend                idle    -     2s     -                       SELECT state,sync_state FROM pg_stat_replication where ap...
  903372  esrep   -         node2                192.168.105.11  walsender                     active  -     -      Activity:WalSenderMain  -
EXIT_CODE=0
```

`--all` 把 idle 的会话和后台进程也列出来，并多一列 `type`（`backend_type`）。walsender 是到备库的复制连接。

## 权限不足

用没有监控角色的 `kbdiag_ro` 连接，注入的会话还在：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro sessions
echo EXIT_CODE=$?
```

```text
sessions  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:25+08:00)

connected: 1 walsender, 15 hidden
  count  user    database  application                 client
  3      esrep   esrep     internal_rwcmgr             ?
  1      -       -         auto vacuum                 ?
  1      -       -         background flush            ?
  1      -       -         check pointer               ?
  1      -       -         wal flush                   ?
  1      system  -         logical replication         ?
  1      system  -         sys_ksh collector           ?
  1      system  kingbase  -                           ?
  1      system  test      kbdiag_inj_idle_txn         ?
  1      system  test      kbdiag_inj_lock_holder      ?
  1      system  test      kbdiag_inj_lock_waiter      ?
  1      system  test      kbdiag_inj_long_query       ?
  1      system  test      kbdiag_inj_prepared_waiter  ?

not idle: 0 visible, 15 hidden
redacted: 15 rows of session.activity hide state, backend_type, client_addr, ages, wait, query (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- 这个账号看不到别人会话的状态、类型、客户端地址、各项时长、等待事件和 SQL，分不出会话是在干活、idle 还是后台进程，所以不说它们是 idle：15 个全算 `hidden`，照样按用户、库、应用计进汇总。
- `?` 是这个账号看不到的值，`-` 是空值。
- 这些会话判不了，所以结论是 UNKNOWN、退出码 3，而不是 OK。`redacted` 行写明了被遮蔽的列和解决办法：授予 `sys_monitor`。
- 会话自己关掉 `track_activities`（`SET` 或 `ALTER ROLE ... SET`）时，状态显示 `disabled`。它照样列出，但时长显示 `?`：服务器里留的是旧值。它同样让结论变成 UNKNOWN，原因是 `track_activities_off`。

## JSON

`--json` 总是包含全部会话（包括 idle 的会话和后台进程），值是原始值：时长以秒计，SQL 是完整的。格式见[读懂一次真实结果]({{< relref "/docs/get-started/reading-results" >}})。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：有会话 idle in transaction 太久 |
| 3 | UNKNOWN：有会话没采到或看不到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
