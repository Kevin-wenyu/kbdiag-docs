# Documentation checks

Run with Python 3.10+ and the Hugo Extended version pinned in the workflow:

```sh
hugo --cleanDestinationDir --gc --minify --environment production --printPathWarnings --panicOnWarning
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check-site.py
```

The build rejects Hugo warnings. The Python check validates local href/src targets, fragment IDs, Pages base-path containment, required bilingual pages, evidence markers, referenced offline search records, and the downloadable report's summary counts. External websites are not crawled. It does not prove the correctness of database conclusions or automatically detect every secret; manually review samples before publication.

PRs build and validate without deployment credentials. Main pushes deploy only after validation. Keep CORE in scripts/check-site.py aligned with intentional page/sample changes. Do not remove checks merely to bypass a failure.
