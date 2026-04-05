# Installation

## Requirements

- Linux
- Python 3.11 or newer
- `rsync`

For interactive drive discovery, `lsblk` also needs to be available.

The runtime itself is small. Most of the real work is still done by `rsync`, so the main requirement is not a large Python stack but a machine where the expected system tools exist and behave normally.

## Install from PyPI

```bash
pip install suisave
```

## Install on Arch-based distributions

If you are on an Arch-based system, `suisave` is also available through the AUR.

With a helper such as `paru`:

```bash
paru -S suisave
```

Or with `yay`:

```bash
yay -S suisave
```

This is usually the most convenient option if you already manage user-installed CLI tools through the AUR.

## Install from source

```bash
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

Installing from source is useful when you want the latest changes in this repository before they land in a packaged release.

## Install docs tooling

If you want to work on the documentation site:

```bash
pip install -e ".[docs]"
```

Then run:

```bash
mkdocs serve
```

That starts a local documentation server, usually at `http://127.0.0.1:8000/`.

## Optional desktop entry

To create the launcher entry:

```bash
suidesk
```

This is only for the local-backup mode. It creates a desktop launcher that runs `suisave run`.
