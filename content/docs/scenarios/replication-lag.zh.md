---
title: "复制延迟排查"
description: "结合主备状态与 LSN 判断复制是否积压。"
weight: 30
---

2026-09-16 测试环境实测；KingbaseES V008R006C009B0014，工具源码 `3bea0be`。主机地址替换为文档专用地址。以下是正常复制基线，没有人为暂停回放或模拟故障。

## 1. 分别检查主备

先用 `~/kbdiag status` 确认连接目标与角色，再分别运行：

```bash
~/kbdiag replication -v --no-color --exit-code
```

主节点输出及系统视图核对：

```text
==> Replication
[INFO]  Standby connections:
client_addr        state      sync_state  replay_lag
192.0.2.11/32  streaming  quorum      0 bytes
[OK]    1 standby(s) connected
EXIT_CODE=0
current_timestamp|application_name|state|sync_state|sent_lsn|write_lsn|flush_lsn|replay_lsn
2026-09-16 08:38:13.508273+08|node2|streaming|quorum|0/A00117E8|0/A00117E8|0/A00117E8|0/A00117E8
(1 row)
```
备节点输出及独立核对：

```text
==> Replication
[OK]    WAL receiver: streaming
[INFO]  Replay delay : +00000000000:00:43.000000000
[INFO]  Receive LSN  : 0/A00117E8
[INFO]  Replay  LSN  : 0/A00117E8
EXIT_CODE=0
current_timestamp|status
2026-09-16 08:38:15.648926+08|streaming
(1 row)
pg_last_wal_receive_lsn|pg_last_wal_replay_lsn
0/A00117E8|0/A00117E8
(1 row)
```

## 2. 字节差与时间不是同一个指标

- 主节点 `replay_lag` 是 `sent_lsn - replay_lsn` 的字节差，不是秒。本次为 0 bytes。
- 备节点 receive/replay LSN 相同，表示在此采样点接收的 WAL 已回放到同一位置。主备查询并非原子快照。
- `Replay delay` 是当前时间减去最近回放事务时间。空闲时即使已追平，它也可能增长；本例约 43 秒，不能解释为积压 43 秒。
- `streaming` 仅表示当前接收状态，不能单独证明没有延迟；`quorum` 也不是完整的容灾验收。
- 本次退出码 0；此命令没有对所有延迟值实施阈值判定。不能只用退出码监控复制时延。

## 3. 按证据分流

| 现象 | 下一步 |
|---|---|
| 主节点没有预期备库连接 | 核对备库进程、连接日志、网络和认证；独立单机可能本就没有备库 |
| 接收位置持续落后于主节点发送位置 | 同时检查两端网络、WAL sender/receiver 与备库写入能力 |
| 已接收位置领先于回放位置，差值持续扩大 | 核对回放是否暂停、恢复冲突、磁盘负载及相关日志 |
| LSN 已追平，只有时间值增加 | 观察业务写入是否空闲，不要直接判为复制故障 |

可用 `~/kbdiag check` 与 `~/kbdiag cluster ready` 补充检查，但不要为了消除告警而切主、重建备库或推进复制槽。

## 4. 验证恢复

在有正常业务提交时进行多次采样，确认预期备库保持连接，接收和回放位置持续推进，差值收敛，并核对业务可见性。短暂追平不等于持续稳定，也不等于备份可恢复。
