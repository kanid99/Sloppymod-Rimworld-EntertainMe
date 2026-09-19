# Entertaining Ideas

A RimWorld mod that adds six recreation ideas, one for roughly each rung of the
tech ladder, so a colony always has something worth doing — from a hide mat full
of knucklebones to a room-sized shared hallucination.

Pure XML. No Harmony, no assemblies, no dependencies. Targets RimWorld 1.5 and 1.6.

## What it adds

| Building | Tech | Recreation type | Research | Notes |
|---|---|---|---|---|
| Knucklebone mat | Neolithic | Cerebral | — | Sit-adjacent, no chair needed. The one cerebral game a tribe can build on day one. |
| Dartboard | Medieval | Dexterity | — | Played from a watch area 3–5 tiles out. Trains shooting. |
| Pinball machine | Industrial | Dexterity | Pinball engineering | 1×3 cabinet, player stands at the flipper end. |
| Boomalope blitz pinball | Industrial | Dexterity | Pinball engineering | Chemfuel flash pots; rowdier and prettier, more power. |
| Mech rampage pinball | Industrial | Dexterity | + Microelectronics basics | Solid-state scoring, highest joy of the wired tables. |
| Archotech dreamtable | Spacer | Dexterity | Holographic entertainment | Projected ball, glows, absurdly expensive. |
| Cocktail arcade table | Industrial | Dexterity | + Microelectronics basics | 1×1, seats two — put a chair on either side. |
| Hologame pod | Spacer | Cerebral | Holographic entertainment | Trains intellectual. |
| Dreamloop holotheater | Ultra | Television | Dreamloop projection | 3×1, whole room watches, bedridden colonists included. |

Three research projects chain off vanilla: **pinball engineering**
(Electricity + Complex furniture) → **holographic entertainment**
(+ Microelectronics basics) → **dreamloop projection** (+ Fabrication).

Everything lands in the Recreation tab of the architect menu.

## How it is wired

A `<joyKind>` on a ThingDef is only a label — it does not make pawns use the
building. Anything usable needs a `JoyGiverDef` that names it in `<thingDefs>`
plus the `JobDef` that giver points at. This mod uses vanilla driver and giver
classes only:

| Interaction | JoyGiver | JobDriver | Used by |
|---|---|---|---|
| Sit at it | `JoyGiver_InteractBuildingSitAdjacent` | `JobDriver_SitFacingBuilding` | knucklebone mat, cocktail table |
| Stand at its interaction cell | `JoyGiver_InteractBuildingInteractionCell` | `JobDriver_WatchBuilding` | pinball tables, hologame pod |
| Stand back in a watch area | `JoyGiver_WatchBuilding` | `JobDriver_WatchBuilding` / `JobDriver_WatchTelevision` | dartboard, holotheater |

Powered machines are gated by the giver, which skips buildings whose
`CompPowerTrader` is off, so an unpowered cabinet is simply never chosen.

## Layout

```
About/            mod metadata and preview image
Defs/             ThingDefs, JobDefs, JoyGiverDefs, ResearchProjectDefs
Textures/         EntertainingIdeas/Buildings/*.png
Source/           tooling, not shipped code
  validate.py     checks the defs without launching the game
  TextureGen/     regenerates every texture and the preview image
```

## Working on it

```bash
python3 Source/validate.py                    # def sanity checks
python3 Source/TextureGen/generate_textures.py # redraw all art + Preview.png
```

`validate.py` catches the failures that are otherwise silent until runtime: a
recreation building no `JoyGiverDef` lists, a `texPath` with no file behind it, a
`Graphic_Multi` missing a rotation, and references to defs the mod never defines.

The art is generated, not hand-drawn — `Source/TextureGen/` contains a small
dependency-free PNG writer and the drawing code for each building, so the
textures are reproducible and easy to restyle. They are honest placeholder
sprites; swap in hand-drawn art any time by replacing the PNGs.

## Installing

Copy the repository folder into `RimWorld/Mods/` (or symlink it) and enable
**Entertaining Ideas** in the mod list. Load order does not matter.
