---
title: "功能概览"
description: "按健康、复制、SQL、锁、维护和诊断六类问题选择命令。"
weight: 20
---

先确定你要回答的问题，再选择命令。下面的示例假定工具已安装到 `~/kbdiag`；完整参数见[使用手册](../reference/)。

## 健康巡检 {#health}

**问题：数据库现在正常吗？哪些项目需要关注？**

- `status`：进程、连接性、角色和运行时长。
- `check`：根据阈值输出健康判定；`check --os` 增加操作系统符合性检查。
- `report [file]`：将多项现有检查汇总为 Markdown 巡检报告。

```bash
~/kbdiag status
~/kbdiag check
~/kbdiag report inspection.md
```

先查看 WARN / FAIL，再选择深查命令。`report` 会在指定位置写文件；它汇总检查结果，不替代备份或持续监控。文件名请使用新名称，避免覆盖已有报告。

→ [完成首次巡检并理解结果](../get-started/)

## 主备与复制 {#replication}

**问题：主备拓扑怎样？复制是否落后？切换条件是否满足？**

- `cluster`：查看 repmgr 集群拓扑。
- `cluster ready`：检查切换就绪条件。
- `replication`：查看复制状态与延迟。

```bash
~/kbdiag cluster
~/kbdiag replication
~/kbdiag cluster ready
```

主库和备库可见的指标不同。repmgr、节点配置及相关进程影响集群检查范围。就绪检查不是执行切换，也不能代替切换演练。

## SQL 与性能 {#performance}

**问题：现在什么查询慢？历史上谁耗时多？一段时间内负载怎样变化？**

| 观察角度 | 命令 | 重点 |
|---|---|---|
| 当前活动 | `perf slow`、`wait` | 当前慢查询与等待分布 |
| 累积 SQL 统计 | `stmt` | 已记录 SQL 的耗时、调用等统计 |
| 执行计划 | `explain` | 计划结构与值得复核的提示 |
| 时间区间 | `workload` | 根据可用历史信息查看负载 |

```bash
~/kbdiag perf slow
~/kbdiag stmt
~/kbdiag workload --from 1h --no-snapshot
```

历史分析依赖相应扩展或统计视图，不能把“没有记录”解释成“没有慢查询”。`workload` 优先使用 `sys_kwr`；缺少它时回退最近 15 分钟的滚动指标，不等同于任意时间窗口报告。快照不足时，默认可能在可写主库补建快照；`--no-snapshot` 禁用补建。

## 锁与会话 {#locks}

**问题：谁在等待？谁可能阻塞了它？会话正在执行什么？**

```bash
~/kbdiag sessions
~/kbdiag locks wait
~/kbdiag locks hold
```

先检查等待与持锁信息，再使用 `sql <pid>` 查看对应会话 SQL。PID 来自当次输出，会话可能在下一次检查前结束。

`kill` 属于处理动作：默认取消查询，`--terminate` 会终止会话。应先核实会话与业务影响；首次巡检不需要执行它。

## 空间与维护 {#maintenance}

**问题：空间花在哪里？索引、统计信息和维护状态有哪些线索？**

```bash
~/kbdiag space
~/kbdiag idx
~/kbdiag advisor index
```

`obj <schema.table>` 深查指定对象，`colstat <schema.table>` 查看列统计，`perf bloat` / `perf vacuum` 提供相关检查入口。

索引使用统计和估算值需要结合采样窗口与业务判断。`advisor index --fix` 生成建议 SQL，不执行；生成的删除或创建语句仍需人工审查。

## 综合诊断与现场采集 {#diagnosis}

**问题：多项异常如何联系起来？怎样保留现场供后续调查？**

- `diagnose` / `diagnose --full`：关联检查信号，输出诊断与建议。
- `advisor`：按索引、vacuum、参数和统计信息等维度给出建议。
- `snapshot [file]`：将会话、锁、等待、性能和部分日志等信息打包。

```bash
~/kbdiag diagnose
~/kbdiag advisor
~/kbdiag snapshot incident.tar.gz
```

诊断结论应回到具体指标核实。`snapshot` 在本地写归档文件，不能用于恢复数据库。当前实现遮盖单引号字面量，并不保证移除所有敏感信息；对外分享前检查归档内容。

## 将结果接入脚本 {#automation}

多数命令支持 `--format json`，`watch` 除外。`check` 等判定型命令直接返回健康判定；多数数据查询命令默认不按检查发现返回非零值，需要时使用 `--exit-code`。参数错误和执行失败仍可能返回非零值。

```bash
~/kbdiag --format json check
```

接入前请核实具体命令行为，见[退出码说明](../get-started/#exit-codes)。

[按场景排查：慢 SQL 与锁等待]({{< relref "/docs/scenarios" >}})
