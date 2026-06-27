"""Enables `python3 -m arcturus ...` during development."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
