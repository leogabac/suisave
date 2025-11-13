# suisave

A simple text-configured backup tool written in C++. In summary, an automated frontend for rsync, or in better words, a simpler and less-capable version of [Timeshift](https://github.com/linuxmint/timeshift).

This tool was designed as a simple project to learn C++ along the way. Most probably the code is garbage, but it is _my_ garbage.

## Installation

Clone the repository, and change directory to it
```bash 
git clone https://github.com/leogabac/suisave.git
cd suisave
```

Run the installation script.
```bash
python3 install.py
```
The installation script
1. Will compile the binaries
2. Move the binaries to `$HOME/.local/bin/`
3. Throw a warning if the above directory is not in `PATH`. Add it with
```bash
export PATH="$HOME/.local/bin:$PATH"
```
4. Create the configuration directory `$HOME/.config/suisave/`.
5. Guide you through the process of making a basic config file for the first time.

## Configuration

The backups are configured through a `.toml` file under `~/.config/suisave/config.toml`. Here is a quick template
```bash 
[general]
rsync_flags = "-avh --delete"
pcname = "hostname"
tgbase = "pc_backups"

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
tgbase = "mountpoint/base_dir"
rsync_flags = "-avh --delete"

```

Notice that you can to setup manually the drive labels and UUIDs, to do this run in a terminal
```bash
lsblk -o NAME,LABEL,UUID
```

### Default backups

The default behavior of this utility is to mirror the sources in your PC to an external/removable drive. Similar to a cloud.

1. Takes the list of `sources` from `[[default]]`
2. Syncs it with the `rsync_flags` from `[[general]]` into `/mountpoint/tgbase/pcname/`. Note that if no `tgbase` and `pcname` are not given under `[[general]]` then it will fallback to `/mountpoint/pc_backups/hostname`.

It uses any mounted drive from the `[[drives]]` table. If there is more than one drive mounted, it will make a backup to all of them.

> [!WARNING]
> The `[[general]]` and `[[drives]]` tables must be created. Otherwise, the program will throw an error. In the future, I will provide a way to skip them if necessary.

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

- Logging.
- Root backups.
- A Simple GUI so that my mother can use it.
- A GUI or TUI that helps you make configuration files



