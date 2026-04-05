# Local Backup Overview

The local-drive mode uses:

```text
~/.config/suisave/comet.toml
```

This mode is for mounted external drives identified by UUID.

It is the original `suisave` use case: one command that pushes a known set of local directories into one or more mounted backup disks without having to rebuild the `rsync` call manually.

The local-drive side of `suisave` is best understood as a small backup registry. You declare which disks exist, which sources belong to which jobs, and which defaults should apply. After that, the command becomes repetitive in a good way.

## Main command

```bash
suisave run
```

Run only selected jobs:

```bash
suisave run --name general
```

If no job names are given, `suisave` loads all configured jobs whose required drives are currently mounted.

## Setup summary

1. register one or more drives under `[drives]`
2. define jobs under `[jobs.backup]` or `[jobs.custom]`
3. mount the drive
4. run `suisave run`

The design favors predictable repetition. Once the drives and jobs are written down, the day-to-day habit becomes “mount the disk and run the command”.

That may sound almost too simple, but that simplicity is the whole point. A backup tool is most useful when the routine is boring enough that you actually keep doing it.

## Next pages

- [Config](config.md)
- [Commands](commands.md)
