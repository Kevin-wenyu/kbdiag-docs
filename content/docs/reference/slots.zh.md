---
title: "slots：复制槽"
description: "列出复制槽：谁在消费、保留了多少 WAL、有没有压着 vacuum。"
weight: 70
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。WARN 的例子由故障注入脚本造出来：它暂停（SIGSTOP）备库的 WAL 接收进程，过了 `wal_sender_timeout`（这里是 30 秒）后主库上的槽变成不活跃，和备库挂掉时一样。数值只属于本次采样。

## 用法

```text
kbdiag slots [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 正常

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:34:45+08:00)

slots: 1
  name           type      active            retained  xmin  xmin age  restart_lsn
  repmgr_slot_2  physical  yes (pid 903372)  0 bytes   6342  0         0/A42EE580
EXIT_CODE=0
```

- `active` 说明有没有人在消费这个槽，以及是哪个进程（这里是到备库的 walsender）。
- `retained` 是这个槽让实例保留的 WAL 量，按 1024 进位，和 `pg_size_pretty` 一致。主库上从当前 WAL 位置算，备库上从回放位置算。
- `xmin` 是这个槽要求实例保留的最老事务号。这个物理槽的 xmin 来自备库的 `hot_standby_feedback`。`xmin age` 是它落后当前事务号多少。
- 逻辑槽还可能带 `catalog_xmin`，它压着系统表的 vacuum。只有某个槽带它时才出现这一列。（实验环境是 `wal_level=replica`，没有逻辑槽。）

备库自己没有槽时：

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:21+08:00)

slots: 0
EXIT_CODE=0
```

## 不活跃的槽

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:37:55+08:00)

[WARN] slot.inactive  replication slot repmgr_slot_2 is inactive, retaining 216 bytes WAL, xmin 6354 holding back the vacuum horizon
  verify: kbdiag status  # run on this slot's downstream node (usually a standby): if it cannot connect, the node is down; inst.upstream with no receiver or not streaming means it is not receiving WAL; if it shows streaming, run it again after 10-20s: a last_msg that keeps growing means the receiver is stuck

slots: 1
  name           type      active  retained   xmin  xmin age  restart_lsn
  repmgr_slot_2  physical  no      216 bytes  6354  0         0/A42FF338
EXIT_CODE=1
```

- 不活跃的槽没人消费，却照样保留 WAL；带 `xmin` 的还会让 VACUUM 清不掉旧的行版本。不活跃本身就是那条线，所以没有时间阈值，也没有参数。
- 报 WARN 而不是 FAIL：业务照常。危害（WAL 撑满磁盘、表膨胀、没有跟得上的备库）是以后的事。
- 刚注入完几乎没保留什么 WAL，真出故障时它会一直涨。
- repmgr 重启备库的那几秒，槽也会不活跃，同样会报。
- 只有确认下游真的不要了才删槽。kbdiag 不会替你删。

## 按 verify 行往下查

`verify` 行让你到这个槽的下游节点上跑 `kbdiag status`，通常是备库（备库也可以有自己的下游）。在被暂停的备库上：

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:37:55+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 21h)
  connections     3 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  44s ago

inst.downstreams: 0

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  kingbase   14 MB
  mydb       14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   12 GB / 199 GB  (6%)
  free  187 GB
EXIT_CODE=0
```

WAL 接收进程仍显示 `streaming`，因为被暂停的进程不会改自己的状态。照注释说的，隔 10–20 秒再跑一次：

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T13:38:11+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 21h)
  connections     3 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  1m 0s ago

inst.downstreams: 0

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  kingbase   14 MB
  mydb       14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   12 GB / 199 GB  (6%)
  free  187 GB
EXIT_CODE=0
```

`last_msg` 从 44 秒涨到 1 分钟：接收进程卡住了。status 不判 `last_msg`，因为空闲的主库每 `wal_receiver_status_interval`（默认 10 秒）才发一条消息。如果节点根本连不上，说明它挂了；如果 `inst.upstream` 没有接收进程或者不是 `streaming`，status 会报 WARN。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：有不活跃的槽 |
| 3 | UNKNOWN：数据没采到 |
| 64 | 用法错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
