# Local Backup Commands

## Run all jobs

```bash
suisave run
```

This is the normal day-to-day command. It loads the global config, resolves mounted drives, and runs every eligible job.

If you use `suisave` mainly for personal backups, this is probably the command you will run most often.

## Run selected jobs

```bash
suisave run --name general photos
```

Use this when you want the same config file but only a subset of jobs for a given run.

## Initialize the config file

```bash
suisave config init
```

This creates `~/.config/suisave/comet.toml` with a starter template.

If the file already exists and you intentionally want to replace it, run:

```bash
suisave config init --force
```

## Show the config path

```bash
suisave config path
```

This prints the local config path that the mounted-drive backup flow uses.

## Add a drive

```bash
suisave config drive add LABEL UUID
```

This writes the drive registration directly into `~/.config/suisave/comet.toml`.

## Remove a drive

```bash
suisave config drive rm LABEL
```

Removing a drive also removes references to that label from configured jobs.

## List configured drives

```bash
suisave config drive ls
```

This shows the configured labels, UUIDs, and whether each drive is currently mounted.

## Detect mounted devices

```bash
suisave config drive detect
```

This lists mounted block devices discovered from `lsblk` so you can grab the UUID you want.

## Select drives interactively

```bash
suisave config drive select
```

Interactive mode is a convenience wrapper around `lsblk` and `questionary`. It is useful when you do not want to look up the UUID manually or want to remove a configured drive from a picker.

## Show current config

```bash
suisave config show
```

This is mainly a quick sanity check for the current local config state.

It is useful after adding or removing drives, or when you want to confirm the effective target bases, default flags, and mounted-drive status that `suisave` will actually use.

## Open the config editor TUI

```bash
suisave config tui
```

This opens the Textual config editor for the local backup model.

Use it when you want a structured editor with live validation, target-base preview, and save/reload controls instead of editing the TOML file manually.

The editor is keyboard-first:

- normal mode: `j`/`k` or arrow keys move through the config tree
- `enter` or `i`: switch into insert mode for the selected item
- insert mode: edit fields directly, then press `escape` to return to normal mode
- `d`: delete the selected drive or job
- `D`: add a drive
- `B`: add a backup job
- `C`: add a custom job
- `ctrl+s`: save
- `ctrl+r`: reload from disk
