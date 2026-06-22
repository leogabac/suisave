# Remote Sync Commands

## Push all configured jobs

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

This runs every selected job with local as the authoritative side.
If a job references several remotes, push iterates through all of them.

## Pull all configured jobs

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

This runs every selected job with remote as the authoritative side.
If a job references more than one remote, you must choose one with `--target`.

## Use most recent

```bash
suisave remote sync --config ./suisave.remote.toml --most-recent
```

Use this only when timestamp-based direction selection is acceptable for the task.
If a job references more than one remote, you must choose one with `--target`.

## Run only one named job

```bash
suisave remote sync --config ./suisave.remote.toml --name project --push
```

This is useful when one config file holds several jobs but you only want to run one of them.

## Run an ad hoc source

```bash
suisave remote sync --config ./suisave.remote.toml --source "$PWD" --push
```

Ad hoc mode is convenient for one-off runs because it does not require `[[jobs.sync]]` entries. The connection block and global defaults still come from the config file.

## Choose one remote target

```bash
suisave remote sync --config ./suisave.remote.toml --pull --target home_server
```

This is required when a job references multiple remotes and you want to pull or use `--most-recent`.

## Route through a jump host

```bash
suisave remote sync --config ./suisave.remote.toml --push --use-jump-host
```

Use this when the selected remote defines a nested `jump_host` table and the run
should go through that.

This is opt-in at runtime. Defining `jump_host` in the config does not force all
runs to use it.

## Use an alternate host

```bash
suisave remote sync --config ./suisave.remote.toml --push --use-alternate-host
```

Use this when a remote defines an `alternate_host` table and you want that run
to use a different endpoint, such as a private-network or Tailscale address.

Like `jump_host`, this is opt-in for each run.

## Use both routing options together

```bash
suisave remote sync --config ./suisave.remote.toml --push --jump-and-alt-host
```

This is shorthand for using both the configured jump host and alternate host in
the same run.

## Override delete behavior

```bash
suisave remote sync --config ./suisave.remote.toml --push --delete
suisave remote sync --config ./suisave.remote.toml --pull --no-delete
```

This is the most direct way to force the behavior for a specific run, regardless of what the job defaults say.

## Preview a remote run

```bash
suisave remote sync --config ./suisave.remote.toml --push --dry-run
```

Use this to preview the remote `rsync` changes without writing them.

This is especially useful before a push that may apply `--delete`.

Remote runs also use a lock so two `suisave remote sync` commands do not overlap accidentally.
