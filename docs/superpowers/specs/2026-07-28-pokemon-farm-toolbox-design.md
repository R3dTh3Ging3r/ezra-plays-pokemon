# Pokemon Farm Toolbox Design

## Goal

Provide a Windows-local toolbox that automates repeatable farming in Pokemon Generation 2 and Generation 3 games while keeping every original game file and save untouched.

## Scope

- Generation 3: Ruby, Sapphire, Emerald, FireRed, and LeafGreen through PokeBot Gen3.
- Generation 2: Gold, Silver, and Crystal through BizHawk and Pokebot.
- Automated actions may include encounters, catching, healing, item collection, breeding, and save progression when a selected bot mode supports them.
- Every run uses an isolated working copy and makes timestamped save backups before mutation.

## Architecture

The workspace will contain a launcher-oriented `farm-toolbox` directory. It manages profiles and delegates game automation to the appropriate upstream bot.

```text
farm-toolbox/
  source-games/             # Read-only references or user-supplied copies; never modified
  profiles/
    <profile-name>/
      game/                 # Per-profile ROM copy
      bot-profile/          # Per-profile PokeBot Gen3 profile and current_state.ss1
      save/                 # Per-profile Gen 2 working save
      backups/              # Timestamped save/state snapshots
      logs/                 # Bot and launcher logs
      profile.json          # Game, bot, paths, mode, and safety configuration
  tools/
    pokebot-gen3/           # Gen 3 upstream bot installation
    bizhawk/                # Gen 2 emulator installation
    pokebot-gsc/            # Gen 2 upstream bot installation
  scripts/                  # Preflight, profile creation, backup, launch, and recovery helpers
```

The existing `Pokemon Roms/` directory is user data. It will not be moved, edited, or committed. Profiles will copy only a user-selected game file into their own `game/` directory.

## Profile Lifecycle

1. Create a profile from one supported game file. A Gen 3 profile is provisioned once through PokeBot's native profile screen; an existing mGBA save state can be imported there if needed.
2. Validate the file extension, known game family, profile paths, and free disk space.
3. Copy the game file and keep all mutable state in the profile; never open the source file for write access.
4. Make a timestamped backup of the working Gen 2 save or Gen 3 PokeBot `current_state.ss1` before each bot run.
5. Launch the appropriate bot against the profile copy with the selected mode.
6. Record the launch configuration and return a clear recovery command that restores the latest or a named backup.

## Bot Boundaries

| Game family | Primary tool | Primary jobs |
| --- | --- | --- |
| Generation 3 | PokeBot Gen3 | Level grinding, encounter farming, fishing, breeding, shiny hunting, and supported item collection |
| Gold / Silver / Crystal | BizHawk + Pokebot | Encounter, fishing, starter, static, and other supported Gen 2 farming loops |

The launcher will expose only modes the underlying bot declares available for that selected game. It will refuse to launch a mode without a valid save and profile copy.

## Data Safety and Recovery

- Source games and source saves are never modified.
- No profile shares a save, PokeBot profile, or bot state with another profile.
- Backups are copied before every automated session and retained until explicitly removed by the user. For Gen 3, the recoverable state is PokeBot's native `current_state.ss1`.
- A failed preflight or bot exit leaves the working save in place and reports its path; it does not attempt destructive cleanup.
- The user can manually inspect, pause, or stop a bot at any time.

## Verification

The implementation will verify:

1. A profile creation leaves the source game file hash unchanged.
2. A pre-run backup is created before the bot process launches.
3. The Gen 3 tool recognizes a selected supported profile.
4. The Gen 2 emulator and bot open a selected supported profile without using the source game location.
5. Restoring a profile backup replaces only that profile's working save or Gen 3 state.

## Out of Scope

- Downloading, distributing, or modifying game ROMs.
- Generation 1, DS, 3DS, Switch, or online-game automation.
- A general vision-language AI player; deterministic farm bots are preferred for reliability and predictable saves.
