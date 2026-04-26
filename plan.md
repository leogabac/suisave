# Remote Sync Feature Plan

## Goal

Add a new remote-sync feature that lets `suisave` sync one or more local directories to remote directories with `rsync`, using a config file that lives in the current project directory instead of the global `~/.config/suisave/comet.toml`.

This should be a separate path from the current mounted-drive backup flow, not a small conditional added on top of `[drives]`.

## Recommendation

Treat this as a new command family with its own config schema:

```bash
suisave remote sync --config ./suisave.remote.toml
```

Optional selectors can be added on top:

```bash
suisave remote sync --config ./suisave.remote.toml --name docs
suisave remote sync --config ./suisave.remote.toml --source "$PWD"
```

I recommend `--config` be required for remote sync. That keeps private remote definitions out of the global config and makes the execution context explicit.

## Why This Should Be Separate

The current code assumes all targets are local mounted drives:

- `Comet.load()` requires `[drives]`
- `Drive` only models `uuid` and `mountpoint`
- `get_st_pairs()` builds targets from `drive.mountpoint`
- job validation depends on mounted-drive resolution

Trying to fit remote targets into `[drives.<label>]` would blur two different models:

- local block devices identified by UUID
- remote endpoints identified by SSH connection details

That would make parsing, validation, and execution harder to reason about.

## Proposed CLI

### New command tree

```bash
suisave remote sync --config <path> [--name <job> ...] [--source <path> ...]
```

### Suggested semantics

- `remote`: top-level command namespace for non-mounted-drive operations
- `sync`: execute one or more remote jobs from a local config file
- `--config`: path to a TOML file, relative or absolute
- `--name`: run only specific jobs from the remote config
- `--source`: optional ad hoc source override for quick one-off syncs

### Scope recommendation

For the first implementation, keep the command surface small:

- implement only `suisave remote sync`
- do not add remote config editing commands yet
- do not merge remote jobs into `suisave run`

That keeps the feature understandable and avoids mixing two incompatible config models in one runtime path.

## Proposed Config Shape

The config should look familiar to `comet.toml`, but not reuse `[drives]`.

Recommended file name:

- `suisave.remote.toml`

### Example

```toml
[global]
default_rsync_flags = ["-azvh", "--delete"]
default_transport = "ssh"
default_remote_base = "backups"

[connection]
host = "storage.example.com"
user = "backup"
port = 22
identity_file = "./.secrets/suisave_ed25519"
ssh_options = [
  "StrictHostKeyChecking=accept-new",
]

[[jobs.sync]]
name = "project"
sources = ["./"]
target_base = "projects/my-project"

[[jobs.sync]]
name = "notes"
sources = [
  "./notes",
  "./docs",
]
target_base = "projects/my-project"
flags = ["-azvh"]
```

## Config Design Notes

### Similarities to `comet.toml`

- keep a `[global]` table
- keep `[[jobs.*]]` arrays of tables
- keep `name`, `sources`, and optional per-job `flags`
- keep `target_base` semantics

This makes it easy for current users to understand.

### Intentional differences

- replace `[drives]` with a single `[connection]` table
- use `[[jobs.sync]]` instead of `[[jobs.backup]]` or `[[jobs.custom]]`
- require `--config` instead of relying on `CONFIG_PATH`

This avoids pretending remote sync is just another drive.

## Credentials Guidance

The config is where connection details should live, but I do not recommend supporting plain-text passwords in TOML for the first version.

Preferred authentication:

- SSH key via `identity_file`
- SSH agent if `identity_file` is omitted

Avoid in v1:

- password fields in TOML
- prompting for passwords
- embedding `sshpass`

That keeps the implementation smaller and avoids handling secrets poorly.

## Suggested Execution Model

Use `rsync` over SSH rather than introducing a second transfer engine.

### Command shape

For each source/target pair, build something conceptually like:

```bash
rsync -azvh --delete -e "ssh -p 22 -i ./key -o StrictHostKeyChecking=accept-new" \
  ./source/ backup@host:backups/projects/my-project/source-relative-path/
```

### Target mapping recommendation

For parity with the current local behavior, mirror each source under:

```text
<target_base>/<source relative to anchor>
```

For remote sync, the safest anchor is not necessarily `$HOME`. I recommend:

- if source is under current working directory, make it relative to current working directory
- otherwise require an explicit behavior, such as storing only the source basename

Recommended first-version rule:

- anchor relative paths to `Path.cwd()`
- allow absolute paths, but map them by basename only

Examples:

- `./docs` -> `projects/my-project/docs`
- `/home/user/file.txt` -> `projects/my-project/file.txt`

This avoids the current local-only `$HOME` assumption from `get_st_pairs()`.

## Implementation Plan

### Phase 1: Introduce a parallel remote model

Add new remote-specific structures instead of stretching `Drive` and `AbstractJob`.

Suggested additions:

- `RemoteConfig`
- `RemoteConnection`
- `RemoteJob`
- `RemoteComet` or `RemoteConfigLoader`

Suggested file placement:

- `src/suisave/struct/remote.py`
- `src/suisave/cmds/remote.py`

Do not fold remote parsing into `struct/comet.py` initially. The current `Comet` parser is strongly coupled to `[drives]`.

### Phase 2: Add CLI wiring

Update `src/suisave/cli.py` to support:

- `suisave remote`
- `suisave remote sync`
- `--config`
- `--name`
- optional `--source`

Keep the existing `run` command untouched.

### Phase 3: Add remote config parsing and validation

Implement validation for:

- config file exists
- `[connection]` exists
- `host` exists
- each job has `name`
- each job has `sources`
- each source exists locally
- per-job flags fall back to `[global].default_rsync_flags`
- `target_base` falls back to `[global].default_remote_base` if omitted

Validation should fail early, before any `rsync` call.

### Phase 4: Add remote rsync command construction

Add a helper in `core.py` or a remote-specific module to build:

- SSH transport args
- remote destination strings
- final `rsync` command list

I recommend not reusing `run_rsync()` blindly if remote mode needs richer error messages later, but it can probably be reused in v1.

### Phase 5: Add remote execution path

Implement a remote equivalent of `run_single()` that:

- resolves source to remote-target pairs
- runs rsync for each pair
- logs source and destination clearly

I would skip live progress scanning in v1. The current progress monitor depends on reading the target filesystem locally, which is not practical for remote destinations.

Instead:

- show current source -> remote target
- print rsync output on failure
- maybe add `--info=progress2` later as an opt-in

### Phase 6: Docs and templates

Add:

- `templates/suisave.remote.toml`
- README section for remote sync
- usage examples for project-local configs

Keep the existing `templates/comet.toml` focused on local drives.

## Files Likely To Change

- `src/suisave/cli.py`
- `src/suisave/core.py`
- `README.md`

Likely new files:

- `src/suisave/cmds/remote.py`
- `src/suisave/struct/remote.py`
- `templates/suisave.remote.toml`

## Things I Would Explicitly Avoid In The First Pass

- mixing remote jobs into `comet.toml`
- adding remote targets under `[drives]`
- password auth in TOML
- remote config mutation commands
- progress calculation by scanning the remote target
- trying to support arbitrary transports beyond SSH

## Suggested Usage

### Project-local config

```bash
mkdir -p .secrets
chmod 700 .secrets
touch suisave.remote.toml
chmod 600 suisave.remote.toml
```

Example run:

```bash
suisave remote sync --config ./suisave.remote.toml
```

Run only one job:

```bash
suisave remote sync --config ./suisave.remote.toml --name project
```

One-off explicit source:

```bash
suisave remote sync --config ./suisave.remote.toml --source "$PWD"
```

## Source Of Truth And Direction

This needs to be explicit. `rsync` does not do true bidirectional reconciliation by itself; it applies one side onto the other side. So for remote sync, the command must declare which side is authoritative for that run.

### Recommended model

Treat every invocation as a directional operation with a declared sync mode.

Suggested flags:

```bash
suisave remote sync --config ./suisave.remote.toml --local
suisave remote sync --config ./suisave.remote.toml --remote
suisave remote sync --config ./suisave.remote.toml --most-recent
```

Meaning:

- `--local`: local source of truth, push local to remote
- `--remote`: remote source of truth, pull remote to local
- `--most-recent`: compare timestamps and choose a direction automatically

I would make exactly one of these required unless the job defines a default mode in config.

### Why this is necessary

The dangerous case is delete behavior:

- local -> remote with `--delete` removes remote-only files
- remote -> local with `--delete` removes local-only files

If the source-of-truth rule is implicit, the user can lose data by running the right command with the wrong mental model.

## Proposed Direction Semantics

### `--local`

Use when the working copy in the current machine should replace the remote copy.

Equivalent mental model:

- "send"
- "publish local state"
- "remote should match what I have here"

Implementation shape:

```bash
rsync ... LOCAL/ user@host:REMOTE/
```

Good for:

- project deployment to a personal box
- replacing stale remote contents
- pushing edits after local work

### `--remote`

Use when the remote copy should replace the local directory.

Equivalent mental model:

- "get"
- "restore from remote"
- "my machine should match the remote"

Implementation shape:

```bash
rsync ... user@host:REMOTE/ LOCAL/
```

Good for:

- pulling a newer copy from another machine
- restoring a project onto a fresh machine
- replacing local state with the remote version

### `--most-recent`

Use when you want `suisave` to choose between push and pull automatically.

My recommendation is to support this only with a conservative algorithm and clear limitations.

Suggested rule:

1. inspect the newest modification timestamp under the local source tree
2. inspect the newest modification timestamp under the remote target tree
3. if local is newer, behave like `--local`
4. if remote is newer, behave like `--remote`
5. if equal or inspection fails, abort unless `--force` is given

Important limitation:

- "most recent" is only a heuristic
- it does not detect divergent edits on both sides
- it can be wrong if mtimes are noisy, preserved differently, or skewed by clock drift

So `--most-recent` is fine as a convenience mode, but it should not be presented as conflict resolution.

## Better Naming Options

There are two reasonable UX styles.

### Option A: source-of-truth flags

```bash
--local
--remote
--most-recent
```

Pros:

- short
- easy to remember
- matches the way you described the workflow

Cons:

- `--local` and `--remote` describe authority, not transfer direction, so they need help text

### Option B: directional verbs

```bash
--push
--pull
--most-recent
```

Pros:

- instantly clear what direction data moves
- aligns with your old `send` and `get` scripts

Cons:

- slightly less explicit about "source of truth"

My recommendation:

- use `--push` and `--pull` in the CLI
- support `--local` as an alias of `--push`
- support `--remote` as an alias of `--pull`

That gives a clear CLI and keeps your preferred wording available.

## Config Support For Direction

I recommend a per-job default mode, overridable by CLI flags.

Example:

```toml
[[jobs.sync]]
name = "project"
sources = ["./"]
target_base = "projects/my-project"
default_mode = "push"
```

Allowed values:

- `push`
- `pull`
- `most_recent`

Resolution order:

1. explicit CLI flag
2. job `default_mode`
3. global `default_mode`
4. otherwise abort with a clear error

This is better than silently assuming one direction.

## Delete Policy Recommendation

Direction and delete policy should be separate concerns.

Suggested defaults:

- `push`: default to `--delete`
- `pull`: do not default to `--delete`
- `most_recent`: inherit the delete policy of the chosen direction

Reasoning:

- push usually means "make remote match local"
- pull is often used as recovery, where deleting local-only files is riskier

Possible flags:

```bash
--delete
--no-delete
```

And config:

```toml
[[jobs.sync]]
name = "project"
delete = true
```

## Safety Model Recommendation

For the first version, I recommend these rules:

1. Require one mode: `--push`, `--pull`, or `--most-recent`, unless a default is configured.
2. Print the resolved mode before running.
3. In `--most-recent`, show both timestamps and the chosen direction.
4. Abort `--most-recent` if either side is missing, unless the user passes `--assume-missing-local` or `--assume-missing-remote` later.
5. Do not attempt bidirectional merge behavior.

## Recommended First Implementation

If you want the cleanest first version, I would stage it like this:

### v1

- support `--push`
- support `--pull`
- support aliases `--local` and `--remote`
- support per-job `default_mode`
- support explicit `--delete` and `--no-delete`

### v2

- add `--most-recent`
- add remote timestamp probing
- add clearer conflict and ambiguity handling

This sequence is safer because `--most-recent` sounds simple but is the first feature that starts pretending to resolve state ambiguity.

## Open Decisions To Confirm Before Coding

1. Should remote sync support one shared `[connection]` per config only, or multiple named remotes like `[remotes.prod]` and `[remotes.archive]`?
2. Should `--source` mean:
   a. run an ad hoc sync without requiring any job definitions, or
   b. filter/override sources inside a named job?
3. Should remote destination mapping preserve current directory structure relative to `$PWD`, or should every source map by basename only?
4. Should `target_base` be required for every job, or should `[global].default_remote_base` be enough?
5. Should the initial release ship only with explicit directional modes (`push` and `pull`), or should it include the heuristic `most_recent` mode immediately?

## Recommended Initial Decision Set

To keep the first implementation tight, I recommend:

1. one `[connection]` per config file
2. `--source` enables ad hoc sync and bypasses named jobs
3. map relative sources relative to `$PWD`
4. allow `target_base` to default from `[global].default_remote_base`
5. ship `push` and `pull` first, then add `most_recent` later if still needed

That yields a simple first version without painting the design into a corner.
