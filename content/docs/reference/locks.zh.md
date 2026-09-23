---
title: "locks：锁等待"
description: "列出锁，标出等锁过久的会话和直接挡住它的会话。"
weight: 30
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `0a4d61e` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。示例里的锁等待是故障注入脚本造出来的：364809 拿着表 `kbdiag_inj_lock` 的排他锁不提交，364818 等它。PID、计数与时间只属于本次采样。

## 用法

```text
kbdiag locks [--limit N] [--lock-wait-warn 秒] [--json]
```

| 参数 | 作用 |
|---|---|
| `--limit N` | 最多显示 N 行，默认 50，`0` 表示全部 |
| `--lock-wait-warn 秒` | 等锁超过多少秒报 WARN，默认 10 |
| `--json` | 输出 JSON |

连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。`--limit` 只影响显示，判定始终覆盖全部锁。

## 有会话在等锁

```bash
~/kbdiag locks
echo EXIT_CODE=$?
```

```text
locks  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T04:38:53+08:00)

[WARN] lock.waiting  会话 364818 等 public.kbdiag_inj_lock 的 AccessShareLock 已 14 秒，被 364809 挡住
  verify: kbdiag session 364809  # 看挡路的会话在干什么

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
364809  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
364818  relation  public.kbdiag_inj_lock  AccessShareLock      false    13.8    [364809]
EXIT_CODE=1
```

- 只列和等待有关的锁：还没拿到的锁，以及挡路会话在同一个对象上已经拿到的锁。没有等待时列表为空，结论 OK。
- `blocked_by` 是直接挡住它的会话，不是整条等待链。
- 每个等锁的会话报一条 `lock.waiting`；等待时间低于 `--lock-wait-warn` 的只列出来，不报。
- `wait_s` 是近似值：用会话最近一次状态变化到现在的时间估算。
- 如果挡路的是一个两阶段提交（prepare 后未结束）的事务，`blocked_by` 显示 `[0]`，因为它已经不属于任何会话；这时去主库跑 [`kbdiag txn`]({{< relref "/docs/reference/txn" >}}) 找它。

## 权限不足时

用没有监控角色的账号 `kbdiag_ro` 远程连接，锁等待还在：

```bash
PGPASSWORD=... ~/kbdiag locks --host 127.0.0.1 -U kbdiag_ro
echo EXIT_CODE=$?
```

```text
locks  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-09-24T04:41:05+08:00)

lock.list: 2 rows
pid     locktype  relation                mode                 granted  wait_s  blocked_by
367208  relation  public.kbdiag_inj_lock  AccessExclusiveLock  true     -       []
367217  relation  public.kbdiag_inj_lock  AccessShareLock      false    -       [367208]

redacted: lock.list.wait_s in 1 rows (insufficient_privilege)
EXIT_CODE=3
```

- 锁本身能看到，谁挡谁也能看到；但这个账号看不到别人会话的时间，`wait_s` 算不出来，没法判断有没有超过阈值，所以结论 UNKNOWN，退出码 3。
- 授予 `sys_monitor` 角色后恢复正常。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
