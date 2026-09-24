---
title: "slots：复制槽"
description: "列出复制槽，标出未激活的槽：它们会一直保留 WAL、压着清理视界。"
weight: 70
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `6803c61` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。FAIL 示例是故障注入脚本造出来的：暂停备库的 WAL 接收进程，主库上的槽在 `wal_sender_timeout`（本环境 30 秒）后变成未激活，模拟备库挂掉。数值只属于本次采样。

## 用法

```text
kbdiag slots [--json]
```

没有命令自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 正常时

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T07:32:44+08:00)

slot.list: 1 rows
slot_name      slot_type  active  active_pid  xmin  catalog_xmin  xmin_age  restart_lsn  retained_wal_bytes
repmgr_slot_2  physical   true    407405      6098  -             0         0/A41581B8   0
EXIT_CODE=0
```

- `active=true`，`active_pid` 是正在用这个槽的 walsender 进程。
- `xmin` 是这个槽要求保留的最老事务号；这里是物理槽，它来自备库开着的 `hot_standby_feedback`。`xmin_age` 是它落后当前事务号多少。
- `retained_wal_bytes` 是这个槽让实例保留的 WAL 量：主库上从当前 WAL 位置算，备库上从已回放位置算。

备库上没有槽时列表为空，结论 OK。

## 槽未激活

```bash
~/kbdiag slots
echo EXIT_CODE=$?
```

```text
slots  FAIL  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T07:32:43+08:00)

[FAIL] slot.inactive  复制槽 repmgr_slot_2 未激活，保留 0 MB WAL，xmin 6098 压着视界
  verify: kbdiag sessions  # 在备库上运行：连不上说明备库实例挂了；列表里没有 walreceiver 进程说明它没在接收 WAL

slot.list: 1 rows
slot_name      slot_type  active  active_pid  xmin  catalog_xmin  xmin_age  restart_lsn  retained_wal_bytes
repmgr_slot_2  physical   false   -           6098  -             0         0/A41581B8   0
EXIT_CODE=2
```

- 未激活的槽没人消费，却会一直保留 WAL；带 `xmin` 的还会让 VACUUM 清不掉旧版本。时间一长可能写满磁盘，所以直接 FAIL，不设时间阈值。
- 刚注入时几乎还没保留 WAL（显示为 0 MB）；真实故障里它会持续增长。
- `verify` 行建议去备库上跑 `kbdiag sessions`：连不上说明备库实例挂了；列表里没有 `walreceiver` 进程说明它没在接收 WAL。备库确实废弃时才考虑删槽；kbdiag 不会替你删。
- 有 FAIL 时退出码 2。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 2 | FAIL |
| 3 | UNKNOWN：有数据没采到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
