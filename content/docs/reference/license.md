---
title: "license: the KES license"
description: "Days the license has left and what the license file says; WARN within 30 days of expiry, FAIL once expired."
weight: 220
---

Captured on 2026-10-23 (UTC+08) on a local KingbaseES V008R006C009B0014 primary and standby, database `test`, using `~/kbdiag` built from Go source commit `5efa1fc` (static linux/amd64 binary). This is lab evidence, not production validation. No fault was injected. Both lab nodes have a permanent license, so the captures below are all OK; the WARN and FAIL examples are taken from the unit-test fixtures, not captured (see below). Values belong to this capture only.

## Usage

```text
kbdiag license [--json]
```

| Option | Effect |
|---|---|
| `--json` | Print JSON |

Connection options are the same as for [`sessions`]({{< relref "/docs/reference/sessions" >}}). There is no threshold option: the 30-day line is the server's own.

## Why this command

KES checks the license only when the instance starts. An expired license does not stop a running instance: queries go on as usual, and the problem shows only at the next restart, which fails with `license file expired`. A planned maintenance restart or a failover is the worst moment to find out. `license` reads the days left with `get_license_validdays()` so that a routine check catches it before then.

## Primary

```bash
~/kbdiag license
echo EXIT_CODE=$?
```

```text
license  OK  (KingbaseES V008R006C009B0014, primary, system@local, 2026-10-23T13:57:00+08:00)

license
  left             permanent
  file             /home/kingbase/cluster/install/kingbase/bin/../../license.dat
  product          KingbaseES V8
  edition          SALES-企业版 V8R6
  version          V008R006C
  produced on      2021-10-13
  validity         0
  floating base    off (counts from the production date)
  mac              00:00:00:00:00:00
  max connections  0
  KES checks the license only when the instance starts
EXIT_CODE=0
```

- `left` comes from `get_license_validdays()`: `-2` is a permanent license (`permanent`), any other negative number means expired, otherwise it is the days left.
- The other lines come from `get_license_info()`: `file` is the license file the instance loaded, then the product, edition template, version, production date, validity period, whether the period counts from the production date or from the day the license was loaded (`floating base`), the bound MAC address and the connection limit. A field the license marks as disabled is shown as `-`.
- `validity 0`, an all-zero MAC and `max connections 0` are shown as KES reports them. What `0` means there is not documented; this permanent license has all three.
- The user name, project name and serial number in the license are not shown: diagnosis does not need them, and they are the customer's information. The file path is shown, because you need to know which `license.dat` the instance reads; it can contain a customer's directory name, so keep that in mind when you paste the output elsewhere.

## Standby

```bash
~/kbdiag license
echo EXIT_CODE=$?
```

```text
license  OK  (KingbaseES V008R006C009B0014, standby, system@local, 2026-10-23T13:57:29+08:00)

license
  left             permanent
  file             /home/kingbase/cluster/install/kingbase/bin/../../license.dat
  product          KingbaseES V8
  edition          SALES-企业版 V8R6
  version          V008R006C
  produced on      2021-10-13
  validity         0
  floating base    off (counts from the production date)
  mac              00:00:00:00:00:00
  max connections  0
  KES checks the license only when the instance starts
EXIT_CODE=0
```

The standby is judged the same way. Each node has its own `license.dat`, and a standby that is promoted needs its own valid license to start again, so run `license` on every node.

## Without privileges

`kbdiag_ro` (no monitoring role, over `127.0.0.1`):

```bash
PGPASSWORD=... ~/kbdiag --host 127.0.0.1 -U kbdiag_ro license
echo EXIT_CODE=$?
```

The output was identical to the primary's above, apart from `kbdiag_ro@remote` in the first line, and the exit code was 0; the same on the standby. Both functions are executable by PUBLIC, so no role is needed.

## JSON

```bash
~/kbdiag --json license
```

```json
{
  "command": "license",
  "verdict": "OK",
  "context": {
    "version": "KingbaseES V008R006C009B0014",
    "role": "primary",
    "location": "local",
    "user": "system",
    "database": "test",
    "collected_at": "2026-10-23T13:57:30+08:00"
  },
  "data": {
    "license.info": {
      "status": "ok",
      "reason": null,
      "columns": [
        "valid_days",
        "file",
        "product",
        "edition",
        "product_version",
        "produced_on",
        "validity_period",
        "floating_base",
        "mac",
        "max_connections"
      ],
      "rows": [
        [
          -2,
          "/home/kingbase/cluster/install/kingbase/bin/../../license.dat",
          "KingbaseES V8",
          "SALES-企业版 V8R6",
          "V008R006C",
          "2021-10-13",
          "0",
          false,
          "00:00:00:00:00:00",
          "0"
        ]
      ],
      "truncated": 0
    }
  },
  "findings": [],
  "redacted": []
}
```

`valid_days` keeps the raw number (`-2` here). For a scheduled check, the exit code alone is enough: 1 means renew soon, 2 means renew before the next restart.

## Expiring and expired

Taken from the unit-test fixtures (`license_expiring` and `license_expired`), not captured: both lab nodes have a permanent license, and a license that is about to expire has to come from the vendor. The rule itself is one integer comparison, covered by unit tests at the edges (`-2`, `-1`, `0`, `1`, `30`, `31`, extreme values, NULL).

```text
license  WARN  (KingbaseES V008R006C009B0014, primary, system@local, 2026-09-27T21:20:09+08:00)

[WARN] license.expiring  the license expires in 12 days: the instance keeps running, but after that it will not start again
  fix: SELECT sys_reload_license('<new license.dat>')  # ask the vendor's sales for a new license now, then load it; or sys_ctl reload_license <file> (V8R6) / sys_ctl -D <data> reload_license -L <file> (V9); the KES FAQ says no restart is needed, not tried by kbdiag: check with the verify step
  verify: SELECT get_license_validdays()  # after the new license.dat is in place: -2 is permanent, else the days left

license
  left             12 days
  ...
```

```text
license  FAIL  (KingbaseES V008R006C009B0014, standby, system@local, 2026-09-27T21:20:09+08:00)

[FAIL] license.expired  the license has expired: the instance keeps running, but it will not start again after a restart
  fix: SELECT sys_reload_license('<new license.dat>')  # do not restart this instance before the new license is loaded; the license itself comes from the vendor's sales; or sys_ctl reload_license <file> (V8R6) / sys_ctl -D <data> reload_license -L <file> (V9); the KES FAQ says no restart is needed, not tried by kbdiag: check with the verify step
  verify: SELECT get_license_validdays()  # after the new license.dat is in place: -2 is permanent, else the days left

license
  left             expired (-1)
  ...
```

- `license.expiring` (WARN): 0 to 30 days left. The line is the server's own: 30 days before expiry, KES warns at login with `License file will expire in 30 days`.
- `license.expired` (FAIL): any negative number other than `-2`. The KES community documents `-1` as expired; other negative numbers have been reported too, and kbdiag treats an unknown negative number as expired rather than calling it OK. The instance is still running, but it is certain to fail at the next start, so this is a FAIL.
- If `get_license_validdays()` returns NULL, `left` says so and the verdict is UNKNOWN.
- The fix loads a new license with `sys_reload_license()`, which exists on both V8R6 and V9. The `sys_ctl` form differs between versions (V8R6C9's `--help` shows `sys_ctl reload_license LICENSE_FILE`; the V9 FAQ shows `sys_ctl -D … reload_license -L …`), so both are in the note. The KES FAQ says no restart is needed; this has not been tried in the lab, so check with the `verify` query afterwards. kbdiag itself never loads a license: it is read-only, and the license comes from the vendor, not from the database.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | WARN: the license expires within 30 days |
| 2 | FAIL: the license has expired; the instance will not start again |
| 3 | UNKNOWN: data not collected or not visible |
| 64 | Usage error |
| 69 | Cannot connect |

[Back to the manual]({{< relref "/docs/reference" >}})
