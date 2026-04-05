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

For many people, that is already enough. The rest of the schema exists so you can add more drives, reuse defaults, and handle less standard destinations without turning the file into guesswork.

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

This is what makes the setup robust across changing mount locations. The config cares about the physical filesystem identity, not about a mountpoint string that may change between sessions.

### `[[jobs.backup]]`

Required fields:

- `name`
- `sources`
- `drives`

Behavior:

- target base becomes `default_target_base / pc_name`
- flags come from `[global]`

Use backup jobs for the common case: “copy these directories into the standard backup layout on whichever configured drive is mounted”.

They are opinionated on purpose. If your backup destination layout is conventional, they keep the config short and readable.

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

That gives the tool some flexibility without forcing every simple config to carry extra detail.

## Mapping behavior

Each source is mirrored under:

```text
<mountpoint>/<job.tg_base>/<source relative to $HOME>
```

That means sources outside `$HOME` are currently not handled well by the local-drive path.

If you plan to back up system paths or directories outside your home directory, review that limitation before relying on this mode.
