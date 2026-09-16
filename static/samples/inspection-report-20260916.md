> Redacted lab capture, 2026-09-16 UTC+08, BEFORE archive repair. Host, addresses, paths, business object names and license/customer fields were replaced. Findings, severity and counters are preserved. Not a production report or a restore test.

# KingbaseES Inspection Report — lab-primary

| | |
|---|---|
| Host | lab-primary (primary) |
| Database | KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu |
| Generated | 2026-09-16 08:38:30 |
| Tool | kbdiag v1.0.0-115 (2026-08-10) |

## Executive summary

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

## Instance status

```text

==> Instance status
[OK]    kingbase process running (pid 1895)
[OK]    DB connectable — KingbaseES V008R006C009B0014 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 4.8.5 20150623 (Red Hat 4.8.5-28), 64-bit
[OK]    Role: PRIMARY
[INFO]  Uptime: +000000000 00:01:57.000000000
[OK]    License: 永久授权（正式）
```

## License

```text

==> License
[OK]    授权状态: 永久授权（正式）
[INFO]  序列号: [REDACTED]
[INFO]  产品名称: KingbaseESV8
[INFO]  版本模板: [REDACTED]
[INFO]  用户名称: [REDACTED]
[INFO]  项目名称: [REDACTED]
[INFO]  生产日期: [REDACTED]
```

## Health check

```text

==> Health check
[OK]    Connections: 12% (12/100)
[OK]    Long transactions: none
[OK]    Waiting locks: none
[WARN]  Archiver: 1419 failed file(s)
[OK]    Autovacuum backlog: none
[OK]    Buffer hit rate: 99.4%
[OK]    Checkpoint pressure: 0 requested checkpoints
[OK]    Temp file usage: 0 bytes
[OK]    Deadlocks: none
[OK]    Replication slot lag: 0bytes
[OK]    BGWriter pressure: 19% backend writes
[OK]    XID age: 4732
[OK]    oldest active transaction: 0s
[WARN]  WAL archiving: failing (1419 failures, last: 2026-09-16 08:37:38.581359+08) — run: kbdiag backup

==> OS check
[OK]    THP: never
[OK]    Swappiness: 10
[OK]    Swap usage: no swap configured
[OK]    Overcommit: vm.overcommit_memory=2
[OK]    Open files limit: 655360
[OK]    Max processes limit: 655360
[OK]    Clock sync: NTP synchronized
[OK]    Data dir filesystem: xfs (rw,relatime,attr2,inode64,logbufs=8,logbsize=32k,noquota)
[INFO]  CPU governor: no cpufreq (typical for VMs) — SKIP
```

## Failover readiness

```text

==> Failover readiness (repmgr)
[OK]    Topology: 1 primary + 1 standby (all active)
[OK]    Promotion: 1 of 1 standby(s) eligible (priority>0)
[OK]    Arbitration: trusted_servers=192.0.2.1
[OK]    repmgrd: running on all 2 node(s), none paused
[OK]    Failover mode: automatic, promote_command set
[OK]    Standby attach: 1 of 1 standby(s) streaming
[OK]    Slots: all replication slots active
[WARN]  Archive backlog: 32 WAL pending (>= 10)
[OK]    Standby node2: promotable (hot_standby=on, no delay, replay active)
[OK]    VIP: 192.0.2.12 correctly bound (local role: primary)
[INFO]  Sync mode: quorum; failover/disconnect events last 7d: 0
[INFO]  Cross-check: repmgr node check / kbdiag replication / kbdiag conf diff
```

## Replication

```text

==> Replication
[INFO]  Standby connections:
[OK]    1 standby(s) connected
```

## Capacity

```text

==> Storage & space
[OK]    Disk usage: 15G/199G used (8%)
[INFO]  WAL directory: 2.6G  (/opt/kingbase/data/sys_wal)
[INFO]  Database sizes:
datname   size
test      325 MB
esrep     15 MB
kingbase  14 MB
sample_db      14 MB
security  14 MB
[INFO]  Top 10 largest tables (total incl. indexes):
schemaname  relname                       total_size  table_size  index_size
public      sample_table_a                        114 MB      62 MB       52 MB
public      sample_table_b           107 MB      64 MB       43 MB
public      sample_table_c                   71 MB       43 MB       28 MB
public      sample_table_d                   8968 kB     6728 kB     2216 kB
perf        kwr_snap_settings             128 kB      56 kB       40 kB
perf        kwr_snap_shmem                96 kB       24 kB       40 kB
sysmac      sysmac_policy                 72 kB       8192 bytes  32 kB
sysmac      sysmac_level                  72 kB       8192 bytes  32 kB
perf        kwr_last_stat_statements_all  64 kB       32 kB       0 bytes
sys_hm      check_type                    56 kB       8192 bytes  16 kB
```

## Backup & archiving

```text

==> Backup & Archiving
[OK]    archive_mode=always
[OK]    wal_level=replica
[INFO]  archive_command: export TZ=Asia/Shanghai;/opt/kingbase/bin/sys_rman --config /archive-repo/sys_rman.conf --stanza=kingbase archive-push %p
[FAIL]  Archiver is FAILING — 1422 failure(s), last: 000000030000000000000080 at 2026-09-16 08:38:39.287573+08 (last success: never)
[INFO]  Verify: run the archive_command by hand as the kingbase user; check config/permissions/disk on the archive target
[WARN]  32 WAL segment(s) pending archive (.ready) — archiver is falling behind
[INFO]  sys_rman (KingbaseES backup tool):
[OK]    sys_rman binary found
[OK]    sys_rman config readable: /archive-repo/sys_rman.conf
[OK]    No inactive replication slots
```

## Throughput

```text

==> Instance throughput (5s sample)
[INFO]  Throughput: 1.6 commits/s, 0.0 rollbacks/s (5s sample)
[INFO]  Temp files: 0.00/s, 0 bytes/s during sample
[OK]    Buffer hit rate: 100.0% (threshold 90%)
[OK]    Rollback ratio: 0.0% (threshold 10%)
[OK]    Deadlocks: 0 during sample

[INFO]  Checkpoint activity (cumulative):
  timed/requested: 95 / 0   write 6.9s   sync 0.0s   buffers 70
```

## Index health

```text

==> Unused indexes (idx_scan=0, table rows > 1000)
[OK]    No unused non-unique indexes found

==> Duplicate indexes (same leading column set)
[WARN]  1 duplicate index pair(s)
schemaname  tablename       index1          index2                   size1
perf        kwr_table_list  uk_toast_table  ix_tables_list_reltoast  8192 bytes

==> Bloated indexes (estimated bloat > 30%)
[WARN]  6 bloated index(es) — consider REINDEX CONCURRENTLY
schemaname  tablename            indexrelname                     index_size  relpages  reltuples  est_bloat_pct
public      sample_table_a               idx_sample_table_a_user_status           30 MB       3871      1000000    74.8
public      sample_table_c          sample_table_c_pkey                 28 MB       3557      645750     82.3
public      sample_table_b  sample_table_b_pkey         22 MB       2760      1000000    64.6
public      sample_table_b  sample_b_time_idx  22 MB       2760      1000000    64.6
public      sample_table_a               sample_table_a_pkey                      22 MB       2760      1000000    64.6
public      sample_table_d          sample_table_d_pkey                 2216 kB     277       100000     64.7

==> Missing FK indexes (large tables with unindexed FK leading column)
[OK]    No missing FK indexes found
```

## Security audit

```text

==> Security Audit
[OK]    Superuser roles: 1 found
rolname
system

[OK]    All login roles have passwords set
[WARN]  5 login role(s) have no password expiry (VALID UNTIL) set
rolname
esrep
lab_user
sao
sso
system
[OK]    No PUBLIC write grants on public schema tables
[WARN]  91 user table(s) without primary keys
schemaname    relname
kdb_schedule  kdb_action
kdb_schedule  kdb_exception
kdb_schedule  kdb_job_action
kdb_schedule  kdb_jobagent
kdb_schedule  kdb_jobclass
kdb_schedule  kdb_joblog
kdb_schedule  kdb_jobsteplog
kdb_schedule  kdb_schedule
kdb_schedule  kdb_schedule_job
perf          ksh_history_data
[INFO]  ... 81 more, use -v to show all
[WARN]  sys_hba.conf: 5 of 10 rule(s) need review
line  type   database     users  source           auth           risk
55    local  all          all    local            trust          any local OS user connects unauthenticated
61    host   all          all    ::/::            scram-sha-256  open to any host
68    host   all          all    0.0.0.0/0.0.0.0  scram-sha-256  open to any host
69    host   replication  all    0.0.0.0/0.0.0.0  scram-sha-256  replication open to any host
70    host   replication  all    ::/::            scram-sha-256  replication open to any host
[WARN]  SSL is disabled — client connections are unencrypted
[WARN]  Three-power separation (sepapower) is disabled — the DBA role has unrestricted control over audit/security config
[OK]    Audit rule/log details are restricted to the sso/sao role (three-power separation enforced) — inspect via: ksql -U sso -c 'SELECT * FROM sysaudit.all_audit_rules;'
[OK]    sysmac installed, no MAC policies defined (not in use)
[OK]    Masking policy details are restricted (no schema access for the DBA role) — inspect via the sso/sao role, or GRANT USAGE ON SCHEMA anon
```

## Recommendations

```text

==> Advisor: Index
[OK]    No unused non-unique indexes found
[WARN]  1 duplicate index pair(s) — run 'kbdiag idx dup' for detail
[OK]    No missing FK indexes on large tables

==> Advisor: Vacuum
[OK]    No tables with >20% dead tuples
[WARN]  sys_catalog._kingbase_loginfo: xid_age=2147483647 — freeze risk, run VACUUM FREEZE

==> Advisor: Params
[WARN]  shared_buffers=512MB — recommend 1986MB (25% of 7946MB RAM)
[WARN]  checkpoint_completion_target=0.5 — recommend 0.9
[WARN]  work_mem=4MB — recommend ~19MB (RAM/100conn/4)

==> Advisor: Analyze
[OK]    No tables with stale statistics (all analyzed within 7 days, drift < 10%)
```

---
Thresholds are tunable via KB_WARN_*/KB_FAIL_* environment variables.
Cross-check any finding with the matching kbdiag command (see `kbdiag --help`).
