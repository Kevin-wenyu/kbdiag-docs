---
title: "params: changed parameters"
description: "Which parameters are not at their default and where they are set; flags changes waiting for a restart."
weight: 120
---

Captured on 2026-10-07 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `96c874f` (static linux/amd64 binary). This is lab evidence, not production validation. The WARN example was created by an injection script: it changed `max_files_per_process` (a parameter that needs a restart) with `ALTER SYSTEM`, reloaded the configuration, and did not restart, so the running value differs from the file. Values belong to this capture only.

## Usage

```text
kbdiag params [--json]
```

No options of its own, and no pattern argument: to see one parameter use `ksql -c 'show x'`, or `--json` with jq. Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}).

## Healthy primary

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

- `pending restart` lists the parameters whose file value differs from what is running (the server's own `pending_restart` flag). None here.
- `changed` lists only what someone set: sources other than `default`, `override` (fixed at compile or initdb time) and this connection's own `client`/`session` (those are kbdiag's own settings and would be noise). `file` is the file and line that set it.
- The line under `changed` names the two limits of what can be seen. kbdiag sets `application_name`, `default_transaction_read_only`, `lock_timeout` and `statement_timeout` itself on its connection, so their configured values are not shown. Per-role and per-database settings show only for this role and database.
- Long values such as `archive_command` are cut with `...`; `--json` has them in full.
- The standby shows a similar list, with `primary_conninfo`, `primary_slot_name` and `synchronous_standby_names` differing (captured on kes-node2; 63 parameters changed there too).

## Without privileges

`kbdiag_ro` (no monitoring role, over `127.0.0.1`):

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

- `file` is `?`: this account cannot see `sourcefile` and `sourceline`. They are recorded under `redacted`.
- The list is shorter (59 instead of 63) because superuser-only parameters are not visible to this account at all, and the text says so on its last line. Their `pending_restart` flag is invisible too, so with no finding the verdict is UNKNOWN: kbdiag will not say OK about something it cannot see.

## A change waiting for a restart

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

- `params.pending_restart` is a WARN, one per parameter. The line is the server's own `pending_restart` flag. The business is not affected now: the instance still runs the old value. But the next restart, including one after a failover, will suddenly switch to the new value.
- `pending restart` shows the running value; the value waiting in the file is shown as `-` here. The `verify` line gives a query for it (`sys_file_settings`; it needs a superuser).
- The `fix` line writes the running value back with `ALTER SYSTEM SET x = '<running value>'` and then `SELECT sys_reload_conf()`. In PostgreSQL 12 a reload clears the pending flag only when the file's value equals the running value, so `ALTER SYSTEM RESET` alone would leave the flag until the next restart. If the change was meant, plan the restart instead.
- `max_files_per_process` is listed in `changed` with source `default`: a parameter that waits for a restart is listed whatever its source, because after the change its source still reads `default`.
- Config file errors (`sys_file_settings.error`) are not checked: `kbdiag_ro` cannot read that view.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: a parameter change waits for a restart |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
