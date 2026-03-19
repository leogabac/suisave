# suisave

![Static Badge](https://img.shields.io/badge/repo-suisave-blue?logo=github) ![Static Badge](https://img.shields.io/badge/status-alpha-green?logo=github)

A simple, declarative backup tool. An automated frontend for [rsync](https://github.com/RsyncProject/rsync).

> [!WARNING]
> This project was completely rewritten on v. 0.3.0-alpha with many breaking changes. To recompile the previous version, refer to the alternative branches.

suisave automates the process of making backups of your files to external storage, in a _declarative_ way. That is, given a static configuration file `comet.toml`, `suisave` will parse it and make all of your backups to their corresponding devices exactly how you wrote it. Being just a set of files, or your whole PC.

This project started because I am lazy enough to copy and paste my files manually, or to copy and paste the same command multiple times. Therefore I decided to make an overkill CLI to perform one simple task.

**Why choose `suisave`?**

If you...

* are in the niche of being constantly tired of having to think about managing your backups properly into physical, external devices, adding redundancy, and copying and pasting multiple times. Then suisave is for you.

* like to only execute one single command to execute all of your backups from a single, static configuration file.

Then suisave is for you. Additionally, suisave is simple enough that even my mom uses it.

> [!NOTE]
> The name _suisave_.
> I am obsessed with VTubers, and put references everywhere I can. This is a reference to my kamioshi [Hoshimachi Suisei](https://www.youtube.com/channel/UC5CwaMl1eIgY8h02uZw7u8A).

## Support and Requirements

**Supported Operating Systems**

* Linux (any with pip)
* Arch Linux based (through the AUR)

> [!NOTE]
> The library contains one specific subprocess call to `lsblk` in interactive mode that will break in MacOS. There are future plans to support it though.
>
> No Windows support, and no current plans to do so.

## Installation

### From PyPI (pip)

Simply enter your virtual environment and run
```bash
pip install suisave
``` 

### Local installation from source (pip)

In case new features are not avaiable on the PyPI build, you can directly clone and install the package into your virtual environment.
```bash 
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

### Arch-Based Linux Distributions (system-wide)

Use any AUR helper like `paru` or `yay`.
```bash
paru -S suisave
```

### Post Install

Run the following command: 
```bash
suidesk
```
This will create a `suisave.desktop` under `~/.local/share/applications/` for you to find with your preferred application launcher.

## Configuration and Usage

The backups are configured through a `.toml` file under `~/.config/suisave/comet.toml`. See the [example template](./templates/comet.toml).

In summary, suisave requires two things
1. A table of drives that you can use, each identified by their UUID
2. Rsync jobs to do

once that is set up, simply run
```
suisave run
```

### Registering drives

Drives are registered by a `LABEL` and their `UUID`. You can manually get them via `lsblk`, and either edit the config file or run
```
suisave config drive --add LABEL UUID
```
A better way is to connect and mount the desired drives to add and run the `--interactive` flag.
```
suisave config drive --interactive
```

> [!NOTE]
> To remove a drive, run
> ```
> suisave config drive --remove LABEL # the registered label
> ```
> No need for UUID here. Or simply do it via the `--interactive` flag.


### Jobs

Any rsync job requires
1. A name
2. A `target_base` directory (relative to drive mountpoint)
3. A list of `sources`
4. A list of `drives`
5. A list of `flags`

Then rsync runs
```
rsync flags /path/to/source /mountpoint/target_base/relative/path/to/source
```

There are two types of jobs: backups and custom. 

**Backup Jobs:**

Backup jobs are a subset of the custom jobs where some defaults are assumed

1. The target base is by default `backups/hostname-machine-id`. 
The main idea is to have an identical copy of your home directory with redundancy backed up. This way you can have multiple computer backed up to the same drive.

These options can be changed via the `tg_base` and `pc_name` in the `[global]` table

2. The rsync flags are taken from the `[global]` table.

**Custom Jobs:**

These are general and require you to provide all fields. They exist just in case you need more flexibility.
