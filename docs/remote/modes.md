# Remote Sync Modes

## `--push`

Local is the source of truth.

Data flow:

```text
local -> remote
```

Use this when the remote copy should match what you have on the current machine.

This is the closest match to an old `send` script. You make local changes, decide that local is authoritative, and publish that state to the remote side.

## `--pull`

Remote is the source of truth.

Data flow:

```text
remote -> local
```

Use this when the local copy should be replaced by the remote state.

This is the closest match to an old `get` script. It is useful for restoring a working copy on a new machine or replacing local contents with the version already stored remotely.

## `--most-recent`

`suisave` compares the newest local and remote mtimes for each source pair.

Behavior:

- if local is newer, it chooses `push`
- if remote is newer, it chooses `pull`
- if remote is missing, it chooses `push`
- if timestamps are effectively equal, it aborts

This is intentionally conservative. It is not conflict resolution or bidirectional merge logic.

It is best understood as a convenience heuristic, not as a sync algorithm that can reconcile divergent histories.

If you already know which side should win, prefer `--push` or `--pull` directly. That keeps the command easier to reason about and easier to repeat later.

## Aliases

- `--local` is an alias for `--push`
- `--remote` is an alias for `--pull`

The aliases exist because some people think in terms of transfer direction, while others think in terms of which side is the source of truth.

## Delete behavior

- `push` defaults to `--delete`
- `pull` does not force `--delete`
- job `delete = true` or `delete = false` can override defaults
- CLI `--delete` and `--no-delete` override both job and mode defaults

This separation matters because direction and delete behavior are related but not identical. Sometimes you want to pull from remote without deleting local-only files, and sometimes you want a strict push that makes the remote tree match local exactly.

Keeping them separate makes the command line more explicit and reduces unpleasant surprises.
