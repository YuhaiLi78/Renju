# Renju

This repository contains a playable Renju implementation in Python, plus a design
specification in [DESIGN.md](DESIGN.md).

## Run the game

```bash
python -m renju.cli
```

Each completed game appends a summary to `history.log` in the current directory.

## Run the GUI

```bash
python -m renju.gui
```

The GUI supports the full opening rules, including color swap and candidate move
selection, and automatically saves each completed game to `history.log`.
