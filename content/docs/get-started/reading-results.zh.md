---
title: "怎样解读真实巡检结果"
description: "真实测试输出、退出码与下一步。"
weight: 10
---

采集于 2026-09-16（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具源码提交 `3bea0be`，使用仓库中的 `dist/kbdiag`。这是测试环境实测，不代表生产环境验收。文中 PID、计数与时间只属于本次采样。

## 命令与完整输出

```bash
KB_DB=test ~/kbdiag check --no-color
rc=$?
printf "EXIT_CODE=%s\n" "$rc"
```

```text
==> Health check
[OK]    Connections: 12% (12/100)
[OK]    Long transactions: none
[OK]    Waiting locks: none
[WARN]  Archiver: 1407 failed file(s)
[OK]    Autovacuum backlog: none
[OK]    Buffer hit rate: 99.6%
[OK]    Checkpoint pressure: 0 requested checkpoints
[OK]    Temp file usage: 0 bytes
[OK]    Deadlocks: none
[OK]    Replication slot lag: 0bytes
[OK]    BGWriter pressure: 0% backend writes
[OK]    XID age: 4717
[OK]    oldest active transaction: 0s
[WARN]  WAL archiving: failing (1407 failures, last: 2026-09-16 07:05:31.025697+08) — run: kbdiag backup
EXIT_CODE=1
```

## 怎样理解

- 连接数为 12/100，连接检查为 OK；它不能覆盖归档等其他检查项。
- 本次没有等待锁。出现等待锁计数时，`check` 统计的是未授予的锁记录，不等于会话数。
- 两条归档 WARN 是相关信号，不能把两个 1407 相加；失败计数包含历史，需结合最后失败时间及后续成功记录判断是否仍在失败。
- 本次完整命令退出码为 1，表示有 WARN、无 FAIL。若有 FAIL，返回 2。

## 下一步

运行 `~/kbdiag backup` 查看备份与归档相关信息，再核实归档命令、目标目录空间、权限和数据库日志。不要为了让检查变绿而清空统计。本文没有修复或验收归档问题。

[锁等待排查]({{< relref "/docs/scenarios/lock-waits" >}}) · [回到首次巡检]({{< relref "/docs/get-started" >}}#run-check)
