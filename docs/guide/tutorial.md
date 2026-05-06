# 10-Minute Tutorial

This page is the quickest path from zero to a working `suisave` setup.

The point is not to explain every option in the schema. The point is to get one local backup and one remote sync command running so the rest of the docs have some concrete context.

## What you will do

In about ten minutes, you will:

1. install `suisave`
2. create a minimal local backup config
3. run one local backup job
4. create a minimal remote sync config
5. run one remote push job

If you only care about one side, you can stop halfway through.

## 1. Install `suisave`

From PyPI:

```bash
pip install suisave
```

Then confirm the command exists:

```bash
suisave --version
```

You also need:

- Linux
- `rsync`
- `lsblk` for the interactive drive helper

For the remote section later, make sure normal SSH access to the target machine already works.

## 2. Create a local backup config

Start by creating the local config file:

```bash
suisave config init
```

If you want to confirm the exact path that local-drive backups use:

```bash
suisave config path
```

Then edit `~/.config/suisave/comet.toml` so it looks like:

```toml
[drives.MYDRIVE]
uuid = "PUT-YOUR-DRIVE-UUID-HERE"

[[jobs.backup]]
name = "documents"
sources = ["/home/YOURUSER/Documents"]
drives = ["MYDRIVE"]
```

If you do not know the UUID yet, either list block devices with `lsblk`:

```bash
lsblk -o NAME,LABEL,UUID,MOUNTPOINT
```

Or use the built-in helper:

```bash
suisave config drive detect
```

You can also use the interactive picker:

```bash
suisave config drive select
```

Pick the UUID of the mounted backup drive you want to use, then either edit the file directly or register it with:

```bash
suisave config drive add MYDRIVE PUT-YOUR-DRIVE-UUID-HERE
```

## 3. Run the local backup

With the drive mounted, run:

```bash
suisave run
```

If the config is correct, `suisave` will:

- load `~/.config/suisave/comet.toml`
- resolve the drive mountpoint from the UUID
- build the destination path
- execute `rsync`

If you want to inspect the effective local config before you run anything:

```bash
suisave config show
```

That is the core local-disk case working end to end.

## 4. Create a remote sync config

Move to a project directory:

```bash
cd /path/to/your/project
```

Create `suisave.remote.toml`:

```toml
[global]
default_rsync_flags = ["-azvh"]
default_mode = "push"

[remotes.home_server]
host = "your-server.example.com"
user = "your-user"
port = 22
base_path = "backups/projects"
identity_file = "./.secrets/suisave_ed25519"

[[jobs.sync]]
name = "project"
sources = ["./"]
remotes = ["home_server"]
```

This config says:

- connect to the named remote target over SSH
- treat the current directory as the source
- sync it into `backups/projects/...` on the remote side

## 5. Run the remote sync

Push the project to the remote host:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

This makes the local side authoritative for the run.

If you later want to restore from the remote copy instead, use:

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

## 6. Understand the three direction modes

Remote sync is directional. That is the most important thing to understand before you rely on it.

- `--push`: local wins
- `--pull`: remote wins
- `--most-recent`: `suisave` compares mtimes and chooses

If you are unsure, prefer `--push` or `--pull` explicitly. `--most-recent` is useful, but it is still a heuristic rather than true conflict resolution.

## 7. Know what to read next

If the local example worked, continue with:

- [Local Backup Overview](../local/overview.md)
- [Local Backup Config](../local/config.md)
- [Local Backup Commands](../local/commands.md)

If the remote example worked, continue with:

- [Remote Sync Overview](../remote/overview.md)
- [Remote Sync Config](../remote/config.md)
- [Remote Sync Modes](../remote/modes.md)
- [Remote Sync Commands](../remote/commands.md)

## Common first mistakes

- using an unmounted drive in the local config
- typing the wrong UUID
- forgetting that remote sync always requires `--config`
- assuming remote sync is bidirectional by default
- expecting `--most-recent` to resolve ties automatically

If something goes wrong, check [Troubleshooting](../reference/troubleshooting.md).
