---
title: "waits：等待事件"
description: "此刻在干活的会话在等什么，扎堆最多的在前。"
weight: 50
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的会话是故障注入脚本造出来的：两个 idle in transaction 的会话、两个在等表锁的会话、一个 `pg_sleep(3600)`。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag waits [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 默认输出

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:35:18+08:00)

not idle: 5
  wait               state                sessions  pids
  Lock:relation      active               2         1045724 1046007
  Client:ClientRead  idle in transaction  2         1045715 1045809
  Timeout:PgSleep    active               1         1046088

not shown: 3 idle, 8 background
EXIT_CODE=0
```

- `not idle` 把在干活的会话按等待事件和状态分组，`sessions` 是个数，`pids` 列出是哪些。人数最多的组在前，因为要找的就是扎堆；人数相同时 `active` 在前。
- `Lock:relation`：两个会话在等表锁；谁挡的、等了多久看 [`locks`]({{< relref "/docs/reference/locks" >}})。
- `Client:ClientRead` 加 `idle in transaction`：会话开着事务，在等客户端发下一条语句。
- `Timeout:PgSleep` 是注入的 `pg_sleep`。active 却没有等待事件的会话写 `(running)`：在 CPU 上，或者这段代码没有埋点。
- `pids` 最多列 10 个，其余写 `... (+N)`，`--json` 里是全的。
- `not shown` 给不列出来的计数：`idle` 的会话不回答"卡在哪"；后台进程在主循环里空闲（任何 `Activity` 类等待，比如没东西可发的 walsender、两次 checkpoint 之间的 checkpointer）也不回答。后台进程卡在真正的等待上（比如 checkpointer 等 `IO:DataFileSync`）照样列出，状态写 `(background)`。

没有阈值，也没有参数：同样是 10 个会话等 IO，对一个库是事故，对另一个库是常态，所以 waits 只报告不判定。等锁太久由 `locks` 判。

空闲的主库：

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:44+08:00)

not idle: 0

not shown: 3 idle, 8 background
EXIT_CODE=0
```

主库忙的时候，追赶中的 walsender 可能以 `IO:WALRead` 之类的等待出现，属正常。

## 在备库上

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:21+08:00)

not idle: 1
  wait           state   sessions  pids
  Lock:advisory  active  1         599825

not shown: 3 idle, 4 background
EXIT_CODE=0
```

## 权限不足

用没有监控角色的 `kbdiag_ro` 连接：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro waits
echo EXIT_CODE=$?
```

```text
waits  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-27T13:35:27+08:00)

not idle: 0

not shown: 1 background, 15 hidden (state unknown)
redacted: 15 rows of wait.summary hide wait, state (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- 别的用户的会话看不到等待事件和状态，不知道是不是 idle，所以计成 `hidden (state unknown)`，不算作 idle。关了 `track_activities` 的会话出于同样原因计成 `untracked (state unknown)`。
- 有看不到的会话，kbdiag 就不能说没人在等，所以结论是 UNKNOWN，退出码 3。授予 `sys_monitor` 后可以看全。

## JSON

`--json` 包含所有分组（包括 idle 和后台进程的），PID 列表是全的：`wait_event_type`、`wait_event`、`state`、`sessions`、`pids`。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：数据没采到或看不到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
