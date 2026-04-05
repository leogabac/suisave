# suisave

![suisave logo](assets/suisave-logo.svg)

`suisave` is a small Linux-only CLI that wraps `rsync` with declarative TOML config files.

It exists for one reason: turn repetitive backup and sync commands into a config you can trust and run without thinking too much every time.

The project is intentionally narrow. It does not try to be a universal backup platform, a cloud sync service, or a full orchestration layer. It focuses on a small set of `rsync`-driven tasks that are common enough to be annoying by hand but simple enough to deserve a direct, readable config.

## What it does

`suisave` currently supports two main modes:

- mounted-drive backups for local external disks identified by UUID
- remote sync over SSH with a project-local config file

## Why use it

- you want one command instead of rebuilding `rsync` invocations every time
- you prefer config files over shell history archaeology
- you want local backups and project-specific remote sync without mixing those concerns

The underlying idea is that a backup command should not live only in your terminal history. If a task matters, it should be written down, named, and easy to repeat.

## Start here

- Read [Installation](guide/installation.md) to install the CLI and docs extras.
- Read [Concepts](guide/concepts.md) for the mental model behind local backups and remote sync.
- Go to [Local Backup Overview](local/overview.md) if your target is a mounted external drive.
- Go to [Remote Sync Overview](remote/overview.md) if your target is a remote SSH host.

## Quick examples

Local backup:

```bash
suisave run
```

Remote push:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

Remote pull:

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

## How the documentation is organized

The site is split into four parts:

- `Guide` explains the overall model and the intended usage.
- `Local Backups` covers the original mounted-drive backup path.
- `Remote Sync` covers the project-local SSH path.
- `Reference` collects templates, edge cases, and troubleshooting notes.

If you are new to the project, the best reading order is:

1. [Installation](guide/installation.md)
2. [Concepts](guide/concepts.md)
3. [10-Minute Tutorial](guide/tutorial.md)
4. either [Local Backup Overview](local/overview.md) or [Remote Sync Overview](remote/overview.md)

## Docs development

Install the docs extras:

```bash
pip install -e ".[docs]"
```

Run the docs locally:

```bash
mkdocs serve
```
