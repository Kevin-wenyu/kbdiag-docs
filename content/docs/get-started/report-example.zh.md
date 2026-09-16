---
title: "巡检报告样例与解读"
description: "下载脱敏报告，理解摘要、退出码及证据边界。"
weight: 20
---

## 生成报告

```bash
~/kbdiag report ./inspection.md --no-color
rc=$?
printf 'EXIT_CODE=%s\n' "$rc"
```

命令写入 Markdown 文件；即使返回 1 或 2，也应检查已生成的报告。避免将退出码非零直接当成“文件未生成”。报告会汇总多个检查，运行期间数据可能变化，不是数据库备份或同一时刻的快照。

## 下载真实样例

[下载脱敏 Markdown 报告]({{< sample-report >}})

这是 2026-09-16 08:38（UTC+08）归档修复前的测试采集，工具 `v1.0.0-115 (2026-08-10)`，源码提交 `3bea0be`。主机、地址、路径、业务对象名和许可证客户字段已替换，告警和计数保留。工具自身不会保证报告脱敏，对外分享前必须审核。

本次退出码为 **2**，摘要如下：

**Overall: FAIL** — 56 OK / 16 WARN / 1 FAIL

| Section | Level | Finding |
|---------|-------|---------|
| Health check | WARN | Archiver: 1419 failed file(s) |
| Health check | WARN | WAL archiving: failing (1419 failures, last: 2026-09-16 08:37:38.581359+08) — run: kbdiag backup |
| Failover readiness | WARN | Archive backlog: 32 WAL pending (>= 10) |
| Backup & archiving | FAIL | Archiver is FAILING — 1422 failure(s), last: 000000030000000000000080 at 2026-09-16 08:38:39.287573+08 (last success: never) |
| Backup & archiving | WARN | 32 WAL segment(s) pending archive (.ready) — archiver is falling behind |
| Index health | WARN | 1 duplicate index pair(s) |
| Index health | WARN | 6 bloated index(es) — consider REINDEX CONCURRENTLY |
| Security audit | WARN | 5 login role(s) have no password expiry (VALID UNTIL) set |
| Security audit | WARN | 91 user table(s) without primary keys |
| Security audit | WARN | sys_hba.conf: 5 of 10 rule(s) need review |
| Security audit | WARN | SSL is disabled — client connections are unencrypted |
| Security audit | WARN | Three-power separation (sepapower) is disabled — the DBA role has unrestricted control over audit/security config |
| Recommendations | WARN | 1 duplicate index pair(s) — run 'kbdiag idx dup' for detail |
| Recommendations | WARN | sys_catalog._kingbase_loginfo: xid_age=2147483647 — freeze risk, run VACUUM FREEZE |
| Recommendations | WARN | shared_buffers=512MB — recommend 1986MB (25% of 7946MB RAM) |
| Recommendations | WARN | checkpoint_completion_target=0.5 — recommend 0.9 |
| Recommendations | WARN | work_mem=4MB — recommend ~19MB (RAM/100conn/4) |


## 解读顺序

1. 先看 Overall：按底层输出的严重程度汇总。本次 1 条 FAIL 来自归档失败。
2. 再看对应章节：同一问题可能出现在健康检查、容灾就绪和备份章节，16 条 WARN 不等于 16 个独立故障。
3. 回到单项命令核实：例如 `~/kbdiag backup`；不同章节失败计数略有差异，是连续采样期间计数继续增长。
4. 最后决定处置：索引膨胀是估算，内存参数是启发式建议。系统对象的 freeze 建议尤其需要核实版本与支持范围，不应从报告直接复制执行维护 SQL。

## 交接时附带什么

附采集时间、版本、目标角色、完整命令、退出码、脱敏说明，以及每项处置的负责人和复核结果。报告中的“OK”只覆盖已执行的检查；异常未输出标记时，不能据此证明一切正常。

## 后续修复记录

2026-09-16，核实并更新归档仓库节点的 SSH 主机密钥，补齐备份检查的端口和角色配置后，`sys_rman check` 成功验证新 WAL 入库。最终两节点待归档队列均为 0；主节点成功归档 35 个 WAL，历史失败数保持 1422。历史 WARN 保留，未重置统计。上文保留修复前采样，不能代表当前状态；本次未做完整恢复演练。
