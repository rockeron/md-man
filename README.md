# mark4

`mark4` is a Textual-based TUI for browsing markdown files under a root
directory, reading them in a two-pane layout, and translating the selected
document into Korean.

## Features

- Recursive markdown file tree
- Mouse and keyboard navigation
- Markdown rendering with scrolling
- Chunk-by-chunk Korean translation updates
- Persistent translation cache across app runs
- In-app status messages for scan, translation, cache, and errors

## Requirements

- Python 3.12+

## Install

Install from PyPI:

```bash
python3 -m pip install mark4
```

## Development Setup

For local development:

```bash
uv sync --extra dev
```

## Run

```bash
mark4 /path/to/markdown/root
```

You can also use:

```bash
PYTHONPATH=src .venv/bin/python -m mark4 /path/to/markdown/root
```

Public-safe options:

```bash
mark4 --no-translate /path/to/markdown/root
mark4 --no-cache /path/to/markdown/root
mark4 --clear-cache /path/to/markdown/root
```

## Key Bindings

- Mouse click: select files and folders
- `Up` / `Down`: move tree selection
- `Left` / `Right`: collapse or expand directories in the tree
- `Enter`: open the selected markdown file
- `r`: rescan the root path
- `t`: first show the translation privacy warning, then toggle Korean translation
- `?`: show help text in the status line
- `q`: quit

## Translation Behavior

- On the first translation attempt in a session, `mark4` warns that document
  content will be sent to an external translation service and may be stored in
  the local cache. Press `t` again to continue.
- Press `t` on an open document to switch the right pane into translation mode.
- Translation runs chunk by chunk and the viewer updates as translated chunks
  arrive.
- Code fences and inline code stay in the original source form.
- If a chunk translation returns no text, the app falls back to the original
  chunk instead of crashing.
- Press `t` again to return to the source markdown.
- Use `--no-translate` to disable all external translation requests.

## Translation Cache

Translated documents are cached in a global user cache directory so they can be
reused after restarting the app.

- macOS: `~/Library/Caches/mark4/translations/`
- Linux: `~/.cache/mark4/translations/`
- Windows: `%LOCALAPPDATA%/mark4/translations/`

Cache validity is based on:

- absolute file path
- source file content hash
- translator/provider identity

If the markdown file changes, the previous cached translation is ignored and a
new translation is generated.

- Use `--no-cache` to disable persistent cache reads and writes.
- Use `--clear-cache` to remove the persistent translation cache directory.

## Status Messages

The status line reports the current document path and important events such as:

- invalid root path
- no markdown files found
- rescan complete
- translation progress such as `번역 중 2/8`
- translation errors

## Known Limitations

- Translation still depends on the external translator provider and network
  availability.
- Cached translations are not pruned automatically yet.
- Large markdown trees may still take time to render because the full file tree
  is built in the TUI.
