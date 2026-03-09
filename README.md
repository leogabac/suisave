# suisave

![Static Badge](https://img.shields.io/badge/repo-suisave-blue?logo=github) ![Static Badge](https://img.shields.io/badge/status-dev-red?logo=github)

A simple, declarative backup tool. An automated frontend for [rsync](https://github.com/RsyncProject/rsync).

> [!WARNING]
> This project is _currently_ in a heavy migration process from a C++ script to a python-based CLI

suisave automates the process of making backups of your files to external storage, or remote storage (NAS, not cloud services) in a _declarative_ way. That is, given a static configuration file `comet.toml`, `suisave` will parse it and make all of your backups to their correspondinge devices exactly how you wrote it. Being just a set of files, or your whole PC.

> [!NOTE]
> This project was completely redisigned on v0.2.0-alpha from a C++ executable, to a python-based cli for simplicity and future development. At the end of the day, `rsync` does the heavy lifting, and `suisave` only parses text files and makes the corresponding process calls.

gremux automates the process of launching a `tmux` session exactly how you want it in a _declarative_ way. That is, given a static configuration file `grem.yaml`, `gremux` will parse it and attach you to a session that matches that setup.

**Why choose `suisave`?**

It's simple enough that my mom uses it.

> [!NOTE]
> The name _suisave_.
> I am obsessed with VTubers, and put references everywhere I can. This is a reference to my favorite VTuber [Hoshimachi Suisei](https://www.youtube.com/channel/UC5CwaMl1eIgY8h02uZw7u8A).

This project started because I am lazy enough to copy and paste my files manually, or to copy and paste the same command multiple times. Therefore I decided to make an overkill CLI to perform one simple task.


## Installation

Clone the repository, and install the package with `pip`.
```bash 
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

Run the basic configuration script.
```bash
suisave-config -n
```
This will guide you through the process of making a "general" backup

---

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



