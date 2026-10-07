---
title: "params：改过的参数"
description: "哪些参数不是默认值、在哪设的；改了要重启才生效的报 WARN。"
weight: 120
---

采集于 2026-10-07（UTC+08），本地 KingbaseES V008R006C009B0014 主节点和备节点，数据库 `test`。工具是 Go 版源码提交 `96c874f` 编译的 `~/kbdiag`（linux/amd64 静态二进制）。这是测试环境实测，不代表生产环境验收。WARN 的例子由注入脚本造出来：它用 `ALTER SYSTEM` 改了 `max_files_per_process`（需要重启的参数），reload 了配置，没有重启，所以运行值和文件里的不一样。数值只属于本次采样。

## 用法

```text
kbdiag params [--json]
```

没有自己的参数，也没有按名字过滤：看单个参数用 `ksql -c 'show x'`，或者 `--json` 配 jq。连接参数和 [`sessions`]({{< relref "/docs/reference/sessions" >}}) 相同。

## 主库，正常

```bash
~/kbdiag params
echo EXIT_CODE=$?
```

```text
params  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:20:55+08:00)

pending restart: 0

changed: 63 parameters not at their default (sources other than default, override and this connection)
  this connection sets application_name, default_transaction_read_only, lock_timeout and statement_timeout itself, so their configured values are not shown; per-role and per-database settings show only for this role and database
  name                          setting                                                       unit  source              file
  archive_command               export TZ=Asia/Shanghai;/home/kingbase/cluster/install/ki...  -     configuration file  es_rep.conf:10
  archive_mode                  always                                                        -     configuration file  es_rep.conf:9
  control_file_copy             /home/kingbase/cluster/install/kingbase/copy_file             -     configuration file  es_rep.conf:11
  DateStyle                     ISO, MDY                                                      -     configuration file  kingbase.conf:654
  default_text_search_config    pg_catalog.english                                            -     configuration file  kingbase.conf:676
  dynamic_shared_memory_type    posix                                                         -     configuration file  kingbase.conf:140
  fsync                         on                                                            -     configuration file  es_rep.conf:23
  full_page_writes              on                                                            -     configuration file  es_rep.conf:3
  hot_standby                   on                                                            -     configuration file  es_rep.conf:13
  hot_standby_feedback          on                                                            -     configuration file  es_rep.conf:14
  lc_messages                   C                                                             -     configuration file  kingbase.conf:669
  lc_monetary                   en_US.UTF-8                                                   -     configuration file  kingbase.conf:671
  lc_numeric                    en_US.UTF-8                                                   -     configuration file  kingbase.conf:672
  lc_time                       en_US.UTF-8                                                   -     configuration file  kingbase.conf:673
  listen_addresses              *                                                             -     configuration file  es_rep.conf:1
  log_autovacuum_min_duration   0                                                             ms    configuration file  es_rep.conf:40
  log_checkpoints               on                                                            -     configuration file  es_rep.conf:38
  log_connections               on                                                            -     configuration file  es_rep.conf:32
  log_destination               stderr                                                        -     configuration file  es_rep.conf:44
  log_directory                 sys_log                                                       -     configuration file  kingbase.conf:432
  log_disconnections            on                                                            -     configuration file  es_rep.conf:33
  log_filename                  kingbase-%d.log                                               -     configuration file  es_rep.conf:43
  logging_collector             on                                                            -     configuration file  es_rep.conf:15
  log_line_prefix               %t [%p]: [%l-1] [%x] user=%u,db=%d,app=%a,client=%h           -     configuration file  es_rep.conf:42
  log_lock_waits                on                                                            -     configuration file  es_rep.conf:39
  log_min_duration_statement    1000                                                          ms    configuration file  es_rep.conf:47
  log_replication_commands      on                                                            -     configuration file  es_rep.conf:18
  log_rotation_age              1440                                                          min   configuration file  es_rep.conf:46
  log_statement                 ddl                                                           -     configuration file  es_rep.conf:36
  log_temp_files                0                                                             kB    configuration file  es_rep.conf:41
  log_timezone                  Asia/Shanghai                                                 -     configuration file  kingbase.conf:540
  log_truncate_on_rotation      on                                                            -     configuration file  es_rep.conf:45
  max_connections               100                                                           -     configuration file  es_rep.conf:7
  max_prepared_transactions     100                                                           -     configuration file  es_rep.conf:21
  max_replication_slots         32                                                            -     configuration file  es_rep.conf:12
  max_stack_depth               3072                                                          kB    configuration file  kingbase.conf:133
  max_wal_senders               32                                                            -     configuration file  es_rep.conf:5
  max_wal_size                  1024                                                          MB    configuration file  kingbase.conf:224
  min_wal_size                  80                                                            MB    configuration file  kingbase.conf:225
  ora_input_emptystr_isnull     on                                                            -     configuration file  kingbase.conf:767
  ora_integer_div_returnfloat   on                                                            -     configuration file  kingbase.conf:768
  password_encryption           scram-sha-256                                                 -     configuration file  kingbase.conf:91
  port                          54321                                                         -     configuration file  es_rep.conf:2
  primary_conninfo              user=esrep connect_timeout=10 host=192.168.105.11 port=54...  -     configuration file  kingbase.auto.conf:3
  primary_slot_name             repmgr_slot_1                                                 -     configuration file  kingbase.auto.conf:4
  shared_buffers                65536                                                         8kB   configuration file  es_rep.conf:22
  shared_preload_libraries      repmgr, synonym, plsql, force_view, kdb_flashback,plugin_...  -     configuration file  kingbase.conf:766
  synchronous_commit            remote_apply                                                  -     configuration file  es_rep.conf:20
  synchronous_standby_names     ANY 1( node2)                                                 -     configuration file  kingbase.auto.conf:7
  sys_stat_statements.track     none                                                          -     configuration file  kingbase.auto.conf:5
  tcp_keepalives_count          0                                                             -     configuration file  es_rep.conf:27
  tcp_keepalives_idle           0                                                             s     configuration file  es_rep.conf:25
  tcp_keepalives_interval       0                                                             s     configuration file  es_rep.conf:26
  tcp_user_timeout              0                                                             ms    configuration file  es_rep.conf:28
  TimeZone                      PRC                                                           -     configuration file  es_rep.conf:24
  track_real_stats              on                                                            -     configuration file  kingbase.auto.conf:6
  wal_compression               on                                                            -     configuration file  es_rep.conf:19
  wal_keep_segments             512                                                           -     configuration file  es_rep.conf:6
  wal_level                     replica                                                       -     configuration file  es_rep.conf:8
  wal_log_hints                 on                                                            -     configuration file  es_rep.conf:4
  wal_receiver_status_interval  2                                                             s     configuration file  kingbase.conf:323
  wal_receiver_timeout          30000                                                         ms    configuration file  es_rep.conf:30
  wal_sender_timeout            30000                                                         ms    configuration file  es_rep.conf:29
EXIT_CODE=0
```

- `pending restart` 列出文件里的值和正在运行的值不同的参数（服务器自己的 `pending_restart` 标志）。这里没有。
- `changed` 只列有人设过的参数：来源不是 `default`、`override`（编译或 initdb 定的）以及本连接自己的 `client`/`session`（那是 kbdiag 自己设的，列出来是噪声）。`file` 是设置它的文件和行号。
- `changed` 下面那行说明看不全的两处。kbdiag 连接时自己设了 `application_name`、`default_transaction_read_only`、`lock_timeout`、`statement_timeout`，所以它们的配置值看不到；按角色、按库的设置只看得到当前角色和库的。
- `archive_command` 这类长值会用 `...` 截断；`--json` 里是完整的。
- 备库上的列表类似，`primary_conninfo`、`primary_slot_name`、`synchronous_standby_names` 不同（kes-node2 上实采，同样是 63 个参数）。

## 没有权限时

`kbdiag_ro`（没有监控角色，走 `127.0.0.1`）：

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro params
echo EXIT_CODE=$?
```

```text
params  UNKNOWN  (KingbaseES V008R006C009B0014, primary, kbdiag_ro@remote, 2026-10-07T17:21:08+08:00)

pending restart: 0

changed: 59 parameters not at their default (sources other than default, override and this connection)
  this connection sets application_name, default_transaction_read_only, lock_timeout and statement_timeout itself, so their configured values are not shown; per-role and per-database settings show only for this role and database
  name                          setting                                                       unit  source              file
  archive_command               export TZ=Asia/Shanghai;/home/kingbase/cluster/install/ki...  -     configuration file  ?
  archive_mode                  always                                                        -     configuration file  ?
  control_file_copy             /home/kingbase/cluster/install/kingbase/copy_file             -     configuration file  ?
  DateStyle                     ISO, MDY                                                      -     configuration file  ?
  default_text_search_config    pg_catalog.english                                            -     configuration file  ?
  dynamic_shared_memory_type    posix                                                         -     configuration file  ?
  fsync                         on                                                            -     configuration file  ?
  full_page_writes              on                                                            -     configuration file  ?
  hot_standby                   on                                                            -     configuration file  ?
  hot_standby_feedback          on                                                            -     configuration file  ?
  lc_messages                   C                                                             -     configuration file  ?
  lc_monetary                   en_US.UTF-8                                                   -     configuration file  ?
  lc_numeric                    en_US.UTF-8                                                   -     configuration file  ?
  lc_time                       en_US.UTF-8                                                   -     configuration file  ?
  listen_addresses              *                                                             -     configuration file  ?
  log_autovacuum_min_duration   0                                                             ms    configuration file  ?
  log_checkpoints               on                                                            -     configuration file  ?
  log_connections               on                                                            -     configuration file  ?
  log_destination               stderr                                                        -     configuration file  ?
  log_disconnections            on                                                            -     configuration file  ?
  logging_collector             on                                                            -     configuration file  ?
  log_line_prefix               %t [%p]: [%l-1] [%x] user=%u,db=%d,app=%a,client=%h           -     configuration file  ?
  log_lock_waits                on                                                            -     configuration file  ?
  log_min_duration_statement    1000                                                          ms    configuration file  ?
  log_replication_commands      on                                                            -     configuration file  ?
  log_rotation_age              1440                                                          min   configuration file  ?
  log_statement                 ddl                                                           -     configuration file  ?
  log_temp_files                0                                                             kB    configuration file  ?
  log_timezone                  Asia/Shanghai                                                 -     configuration file  ?
  log_truncate_on_rotation      on                                                            -     configuration file  ?
  max_connections               100                                                           -     configuration file  ?
  max_prepared_transactions     100                                                           -     configuration file  ?
  max_replication_slots         32                                                            -     configuration file  ?
  max_stack_depth               3072                                                          kB    configuration file  ?
  max_wal_senders               32                                                            -     configuration file  ?
  max_wal_size                  1024                                                          MB    configuration file  ?
  min_wal_size                  80                                                            MB    configuration file  ?
  ora_input_emptystr_isnull     on                                                            -     configuration file  ?
  ora_integer_div_returnfloat   on                                                            -     configuration file  ?
  password_encryption           scram-sha-256                                                 -     configuration file  ?
  port                          54321                                                         -     configuration file  ?
  primary_slot_name             repmgr_slot_1                                                 -     configuration file  ?
  shared_buffers                65536                                                         8kB   configuration file  ?
  synchronous_commit            remote_apply                                                  -     configuration file  ?
  synchronous_standby_names     ANY 1( node2)                                                 -     configuration file  ?
  sys_stat_statements.track     none                                                          -     configuration file  ?
  tcp_keepalives_count          3                                                             -     configuration file  ?
  tcp_keepalives_idle           2                                                             s     configuration file  ?
  tcp_keepalives_interval       2                                                             s     configuration file  ?
  tcp_user_timeout              9000                                                          ms    configuration file  ?
  TimeZone                      PRC                                                           -     configuration file  ?
  track_real_stats              on                                                            -     configuration file  ?
  wal_compression               on                                                            -     configuration file  ?
  wal_keep_segments             512                                                           -     configuration file  ?
  wal_level                     replica                                                       -     configuration file  ?
  wal_log_hints                 on                                                            -     configuration file  ?
  wal_receiver_status_interval  2                                                             s     configuration file  ?
  wal_receiver_timeout          30000                                                         ms    configuration file  ?
  wal_sender_timeout            30000                                                         ms    configuration file  ?
  only the parameters this account may read: superuser-only ones are not listed
redacted: 59 rows of params.changed hide sourcefile, sourceline (insufficient_privilege; grant sys_monitor)
EXIT_CODE=3
```

- `file` 是 `?`：这个账号看不到 `sourcefile` 和 `sourceline`，记在 `redacted` 里。
- 列表更短（59 个，不是 63 个），因为超级用户专属的参数这个账号根本看不到，最后一行说明了这点。这些参数的 `pending_restart` 也就看不到，所以没有 finding 时结论是 UNKNOWN：看不到的东西，kbdiag 不说 OK。

## 改了还没生效

```bash
~/kbdiag params
echo EXIT_CODE=$?
```

```text
params  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-07T17:21:15+08:00)

[WARN] params.pending_restart  parameter max_files_per_process was changed but the instance still runs with 1000: the new value takes effect only after a restart, the next one included
  verify: select sourcefile, sourceline, setting, applied, error from sys_file_settings where name = 'max_files_per_process'  # the value waiting in the file (needs a superuser)
  fix: ALTER SYSTEM SET max_files_per_process = '1000'  # if the change was not meant: writes the running value back; after SELECT sys_reload_conf() the flag clears (a reload clears it only when the file's value equals the running one, so ALTER SYSTEM RESET alone leaves it until a restart). Otherwise plan the restart

pending restart: 1
  name                   running  file
  max_files_per_process  1000     -

changed: 64 parameters not at their default (sources other than default, override and this connection)
  this connection sets application_name, default_transaction_read_only, lock_timeout and statement_timeout itself, so their configured values are not shown; per-role and per-database settings show only for this role and database
  name                          setting                                                       unit  source              file
  archive_command               export TZ=Asia/Shanghai;/home/kingbase/cluster/install/ki...  -     configuration file  es_rep.conf:10
  archive_mode                  always                                                        -     configuration file  es_rep.conf:9
  control_file_copy             /home/kingbase/cluster/install/kingbase/copy_file             -     configuration file  es_rep.conf:11
  DateStyle                     ISO, MDY                                                      -     configuration file  kingbase.conf:654
  default_text_search_config    pg_catalog.english                                            -     configuration file  kingbase.conf:676
  dynamic_shared_memory_type    posix                                                         -     configuration file  kingbase.conf:140
  fsync                         on                                                            -     configuration file  es_rep.conf:23
  full_page_writes              on                                                            -     configuration file  es_rep.conf:3
  hot_standby                   on                                                            -     configuration file  es_rep.conf:13
  hot_standby_feedback          on                                                            -     configuration file  es_rep.conf:14
  lc_messages                   C                                                             -     configuration file  kingbase.conf:669
  lc_monetary                   en_US.UTF-8                                                   -     configuration file  kingbase.conf:671
  lc_numeric                    en_US.UTF-8                                                   -     configuration file  kingbase.conf:672
  lc_time                       en_US.UTF-8                                                   -     configuration file  kingbase.conf:673
  listen_addresses              *                                                             -     configuration file  es_rep.conf:1
  log_autovacuum_min_duration   0                                                             ms    configuration file  es_rep.conf:40
  log_checkpoints               on                                                            -     configuration file  es_rep.conf:38
  log_connections               on                                                            -     configuration file  es_rep.conf:32
  log_destination               stderr                                                        -     configuration file  es_rep.conf:44
  log_directory                 sys_log                                                       -     configuration file  kingbase.conf:432
  log_disconnections            on                                                            -     configuration file  es_rep.conf:33
  log_filename                  kingbase-%d.log                                               -     configuration file  es_rep.conf:43
  logging_collector             on                                                            -     configuration file  es_rep.conf:15
  log_line_prefix               %t [%p]: [%l-1] [%x] user=%u,db=%d,app=%a,client=%h           -     configuration file  es_rep.conf:42
  log_lock_waits                on                                                            -     configuration file  es_rep.conf:39
  log_min_duration_statement    1000                                                          ms    configuration file  es_rep.conf:47
  log_replication_commands      on                                                            -     configuration file  es_rep.conf:18
  log_rotation_age              1440                                                          min   configuration file  es_rep.conf:46
  log_statement                 ddl                                                           -     configuration file  es_rep.conf:36
  log_temp_files                0                                                             kB    configuration file  es_rep.conf:41
  log_timezone                  Asia/Shanghai                                                 -     configuration file  kingbase.conf:540
  log_truncate_on_rotation      on                                                            -     configuration file  es_rep.conf:45
  max_connections               100                                                           -     configuration file  es_rep.conf:7
  max_files_per_process         1000                                                          -     default             -
  max_prepared_transactions     100                                                           -     configuration file  es_rep.conf:21
  max_replication_slots         32                                                            -     configuration file  es_rep.conf:12
  max_stack_depth               3072                                                          kB    configuration file  kingbase.conf:133
  max_wal_senders               32                                                            -     configuration file  es_rep.conf:5
  max_wal_size                  1024                                                          MB    configuration file  kingbase.conf:224
  min_wal_size                  80                                                            MB    configuration file  kingbase.conf:225
  ora_input_emptystr_isnull     on                                                            -     configuration file  kingbase.conf:767
  ora_integer_div_returnfloat   on                                                            -     configuration file  kingbase.conf:768
  password_encryption           scram-sha-256                                                 -     configuration file  kingbase.conf:91
  port                          54321                                                         -     configuration file  es_rep.conf:2
  primary_conninfo              user=esrep connect_timeout=10 host=192.168.105.11 port=54...  -     configuration file  kingbase.auto.conf:3
  primary_slot_name             repmgr_slot_1                                                 -     configuration file  kingbase.auto.conf:4
  shared_buffers                65536                                                         8kB   configuration file  es_rep.conf:22
  shared_preload_libraries      repmgr, synonym, plsql, force_view, kdb_flashback,plugin_...  -     configuration file  kingbase.conf:766
  synchronous_commit            remote_apply                                                  -     configuration file  es_rep.conf:20
  synchronous_standby_names     ANY 1( node2)                                                 -     configuration file  kingbase.auto.conf:7
  sys_stat_statements.track     none                                                          -     configuration file  kingbase.auto.conf:5
  tcp_keepalives_count          0                                                             -     configuration file  es_rep.conf:27
  tcp_keepalives_idle           0                                                             s     configuration file  es_rep.conf:25
  tcp_keepalives_interval       0                                                             s     configuration file  es_rep.conf:26
  tcp_user_timeout              0                                                             ms    configuration file  es_rep.conf:28
  TimeZone                      PRC                                                           -     configuration file  es_rep.conf:24
  track_real_stats              on                                                            -     configuration file  kingbase.auto.conf:6
  wal_compression               on                                                            -     configuration file  es_rep.conf:19
  wal_keep_segments             512                                                           -     configuration file  es_rep.conf:6
  wal_level                     replica                                                       -     configuration file  es_rep.conf:8
  wal_log_hints                 on                                                            -     configuration file  es_rep.conf:4
  wal_receiver_status_interval  2                                                             s     configuration file  kingbase.conf:323
  wal_receiver_timeout          30000                                                         ms    configuration file  es_rep.conf:30
  wal_sender_timeout            30000                                                         ms    configuration file  es_rep.conf:29
EXIT_CODE=1
```

- `params.pending_restart` 是 WARN，每个参数一条，线就是服务器自己的 `pending_restart` 标志。现在业务没受影响：实例还在跑旧值。但下一次重启（包括故障切换后的重启）会突然换成新值。
- `pending restart` 里显示的是运行值；文件里等着的值这里显示 `-`。`verify` 给了一条查询（`sys_file_settings`，需要超级用户）。
- `fix` 是把运行值写回去：`ALTER SYSTEM SET x = '<运行值>'`，再 `SELECT sys_reload_conf()`。PostgreSQL 12 的 reload 只在文件里的值等于运行值时才清掉 pending 标志，只做 `ALTER SYSTEM RESET` 会一直挂到下次重启。如果这个改动是有意的，就该去安排重启。
- `max_files_per_process` 在 `changed` 里来源是 `default`：等着重启的参数不管来源都会列出，因为改了之后它的来源仍然读成 `default`。
- 配置文件有错（`sys_file_settings.error`）这一项没做：`kbdiag_ro` 读不了那个视图。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | OK |
| 1 | WARN：有参数改了要重启才生效 |
| 3 | UNKNOWN：有数据没采到或看不到 |
| 64 | 参数错误 |
| 69 | 连不上数据库 |

[回到使用手册]({{< relref "/docs/reference" >}})
