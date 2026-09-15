---
title: "怎样解读检查结果"
description: "用明确标注的示意片段解释状态、阈值和下一步。"
weight: 10
---

## 示例性质 {#provenance}

以下是**根据当前输出格式编写的示意节选，数值为虚构**，不是测试主机采集结果。它只用于解释阅读方式，也不是一次完整巡检。

真实示例应附带工具版本、数据库版本、节点角色、采集时间、完整命令与退出码。

```text
[OK] Connections: 4% (8/200)
[WARN] Waiting locks: 2
```

## 逐行理解 {#interpretation}

- `Connections`：示意中的当前连接数为 8，上限为 200，整数百分比为 4%。这一项为 OK，不代表其他检查项全部正常。
- `Waiting locks`：当前代码统计 `sys_locks` 中未授予的锁记录；这里的 2 是锁记录数，**不能直接当作两名用户或两个会话**。
- 仅凭节选不能推断完整命令的退出码。完整检查中若有 WARN 而没有 FAIL，`check` 返回 1；有 FAIL 则返回 2。

## 下一步 {#next}

```bash
~/kbdiag locks wait
```

查看等待关系与会话信息，核实相关 SQL 和业务。该示意片段不能说明应该终止哪个会话；不要根据一个计数直接执行 `kill`。

[回到首次巡检]({{< relref "/docs/get-started" >}}#run-check)
