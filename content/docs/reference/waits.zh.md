---
title: "waits：等待事件"
description: "按等待事件和状态汇总会话，看此刻大家在等什么。"
weight: 50
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `0a4d61e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里有一个锁等待是故障注入脚本造出来的：364809 拿着表锁 idle in transaction，364818 等它。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag waits [--json]
```

没有命令自己的参数。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 默认输出

```bash
~/kbdiag waits
echo EXIT_CODE=$?
```

```text
waits  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:54+08:00)

wait.summary: 10 rows
wait_event_type  wait_event           state                sessions  pids
Client           ClientRead           idle                 3         [3294 179417 222736]
Activity         KshMain              idle                 2         [3279 3280]
Activity         AutoVacuumMain       -                    1         [3274]
Activity         BgWriterHibernate    -                    1         [3272]
Activity         CheckpointerMain     -                    1         [3271]
Activity         LogicalLauncherMain  -                    1         [3281]
Activity         WalSenderMain        active               1         [364531]
Activity         WalWriterMain        -                    1         [3273]
Client           ClientRead           idle in transaction  1         [364809]
Lock             relation             active               1         [364818]
EXIT_CODE=0
```

- 每行是一个（等待事件类型、等待事件、状态）组合，`sessions` 是会话数，`pids` 是这些会话的 PID，按会话数从多到少排。
- 没在等的会话（等待事件为空）也按状态归组，所以这张表覆盖除 kbdiag 自己的连接以外的全部会话。
- `waits` 只汇总，不按阈值判定：全部会话都看得见就是 OK，有看不到的会话就是 UNKNOWN（见下文）。示例里 `Lock / relation` 那一行就是 364818 在等锁；要看等了多久、被谁挡住，用 [`locks`]({{< relref "/docs/reference/locks" >}})。

## 权限不足时

用没有监控角色的账号 `kbdiag_ro` 远程连接：

```bash
PGPASSWORD=... ~/kbdiag waits --host 127.0.0.1 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
waits  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-24T04:41:05+08:00)

wait.summary: 2 rows
wait_event_type  wait_event     state   sessions  pids
-                -              -       12        [3271 3272 3273 3274 3279 3280 3281 3294 179417 222736 36...
Activity         WalSenderMain  active  1         [366619]

redacted: wait.summary.wait_event_type in 12 rows (insufficient_privilege)
redacted: wait.summary.wait_event in 12 rows (insufficient_privilege)
redacted: wait.summary.state in 12 rows (insufficient_privilege)
EXIT_CODE=3
```

- 看不到的会话等待事件和状态都是空，归到三个字段都为空的那一行（这里 12 个）；`redacted` 说明这是权限造成的，不是它们真的没在等。
- 有看不到的会话，就不能说"没有异常等待"，所以结论是 UNKNOWN，退出码 3。
- 文本输出里过长的单元格会被截断（结尾 `...`）；`--json` 给出完整的 PID 列表。
- 授予 `sys_monitor` 角色后可以看到完整信息。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
