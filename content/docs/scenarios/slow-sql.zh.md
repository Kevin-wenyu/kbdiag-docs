---
title: "找到长时间运行的 SQL"
description: "找到跑了一阵的语句，看它在等什么。"
weight: 10
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `6803c61` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数和时间只属于本次采样。 故障注入脚本启动了 `select pg_sleep(3600);`，一条只睡觉的语句。它测的是能不能发现，不模拟 CPU 或磁盘压力。

kbdiag 2.0 还没有慢 SQL 阈值：长语句会被列出并排序，但本身不报 WARN。它开着事务太久（`txn`）或让别人等锁（`locks`）时，才会变成 finding。

## 1. 现在在跑什么？

```bash
~/kbdiag sessions --active
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:14+08:00)

session.activity: 2 rows
pid     usename  datname  application_name       client_addr     backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event     query
436010  system   test     kbdiag_inj_long_query  -               client backend  active  -            6101          9           9            9            Timeout          PgSleep        select pg_sleep(3600);
407405  esrep    -        node2                  192.168.105.11  walsender       active  -            -             -           -            10050.7      Activity         WalSenderMain  
EXIT_CODE=0
```

- `--active` 只显示状态为 `active` 的会话；判定仍然覆盖全部会话。
- 按事务时长从长到短排序：436010 在跑 `select pg_sleep(3600);`，已经 9 秒。`query_age_s` 是当前语句跑了多久。
- `walsender` 那一行是给备库的复制连接，总是 active 且没有事务，所以排在客户端会话后面。

## 2. 它在等什么？

```bash
~/kbdiag session 436010
echo EXIT_CODE=$?
```

```text
session  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:14+08:00)

lock.list: 1 rows
pid     locktype    relation  mode           granted  wait_s  blocked_by
436010  virtualxid  -         ExclusiveLock  true     -       []

session.activity: 1 rows
pid     usename  datname  application_name       client_addr  backend_type    state   backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event  query
436010  system   test     kbdiag_inj_long_query  -            client backend  active  -            6101          9.5         9.5          9.5          Timeout          PgSleep     select pg_sleep(3600);
EXIT_CODE=0
```

`Timeout / PgSleep` 说明它是故意在睡。它只持有自己的 `virtualxid` 锁，没有挡住任何人。换成真实语句，你会看到 `IO`（在读数据）、`Lock`（在等别的会话），或者没有等待事件（在用 CPU）。

## 3. 是一条还是一堆？

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:15+08:00)

wait.summary: 9 rows
wait_event_type  wait_event           state   sessions  pids
Client           ClientRead           idle    3         [3294 179417 222736]
Activity         KshMain              idle    2         [3279 3280]
Activity         AutoVacuumMain       -       1         [3274]
Activity         BgWriterHibernate    -       1         [3272]
Activity         CheckpointerMain     -       1         [3271]
Activity         LogicalLauncherMain  -       1         [3281]
Activity         WalSenderMain        active  1         [407405]
Activity         WalWriterMain        -       1         [3273]
Timeout          PgSleep              active  1         [436010]
EXIT_CODE=0
```

`waits` 按等待事件和状态把全部会话分组。空闲客户端和后台进程之外只有一个 `Timeout / PgSleep`，说明是单条语句，不是扎堆。几十个会话等同一个事件时，那个事件就是要查的方向。

## 4. 决定

这里的睡眠是故意的，没什么可调。真实语句要和应用负责人一起看它的执行计划和涉及的数据。kbdiag 不会取消语句；你决定取消时，在 `ksql` 里用 `select pg_cancel_backend(<pid>);`。注入的会话随后被释放，复查时已经没有了。

[继续排查锁等待]({{< relref "/docs/scenarios/lock-waits" >}})
