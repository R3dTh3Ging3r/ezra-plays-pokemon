# Ezra Plays Pokémon

## What it is

Ezra Plays Pokémon is a local, developer-first automation foundation for responsibly progressing through Pokémon games and running long-lived farming jobs. Version 0.1 is a FireRed-only foundation built around auditable, ordinary controller input.

## Status

This repository is at the public-foundation stage. It pauses safely when a state is uncertain, rather than guessing or continuing with uncontrolled inputs.

## Legal and safety boundary

Users must supply their own legally obtained game files. This repository does not include ROMs or save files, savestates, copyrighted screenshots, credentials, tool installations, or personal paths. Automation remains local-only after setup and never distributes games, edits saves, generates items, manipulates RNG, or writes gameplay data directly.

## Current capability

The current package provides an isolated Gen 3 farming-profile toolbox and safe profile, backup, and PokeBot Gen3 handoff instructions. It is not yet an end-to-end game-playing autopilot.

## Roadmap

The approved [design and roadmap](docs/superpowers/specs/2026-07-30-ezra-plays-pokemon-design.md) describes the path from the FireRed control foundation through story progression, collection, breeding, local trade, and later supported games.

## Quick start for developers

Use Python 3.13 or newer, then work inside the toolbox:

```powershell
cd farm-toolbox
py -3.13 -m pytest tests -q
```

The toolbox documentation explains its safe profile workflow. Keep your game assets and runtime tools outside source control.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening an issue or pull request. Contributions must preserve the local-only, safety-first boundary.
