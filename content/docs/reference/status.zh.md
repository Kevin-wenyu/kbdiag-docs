---
title: "status：实例概况"
description: "看版本、角色、运行时长、连接数、各库大小和下游数量。"
weight: 60
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `0a4d61e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。数值只属于本次采样。

## 用法

```text
kbdiag status [--json]
```

没有命令自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 在主库上

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:39:06+08:00)

inst.databases: 5 rows
datname   size_bytes
esrep     15614003
kingbase  15024179
mydb      14877187
security  14844419
test      340459571

inst.downstreams: 1 rows
downstreams
1

inst.info: 1 rows
version                                                       start_time                 uptime_s  connections  max_connections  superuser_reserved_connections  data_directory
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-20T22:19:13+08:00  281992.5  5            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- `inst.info`：版本、实例启动时间、运行秒数、连接数和连接上限。`connections` 只数连到某个库的后端，不含后台进程，可以直接和 `max_connections` 比。
- `inst.databases`：每个非模板库的大小（字节）。
- `inst.downstreams`：本实例正在给多少个下游发 WAL（`sys_stat_replication` 的行数）。主库上 1 表示一个备库连着。
- 第一行的角色（primary / standby）来自 `sys_is_in_recovery()`。
- `status` 只报事实，不判定：采到就是 OK。

## 在备库上

```bash
~/kbdiag status
echo EXIT_CODE=$?
```

```text
status  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-24T04:39:07+08:00)

inst.databases: 5 rows
datname   size_bytes
esrep     15614003
kingbase  15024179
mydb      14877187
security  14844419
test      340459571

inst.downstreams: 1 rows
downstreams
0

inst.info: 1 rows
version                                                       start_time                 uptime_s  connections  max_connections  superuser_reserved_connections  data_directory
KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, comp...  2026-09-23T15:44:58+08:00  46448.3   3            100              3                               /home/kingbase/cluster/install/kingbase/data
EXIT_CODE=0
```

- 角色是 standby；这个备库没有级联下游，所以 `downstreams` 是 0。
- 文本输出里过长的单元格会被截断（结尾 `...`）；`--json` 给出完整版本字符串。

## 权限不足时

账号对某个库没有 CONNECT 权限时，它的 `size_bytes` 为空，并记进 `redacted`。库大小不参与判定，所以结论仍然是 OK，不是 UNKNOWN。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
