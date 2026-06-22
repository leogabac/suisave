# Remote Sync Overview

Remote sync is the SSH-based path for project-local configs.

Instead of using the global backup config, you point `suisave` at a local TOML file:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

That explicit `--config` requirement is on purpose. Remote sync often carries project-specific paths, hosts, and credentials, so it does not quietly share the same config space as mounted-drive backups. That way you can keep the global config file in your dotfiles without worrying on leaking ssh keys.

## When to use it

Use remote sync when:

- the destination is another machine
- connection details should live with the project
- you want explicit push or pull behavior
- you want one job to fan out to more than one remote target

This mode was designed for sending code and retrieving data from a HPC cluster. If that use case rings a bell, then go for it.

## Main ideas

- config is explicit via `--config`
- transport is SSH
- remote targets live under `[remotes.<label>]`
- jobs live under `[[jobs.sync]]`
- direction is `push`, `pull`, or `most_recent`
- routing options such as `jump_host` and `alternate_host` are opt-in per run

The command is still powered by `rsync`, but `suisave` handles the repetitive structure around it: resolving paths, selecting jobs, applying defaults, and deciding which side is authoritative.

In practice, that means one job definition describes both directions cleanly:

- the `sources` field defines where files live locally
- the remote definition’s `base_path` field defines where they live remotely

It also means a single job can push to several named remotes, which makes the remote side behave much more like the local-drive fanout model.

A remote may define a nested `jump_host`
for access or an `alternate_host` for a second endpoint, but those are
only activated when the relevant CLI flags are passed for that run.

The main rule to remember is simple:

- many remotes are fine for push
- one remote must be selected for pull or `--most-recent`

## Next pages

- [Config](config.md)
- [Modes](modes.md)
- [Commands](commands.md)

If you want a guided start rather than jumping straight into the reference pages, begin with the [10-Minute Tutorial](../guide/tutorial.md).
