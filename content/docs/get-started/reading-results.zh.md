---
title: "读懂一次真实结果"
description: "一次真实的 WARN 输出，逐行解读，文本和 JSON 两种格式。"
weight: 10
---

采集于 2026-09-27（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `93bf65d` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数与时间只属于本次采样。idle in transaction 的会话是故障注入脚本造出来的；用 `--idle-in-txn-warn 5` 把报警阈值降到 5 秒，免得例子要等默认的 300 秒。

## 命令和输出

```bash
~/kbdiag sessions --idle-in-txn-warn 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T13:37:04+08:00)

[WARN] session.idle_in_txn  session 1049818 has been idle in transaction for 9s
  verify: kbdiag session 1049818  # which locks it holds, whether it blocks anyone

connected: 4 client sessions (not counting kbdiag), 1 walsender, 7 background
  count  user    database  application          client
  2      esrep   esrep     internal_rwcmgr      192.168.105.10
  1      esrep   esrep     internal_rwcmgr      192.168.105.11
  1      system  test      kbdiag_inj_idle_txn  local

not idle: 2
  pid      user    database  application          client          state                xact  query  wait  sql
  1049818  system  test      kbdiag_inj_idle_txn  local           idle in transaction  11s   10s    -     select txid_current() as kbdiag_last, pg_sleep(1);
  179417   esrep   esrep     internal_rwcmgr      192.168.105.10  active               0s    0s     -     SELECT n.node_id, n.type, n.upstream_node_id, n.node_name...
EXIT_CODE=1
```

## 逐行解读

- **第一行**：命令（`sessions`）、结论（`WARN`）和上下文：服务器版本、角色（`primary`）、`用户@位置`（`local` 是 socket）、采集时间。
- **finding**：`[WARN]`，然后是稳定的 id（`session.idle_in_txn`），再是症状：会话 1049818 处于 idle in transaction 已 9 秒。脚本应当依赖 id 和 JSON 字段，症状的措辞可能会变。
- **`verify:`** 下一步该跑的命令和原因。这里是：看会话 1049818 持有哪些锁、有没有挡住别人。出现 `fix:` 行时，它给的是一条供你审阅的语句，kbdiag 从不执行。
- **数据**：按便于阅读的方式排版。`connected` 按用户、库、应用、客户端给客户端会话计数；`not idle` 列出在干活或开着事务的会话，事务最久的在前。`-` 是空值；`?` 表示这个账号看不到的值。
- `esrep` 那一行是 repmgr 自己的查询，采样时正好在跑。idle 的会话和后台进程只在标题里计数，要看用 `--all`。
- **退出码 1**：WARN，表示还没坏，但放着不管会出事。FAIL（业务已经受影响）是 2，UNKNOWN 是 3。

## 同一份报告的 JSON

`--json` 带同样的内容，字段名稳定。下面是 `~/kbdiag sessions --idle-in-txn-warn 5 --json` 稍后一次运行的 `findings` 数组：

```json
[
  {
    "id": "session.idle_in_txn",
    "level": "WARN",
    "symptom": "session 1049818 has been idle in transaction for 9s",
    "evidence": [
      {
        "probe_id": "session.activity",
        "fields": {
          "backend_xid": 6353,
          "pid": 1049818,
          "state": "idle in transaction",
          "state_age_s": 9.1
        }
      }
    ],
    "cause": null,
    "next": [
      {
        "kind": "verify",
        "command": "kbdiag session 1049818",
        "note": "which locks it holds, whether it blocks anyone"
      }
    ]
  }
]
```

完整报告里还有：

- `command`、`verdict`、`context`。
- `data`：每个 probe 的 `status`、`columns`、`rows`、`truncated`。JSON 保留原始值（秒、字节、完整 SQL），而且总是包含全部会话，idle 的会话和后台进程也在内：这里是 12 行，文本只列了 2 行。
- `redacted`：这个账号无权看到的字段。

退出码和文本模式相同。

## 后来

注入的会话随后被释放，复查确认测试会话已全部清掉。真实场景下，先跑 `verify` 命令，再和应用负责人一起决定：提交、回滚，还是关掉连接。

[排查锁等待]({{< relref "/docs/scenarios/lock-waits" >}}) · [回到第一次检查]({{< relref "/docs/get-started" >}}#exit-codes)
