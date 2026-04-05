# Local Backups

The original `suisave` workflow uses a global config file at:

```text
~/.config/suisave/comet.toml
```

This mode is for backups to mounted local drives identified by UUID.

## Minimal config

```toml
[drives.MYLABEL]
uuid = "XXXXXXXXXXXXXXX"

[[jobs.backup]]
name = "general"
sources = ["/home/USERNAME"]
drives = ["MYLABEL"]
```

## Run

```bash
suisave run
```

## Notes

- Drives are configured under `[drives.<label>]`.
- Jobs can be `[[jobs.backup]]` or `[[jobs.custom]]`.
- Backup jobs default to `backups/<hostname-machine-id>/`.
- Custom jobs can override `target_base` and `flags`.
- Source paths are currently expected to be under `$HOME` for target mapping.

## Drive management

Add a drive:

```bash
suisave config drive --add LABEL UUID
```

Interactive mode:

```bash
suisave config drive --interactive
```

Remove a drive:

```bash
suisave config drive --remove LABEL
```
