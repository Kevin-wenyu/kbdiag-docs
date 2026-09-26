---
title: "status：实例概况"
description: "这是个什么实例、基本面是否正常：角色、复制、连接数、各库大小、磁盘。"
weight: 60
---

采集于 2026-09-26（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `571d8b2` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。FAIL 的例子由故障注入脚本造出来，它把普通用户可用的连接全部占满。数值只属于本次采样。

## 用法

```text
kbdiag status [--json]
```

status 没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

只判两件事：

- **FAIL**：普通用户可用的连接（`max_connections` 减去 `superuser_reserved_connections`）全部占满，业务已经连不上。
- **WARN**：备库没在收 WAL，即没有 WAL 接收进程，或者它的状态不是 `streaming`。这时查询还能跑，但主库一旦挂掉，没有能接管的最新备库。

不报"连接快满"。连接多到什么程度算多，要看应用，所以 status 只给出数字，由你判断。

## 在主库上

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-26T19:19:05+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-20 22:19:13  (up 5d 20h)
  connections     5 / 97  (max_connections 100 - superuser_reserved 3)

inst.downstreams: 1
  name   address         state      sync
  node2  192.168.105.11  streaming  quorum

inst.upstream: not_applicable  (primary)

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  kingbase   14 MB
  mydb       14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   14 GB / 199 GB  (7%)
  free  185 GB
EXIT_CODE=0
```

- 第一行的角色（primary / standby）来自 `sys_is_in_recovery()`。
- `inst.info`：`connections` 只数连到某个库的后端，不含后台进程，可以直接和普通用户可用的 97 个比。
- `inst.downstreams`：本实例给哪些备库发 WAL，一个备库一行，数据来自 `sys_stat_replication`。`sync` 照数据库原样显示，repmgr 下这里是 `quorum`，不是 `sync` / `async`。
- `inst.upstream` 只对备库适用。
- `inst.databases`：非模板库，从大到小排。大小按 1024 进位，和 `pg_size_pretty` 一致。
- `inst.disk`：`data_directory` 所在的文件系统，口径和 `df` 一样。已用加可用小于总量，差的是给 root 预留的块。只展示，不参与判定。

## 在备库上

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-26T19:19:06+08:00)

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-23 15:44:58  (up 3d 3h)
  connections     3 / 97  (max_connections 100 - superuser_reserved 3)

inst.upstream
  status    streaming
  upstream  192.168.105.10:54321
  slot      repmgr_slot_2
  last_msg  4s ago

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

- 备库上游排在前面，数据来自 `sys_stat_wal_receiver`：从哪里收 WAL、走哪个槽、最后一条消息是多久前。
- `last_msg` 只展示，不判。主库空闲时每 `wal_receiver_status_interval`（默认 10 秒）才发一条，几秒是正常值。
- WAL 接收进程被暂停时（比如被 SIGSTOP），状态仍然是 `streaming`，status 不会报。如果 `last_msg` 一直在涨，请自己去备库上看 WAL 接收进程。

## 连接全部占满

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-26T19:19:10+08:00)

[FAIL] inst.connections  连接已用 99 个，达到普通用户可用的 97 个（max_connections 100 减去超级用户保留 3），普通用户已经连不上
  verify: kbdiag sessions --limit 0  # 看连接是谁占的：按 usename、application_name、client_addr 看有没有扎堆

inst.info
  version         V008R006C009B0014
  data_directory  /home/kingbase/cluster/install/kingbase/data
  port            54321
  start_time      2026-09-20 22:19:13  (up 5d 20h)
  connections     99 / 97  (max_connections 100 - superuser_reserved 3)

inst.downstreams: 1
  name   address         state      sync
  node2  192.168.105.11  streaming  quorum

inst.upstream: not_applicable  (primary)

inst.databases: 5, total 382 MB
  test      325 MB
  esrep      15 MB
  kingbase   14 MB
  mydb       14 MB
  security   14 MB

inst.disk  (filesystem of data_directory)
  used   14 GB / 199 GB  (7%)
  free  185 GB
EXIT_CODE=2
```

- 已用 99 个，超过了 97，因为超级用户还能从保留的连接里进来，kbdiag 自己用的 `system` 连接也在其中。
- `verify` 行指向 `sessions --limit 0`，用来按用户、应用名、客户端地址看有没有扎堆。

## 备库没在收 WAL

这种情况还没在测试环境里造出来，下面的 finding 是从源码里摘的文字，不是实采。备库没有 WAL 接收进程时，status 报：

```text
[WARN] inst.upstream  备库没有 WAL 接收进程，没在从主库收 WAL；主库这时挂掉，没有能接管的备库
  verify: kbdiag slots  # 到主库上跑，看这个备库的槽是不是 inactive
```

有接收进程但状态不是 `streaming` 时，finding 里写的是那个状态。退出码是 1。

## 走 TCP 时

只有确定跑在数据库主机上，kbdiag 才读 `inst.disk`，即满足下面一条：

- 走 Unix socket；
- `--host` 是 localhost / 127.0.0.1 / ::1，并且 `data_directory` 在本机存在。要核对目录，是因为端口可能被转发到别的机器。

否则 `inst.disk` 是 `not_applicable`。下面用 `kbdiag_ro` 连主库自己的网络地址：

```bash
PGPASSWORD=... ~/kbdiag status --host 192.168.105.10 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-26T19:19:06+08:00)
...
inst.disk: not_applicable  (remote connection)
EXIT_CODE=0
```

其余各段和上面主库的例子相同。`not_applicable` 不影响结论。

## 权限不足时

`kbdiag_ro` 没有任何监控角色，但在 KingbaseES V8R6 上它照样能完整看到 `sys_stat_replication`、`sys_stat_wal_receiver` 和 `data_directory`，所以 status 给它的结果和 `system` 一样。能被挡住的只有库大小：对某个库没有 CONNECT 权限时，那个库的大小为空，并记进 `redacted`。库大小不参与判定，所以结论仍然是 OK，不是 UNKNOWN。

## JSON

`--json` 保留原始值：大小是字节，时长是秒，版本是短版本号。`inst.info` 多一个 `usable_connections`，`inst.disk` 是 `total_bytes`、`used_bytes`、`avail_bytes`。不适用的 probe 是 `"status": "not_applicable"`，并带原因，比如 `"primary"` 或 `"remote connection"`。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：备库没在收 WAL |
| 2 | FAIL：普通用户可用的连接已经占满 |
| 3 | UNKNOWN：有数据没采到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
