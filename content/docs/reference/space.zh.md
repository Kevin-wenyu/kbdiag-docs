---
title: "space：磁盘、WAL、库大小"
description: "空间账：磁盘、WAL 大小对照参数、各库和表空间大小。"
weight: 80
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。这一页的例子来自正常的实验环境，以及两个看不全的账号：没有监控角色的 `kbdiag_ro`，分别走 `127.0.0.1` 和节点的网络地址。这条命令没有做故障注入；它能报的那一条 FAIL 在实验环境里没有造出来（见最后一节）。数值只属于本次采样。

## 用法

```text
kbdiag space [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库，正常

```bash
~/kbdiag space
echo EXIT_CODE=$?
```

```text
space  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:53+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  15 GB  199 GB  184 GB  7%

wal: 214 files, 3248 MB
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  735 kB
  sysaudit     (in data_directory)  24 kB
EXIT_CODE=0
```

- `disk` 列出放数据目录、WAL 目录和表空间的文件系统，同一个文件系统上的目录合成一行（按设备号合并，所以 `sys_wal` 是指向另一块盘的符号链接时会单独出一行）。`free` 是 `kingbase` 这类非 root 用户能用的量。它用 statfs 读磁盘，所以只有 kbdiag 跑在数据库主机上才有（见下面的“远程连接”）。
- `wal` 是 `sys_wal` 的大小，旁边放着 `max_wal_size` 和 `wal_keep_segments`（写成它保留的大小：512 x 16 MB）。kbdiag 不对它下结论：`max_wal_size` 是软上限，PG12 通常会保留两者之和再加上最近一次检查点以来写的 WAL，只超过其中一个是常态。`sys_wal` 超过这个和时，文本会提示去看 `kbdiag slots` 和 `kbdiag archive`。这里 3248 MB 小于 1024 + 8192 MB。
- `databases` 和 [`status`]({{< relref "/docs/reference/status" >}}) 用的是同一个 probe，所以两处数字一致。
- `tablespaces` 列出每个表空间和位置（默认的写 `in data_directory`）。

## 备库

```bash
~/kbdiag space
echo EXIT_CODE=$?
```

```text
space  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:00+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  13 GB  199 GB  186 GB  6%

wal: 198 files, 3136 MB
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)

databases: 5, total 438 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  security   14 MB
  kingbase   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  735 kB
  sysaudit     (in data_directory)  24 kB
EXIT_CODE=0
```

备库照同样的方式判断。它的 WAL 目录是自己的，所以文件数和大小和主库不同。

## 没有权限时

`kbdiag_ro` 没有监控角色。它走 `127.0.0.1`，这是 TCP（所以第一行写 `kbdiag_ro@remote`），但数据库就在本机，所以磁盘照样读得到：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro space
echo EXIT_CODE=$?
```

```text
space  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:07+08:00)

disk: 1 filesystem
  holds                used   size    free    use
  data_directory, wal  15 GB  199 GB  184 GB  7%

wal: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_waldir)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  ?
  sysaudit     (in data_directory)  ?
redacted: 2 rows of space.tablespaces hide size_bytes (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- `wal: skipped`：这个账号不能调 `sys_ls_waldir`，WAL 大小没采到。`space` 是纯展示的命令，只要有一个 probe 没采到，结论就是 UNKNOWN 而不是 OK：OK 只表示“都采到了”，这里没有。
- 表空间表里的 `?` 表示这个账号看不到那个大小（`pg_tablespace_size(sys_global)` 被拒绝）。kbdiag 把这个调用包在 CASE 里，所以只有那几格是 NULL，整条语句不会失败；这些格子记在 `redacted` 里。授予 `sys_monitor` 后两处都能解除。

## 远程连接

通过节点的网络地址连接时，数据目录可能在另一台机器上，所以 kbdiag 不读磁盘：

```bash
PGPASSWORD=... ~/kbdiag --host 192.168.105.10 -U kbdiag_ro space
echo EXIT_CODE=$?
```

```text
space  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:10+08:00)

disk: not_applicable  (remote connection)

wal: skipped  (insufficient_privilege 42501: permission denied for function sys_ls_waldir)

databases: 5, total 439 MB
  test      381 MB
  esrep      15 MB
  mydb       14 MB
  kingbase   14 MB
  security   14 MB

tablespaces: 3
  name         location             size
  sys_default  (in data_directory)  467 MB
  sys_global   (in data_directory)  ?
  sysaudit     (in data_directory)  ?
redacted: 2 rows of space.tablespaces hide size_bytes (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- `disk: not_applicable  (remote connection)`。只有确定跑在数据库主机上，kbdiag 才读磁盘：走 Unix socket，或者 host 是 `localhost`、`127.0.0.1`、`::1` 并且 `data_directory` 在本机存在。端口可能被转发到别的机器，所以只看主机名不够。
- `not_applicable` 不是失败，但加上上面的权限缺口，这里结论同样是 UNKNOWN。

## 没有造出来的 FAIL

实验环境里没有造出来，下面按源码写：`space.disk_full`（FAIL）。数据目录或 WAL 目录所在的文件系统，可用空间不到一个 WAL 段（这里是 16 MB）时报。要造出它得真把数据盘填满，实验环境不做这个。

- WAL 所在盘上建不出新段，旧段用完后实例会停；数据目录所在盘上，表、事务状态文件、临时文件马上长不了（报 ERROR，实例不停）。finding 会按实际情况分别写。
- 严格说这是“马上就会受影响”，因为离失败只差一个段，没有余地再观察，所以报 FAIL。
- 其他盘（表空间）满了，或者“少但还超过一个段”，因库而异，只展示。
- 每个文件系统一条 finding。段大小来自 `wal` probe，采不到时（比如 `kbdiag_ro`）这条规则不判。

[`status`]({{< relref "/docs/reference/status" >}}) 的 `inst.disk` 是数据目录那块盘的简短版本，只展示。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 2 | FAIL：某个文件系统的可用空间不到一个 WAL 段（实验环境没造出来） |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
