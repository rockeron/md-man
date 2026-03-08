# md-man

`md-man` is a Textual-based TUI for browsing markdown files under a root
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
- `uv`

## Setup

```bash
uv sync --extra dev
```

## Run

```bash
./md-man /path/to/markdown/root
```

You can also use:

```bash
PYTHONPATH=src .venv/bin/python -m md_man /path/to/markdown/root
```

## Key Bindings

- `Up` / `Down`: move selection
- `Left` / `Right`: collapse or expand directories
- `Enter`: open the selected markdown file
- `Tab`: switch focus between the tree and the document view
- `j` / `k`: vim-style up / down movement
- `g` / `G`: jump to top / bottom
- `r`: rescan the root path
- `t`: toggle Korean translation
- `?`: show help text in the status line
- `q`: quit

## Translation Behavior

- Press `t` on an open document to switch the right pane into translation mode.
- Translation runs chunk by chunk and the viewer updates as translated chunks
  arrive.
- Code fences and inline code stay in the original source form.
- If a chunk translation returns no text, the app falls back to the original
  chunk instead of crashing.
- Press `t` again to return to the source markdown.

## Translation Cache

Translated documents are cached in a global user cache directory so they can be
reused after restarting the app.

- macOS: `~/Library/Caches/md-man/translations/`
- Linux: `~/.cache/md-man/translations/`
- Windows: `%LOCALAPPDATA%/md-man/translations/`

Cache validity is based on:

- absolute file path
- source file content hash
- translator/provider identity

If the markdown file changes, the previous cached translation is ignored and a
new translation is generated.

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
- Partial translation rendering may look rough while a long document is still
  in progress because the markdown view is updated incrementally.
