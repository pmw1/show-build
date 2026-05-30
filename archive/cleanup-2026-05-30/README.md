# Root cleanup archive — 2026-05-30

This folder holds files that were cluttering the **repo root** and were archived
(not deleted) on 2026-05-30 to make the project lean. Nothing here is wired into
the running stack — `docker-compose.yml` and `Dockerfile` reference only files
under `app/` and `disaffected-ui/`, none of which were touched.

The repo root went from **134 loose files → 10** (plus dotfiles). Load-bearing
files kept in root: `CLAUDE.md`, `README.md`, `docker-compose.yml`, `Dockerfile`,
`requirements.txt`, `package.json`, `package-lock.json`, `pytest.ini`,
`ACTIVE_WORK_QUEUE.md`, `secret.key`, and dotfiles (`.env*`, `.gitignore`,
`.mcp.json`, `.gather*`).

## Buckets

| Folder | What | Count |
|---|---|---|
| `docs/` | One-off design/status/analysis markdown — the `*_UFDP.md` set, fix reports, `ARCHITECTURAL_ANALYSIS.md`, `DEBUG_FIRST.md`, etc. Historical; superseded by `docs/`. | 21 |
| `scripts/` | One-off Python/shell/bat/ps1 scripts — auth fixers (`fix_bcrypt_hashes.py`, `reset_users.py`…), `import_episode_0241.py`, `populate_blueprints.py`, the dead `minimal_*`/`enhanced_*` experiment set, Windows worker `.bat`s, setup scripts. | 54 |
| `logs/` | Stray `.log` files and the `192.168.51.210-*` capture logs. Regenerable junk. | 9 |
| `images/` | `icon.png` (18.5 MB, 3328×4096 source art, unreferenced), `show-builder.png`, `download.jpg`. | 3 |
| `migration/` | `MIGRATION_*.txt`, `table_counts_source.txt` — artifacts from the 2026-03 prefect migration. | 4 |
| `test-fixtures/` | TTS `.wav` test outputs and standalone `test-*.html` drag/resize demo pages. | 9 |
| `misc/` | Alt docker-composes (`docker-compose.enhanced.yml`, `*postgres-primary/replica*`, `minimal_docker-compose.yml`), `Dockerfile.enhanced`, scratch dumps (`response.txt`, `review_files.txt`, `talkwithclaude.txt`, `tree_output.txt`, `REHYDRATE.NOW`), data dumps (`*_newsweek_quote.json`, `quotes_input.json`, `update_blueprint.sql`, `workload.json`), and leftover junk (`FETCH_HEAD`, `checkpoint3acce64.bundle`, `sh comms`, `show-build.code-workspace`). | 24 |

## How files were moved

- Git-**tracked** files were moved with `git mv` (history preserved).
- **Untracked/ignored** files were moved with plain `mv`.

## Restoring a file

```bash
# from repo root
git mv archive/cleanup-2026-05-30/<bucket>/<file> ./        # for tracked files
mv     archive/cleanup-2026-05-30/<bucket>/<file> ./        # for untracked files
```

## Safe to delete later?

Yes — once you've confirmed nothing here is needed, the whole
`archive/cleanup-2026-05-30/` folder can be removed. The 18.5 MB `icon.png`
is the only meaningful disk reclaim; everything else is small.
