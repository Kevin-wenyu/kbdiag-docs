---
title: "正在运行的慢 SQL"
description: "找到慢查询，并核实它在等待什么。"
weight: 10
---

采集于 2026-09-16（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具源码提交 `3bea0be`，使用仓库中的 `dist/kbdiag`。这是测试环境实测，不代表生产环境验收。文中 PID、计数与时间只属于本次采样。

## 1. 找到候选查询

```bash
~/kbdiag perf slow -v --no-color --exit-code
rc=$?
printf 'EXIT_CODE=%s\n' "$rc"
```

默认筛选运行超过 5 秒的 active 查询，可通过 `KB_SLOW_THRESHOLD` 调整。它不是历史慢日志；短查询或已结束查询可能不会出现。

## 2. 对照真实输出

下面使用有时限的 `pg_sleep(22)` 测试会话验证检测；没有模拟 CPU 或磁盘压力。`PROCESS_EXIT` 为采集脚本记录的进程退出码，不是工具自身输出。

```text
==> Slow queries (running > 5s)
[WARN]  Slow queries: 1 running > 5s
PID    USER    DURATION  CLIENT_ADDR  QUERY
81070  system  0:00:09   -            SET application_name='kbdiag_docs_slow'; SELECT pg_sleep(22);

PROCESS_EXIT=1
```
系统视图独立核对：

```text
pid|application_name|state|wait_event_type|wait_event|query
81070|kbdiag_docs_slow|active|Timeout|PgSleep|SET application_name='kbdiag_docs_slow'; SELECT pg_sleep(22);
(1 row)

PROCESS_EXIT=0
```

## 3. 深查并判断

将当前采样中的 PID 代入 `~/kbdiag sql <PID>`，核对用户、SQL、状态和等待事件；不要照抄本页 PID。该命令还会尝试普通 EXPLAIN，不会执行 EXPLAIN ANALYZE。会话结束、多语句文本或权限限制可能导致计划不可用。

本例 `Timeout / PgSleep` 与主动 sleep 一致，不能据此建议加索引。真实业务需进一步核对锁、执行计划、数据量和调用频率。默认不带 `--exit-code` 时，检测到慢查询并不保证返回非零；本例显式启用后返回 1。

## 4. 验证结束

本次测试自然结束，随后确认测试会话数为 0。实际处理后再次采样，并结合应用响应时间确认改善；一次列表为空不足以证明间歇性问题已解决。

[如果发现锁等待，继续这里]({{< relref "/docs/scenarios/lock-waits" >}})
