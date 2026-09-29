# Working on this repo

## The default branch is the release

The owner installs and updates this mod straight from GitHub: RimSort clones the
default branch (`main`) into RimWorld's Mods folder and pulls it in place. There
is no separate release step, so **every commit pushed to `main` is what the game
loads next**.

- Push finished work straight to `main`. Nothing half-done: each commit must
  load and play as-is.
- The compiled assemblies are committed (`1.5/Assemblies`, `1.6/Assemblies`).
  Rebuild with `bash Tools/build.sh` and commit the DLLs in the same commit as
  any C# change - a stale DLL is what players get.
- Stamp the build number before every commit:
  `python3 Tools/stamp_version.py`. It writes `<modVersion>` and a
  `Build x.y` line at the top of the description in `About/About.xml`, as
  `series.<commit count after this commit>` - the same number
  `Tools/package.sh` puts on a zip. `Tools/validate.py` fails while it is stale.
  Never leave it at a placeholder like `0.9.0-dev`.
- Before pushing: `python3 Tools/validate.py`, `bash Tools/check_api.sh`,
  `bash Tools/build.sh`.
- Keep `packageId` unchanged; saves and RimSort key on it. The display
  `<name>` is "SloppyMods Entertaining Ideas".
- Everything in the repo root lands in the Mods folder. RimWorld reads
  `About/`, `LoadFolders.xml`, `1.5/`, `1.6/`, `Defs/`, `Patches/`,
  `Textures/`, `Sounds/`, `Languages/`; `Source/`, `Tools/`, `docs/` and
  `Workshop/` are ignored by the game. Do not add anything at the root that
  RimWorld would try to load by mistake.
- `About/Preview.png` is the banner in `Source/Promo/`; re-render it
  (`NODE_PATH=$(npm root -g) node Source/Promo/render_preview.js`) when art it
  shows changes. Nothing else writes that file.
- A zip for the Steam Workshop or manual testing still comes from
  `bash Tools/package.sh` when asked.
- Every push to `main` also becomes a GitHub Release, `v<modVersion>`, with
  that zip attached (`.github/workflows/release.yml`). RimSort's GitHub Mods
  panel reads versions from releases and installs the release zip, so the
  stamp must be right before pushing - the workflow checks it.

## Standing preferences

- No Harmony, no hard dependencies, no new research projects. Other mods
  (Dubs Bad Hygiene, Vanilla Furniture Expanded) are optional, reached by
  reflection or `PatchOperationFindMod`.
- Separate 1.5 and 1.6 assemblies (`RW16` define), built against Krafs'
  reference packages.
- Art is generated (`Source/TextureGen/`). For art changes, show prototypes
  or before/after comparisons and get the owner's approval per item before
  replacing anything.
- Licence is CC0, for this and every SloppyMods mod.
- Replies to the owner: concise summaries; attach the build zip when they will
  test in game.
