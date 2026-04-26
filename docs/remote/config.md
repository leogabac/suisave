# Remote Sync Config

## Example

```toml
[global]
default_rsync_flags = ["-azvh"]
default_mode = "push"

[remotes.home_server]
host = "storage.example.com"
user = "backup"
port = 22
base_path = "backups/projects"
identity_file = "./.secrets/suisave_ed25519"
ssh_options = ["StrictHostKeyChecking=accept-new"]

[remotes.offsite_box]
host = "offsite.example.com"
user = "backup"
port = 22
base_path = "mirror/projects"
identity_file = "./.secrets/suisave_ed25519"

[[jobs.sync]]
name = "project"
sources = ["./"]
remotes = ["home_server", "offsite_box"]
mode = "push"
delete = true
```

This example shows the intended shape: one or more named remote targets, then one or more sync jobs that describe what should move and which remote targets should receive it.

The file is meant to stay close to the project it belongs to. In practice, that usually means keeping it in the repository root or in a nearby private directory, not in the global `suisave` config path.

## Sections

### `[global]`

Optional defaults:

- `default_rsync_flags`
- `default_mode`

Default values today:

- `default_rsync_flags = ["-azvh"]`
- `default_mode` is unset unless configured

These defaults let you keep job definitions short when several jobs share the same preferred sync direction.

They also make ad hoc runs via `--source` more useful, because those runs still inherit the same connection block and global defaults.

### `[remotes.<label>]`

Required values:

- `host`
- `base_path`

Optional values:

- `user`
- `port`
- `identity_file`
- `ssh_options`

Notes:

- `identity_file` is resolved relative to the config file
- password auth is not part of the current model

The current implementation assumes SSH-key-based access. That keeps the runtime simpler and avoids introducing a second credential-handling path into the tool.

For a small CLI like `suisave`, that is the right tradeoff. SSH keys and SSH agent support already solve the authentication problem in a standard Unix way.

Each remote definition is a reusable destination target. This is what lets one job push to several remote machines without forcing you to maintain one config file per destination.

### `[[jobs.sync]]`

Required fields:

- `name`
- `sources`
- `remotes`

Optional fields:

- `flags`
- `mode`
- `delete`

Each sync job is intentionally small. It declares a name, one or more sources, the remote targets it can use, and the sync policy for running against those targets.

## Source mapping

Remote sync maps sources differently from local backups:

- if the source is under `Path.cwd()`, it is mapped relative to `Path.cwd()`
- otherwise it is mapped by basename

This same rule is used for pull targets on the local machine.

For push:

- local `source` -> remote `base_path / source-suffix`

For pull:

- remote `base_path / source-suffix` -> local `source`

That means the configured `sources` are the source of truth for local destination paths, while each remote definition owns its own remote-side base path.

That mapping rule is different from the mounted-drive backup path because the remote side is anchored to the current working directory, not to `$HOME`.

That tends to match how project sync is actually used: the current directory is the natural reference point.
