# Concepts

`suisave` has two separate operating modes. Keeping them separate is deliberate.

That separation is not accidental or cosmetic. The local-drive and remote-sync paths solve different problems, depend on different assumptions, and need different kinds of configuration. Treating them as one combined target model would make the CLI harder to understand and the config harder to trust.

## Local backups

This is the original mode of operation.

- config path: `~/.config/suisave/comet.toml`
- targets: mounted local drives
- target identity: filesystem UUID
- main command: `suisave run`

Use this when the destination is a local disk you physically mount on the machine.

This mode is built around repeatable personal backups. You register a drive once, refer to it by label in jobs, and let `suisave` resolve the real mountpoint through the drive UUID. That way, the backup command does not depend on where the operating system happened to mount the disk this time.

## Remote sync

This is the project-local mode.

- config path: chosen explicitly with `--config`
- targets: one or more named remote destinations over SSH
- target identity: remote label, host, user, SSH key, and remote base path
- main command: `suisave remote sync`

Use this when the destination is another machine and the connection details should stay near the project instead of inside the global backup config.

This mode is intentionally project-local. A repo or working directory can carry its own remote sync definition without leaking that information into your general machine-wide backup setup.

It is also now intentionally multi-target. A single job can push to several named remotes, which makes the remote side behave more like the mounted-drive side where one job can target several drives.

## Direction matters

Remote sync is not a true bidirectional merge engine. It is directional.

- `--push`: local is the source of truth
- `--pull`: remote is the source of truth
- `--most-recent`: `suisave` compares mtimes and picks `push` or `pull`

If `--most-recent` sees effectively equal mtimes, it aborts instead of guessing.

If a job references more than one remote target, `pull` and `--most-recent` require you to select one explicitly with `--target`.

That behavior is conservative on purpose. Once deletes and overwrites are involved, silently guessing the direction is the wrong tradeoff.

## Config philosophy

The project leans toward:

- small, explicit TOML files
- direct mapping to the underlying `rsync` call
- minimal hidden behavior

That is why local-drive and remote-sync configs are not merged into one overloaded schema.

In practice, that means:

- local backups optimize for stable named jobs against known drives
- remote sync optimizes for explicit per-project intent, reusable named remotes, and source-of-truth control

## A good rule of thumb

If you are asking yourself "where is the data going?", start with the local-backup pages.

If you are asking yourself "which side should win?", start with the remote-sync pages.
