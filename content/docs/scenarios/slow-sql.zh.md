---
title: "找到长时间运行的 SQL"
description: "找到跑了一阵的语句，看它在等什么。"
weight: 10
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数和时间只属于本次采样。故障注入脚本启动了 `select pg_sleep(3600);`，一条只睡觉的语句。它测的是能不能发现，不模拟 CPU 或磁盘压力。

kbdiag 2.0 还没有慢 SQL 阈值：长语句会被列出并排序，但本身不报 WARN。它开着事务太久（`txn`）或让别人等锁（`locks`）时，才会变成 finding。

## 1. 现在在跑什么？

```bash
~/kbdiag sessions
echo EXIT_CODE=$?
```

```text
sessions  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:49+08:00)

connected: 4 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application            client
  2      esrep   esrep     internal_rwcmgr        192.168.105.10
  1      esrep   esrep     internal_rwcmgr        192.168.105.11
  1      system  test      kbdiag_inj_long_query  local

not idle: 1
  pid      user    database  application            client  state   xact  query  wait             sql
  1049328  system  test      kbdiag_inj_long_query  local   active  13s   13s    Timeout:PgSleep  select pg_sleep(3600);
EXIT_CODE=0
```

- `connected` 按用户、库、应用、客户端给客户端会话计数；walsender 和后台进程只计数（`--all` 才列出）。
- `not idle` 列出在干活或开着事务的会话，事务最久的在前。1049328 在跑 `select pg_sleep(3600);`，已经 13 秒。`query` 是当前语句跑了多久，`wait` 是它在等什么。
- `sql` 列截到 60 个字符；`session <pid>` 显示完整文本。

## 2. 它在等什么？

```bash
~/kbdiag session 1049328
echo EXIT_CODE=$?
```

```text
session  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:50+08:00)

session 1049328
  user         system
  database     test
  application  kbdiag_inj_long_query
  client       local
  type         client backend
  state        active  (for 14s)
  xact         14s
  query        14s
  wait         Timeout:PgSleep
  xid / xmin   - / 6353

sql
  select pg_sleep(3600);

waiting for: 0

blocking: 0

holds: 0
EXIT_CODE=0
```

`Timeout:PgSleep` 说明它是故意在睡。它没在等谁，也没挡住谁，也没有值得列出的锁（每个事务自己的 `virtualxid` 锁不列）。换成真实语句，你会看到 `IO`（在读数据）、`Lock`（在等别的会话），或者没有等待事件（在用 CPU）。

## 3. 是一条还是一堆？

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:36:51+08:00)

not idle: 1
  wait             state   sessions  pids
  Timeout:PgSleep  active  1         1049328

not shown: 3 idle, 8 background
EXIT_CODE=0
```

`waits` 把在干活的会话按等待事件和状态分组。只有一个 `Timeout:PgSleep` 会话，说明是单条语句，不是扎堆；idle 的会话和空闲的后台进程只计数。几十个会话等同一个事件时，那个事件就是要查的方向。

## 4. 决定

这里的睡眠是故意的，没什么可调。真实语句要和应用负责人一起看它的执行计划和涉及的数据。kbdiag 不会取消语句；你决定取消时，在 `ksql` 里用 `select pg_cancel_backend(<pid>);`。注入的会话随后被释放，复查时已经没有了。

[继续排查锁等待]({{< relref "/docs/scenarios/lock-waits" >}})
