# suisave
A simple text-configured backup tool written in C++. In summary, an automated frontend for rsync, or in better words, a simpler and less-capable version of [Timeshift](https://github.com/linuxmint/timeshift).

This tool was designed as a simple project to learn C++ along the way. Most probably the code is garbage, but it is _my_ garbage.

## Installation

> [!NOTE]
> Up to this point, there is no fancy way of installing and configuring these binaries.

> [!WARNING]
> If there is no `~/.config/suisave/config.toml`, nothing will work.



Clone the repository, and change directory to it
```bash 
git clone https://github.com/leogabac/suisave.git
cd suisave
```

Compile
```bash
python3 install.py
```
The installation script
1. Will compile the binaries
2. Move the binaries to `$HOME/bin`
3. Throw a warning if the above directory is not in `PATH`. Add it with
```
export PATH="$HOME/bin:$PATH"
```

## Configuration

The backups are configured through a `.toml` file under `~/.config/suisave/config.toml`. Here is a quick template
```bash 
[general]
rsync_flags = "-avh --delete"

[[drives]]
label = "label 1"
uuid = "uuid 1"

[[drives]]
label = "label 2"
uuid = "uuid 2"

[[default]]
name = "name 1"
sources = ["/path/to/dir1", "/path/to/dir2"]

[[custom]]
name = "custom name"
label = "label"
uuid = "uuid"
sources = ["/path/to/dir"]
tgbase = ""
rsync_flags = "-avh --delete"

```

Notice that you need to setup manually the drive labels and UUIDs, to do this run in a terminal
```bash
lsblk - NAME,LABEL,UUID
```

> [!CAUTION]
> Many error handling is missing.

### Default backups

The default behavior of this utility is to mirror the sources in your PC to an external/removable drive. Similar to a cloud.

1. Takes the list of `sources` from `[[default]]`
2. Syncs it with the `rsync_flags` from `[[general]]` into `/mountpoint/pc_backups/hostname/`.

It uses any mounted drive from the `[[drives]]` table. If there is more than one drive mounted, it will make a backup to all of them.

> [!WARNING]
> The `[[general]]` `[[drives]]` and `[[default]]` tables must be created. Otherwise, the program will throw an error. In the future, I will provide a way to skip them if necessary.

### Custom backups

The custom behavior of this utility is to run `rsync` with the provided information.
- `name`: Name of the backup.
- `label`: Partition label.
- `uuid`: Paritition UUID.
- `sources`: List of sources to sync.
- `tgbase`: Target relative path to the partition's mountpoint.
- `rsync_flags`: Custom flags.

This runs the command
```bash
rsync -flags /path/to/source /mountpoint/tgbase/
```
> [!WARNING]
> For the time being, all options must be provided. In the future, fallback to some default options will be implemented.

## Todo
There is a lot to do, here are some ideas left to implement.

- Intallation script with a `.desktop` for easy access.
- Configuration script.
- Logging.
- Root backups.
- A Simple GUI so that my mother can use it.



