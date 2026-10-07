---
title: "wal：WAL 位置和谁让它留着"
description: "WAL 写到哪了、`sys_wal` 多大，以及是什么让它留着：参数、槽、归档。"
weight: 200
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。数值只属于本次采样。

## 用法

```text
kbdiag wal [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库

```bash
~/kbdiag wal
echo EXIT_CODE=$?
```

```text
wal  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:59+08:00)

position
  lsn   0/C9352468
  file  0000000300000000000000C9

sys_wal: 214 files, 3248 MB

what keeps WAL here
  max_wal_size        1024 MB
  wal_keep_segments   8192 MB  (512 x 16 MB)
  slot repmgr_slot_2  0 bytes  (active)
  archiving           38 .ready files waiting  (kbdiag archive)
EXIT_CODE=0
```

- `position` 是当前写到的位置和它所在的 WAL 文件。
- `sys_wal` 的大小和 [`space`]({{< relref "/docs/reference/space" >}}) 里一致：同一个 probe，同样的列。
- `what keeps WAL here` 把原来要分别跑三条命令再拼起来的信息放在一屏：参数（`max_wal_size`，`wal_keep_segments` 折成它保留的大小）、每个复制槽保留的 WAL 和是否活跃、归档积压。这里槽保留 0 字节而且活跃，但有 38 个 `.ready` 文件在等归档（实验环境的归档本来就在失败，见 [`archive`]({{< relref "/docs/reference/archive" >}})）。
- 它只展示，不重复判定。槽不活跃由 `kbdiag slots` 报，归档失败由 `kbdiag archive` 报，这一屏只指过去。同一个问题在三条命令里各报一次，只会让人以为出了三件事。
- WAL 生成速率要隔一段时间采两次，单次查询给不了，这个版本不做。

## 备库

```bash
~/kbdiag wal
echo EXIT_CODE=$?
```

```text
wal  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:06+08:00)

position
  replayed  0/C9352A80

sys_wal: 198 files, 3136 MB

what keeps WAL here
  max_wal_size       1024 MB
  wal_keep_segments  8192 MB  (512 x 16 MB)
  slots              none
  archiving          0 .ready files waiting
EXIT_CODE=0
```

备库上 `position` 是回放位置（没有写入位置，也没有 WAL 文件名）。这个备库自己没有槽，也没有等着归档的文件。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
