# Troubleshooting

## Local backup job cannot find a drive

Check:

- the drive is mounted
- the UUID in the config is correct
- the drive label referenced by the job exists under `[drives]`

If none of the requested drives for a job are mounted, the job will not run.

## Local backup source fails outside `$HOME`

The local-drive path currently maps targets using the source path relative to `$HOME`.

If the source is outside `$HOME`, review the current limitation before using that path in local backup jobs.

This is a limitation of the current target-path mapping, not of `rsync` itself.

## Remote sync cannot connect

Check:

- host, user, and port in `[connection]`
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

## Where to read next

If the issue is about initial setup, read the [10-Minute Tutorial](../guide/tutorial.md).

If the issue is about direction or delete behavior, read [Remote Sync Modes](../remote/modes.md).

If the issue is about config structure, read [Local Backup Config](../local/config.md) or [Remote Sync Config](../remote/config.md).
