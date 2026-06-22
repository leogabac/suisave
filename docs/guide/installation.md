# Installation

## Requirements

- Linux (sorry)
- Python 3.11 or newer
- `rsync`

For interactive drive discovery, `lsblk` also needs to be available.

The runtime itself is small. Most of the real work is still done by `rsync`.

## Install from PyPI

```bash
pip install suisave
```

The base install is enough for the non-Textual CLI flow, including:

- `suisave config ...`
- `suisave remote sync ...`
- `suisave run --no-interactive`

If you want the Textual transfer dashboard used by the default `suisave run`,
install the `tui` extra:

```bash
pip install "suisave[tui]"
```

## Install on Arch-based distributions

If you are on an Arch-based system, `suisave` is also available through the AUR (no virus included, I promise).

With a helper such as `paru`:

```bash
paru -S suisave
```

Or with `yay`:

```bash
yay -S suisave
```

## Install from source

```bash
git clone https://github.com/leogabac/suisave.git
cd suisave
pip install .
```

Installing from source is useful when you want the latest changes in this repository before they land in a packaged release.

If you want the Textual transfer dashboard from source as well:

```bash
pip install ".[tui]"
```

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

If you did not install the `tui` extra, prefer running `suisave run --no-interactive`
from the shell instead.
