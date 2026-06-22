# Local Backup Overview

The local-drive mode uses:

```text
~/.config/suisave/comet.toml
```

This mode is for mounted external drives identified by UUID.

It is the original `suisave` use case: one command that pushes a known set of local directories into one or more mounted backup disks without having to rebuild the `rsync` call manually.

The local-drive side of `suisave` is best understood as a small backup registry. You declare which disks exist, which sources belong to which jobs, and which defaults should apply. After that, the command becomes repetitive in a good way.

The config interaction around this mode now has its own small workflow:

- `suisave config init` to create the starter file
- `suisave config drive detect` or `suisave config drive select` to find/assign a drive
- `suisave config drive add LABEL UUID` to register it
- `suisave config show` to inspect the effective config before a run

## Main command

```bash
suisave run
```

This default command expects the optional `tui` extra to be installed.
If you are using the base package only, run:

```bash
suisave run --no-interactive
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
4. optionally check the effective config with `suisave config show`
5. run `suisave run`

That may sound almost too simple, but that is the whole point. A backup tool is most useful when the routine is boring enough that you actually keep doing it.

## Next pages

- [Config](config.md)
- [Commands](commands.md)
