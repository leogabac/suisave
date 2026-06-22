# Changelog

This file was written by codex.

All notable changes to this project will be documented in this file.

This repository did not keep a clean tagged release boundary for `0.3.1`.
For changelog purposes, `0.3.1` is reconstructed as commit `2c866dd`
(`added alternate host`), which is the first commit where `pyproject.toml`
already reports `0.3.2`.

## [0.3.2] - 2026-06-22

### Changed

- Removed the local config editor TUI exposed as `suisave config tui`.
- Kept the transfer runner TUI for `suisave run` intact.
- Cleaned up CLI and docs so the local config workflow points back to file-based
  editing plus drive management commands.
- Aligned the CLI version string with the package version at `0.3.2`.
- Local-mode commands now honor `SUISAVE_CONFIG_PATH`, falling back to
  `~/.config/suisave/comet.toml` when the environment variable is unset.

### Fixed

- Removed a stale `config_tui` export that broke imports after the config editor
  TUI was deleted.
- Clarified the local-config docs so they describe the environment-variable
  override instead of treating the path as always fixed.

## [0.3.1] - reconstructed from `v0.3.0..2c866dd`

### Added

- Added remote sync support with a dedicated `suisave remote sync` command and a
  separate remote TOML config model.
- Added `most_recent` remote sync mode based on local and remote mtimes.
- Added multi-remote target support, jump-host support, and alternate-host
  selection for remote sync runs.
- Added a Textual run dashboard for transfer monitoring.
- Added a richer local config command family, including config initialization,
  inspection, drive listing, drive detection, and interactive drive selection.
- Added a documentation site with MkDocs, guide pages, remote usage docs, and
  GitHub Pages deployment.

### Changed

- Reworked the project from a local-drive-only backup tool into two parallel
  flows: mounted-drive backups and SSH remote sync.
- Expanded README, templates, and docs to describe the local and remote config
  models.
- Updated packaging metadata, optional dependencies, and console entry points to
  support the newer CLI surface.

### Fixed

- Fixed remote pull target mapping.
- Fixed a `suidesk` desktop-entry issue.
- Cleaned up gitignore, docs, and various CLI/config rough edges during the
  remote-sync and TUI work.

## [0.3.0]

### Changed

- Tagged release `v0.3.0`.
