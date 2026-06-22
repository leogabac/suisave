# Troubleshooting

## Local backup job cannot find a drive

Check:

- the drive is mounted
- the UUID in the config is correct
- the drive label referenced by the job exists under `[drives]`

If none of the requested drives for a job are mounted, the job will not run.

## `suisave run` says Textual is not installed

The default `suisave run` command uses the optional Textual transfer UI.

Either install the extra:

```bash
pip install "suisave[tui]"
```

Or use the non-Textual runner:

```bash
suisave run --no-interactive
```

## Local backup source fails outside `$HOME`

The local-drive path maps in-home sources relative to `$HOME`.

For sources outside `$HOME`, `suisave` stores them under `__outside_home__/...` inside the backup target tree so the destination stays deterministic.

## Remote sync cannot connect

Check:

- host, user, and port in the selected `[remotes.<label>]`
- SSH key path in `identity_file`
- whether you can connect with plain `ssh` first

If a normal `ssh` command to the host does not work, `suisave remote sync` will not fix that underlying connection problem.

## `--most-recent` aborts

That happens when the newest local and remote mtimes are effectively equal.

In that case, run the command again with an explicit direction:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

or

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

This is the intended safety valve. When the heuristic cannot make a clean decision, the user should make the decision instead.

## Remote host lacks tools for `--most-recent`

The remote host needs:

- `sh`
- `find`
- `sort`
- `head`
- `stat`

If those are missing, use `--push` or `--pull` explicitly.

## I want to inspect changes before copying or deleting anything

Use dry run first:

```bash
suisave run --dry-run --no-interactive
suisave remote sync --config ./suisave.remote.toml --push --dry-run
```

`--dry-run` previews the `rsync` changes but does not transfer files.

## `suisave` says another run is already active

`0.3.2` now uses per-mode run locks for local and remote execution.

If you see a lock error, it usually means another `suisave run` or `suisave remote sync` process is still active in another terminal.

Wait for the other run to finish or stop that process before retrying.

## Where to read next

If the issue is about initial setup, read the [10-Minute Tutorial](../guide/tutorial.md).

If the issue is about direction or delete behavior, read [Remote Sync Modes](../remote/modes.md).

If the issue is about config structure, read [Local Backup Config](../local/config.md) or [Remote Sync Config](../remote/config.md).
