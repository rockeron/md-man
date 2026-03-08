# Markdown TUI Viewer Design

**Date:** 2026-03-08

**Goal:** Build a Textual-based TUI that loads a root path from the CLI, shows the full recursive markdown file tree, and renders selected documents with optional Korean translation.

## Scope

- Launch with `md-man <root-path>`
- Recursively show the full directory tree under the root
- Only `.md` files are selectable and openable
- Support mouse clicks and keyboard navigation
- Render markdown in the main document pane
- Start with an instructional empty state before a file is selected
- Toggle Korean translation with `t`

## Non-Goals

- In-app path picker for v1
- Persistent translation cache across sessions
- Editing markdown files
- Multi-language translation target selection

## Recommended Architecture

The app uses `Textual` for the TUI shell and event handling. The left pane is a custom markdown-aware tree view derived from `DirectoryTree` behavior. The right pane is a markdown rendering view that swaps between an instructional empty state, rendered source markdown, and rendered translated markdown.

Translation is isolated behind a `Translator` interface. The first provider uses `deep-translator` with `GoogleTranslator(source="auto", target="ko")`. This keeps the UI independent from the provider and makes it straightforward to replace later if reliability becomes an issue.

## Project Structure

```text
src/md_man/
  __init__.py
  main.py
  app.py
  scanner.py
  translator.py
  widgets.py
  app.tcss
tests/
  test_scanner.py
  test_translator.py
  test_app.py
```

## UX Flow

1. User runs `md-man /path/to/docs`
2. App validates the root path
3. Left pane loads the full recursive tree for the root
4. Right pane initially shows guidance: `왼쪽 트리에서 Markdown 파일을 선택하세요`
5. User selects a markdown file with mouse or keyboard
6. Right pane renders the markdown document
7. User presses `t` to toggle Korean translation for the current document

## Layout

- Header: current root path and transient status text
- Left pane: recursive file tree
- Right pane: markdown viewer or empty/error state
- Footer: key hints and current mode

## Tree Rules

- Walk the root path recursively
- Keep directory nodes so the hierarchy remains visible
- Mark only `.md` files as selectable
- Ignore non-markdown files in the visible tree
- Support expand/collapse with keyboard and mouse

## Key Bindings

- `Up` / `Down`: move selection
- `Left` / `Right`: collapse or expand directory nodes
- `Enter`: open selected markdown file
- `Tab`: switch focus between tree and viewer
- `j` / `k`: vim-style movement
- `g` / `G`: jump to top or bottom
- `r`: rescan the root path
- `t`: toggle Korean translation for the open document
- `?`: open help overlay
- `q`: quit

## State Model

The app should track:

- `root_path`
- `selected_file`
- `source_markdown`
- `translated_markdown`
- `show_translation`
- `status_message`
- `last_error`

Translation results are cached in memory by absolute file path for the current session. If a translation exists, `t` switches views without another network request.

## Error Handling

- Invalid root path: show a full-screen error state
- No markdown files found: show an empty-state message in the viewer pane
- File read failure: keep the app running and show the error in the viewer pane
- Translation failure: preserve the current source view and show the error in the status area

## Testing Strategy

- Unit test recursive markdown discovery and filtering
- Unit test translation toggle state and caching behavior
- App-level tests for initial empty state, file opening, and key handling
- Use a stub translator in tests instead of making network calls

## Risks

- `deep-translator` is convenient but not a durable contract. The provider can break when upstream behavior changes.
- Large markdown documents may need chunking if provider request size becomes an issue.
- Terminal mouse behavior can vary slightly across emulators, so app-level tests should focus on Textual event handling rather than emulator specifics.

## Future Extensions

- Add an in-app root-path switcher
- Persist translation cache
- Add search within tree and viewer
- Support frontmatter-aware previews
