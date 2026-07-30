# Ezra Plays Pokémon — Design and Roadmap

## Purpose

Ezra Plays Pokémon is a local, developer-first automation framework for responsibly progressing through Pokémon games and operating long-running farming jobs. Its first target is Pokémon FireRed. The ultimate project goal is a verified living-dex operation: complete the story, gather obtainable Pokémon and items, retain every obtainable evolutionary stage, breed and train capable teams, hunt shinies, and later coordinate owned local game profiles through an auditable bank.

The project is intentionally not a ROM distributor, save editor, RNG manipulator, or item generator. Users must supply their own legally obtained game files. All gameplay actions that affect a game use ordinary controller input.

## Guiding principles

- Operate entirely locally after setup. No paid API, cloud model, or Internet connection is required during play.
- Prefer reliable, game-aware automation over screen-only guessing. The controller may read emulator memory for state such as maps, party data, battles, inventory, and event progression, but it never fabricates in-game resources or changes gameplay data directly.
- Protect player progress. Back up before risky operations, verify hashes and outputs before replacement, log decisions, and pause rather than guessing when recovery is uncertain.
- Build reusable capabilities rather than a one-off keystroke script. Navigation, battle decisions, healing, shopping, saving, farming handoffs, and recovery have clear interfaces and tests.
- Keep all personal and copyrighted material out of public source control: ROMs, saves, savestates, screenshots containing game assets unless their rights are confirmed, API credentials, and local absolute paths.

## First-release scope

The first release is FireRed only and developer-first. It accepts a prepared, user-owned save and aims to advance the story safely, including automatic level grinding at deliberately selected locations. It is allowed to stop at rare uncertainty checkpoints and request human intervention; zero-touch completion is a later quality target.

No polished one-click installer is required for this release. Documentation and repeatable scripts are required.

## Architecture

### Orchestrator

The orchestrator owns a protected game profile and runs one small objective at a time. Objectives have explicit preconditions, actions, success criteria, retry/recovery paths, and a pause condition. Examples include reaching a named location, preparing for a gym, defeating a gym, obtaining a required item, or returning to a safe healing point.

### Observer

The observer reads supported emulator memory and captures screen frames as corroborating evidence. It exposes stable normalized state: game identity and version, map/location, player position, party and storage summaries, battle state, dialogue/menu state, bag/money, badges, known events, and save state. The observer never writes game memory.

### Story controller

The story controller selects and executes objectives through a goal graph. It uses map-aware navigation and explicit recovery rules instead of a long fixed input recording. It asks for human help when a state is unknown, a required input cannot be verified, or a retry budget is exhausted.

### Battle controller

The battle controller makes explainable choices from accessible state: legal moves, PP, types, HP, status, held items, party alternatives, healing resources, and a goal-specific risk policy. It uses normal button input only.

### Farm-worker adapter

The adapter delegates repeatable encounter, leveling, catch, and shiny-hunting jobs to supported specialist modes such as PokéBot Gen3. A handoff occurs only from a validated safe state. On completion, the adapter checks the native save, compares the expected outcome, records the job, and returns control to the story controller.

### Safety and audit services

Profiles, game-native save backups, hashes, run logs, diagnostic snapshots, and a transfer ledger protect each operation. On an unsafe or unexpected condition, the system releases inputs, records context, preserves the latest known-good state, and pauses.

### Optional local-model plug-in

The core requires no language or vision model. An optional local provider may later suggest high-level objectives or help interpret unfamiliar text. It receives a constrained summary of state and can propose plans only; the orchestrator validates plans and remains the only component allowed to actuate the emulator.

## Data flow

1. A user selects a protected, user-owned FireRed profile and a starting objective.
2. The observer validates the game and current state; the safety service creates a recoverable checkpoint.
3. The story controller chooses the next verified action block.
4. The executor sends normal controller inputs and the observer confirms the expected state change.
5. When preparation is required, the orchestrator creates a farm job, delegates it, validates the returned save, and resumes the story objective.
6. Every material action, outcome, backup, capture, evolution, and later trade is recorded in an audit log.
7. Uncertain or invalid states halt safely for human review rather than triggering uncontrolled inputs.

## Roadmap

### Phase 0 — Public project foundation

- Publish the `ezra-plays-pokemon` repository with a welcoming README, contributor guidance, legal-use rules, local configuration examples, supported-game table, and honest status labels.
- Publish only source, tests, documentation, and synthetic fixtures. Ignore ROMs, saves, savestates, credentials, tool installations, and personal data.
- Retain the existing protected Gen 3 profile/backups and specialist farm integration as local development tools.

### Phase 1 — FireRed control foundation

- Establish a supported emulator bridge for observing FireRed and supplying controller input.
- Add a validated profile format, durable logging, checkpointing, a pause mechanism, and a deterministic mock-emulator test harness.
- Begin from a prepared legal save, not a fresh boot flow.

### Phase 2 — Early-game vertical slice

- Implement navigation, dialogue/menu handling, battle choices, healing, shopping, ordinary game saves, and recovery.
- Demonstrate a complete loop from a controlled early-game save through preparation for the first gym, farming if required, defeating it, and returning to a confirmed safe state.
- Treat any unresolved state as a supervised checkpoint.

### Phase 3 — FireRed story completion

- Expand the objective graph badge by badge through the Elite Four.
- Generalize recurring capabilities rather than copying per-route keypress recordings.
- Instrument every failure, improve recovery rules from recorded data, and earn progressively longer unattended runs.

### Phase 4 — FireRed collection operation

- Maintain a collection ledger for all Pokémon obtainable in FireRed, including species, location/method, ownership status, evolutionary stage, and gaps.
- Plan and perform capture, item collection, evolution, encounter farming, and safe shiny-hunting jobs.
- Preserve one owned instance of every obtainable evolutionary stage where game rules allow it.

### Phase 5 — Breeding and strong teams

- Automate safe daycare and breeding workflows with user-selected goals.
- Add transparent evaluation and training plans for practical battle teams: moves, level, nature, ability, and resource requirements, subject to what is obtainable through normal gameplay.

### Phase 6 — Local trade and bank

- Coordinate owned local emulator profiles only after link behavior is verified.
- Execute in-game trades using supported link capabilities and keep a durable ledger containing source, destination, Pokémon identity, timestamp, and verification result.
- Create a backed-up local bank profile; never silently overwrite it.

### Phase 7 — Expansion and portability

- Extend the common interfaces to Emerald, Ruby, Sapphire, and LeafGreen before considering the distinct Gen 2 architecture.
- Add manual `.sav` import/export workflows so a user may safely move their own game-native save between a phone and the PC operation. Transfers require an explicit user action, a closed emulator at both ends, integrity checks, and retained backups.
- Treat cross-device RetroArch Netplay/link trading as research only. It is not a dependency or promised feature: mGBA currently documents same-computer link support and lists networked link-cable support as planned.

### Phase 8 — Gold, Silver, and Crystal

- Build a separate compatible adapter for the Gen 2 emulator and save format after the Gen 3 orchestration interfaces are proven.
- Reuse only game-agnostic abstractions; do not assume Gen 3 memory maps, save semantics, or link behavior apply.

## Error handling and recovery

- Validate game identity, supported version, emulator readiness, and profile integrity before any automated input.
- Use bounded action blocks with observable expected outcomes; retry only when the state proves the retry is safe.
- Stop on unexpected map changes, menus, dialogue, battle conditions, input loss, corrupted/changed saves, unsupported ROM revisions, or a failed worker handoff.
- Preserve diagnostic evidence and the last known-good checkpoint. Never erase a player save, a farm result, or a bank state as part of recovery.
- Require a manual confirmation for portable-save imports and exports. The tool must show source and destination hashes before replacement.

## Testing and evidence

- Unit test state normalization, objective preconditions/outcomes, battle policies, transfer and backup safeguards, and farm-worker contracts with synthetic data.
- Use mocked memory and synthetic screen traces in the public test suite; do not publish copyrighted game assets or personal save data.
- Use optional end-to-end smoke tests only against a developer's own legal FireRed setup.
- Gate each roadmap phase on a reproducible demonstration, logs, and defined acceptance tests. Claims of game completion or feature support must cite passing evidence.

## Explicit non-goals for the first release

- A polished graphical installer or consumer-friendly app.
- Fresh-game, zero-touch, no-pause completion.
- Full Pokédex/living-dex fulfillment, breeding, multi-instance trade, Gen 2 support, or phone integration.
- ROM distribution, cloud inference requirements, account/API-key collection, save editing, item creation, or RNG manipulation.
