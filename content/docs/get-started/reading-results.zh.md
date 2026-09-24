---
title: "读懂一个真实结果"
description: "测试环境实测的一个 WARN，逐行解读文本和 JSON 输出。"
weight: 10
---

采集于 2026-09-24（UTC+08），本地 KingbaseES V008R006C009B0014 主节点，数据库 `test`。工具是 Go 版源码提交 `6803c61` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。PID、计数和时间只属于本次采样。 idle in transaction 的会话由故障注入脚本造出来；为了不用等默认的 300 秒，用 `--idle-in-txn-warn 5` 把报警阈值调到了 5 秒。

## 命令和输出

```bash
~/kbdiag sessions --idle-in-txn-warn 5 --limit 5
echo EXIT_CODE=$?
```

```text
sessions  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-24T10:20:28+08:00)

[WARN] session.idle_in_txn  会话 436492 处于 idle in transaction 已 9 秒
  verify: kbdiag session 436492  # 看它持有哪些锁、有没有挡住别人

session.activity: 5 rows
pid     usename  datname  application_name     client_addr  backend_type         state                backend_xid  backend_xmin  xact_age_s  query_age_s  state_age_s  wait_event_type  wait_event        query
436492  system   test     kbdiag_inj_idle_txn  -            client backend       idle in transaction  6101         -             11.1        10.1         9.1          Client           ClientRead        select txid_current() as kbdiag_last, pg_sleep(1);
3271    -        -        check pointer        -            checkpointer         -                    -            -             -           -            -            Activity         CheckpointerMain  
3272    -        -        background flush     -            background writer    -                    -            -             -           -            -            Activity         BgWriterMain      
3273    -        -        wal flush            -            walwriter            -                    -            -             -           -            -            Activity         WalWriterMain     
3274    -        -        auto vacuum          -            autovacuum launcher  -                    -            -             -           -            -            Activity         AutoVacuumMain    
... 7 more rows not shown (use --limit 0 to show all)
EXIT_CODE=1
```

## 逐行看

- **第一行**：命令（`sessions`）、结论（`WARN`）和上下文：数据库版本、角色（`primary`）、`用户@位置`（`local` 表示走 socket）和采集时间。
- **finding**：`[WARN]`，然后是稳定的编号（`session.idle_in_txn`），再是症状：会话 436492 处于 idle in transaction 已 9 秒。脚本要依赖的是编号和字段，不是症状文字。
- **`verify:`**：下一步要跑的命令和原因。这里是去看会话 436492 持有哪些锁、有没有挡住别人。如果出现 `fix:` 行，那是一条让你自己判断的语句，kbdiag 从不执行它。
- **数据**：每个探针一张表，表名就是探针编号（`session.activity`）。`-` 表示空值。会话按事务时长排序，所以 idle in transaction 的会话排第一；后台进程也属于这张列表，跟在后面。
- **截断**：`--limit 5` 显示了 5 行，另有 7 行没显示。判定仍然覆盖全部行，没显示的行里有问题照样会影响结论。
- **退出码 1**：WARN。FAIL 是 2，UNKNOWN 是 3。

## 同一份报告的 JSON

`--json` 内容相同，字段名稳定。下面摘的是稍后一刻运行 `~/kbdiag sessions --idle-in-txn-warn 5 --limit 2 --json` 得到的 `findings` 数组：

```json
[
  {
    "id": "session.idle_in_txn",
    "level": "WARN",
    "symptom": "会话 436492 处于 idle in transaction 已 10 秒",
    "evidence": [
      {
        "probe_id": "session.activity",
        "fields": {
          "backend_xid": 6101,
          "pid": 436492,
          "state": "idle in transaction",
          "state_age_s": 9.6
        }
      }
    ],
    "cause": null,
    "next": [
      {
        "kind": "verify",
        "command": "kbdiag session 436492",
        "note": "看它持有哪些锁、有没有挡住别人"
      }
    ]
  }
]
```

完整报告里还有 `command`、`verdict`、`context`、`data`（每个探针带 `status`、`columns`、`rows` 和 `truncated`）以及 `redacted`（当前账号无权看到的字段）。退出码和文本模式一样。

## 后续

注入的会话随后被释放，复查时已经没有测试会话。真实情况下，先跑 `verify` 命令，再和应用负责人一起决定这个事务该提交、回滚还是断开连接。

[排查锁等待]({{< relref "/docs/scenarios/lock-waits" >}}) · [回到第一次检查]({{< relref "/docs/get-started" >}}#exit-codes)
