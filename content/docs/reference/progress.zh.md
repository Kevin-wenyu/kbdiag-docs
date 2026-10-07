---
title: "progress：长操作进度"
description: "正在跑的 VACUUM、CREATE INDEX、CLUSTER / VACUUM FULL、CHECKPOINT 到哪了。"
weight: 180
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。进行中的例子由注入脚本造出来：它在 `public.orders`（100 万行）上跑 `CREATE INDEX`，运行期间读了三次，其中一次用 `kbdiag_ro`。PID 和时间只属于本次采样。

## 用法

```text
kbdiag progress [--json]
```

没有自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 没有在跑的

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:58+08:00)

running: 0  (VACUUM, CREATE INDEX, CLUSTER and VACUUM FULL, CHECKPOINT; ANALYZE and base backups have no progress view in this version)
EXIT_CODE=0
```

文本写明了它看哪几种操作，也写明了看不到什么：这个版本没有 ANALYZE 和 base backup 的进度视图。备库（kes-node2）上打印的是同一行。

- kbdiag 把 PostgreSQL 的三个进度视图（VACUUM、CREATE INDEX、CLUSTER / VACUUM FULL）合成一个 probe，因为读者问的是“那个长操作到哪了”，不关心它在哪个视图里。KingbaseES 自己的 checkpoint 视图单独一个 probe：只观察到了它的列名，它出错时不能连累另外三个。

## CREATE INDEX 进行中

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:24+08:00)

running: 1
  pid    command       database  relation  phase                           progress                  running
  43243  CREATE INDEX  test      orders    building index: scanning table  5058 / 7896 blocks (64%)  3s
EXIT_CODE=0
```

几秒之后的同一个构建：

```bash
~/kbdiag progress
echo EXIT_CODE=$?
```

```text
progress  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:29+08:00)

running: 1
  pid    command       database  relation  phase                           progress                   running
  43243  CREATE INDEX  test      orders    building index: scanning table  7896 / 7896 blocks (100%)  8s
EXIT_CODE=0
```

- `phase` 是操作自己的阶段，`progress` 是已做/总量加单位和百分比。已做/总量按阶段取：块计数在扫描结束后停住，接着的阶段（vacuum 的回收、建索引的排序和装载）要换计数，否则会长时间显示 100%。第二次采样的 100% 是表扫描结束，不是索引建完。
- `running` 是操作已经跑了多久。
- 它只展示。多久算慢没有客观线，vacuum 该不该跑由 `kbdiag vacuum` 判。`CREATE INDEX CONCURRENTLY` 还在等别的事务时，阶段后面会写还剩几个，并指向 `kbdiag locks`：这正是它看起来卡住的常见原因。

## 没有权限时

`kbdiag_ro`（没有监控角色，走 `127.0.0.1`）读同一个构建：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro progress
echo EXIT_CODE=$?
```

```text
progress  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:25+08:00)

running: 1
  pid    command                  database  relation  phase  progress  running
  43243  CREATE INDEX or REINDEX  test      -         ?      ?         ?
redacted: 1 row of progress.list hides phase (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

操作看得到，但 `phase` 被遮蔽（`?`），所以进度、运行时间和表都不显示，命令标成 `CREATE INDEX or REINDEX`。被遮蔽的格子记在 `redacted` 里。因为有东西没看到，结论是 UNKNOWN，虽然操作本身找到了。授予 `sys_monitor` 后解除。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
