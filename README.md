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
g++ main.cpp -o suisave
```
Move the binary to somewhere you have access to. Typically I use
```bash
mkdir $HOME/bin
mv suisave $HOME/bin/
```
and in my `~/.bashrc`
```
export PATH="$HOME/bin:$PATH"
```

## Configuration

The backups are configured through a `.toml` file under `~/.config/suisave/config.toml`. Here is a quick template
```bash 
[general]
rsync_flags = "-avh --delete"

[[drives]]
label = "LABEL 1"
uuid = "UUID"

[[drives]]
label = "LABEL 2"
uuid = "UUID 2"

[[backups]]
name = "General"
sources = ["/path/to/directory", "/path/to/directory"]
```

Notice that you need to setup manually the drive labels and UUIDs, to do this run in a terminal
```bash
lsblk - NAME,LABEL,UUID
```

> [!CAUTION]
> Many error handling is missing. If a drive or directory is written incorrectly, it will run, but do nothing.


## Todo
There is a lot to do, here are some ideas left to implement.

- Intallation script with a `.desktop` for easy access.
- Configuration script.
- Logging.
- Custom backups that point to specific directories, users, disks and flags.
- Root backups.
- A Simple GUI so that my mother can use it.



