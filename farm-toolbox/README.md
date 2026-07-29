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
