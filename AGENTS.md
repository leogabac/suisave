# AGENTS.md

## Repository Overview

`suisave` is a Linux-only Python CLI that wraps `rsync` behind declarative TOML
configuration.

The repository currently supports two operational modes:

- local-drive backups to mounted external drives identified by filesystem UUID
- remote synchronization over SSH using a project-local config file

The project is small, but the local and remote flows are intentionally separate.
Agents should treat them as related features with different data models and
execution paths.

## Supported Runtime Model

### Local-drive mode

Local-drive backups use the user config at:

- `~/.config/suisave/comet.toml`

Example template:

- `templates/comet.toml`

Key assumptions:

- configured drives live under `[drives.<label>]`
- each drive is identified by UUID
- a drive is usable only when its UUID resolves to a mounted path
- jobs reference drives by label
- backup targets are created under the mounted drive

### Remote-sync mode

Remote sync uses an explicit config passed to:

- `suisave remote sync --config ...`

Example template:

- `templates/suisave.remote.toml`

Key assumptions:

- remote configs use `[connection]`, not `[drives]`
- remote jobs live under `[[jobs.sync]]`
- transport is SSH only
- sync direction is explicit: `push`, `pull`, or `most_recent`
- `most_recent` is an mtime heuristic, not merge or conflict resolution logic

## Repository Layout

- `src/suisave/cli.py`: top-level CLI parser and command wiring
- `src/suisave/cmds/run.py`: local-drive execution flow and run UI selection
- `src/suisave/cmds/config.py`: local config inspection and drive management
- `src/suisave/cmds/remote.py`: remote sync execution and direction handling
- `src/suisave/core.py`: shared paths, helpers, subprocess execution, errors
- `src/suisave/struct/comet.py`: local config parsing and job materialization
- `src/suisave/struct/context.py`: local config data structures
- `src/suisave/struct/remote.py`: remote config parsing and dataclasses
- `src/suisave/struct/stats.py`: directory statistics used for summaries
- `src/suisave/struct/logger.py`: Rich logger setup
- `src/suisave/ui/textual_run.py`: Textual run dashboard for transfers
- `src/suisave/ui/rich_run.py`: non-Textual terminal run presentation
- `README.md`: user-facing overview
- `CHANGELOG.md`: release history

## Current CLI Surface

Primary commands:

- `suisave run`
- `suisave run --name ...`
- `suisave run --no-interactive`
- `suisave config path`
- `suisave config init`
- `suisave config show`
- `suisave config drive add LABEL UUID`
- `suisave config drive rm LABEL`
- `suisave config drive ls`
- `suisave config drive detect`
- `suisave config drive select`
- `suisave remote sync --config ...`

Important status note:

- the local config editor TUI was removed in `0.3.2`
- the transfer TUI for `suisave run` remains supported

## Execution Notes

### Local-drive flow

Primary path:

1. `suisave.cli.main()`
2. `cmd.run_jobs()`
3. `Comet(CONFIG_PATH).load()`
4. local config parsing and validation
5. `run_single()` for each selected job
6. target path construction
7. `run_rsync()`

Important details:

- `CONFIG_PATH` is defined in `src/suisave/core.py`
- local config loading validates sources before execution
- target directories are created before `rsync` runs
- local progress monitoring scans the target tree repeatedly while syncing
- if no required drives are mounted, the run fails early

### Remote-sync flow

Primary path:

1. `suisave.cli.main()`
2. `cmd.remote_sync()`
3. `RemoteConfigLoader(...).load()`
4. direction resolution
5. remote/local target mapping
6. `run_rsync()`

Important details:

- remote sync never uses `CONFIG_PATH`
- `--config` is required
- relative sources are resolved from the current working directory
- `identity_file` is resolved relative to the remote config file
- pull mode creates local parent directories before syncing
- remote sync does not use the local transfer progress scanner

## Config Semantics

### Local config

Job groups:

- `[[jobs.backup]]`
- `[[jobs.custom]]`

Shared required fields:

- `name`
- `sources`
- `drives`

Default behavior:

- backup jobs derive target base from global defaults
- custom jobs may override target base and flags
- parser defaults are synthesized when global config is omitted

Current defaults:

- `pc_name`: `<hostname>-<machine-id-prefix>`
- `default_target_base`: `backups`
- `default_rsync_flags`: `["-avh", "--delete"]`

### Remote config

Sections:

- optional `[global]`
- required `[connection]`
- one or more `[[jobs.sync]]`, unless ad hoc `--source` is used

Common remote job fields:

- `name`
- `sources`
- optional `target_base`
- optional `flags`
- optional `default_mode`
- optional `delete`

Current remote defaults:

- `default_rsync_flags`: `["-azvh"]`
- `default_remote_base`: `.`

Allowed remote modes:

- `push`
- `pull`
- `most_recent`

## Implementation Constraints

- Local-drive and remote-sync code should not be casually collapsed into one
  abstraction. The split is deliberate.
- Local source mapping assumes sources can be mirrored relative to `$HOME`.
  Sources outside the home directory require careful review of target mapping.
- Remote source mapping uses a different rule: relative to `Path.cwd()` when
  possible, otherwise basename-only.
- `most_recent` is intentionally conservative and should not be represented as a
  bidirectional sync feature.
- The progress scanner can be expensive on large directory trees.
- `DirStats` behavior in `src/suisave/struct/stats.py` should be reviewed before
  relying on exact byte totals for new features.

## Dependencies and Environment

Python/runtime expectations:

- Python 3.11+
- Linux
- `rsync`
- `lsblk`
- local SSH client for remote sync

Python dependencies of note:

- `rich`
- `tomlkit`
- `questionary`
- `psutil`
- `desktop-notifier`

Optional UI dependency:

- `textual` for the transfer TUI

Remote `most_recent` expectations:

- remote host must provide standard shell tools such as `sh`, `find`, `sort`,
  `head`, and `stat`

## Agent Behavior

Agents modifying this repository should follow these rules:

- Start from the current CLI surface, not from older branches or removed
  features.
- Preserve the distinction between local-drive backups and remote sync unless
  the change explicitly requires a model redesign.
- Keep `README.md`, `CHANGELOG.md`, and config templates aligned with any schema
  or CLI changes.
- Do not reintroduce the removed local config editor TUI unless explicitly
  requested.
- Preserve the run/transfer TUI unless the requested change clearly targets it.
- Prefer small, traceable changes; this repository has no automated test suite.
- Validate behavior with targeted commands such as `python -m compileall src`
  and relevant CLI invocations when possible.
- Be cautious with `CONFIG_PATH` changes because multiple modules rely on it
  directly.

## Known Gaps

- No automated test suite
- Remote sync supports SSH only
- `most_recent` is heuristic only
- Progress scanning is simple and potentially expensive
- Some code paths remain alpha-quality and rely on manual validation
