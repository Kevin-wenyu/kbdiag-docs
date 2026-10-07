---
title: "archive：WAL 归档"
description: "归档是不是在正常工作：设置、最后一次成功和失败、等着归档的 WAL。"
weight: 110
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。主库的 WAL 归档在实验环境里本来就在失败（`archive_command` 调 `sys_rman archive-push`，最后一次成功在 21 天前），所以下面的 WARN 就是实验环境的真实状态；失败原因这一页没有去查，因为 kbdiag 不读服务器日志。数值只属于本次采样。

## 用法

```text
kbdiag archive [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库：归档在失败

```bash
~/kbdiag archive
echo EXIT_CODE=$?
```

```text
archive  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:55+08:00)

[WARN] archive.failing  archiving is failing: the last attempt failed (0000000300000000000000A3, 6s ago) and the last success was 21d 3h ago (0000000300000000000000A2); 22590 failures since the statistics reset. WAL that is not archived stays in sys_wal and is missing from the backups
  verify: kbdiag space  # how big sys_wal has grown; why archive_command fails is in the server log (log_directory)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-09-15 23:12:34)
  archived  35     last 0000000300000000000000A2  21d 3h ago
  failed    22590  last 0000000300000000000000A3  6s ago

waiting: 38 .ready, 174 .done  (oldest .ready 21d 3h)
EXIT_CODE=1
```

- `archive.failing`（WARN）的线是“最后一次尝试失败了”：最后一次失败晚于最后一次成功，或者从没成功过。没归档的 WAL 会留在 `sys_wal`，备份里缺这几段，但业务照常，所以是 WARN。
- `settings` 显示 `archive_mode`、`archive_command` 和 `archive_timeout`。kbdiag 先排除主动配置的情况：`archive_mode=off` 不判；备库上 `archive_mode=on` 也不判，因为备库只有 `always` 才归档。
- `archiver` 是服务器的归档统计，从统计重置时间开始算：成功和失败各多少次，各自最后一个 WAL 文件和多久前。
- `waiting` 数 `.ready`（等着归档的 WAL）和 `.done` 文件，以及最老的 `.ready` 等了多久。它只展示，不能影响结论。
- `verify` 指向 `kbdiag space`（看 `sys_wal` 撑到多大）。命令为什么失败，只在服务器日志（`log_directory`）里有。
- `archive_command` 为空不判：PostgreSQL 文档说这时 WAL 会一直留着，但 KingbaseES 上没核实，文本只写 `(empty)`。

## 备库

```bash
~/kbdiag archive
echo EXIT_CODE=$?
```

```text
archive  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:02+08:00)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-10-07 16:49:26)
  archived  38  last 0000000300000000000000C8  2m 17s ago
  failed    0

waiting: 0 .ready, 212 .done
EXIT_CODE=0
```

备库是 `archive_mode=always`，所以它也归档。它从自己启动时开始计数，这里成功、没有积压，所以是 OK。

## 没有权限时

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro archive
echo EXIT_CODE=$?
```

```text
archive  WARN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:09+08:00)

[WARN] archive.failing  archiving is failing: the last attempt failed (0000000300000000000000A3, 20s ago) and the last success was 21d 3h ago (0000000300000000000000A2); 22590 failures since the statistics reset. WAL that is not archived stays in sys_wal and is missing from the backups
  verify: kbdiag space  # how big sys_wal has grown; why archive_command fails is in the server log (log_directory)

settings
  archive_mode     always
  archive_command  export TZ=Asia/Shanghai;/home/kingbase/cluster/install/kingbase/bin/sys_rman --config /rman/kbbr_repo/sys_rman.conf --stanza=kingbase archive-push %p
  archive_timeout  0 (off)

archiver  (counting since 2026-09-15 23:12:34)
  archived  35     last 0000000300000000000000A2  21d 3h ago
  failed    22590  last 0000000300000000000000A3  20s ago

waiting: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_archive_statusdir)
EXIT_CODE=1
```

`kbdiag_ro` 不能调 `sys_ls_archive_statusdir`，所以 `waiting` 是 `skipped`。这个 probe 只展示，不允许影响结论。finding 本身来自统计视图，这个账号读得到。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：最后一次归档失败 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
