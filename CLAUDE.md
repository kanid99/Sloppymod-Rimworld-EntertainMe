# Working on this repo

## The default branch is the release

The owner installs and updates this mod straight from GitHub: RimSort clones the
default branch (`main`) into RimWorld's Mods folder and pulls it in place. There
is no separate release step, so **every commit pushed to `main` is what the game
loads next**.

- Push finished work straight to `main`. Nothing half-done: each commit must
  load and play as-is.
- **Snapshot every build on its own branch.** Every commit carries a build
  number (`0.9.<commit count>`, stamped below). Push the same commit to
  `main` AND to a branch named after that build, so any build can be
  restored:

      git push origin HEAD:main HEAD:refs/heads/build/0.9.N

  Build branches are restore points: never move or delete one. To roll back,
  reset `main` to an earlier `build/...` branch - only when the owner asks.
  The release workflow only runs on `main`, so build branches publish nothing.
- **Every update carries its change notes** as BBCode (the Steam Workshop
  change-notes format), in `Changelog/<build>.bbcode` - e.g.
  `Changelog/0.9.N.bbcode` - committed in the same commit as the change, so
  each `build/` branch carries its own notes. Write them for players: what was
  added, changed and fixed, not how. Format:

      [h2]Build 0.9.N[/h2]
      [h3]Added[/h3]
      [list]
      [*]...
      [/list]

  Use only the sections that apply (Added, Changed, Fixed, Removed).
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
- Art is generated (`Source/TextureGen/`). For art changes, show the owner
  before/after comparisons - but they ship to the default branch like any
  other change; the build branch is the way back.
- Licence is CC0, for this and every SloppyMods mod.
- Replies to the owner: concise summaries; attach the build zip when they will
  test in game.
