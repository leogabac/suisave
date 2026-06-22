# Local Backup Config

## Minimal example

```toml
[drives.MYLABEL]
uuid = "XXXXXXXXXXXXXXX"

[[jobs.backup]]
name = "general"
sources = ["/home/USERNAME"]
drives = ["MYLABEL"]
```

This is the smallest useful local-backup config: register one drive, define one backup job, and run it with `suisave run`.

For many people, that is already enough. The rest of the schema exists so you can add more drives, reuse defaults, and handle less standard destinations.

If you want a starter file instead of creating this manually, run `suisave config init`.

The local config path defaults to `~/.config/suisave/comet.toml`.
If `SUISAVE_CONFIG_PATH` is set, local-mode commands use that path instead.

## Sections

### `[global]`

Optional.

This section exists to keep repetitive values in one place. If you omit it entirely, the parser synthesizes defaults for you.

Supported defaults:

- `pc_name`
- `default_target_base`
- `default_rsync_flags`

Default values today:

- `pc_name = "<hostname>-<machine-id-prefix>"`
- `default_target_base = "backups"`
- `default_rsync_flags = ["-avh", "--delete"]`

### `[drives.<label>]`

Each drive entry stores:

- label
- UUID

The drive is only usable when the UUID resolves to a mounted path.

### `[[jobs.backup]]`

Required fields:

- `name`
- `sources`
- `drives`

Behavior:

- target base becomes `default_target_base / pc_name`
- flags come from `[global]`

Use backup jobs for the common case: “copy these directories into the standard backup layout on whichever configured drive is mounted”.

### `[[jobs.custom]]`

Required fields:

- `name`
- `sources`
- `drives`

Optional fields:

- `target_base`
- `flags`

Behavior:

- `target_base` is relative to the drive mountpoint
- flags override the global defaults

Custom jobs exist for the cases where the default backup layout is too opinionated and you want to control the destination root more directly.

## Mapping behavior

Each source is mirrored under:

```text
<mountpoint>/<effective target base>/<source relative to $HOME>
```

If a source is outside `$HOME`, `suisave` stores it under:

```text
<mountpoint>/<effective target base>/__outside_home__/<absolute source path without leading />
```

That keeps out-of-home sources deterministic and avoids collapsing them down to a basename-only destination.
