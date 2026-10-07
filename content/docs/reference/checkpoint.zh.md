---
title: "checkpoint：检查点"
description: "最近一次 checkpoint，定时和被请求的各多少，脏页是谁写的，相关参数。"
weight: 190
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。没有注入故障。数值只属于本次采样。

## 用法

```text
kbdiag checkpoint [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库

```bash
~/kbdiag checkpoint
echo EXIT_CODE=$?
```

```text
checkpoint  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:59+08:00)

last checkpoint
  time  2026-10-07 17:18:33  (2m 26s ago)
  redo  0/C651C548  (0000000300000000000000C6)

since the statistics reset 2026-09-15 23:12:34 (21d 18h ago)
  checkpoints        1606: 1606 timed, 0 requested (0%; requested covers WAL volume, CHECKPOINT, base backups, promotion)
  write, sync time   6m 54s, 490 ms
  buffers written    17029: checkpointer 10565 (62%), bgwriter 0 (0%), backends and others 6464 (38%)
  buffers allocated  37300
  backend fsyncs     0
  bgwriter stopped   0 times at bgwriter_lru_maxpages

settings
  checkpoint_timeout            5m 0s
  max_wal_size                  1024 MB
  checkpoint_completion_target  0.5
  checkpoint_warning            30s
  log_checkpoints               on
EXIT_CODE=0
```

- `last checkpoint` 是最近一次 checkpoint 的时间和 `redo` 位置（带 WAL 文件名）。
- `checkpoints` 数统计重置以来定时的和被请求的 checkpoint。“requested”不只是 WAL 量：手工 `CHECKPOINT`、基础备份（包括 repmgr clone）、promote、建库删库也算。kbdiag 只给比例，不下结论。服务器自己的“checkpoint 太频繁”看的是两次 checkpoint 的间隔（`checkpoint_warning`），累计计数算不出间隔。
- `buffers written` 把脏页写入分成三方：checkpointer、后台写进程、“backends and others”。第三项不能读成“checkpointer 跟不上”：PG12 的 `buffers_backend` 还算关系扩展、VACUUM 和 COPY 的环形缓冲，以及备库的 startup 进程，空闲节点上也能占六七成（这个环境实采过 65% 和 70%）。
- `backend fsyncs` 大于 0 只展示，不报 WARN。它表示 fsync 请求没能交给 checkpointer，队列满或 checkpointer 当时没在跑都会（这个环境的 node2 被 kbha 拉起过，实采过 9）。
- `settings` 是相关参数。
- 只展示，所以任何一个 probe 没采到，结论就是 UNKNOWN；OK 只表示“都采到了”，不表示数值好。

## 备库

```bash
~/kbdiag checkpoint
echo EXIT_CODE=$?
```

```text
checkpoint  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-07T17:21:06+08:00)

checkpoint record the last restartpoint started from (written by the primary)
  time  2026-10-07 17:18:33  (2m 33s ago)
  redo  0/C651C548  (0000000300000000000000C6)

since the statistics reset 2026-10-07 16:49:26 (31m 40s ago)
  checkpoints        43 timed, 0 requested restartpoint attempts (a standby counts every try, one every 15s while no new checkpoint record has arrived)
  write, sync time   2m 51s, 26 ms
  buffers written    45117: checkpointer 7496 (17%), bgwriter 0 (0%), backends and others 37621 (83%)
  buffers allocated  38458
  backend fsyncs     1
  bgwriter stopped   0 times at bgwriter_lru_maxpages

settings
  checkpoint_timeout            5m 0s
  max_wal_size                  1024 MB
  checkpoint_completion_target  0.5
  checkpoint_warning            30s
  log_checkpoints               on
EXIT_CODE=0
```

- 备库上这些不是 restartpoint 的计数。PG12 的 checkpointer 每次尝试都加一，没有新的 checkpoint 记录时每 15 秒试一次（这个环境里 4 天有 15917 次），所以文本写 `restartpoint attempts`，也不给比例。
- 标题写明：最近一次 restartpoint 起点的 checkpoint 记录是主库写的，所以时间是主库的。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[返回使用手册]({{< relref "/docs/reference" >}})
