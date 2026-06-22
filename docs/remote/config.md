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

[remotes.home_server.jump_host]
host = "jump.example.com"
user = "relay"
port = 22
identity_file = "./.secrets/suisave_jump_ed25519"
ssh_options = ["StrictHostKeyChecking=accept-new"]

[remotes.workstation]
host = "10.96.5.90"
user = "reiko"
base_path = "/home/reiko/Documents/experiment-code"

[remotes.workstation.alternate_host]
host = "100.64.12.34"
user = "reiko"

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

The file is meant to stay close to the project it belongs to. In practice, that usually means keeping it in the repository root or in a nearby private directory, not in the global `suisave` config path.

## Sections

### `[global]`

Optional defaults:

- `default_rsync_flags`
- `default_mode`

Default values today:

- `default_rsync_flags = ["-azvh"]`
- `default_mode` is unset unless configured

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
- `jump_host`
- `alternate_host`

Notes:

- `identity_file` is resolved relative to the config file
- `jump_host` is a nested SSH table used only when `--use-jump-host` is passed
- `alternate_host` is a nested SSH table used only when `--use-alternate-host`
  or `--jump-and-alt-host` is passed
- password auth is not part of the current model

The current implementation assumes SSH-key-based access.

### `[remotes.<label>.jump_host]`

Optional nested SSH definition.

Supported fields match the normal SSH connection fields:

- `host`
- `user`
- `port`
- `identity_file`
- `ssh_options`
- optional nested `jump_host`

It is only used when the command
is run with `--use-jump-host` or `--jump-and-alt-host`.

### `[remotes.<label>.alternate_host]`

Optional nested SSH definition.

Supported fields:

- `host`
- `user`
- `port`
- `identity_file`
- `ssh_options`
- optional `jump_host`

Use this when the same logical remote can be reached through a different
endpoint for some runs, such as a VPN, Tailscale, Zerotier, or LAN address.

This is only used when the command is run with `--use-alternate-host` or
`--jump-and-alt-host`.

### `[[jobs.sync]]`

Required fields:

- `name`
- `sources`
- `remotes`

Optional fields:

- `flags`
- `mode`
- `delete`

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
