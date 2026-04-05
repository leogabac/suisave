# Remote Sync

Remote sync is separate from the mounted-drive backup flow.

Use it when you want a project-local config instead of storing remote connection details in:

```text
~/.config/suisave/comet.toml
```

## Config file

Use a local config such as `./suisave.remote.toml`.

Example:

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

## Commands

Push local files to the remote host:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

Pull remote files to the local machine:

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

Let `suisave` pick the direction from the newest local or remote mtime:

```bash
suisave remote sync --config ./suisave.remote.toml --most-recent
```

Aliases:

```bash
suisave remote sync --config ./suisave.remote.toml --local
suisave remote sync --config ./suisave.remote.toml --remote
```

Run only one job:

```bash
suisave remote sync --config ./suisave.remote.toml --name project --push
```

Run an ad hoc source from the current directory:

```bash
suisave remote sync --config ./suisave.remote.toml --source "$PWD" --push
```

## Notes

- Remote configs use `[connection]`, not `[drives]`.
- Relative `sources` are resolved from the current working directory.
- `identity_file` is resolved relative to the remote config file.
- `default_mode` can be `push`, `pull`, or `most_recent`.
- `push` defaults to `--delete` unless overridden.
- `most_recent` compares newest local and remote mtimes for each source pair.
- If `most_recent` sees effectively equal mtimes, it aborts and asks for an explicit direction.
- The remote host needs `sh`, `find`, `sort`, `head`, and `stat` for `most_recent`.
