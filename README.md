# suisave

![Static Badge](https://img.shields.io/badge/repo-suisave-blue?logo=github) ![Static Badge](https://img.shields.io/badge/status-dev-red?logo=github)

A simple, declarative backup tool. An automated frontend for [rsync](https://github.com/RsyncProject/rsync).

> [!WARNING]
> This project is _currently_ in a heavy migration process from a C++ script to a python-based CLI

suisave automates the process of making backups of your files to external storage, in a _declarative_ way. That is, given a static configuration file `comet.toml`, `suisave` will parse it and make all of your backups to their corresponding devices exactly how you wrote it. Being just a set of files, or your whole PC.

> [!NOTE]
> This project was completely redisigned on v0.2.0-alpha from a C++ executable, to a python-based cli for simplicity and future development. At the end of the day, `rsync` does the heavy lifting, and `suisave` only parses text files and makes the corresponding process calls.

**Why choose `suisave`?**

It's simple enough that my mom uses it.

> [!NOTE]
> The name _suisave_.
> I am obsessed with VTubers, and put references everywhere I can. This is a reference to my oshi [Hoshimachi Suisei](https://www.youtube.com/channel/UC5CwaMl1eIgY8h02uZw7u8A).

This project started because I am lazy enough to copy and paste my files manually, or to copy and paste the same command multiple times. Therefore I decided to make an overkill CLI to perform one simple task.


## Installation

Clone the repository, and install the package with `pip` into some virtual environment.
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
[global]
default_rsync_flags = ["-avh", "--delete"]

[drives.label1]
uuid = "uuid"

[drives.label2]
uuid = "uuid"

[drives.label3]
uuid = "uuid"

[[jobs]]
name = "my_home"
sources = [
  "/home/user/dotfiles",
  "/home/user/Desktop",
  "/home/user/Pictures",
  "/home/user/Videos",
  "/home/user/Downloads",
  "/home/user/Documents",
  "/home/user/Music",
]
drives = ["label1", "label2", "towa"]

[[jobs]]
name = "common_dir"
target_base = "" # this is a skip
pc_name = "" # this is a skip
sources = ["/home/user/share/"]
drives = ["label3"]
```

Notice that you can to setup manually the drive labels and UUIDs, to do this run in a terminal
```bash
lsblk -o NAME,LABEL,UUID
```
