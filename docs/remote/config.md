# Remote Sync Config

## Example

```toml
[global]
default_rsync_flags = ["-azvh"]
default_remote_base = "backups"
default_mode = "push"

[connection]
host = "storage.example.com"
user = "backup"
port = 22
identity_file = "./.secrets/suisave_ed25519"
ssh_options = ["StrictHostKeyChecking=accept-new"]

[[jobs.sync]]
name = "project"
sources = ["./"]
target_base = "projects/my-project"
default_mode = "push"
delete = true
```

This example shows the intended shape: one connection block for the remote host, then one or more named sync jobs that describe what should move and where it should land.

The file is meant to stay close to the project it belongs to. In practice, that usually means keeping it in the repository root or in a nearby private directory, not in the global `suisave` config path.

## Sections

### `[global]`

Optional defaults:

- `default_rsync_flags`
- `default_remote_base`
- `default_mode`

Default values today:

- `default_rsync_flags = ["-azvh"]`
- `default_remote_base = "."`
- `default_mode` is unset unless configured

These defaults let you keep job definitions short when several jobs share the same remote destination root or the same preferred sync direction.

They also make ad hoc runs via `--source` more useful, because those runs still inherit the same connection block and global defaults.

### `[connection]`

Required values:

- `host`

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

### `[[jobs.sync]]`

Required fields:

- `name`
- `sources`

Optional fields:

- `target_base`
- `flags`
- `default_mode`
- `delete`

Each sync job is intentionally small. It declares a name, one or more sources, and just enough additional information to decide how those sources should map onto the remote side.

## Source mapping

Remote sync maps sources differently from local backups:

- if the source is under `Path.cwd()`, it is mapped relative to `Path.cwd()`
- otherwise it is mapped by basename

This same rule is used for pull targets on the local machine.

That mapping rule is different from the mounted-drive backup path because the remote side is anchored to the current working directory, not to `$HOME`.

That tends to match how project sync is actually used: the current directory is the natural reference point.
