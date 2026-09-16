---
title: "Inspection report example"
description: "Download a redacted report and interpret its findings."
weight: 20
---

## Generate a report

```bash
~/kbdiag report ./inspection.md --no-color
rc=$?
printf 'EXIT_CODE=%s\n' "$rc"
```

The command writes Markdown. Inspect the generated file even when the exit status is 1 or 2; a nonzero status does not necessarily mean generation failed. Sections are collected sequentially, not as an atomic snapshot. This file is not a database backup.

## Download a real sample

[Download the redacted Markdown report]({{< sample-report >}})

Captured in the lab at 08:38 UTC+08 on 2026-09-16, before archive repair, using tool `v1.0.0-115 (2026-08-10)` from source `3bea0be`. Host, addresses, paths, business object names and license/customer fields were replaced; findings and counters remain. kbdiag does not guarantee redaction: review reports before sharing.

The command returned **2**, with this summary:

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


## Reading order

1. Start with Overall, derived from underlying output markers. The single FAIL here is archiving.
2. Read the corresponding sections. One issue can appear in health, failover readiness and backup checks; 16 WARN lines do not mean 16 independent incidents.
3. Recheck individual commands, such as `~/kbdiag backup`. Archive failure counts differ slightly because they continued increasing during sequential collection.
4. Decide on action only after verification. Index bloat is estimated and memory settings are heuristics. In particular, verify version support before acting on freeze suggestions for system objects; do not execute maintenance SQL directly from this report.

## Handover checklist

Include collection time, versions, target role, full command, exit status, redaction notes, action owners and verification results. OK covers the checks that ran; errors without recognized output markers cannot establish a clean environment.

## Follow-up repair

On 2026-09-16, the repository SSH host key was independently verified and updated, and the backup check connection port/user were corrected. `sys_rman check` confirmed newly archived WAL. Both pending queues were zero; the primary had archived 35 WAL segments while historical failures remained 1422. Statistics were not reset. The sample above preserves the pre-repair state; this was not a full restore drill.
