---
title: "排查锁等待"
description: "核对等待关系，确认事务，再验证恢复。"
weight: 20
---

采集于 2026-09-16（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具源码提交 `3bea0be`，使用仓库中的 `dist/kbdiag`。这是测试环境实测，不代表生产环境验收。文中 PID、计数与时间只属于本次采样。

## 1. 查看等待关系

```bash
~/kbdiag locks wait -v --no-color --exit-code
```

先保存退出码及输出，再用 `~/kbdiag sql <WAIT_PID>`、`~/kbdiag sql <BLOCK_PID>` 查看当前会话详情。PID 可能消失或被复用，操作前应重新确认用户、应用和 SQL。

## 2. 真实测试输出

本次在专用表上构造两个事务更新同一行：持锁方暂停 28 秒后回滚；等待方设置 35 秒语句超时，完成后也回滚。它模拟单一行更新阻塞，不是死锁实验。以下 SQL 列是工具原样截断输出。

```text
==> Waiting locks
[WARN]  Waiting locks: 1 blocked session(s) (longest 6s, showing top 10)
[OK]    Long lock waits: none > 60s

WAIT_PID  WAIT_USER  BLOCK_PID  BLOCK_USER  LOCKTYPE       MODE       WAIT     WAIT_QUERY                                                                                            BLOCK_QUERY
81518     system     81440      system      transactionid  ShareLock  0:00:06  SET application_name='kbdiag_docs_waiter'; SET statement_timeout='35000'; BEGIN; UPDATE kbdiag_docs_  SET application_name='kbdiag_docs_holder'; BEGIN; UPDATE kbdiag_docs_20260916.lock_demo SET value=1 

PROCESS_EXIT=1
```
独立系统视图证据：

```text
pid|application_name|state|wait_event_type|wait_event
81440|kbdiag_docs_holder|active|Timeout|PgSleep
81518|kbdiag_docs_waiter|active|Lock|transactionid
(2 rows)
pid|locktype|mode|granted
81518|transactionid|ShareLock|f
(1 row)

PROCESS_EXIT=0
```

## 3. 怎样判断

- `WAIT_PID=81518` 正在等待，`BLOCK_PID=81440` 持有相关锁；仅在本次受控场景中核实这对关系。
- `transactionid / ShareLock` 表示等待相关事务结束，并不是“整张表被 ShareLock 锁住”。
- `WAIT` 来自查询开始至采样时的时长，不是精确的锁等待计时。
- 存在等待就会 WARN；没有超过默认 60 秒的长等待仍可显示 OK。两行并不矛盾。
- 输出中的计数来自锁关联结果，复杂场景可能一会话对应多行；不要直接当作受影响用户数。
- 本例开启 `--exit-code`，返回 1。`PROCESS_EXIT` 是采集脚本附加的标记。

## 4. 处置与复核

先联系事务所属业务，确认它是否应继续、提交或回滚。不要看到 PID 就终止会话。`kbdiag kill <PID>` 默认取消当前语句，`--terminate` 才结束连接；取消语句不保证事务已结束、全部锁已释放，尤其不能假定 idle in transaction 会因此消失。

本实验通过持锁事务主动回滚释放锁。两个测试事务退出后，核对原行仍为 `id=1, value=0`，删除专用表和 schema，并确认测试会话与 schema 计数均为 0。

真实处置后重新运行 `locks wait`，同时核对应用请求恢复及事务状态。当前等待清空与累计死锁统计是不同问题；本实验没有产生或重置死锁统计。
