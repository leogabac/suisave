# Concepts

`suisave` has two separate operating modes. Keeping them separate is deliberate since I am no kami-tier developer.

## Local backups

This is the original mode of operation.

- config path: `~/.config/suisave/comet.toml` by default, or `SUISAVE_CONFIG_PATH` when set
- targets: mounted local drives
- target identity: filesystem UUID
- main command: `suisave run`

Use this when the destination is a local disk you physically mount on the machine.

This mode is built around repeatable personal backups. You register a drive once, refer to it by label in jobs, and let `suisave` resolve the real mountpoint through the drive UUID. That way, the backup command does not depend on where the operating system happened to mount the disk this time.

## Remote sync

This is the project-local mode. Designed towards sending/retrieving data from servers.

- config path: chosen explicitly with `--config`
- targets: one or more named remote destinations over SSH
- target identity: remote label, host, user, SSH key, and remote base path
- main command: `suisave remote sync`

Use this when the destination is another machine and the connection details should stay near the project.

This mode is project-local. A repo or working directory can carry its own remote sync definition without leaking that information into your general machine-wide backup setup.

## Direction matters

Remote sync is directional.

- `--push`: local is the source of truth
- `--pull`: remote is the source of truth
- `--most-recent`: `suisave` compares mtimes and picks `push` or `pull`

If `--most-recent` sees effectively equal mtimes, it aborts.

If a job references more than one remote target, `pull` and `--most-recent` require you to select one explicitly with `--target`.

That behavior is conservative. Once deletes and overwrites are involved, silently guessing the direction is a questionable decision to make.

## Config philosophy

The project leans toward:

- small, explicit TOML files
- direct mapping to the underlying `rsync` call
- minimal hidden behavior

In practice, that means:

- local backups optimize for stable named jobs against known drives
- remote sync optimizes for explicit per-project intent, reusable named remotes, and source-of-truth control
