# suisave

![Repository](https://img.shields.io/badge/repo-suisave-blue?logo=github) ![Development Status](https://img.shields.io/badge/status-alpha-green?logo=github)

![PyPI - Version](https://img.shields.io/pypi/v/suisave) ![AUR Version](https://img.shields.io/aur/version/suisave)

![logo](./assets/suisave-logo.svg)

A simple, declarative backup tool. An automated frontend for [rsync](https://github.com/RsyncProject/rsync).

> [!WARNING]
> This project was completely rewritten on v.0.3.0 with many breaking changes. To recompile the previous version, refer to the alternative branches.

suisave automates the process of making backups of your files to external storage, in a _declarative_ way. That is, given a static configuration file `comet.toml`, `suisave` will parse it and make all of your backups to their corresponding devices exactly how you wrote it. Being just a set of files, or your whole PC.

**Why choose `suisave`?**

If you...

* are in the niche of being constantly tired of having to think about managing your backups properly into physical, external devices, adding redundancy, and copying and pasting multiple times.

* like to only execute one single command to execute all of your backups from a single, static configuration file.

Then suisave is for you. Additionally, suisave is simple enough that even my mom uses it.

> [!NOTE]
> The name _suisave_.
> I am obsessed with VTubers, and put references everywhere I can. This is a reference to my kamioshi [Hoshimachi Suisei](https://www.youtube.com/channel/UC5CwaMl1eIgY8h02uZw7u8A).

## Support and Requirements

**Supported Operating Systems**

* Linux (any with pip)
* Arch Linux based (through the AUR)
* NO MacOS
* NO Windows

> [!NOTE]
> The library contains one specific subprocess call to `lsblk` in interactive mode that will break in MacOS. There are future plans to support it though.
>
> No Windows support, and no current plans to do so.

**Requirements**
 
* Python >= 3.11
* rsync

## Quick start

Get up and runninbg in under 5 minutes.

### Installation

**Arch-Based Linux Distributions (Recommended)**

Use any AUR helper like `paru` or `yay`.
```bash
paru -S suisave
```

**Any other Linux distribution: From PyPI (Recommended)**

Simply enter a virtual environment and run
```bash
pip install suisave
``` 

For the full-screen local backup TUI, install the optional `tui` extra:
```bash
pip install "suisave[tui]"
```

**Local installation from source (Bleeding edge)**

In case new features are not avaiable on the PyPI build, you can directly clone and install the package into your virtual environment.
```bash 
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

### Optional Post Install

Run the following command: 
```bash
suidesk
```
This will create a `suisave.desktop` under `~/.local/share/applications/` for you to find with your preferred application launcher.

### Minimal Coniguration file

Create the file `~/.config/suisave/comet.toml` and add the following information

```toml
[drives.MYLABEL]
uuid = "XXXXXXXXXXXXXXX"


[[jobs.backup]]
name = "general"
sources = ["/home/USERNAME"]
drives = ["MYLABEL"]
```
> [!NOTE]
> You can retrieve the UUID of your disk with
> ```
> lsblk -o NAME,LABEL,UUID
> ```

### Running

Connect and mount the registered drive in the configuration file, and run

```bash
suisave run
```

For the non-TUI terminal dashboard plus shell summary table:

```bash
suisave run --no-interactive
```

Your files will be synced to `/path_to_disk/backups/hostname-machine-id/`

## Detailed Configuration and Usage

The backups are configured through a `.toml` file under `~/.config/suisave/comet.toml`. See the [commented example template](./templates/comet.toml).

In summary, suisave requires two things
1. A table of drives that you can use, each identified by their UUID
2. Rsync jobs to do

once that is set up, simply run
```
suisave run
```

The default local runner uses the Textual TUI.
If you want the non-interactive terminal dashboard and shell summary output instead, run `suisave run --no-interactive`.

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

For local-drive backups, `suisave` automatically adds `--exclude=.venv/` unless
that exclude is already present in the job flags.

There are two types of jobs: backups and custom. 

**Backup Jobs:**

Backup jobs are a subset of the custom jobs where some defaults are assumed

1. The target base is by default `backups/hostname-machine-id`. 
The main idea is to have an identical copy of your home directory with redundancy backed up. This way you can have multiple computer backed up to the same drive.

These options can be changed via the `tg_base` and `pc_name` in the `[global]` table

2. The rsync flags are taken from the `[global]` table.
By default local backups also skip `.venv/` directories.

**Custom Jobs:**

These are general and require you to provide all fields. They exist just in case you need more flexibility.
Local custom jobs also get the `.venv/` exclude added automatically.

## Remote Sync

Remote sync is separate from the mounted-drive backup flow. Use it when you want to sync a project-local directory to a remote machine over SSH without storing that config in `~/.config/suisave/comet.toml`.

Use a local config file instead. See [templates/suisave.remote.toml](./templates/suisave.remote.toml).

### Remote config example

```toml
[global]
default_rsync_flags = ["-azvh"]
default_mode = "push"

[remotes.home_server]
host = "storage.example.com"
user = "backup"
port = 22
base_path = "backups/projects"
identity_file = "./.secrets/suisave_ed25519"
ssh_options = ["StrictHostKeyChecking=accept-new"]

[remotes.offsite_box]
host = "offsite.example.com"
user = "backup"
port = 22
base_path = "mirror/projects"
identity_file = "./.secrets/suisave_ed25519"

[[jobs.sync]]
name = "project"
sources = ["./"]
remotes = ["home_server", "offsite_box"]
mode = "push"
delete = true
```

### Remote usage

Push local files to the remote host:

```bash
suisave remote sync --config ./suisave.remote.toml --push
```

Pull remote files into the current machine:

```bash
suisave remote sync --config ./suisave.remote.toml --pull
```

Let `suisave` choose the direction from the newest local or remote mtime:

```bash
suisave remote sync --config ./suisave.remote.toml --most-recent
```

Aliases are also supported:

```bash
suisave remote sync --config ./suisave.remote.toml --local
suisave remote sync --config ./suisave.remote.toml --remote
```

Run only one named job:

```bash
suisave remote sync --config ./suisave.remote.toml --name project --push
```

Run an ad hoc sync from the current directory without using `[[jobs.sync]]`:

```bash
suisave remote sync --config ./suisave.remote.toml --source "$PWD" --push
```

Choose one remote target explicitly:

```bash
suisave remote sync --config ./suisave.remote.toml --pull --target home_server
```

### Remote config notes

* `[remotes.<label>]` replaces `[drives]` for this mode.
* `identity_file` is resolved relative to the remote config file.
* Relative job `sources` are resolved from the current working directory.
* `base_path` belongs to each remote target and defines the remote-side root path.
* Jobs reference one or more remotes with `remotes = ["label"]`.
* `default_mode` can be `push`, `pull`, or `most_recent`.
* `--most-recent` compares the newest local and remote mtimes for each source pair.
* If `--most-recent` sees effectively equal mtimes, it aborts and asks for an explicit direction.
* `push` defaults to `--delete` unless overridden by `delete = false` or `--no-delete`.
* `push` can fan out to several remotes, but `pull` and `--most-recent` require a single selected remote when a job references many.
* The remote host needs standard shell tools for `--most-recent`: `sh`, `find`, `sort`, `head`, and `stat`.
