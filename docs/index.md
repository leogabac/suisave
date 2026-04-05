# suisave

`suisave` is a small Linux-only CLI that wraps `rsync` with declarative TOML config files.

It supports two workflows:

- local-drive backups to mounted external drives identified by UUID
- remote sync to or from remote directories over SSH with a project-local config

## Install

From PyPI:

```bash
pip install suisave
```

From source:

```bash
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

To work on the docs locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Commands

Local backups:

```bash
suisave run
```

Remote sync:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

## Documentation

- See [Local Backups](local.md) for the mounted-drive workflow.
- See [Remote Sync](remote.md) for the SSH workflow.
