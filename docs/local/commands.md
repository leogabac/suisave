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

## Add a drive

```bash
suisave config drive --add LABEL UUID
```

This writes the drive registration directly into `~/.config/suisave/comet.toml`.

## Add a drive interactively

```bash
suisave config drive --interactive
```

Interactive mode is a convenience wrapper around `lsblk` and `questionary`. It is useful when you do not want to look up the UUID manually.

## Remove a drive

```bash
suisave config drive --remove LABEL
```

Removing a drive also removes references to that label from configured jobs.

## Show current config

```bash
suisave config show
```

This is mainly a quick sanity check for the current local config state.

It is useful after adding or removing drives, or when you want to confirm that the config matches what you think you saved.
