# Remote Sync Commands

## Push all configured jobs

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

This runs every selected job with local as the authoritative side.

## Pull all configured jobs

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

This runs every selected job with remote as the authoritative side.

## Use most recent

```bash
suisave remote sync --config ./suisave.remote.toml --most-recent
```

Use this only when timestamp-based direction selection is acceptable for the task.

## Run only one named job

```bash
suisave remote sync --config ./suisave.remote.toml --name project --push
```

This is useful when one config file holds several jobs but you only want to run one of them.

It is also a good habit while you are still validating a new config, because it lets you verify one job before trusting the whole file.

## Run an ad hoc source

```bash
suisave remote sync --config ./suisave.remote.toml --source "$PWD" --push
```

Ad hoc mode is convenient for one-off runs because it does not require `[[jobs.sync]]` entries. The connection block and global defaults still come from the config file.

That makes it useful for experimentation and temporary sync tasks where creating a permanent named job would just add clutter.

## Override delete behavior

```bash
suisave remote sync --config ./suisave.remote.toml --push --delete
suisave remote sync --config ./suisave.remote.toml --pull --no-delete
```

This is the most direct way to force the behavior for a specific run, regardless of what the job defaults say.
