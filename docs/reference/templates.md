# Templates

The repository ships two example templates:

- `templates/comet.toml`
- `templates/suisave.remote.toml`

Use them as starting points instead of inventing the schema from scratch.

That is usually the fastest way to get a correct config, especially when you are still learning which fields are optional and which defaults are implied by the parser.

## Local backup template

Path:

```text
templates/comet.toml
```

Use this for mounted-drive backups through `suisave run`.

It documents the `global`, `drives`, `jobs.backup`, and `jobs.custom` structure expected by the local-backup path.

## Remote sync template

Path:

```text
templates/suisave.remote.toml
```

Use this for SSH sync through `suisave remote sync --config ...`.

It documents the `global`, `remotes.<label>`, and `jobs.sync` structure used by the remote path.

The important idea in the current template is that named remotes are reusable. One job can reference one or many remote targets, and push can iterate through all of them.
