# Pokemon Farm Toolbox

Pokemon Farm Toolbox creates isolated Gen 3 farming profiles. The source ROM is
read only: each profile receives its own working copy and profile-local runtime
state.

Install the package, then supply paths explicitly for every profile operation.
The `create` command has no default ROM or source directory.

```powershell
pokemon-farm create --name emerald-level-grind --game emerald --rom C:\ROMs\PokemonEmerald.gba --profiles-root C:\PokemonFarm\profiles
```

Use the profile manifest to inspect its source integrity and native PokeBot
runtime-state provisioning. An unprovisioned native state is reported without
being a source-hash error.

```powershell
pokemon-farm verify --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json
```

Back up the native runtime state after PokeBot has provisioned it:

```powershell
pokemon-farm backup --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json --label before-level-grind
```

Restore requires both the manifest and an explicit backup path. The backup must
be inside that profile's `backups` directory.

```powershell
pokemon-farm restore --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json --backup C:\PokemonFarm\profiles\emerald-level-grind\backups\20260728T200000Z-before-level-grind.ss1
```

## PokeBot Gen3

Keep the upstream PokeBot checkout and its virtual environment outside Git
tracking. The toolbox never downloads, supplies, or relocates a game image; use
only a game dump you are legally entitled to use.

```powershell
git clone https://github.com/40Cakes/pokebot-gen3.git farm-toolbox/tools/pokebot-gen3
py -3.13 -m venv farm-toolbox/tools/pokebot-gen3/.venv
farm-toolbox/tools/pokebot-gen3/.venv/Scripts/python.exe farm-toolbox/tools/pokebot-gen3/pokebot.py
```

PokeBot installs its declared dependencies and libmGBA on its first run. For
one-time native provisioning, stage the validated ROM copy and open PokeBot:

```powershell
pokemon-farm provision-gen3 --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json --tool-root C:\PokemonFarm\tools\pokebot-gen3
```

In PokeBot, create the profile with the same name (`emerald-level-grind`),
select the staged profile-named ROM, and begin a new game or use **Load Existing
Save** for an mGBA state you own. Close PokeBot normally, then copy its native
profile back into profile-owned storage:

```powershell
pokemon-farm sync-gen3 --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json --tool-root C:\PokemonFarm\tools\pokebot-gen3
```

Future launches validate the tool, source hash, metadata, and native state;
create a pre-launch state backup; stage only profile-owned copies; and sync a
cleanly exited run back to the selected profile:

```powershell
pokemon-farm launch-gen3 --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json --tool-root C:\PokemonFarm\tools\pokebot-gen3 --mode "Level Grind"
pokemon-farm verify --profile C:\PokemonFarm\profiles\emerald-level-grind\profile.json
```

If PokeBot exits nonzero, the toolbox reports the retained upstream profile
path and does not sync or delete that recoverable state.
