# Entertaining Ideas

A RimWorld mod that adds eight recreation ideas, one for roughly each rung of
the tech ladder, so a colony always has something worth doing — from a hide mat
full of knucklebones to a room-sized shared hallucination.

Mostly XML, plus a small assembly for the moving parts. No Harmony, no mod
dependencies. Targets RimWorld 1.5 and 1.6.

## What it adds

| Building | Tech | Recreation type | Research | Notes |
|---|---|---|---|---|
| Knucklebone mat | Neolithic | Cerebral | — | Sit-adjacent, no chair needed. The one cerebral game a tribe can build on day one. |
| Shadow lantern theater | Medieval | Social | — | 2×1, watched from 2–5 tiles by up to six colonists. The shadows walk on their own. |
| Pinball machine | Industrial | Dexterity | Pinball engineering | 1×3 cabinet, player stands at the flipper end. |
| Boomalope blitz pinball | Industrial | Dexterity | Pinball engineering | Chemfuel flash pots; rowdier and prettier, more power. |
| Mech rampage pinball | Industrial | Dexterity | + Microelectronics basics | Solid-state scoring, highest joy of the wired tables. |
| Archotech dreamtable | Spacer | Dexterity | Holographic entertainment | Projected ball, glows, absurdly expensive. |
| Cocktail arcade table | Industrial | Dexterity | + Microelectronics basics | 1×1, seats two — put a chair on either side. Screen animates in play. |
| Massage chair | Industrial | Solitary relaxation | Complex furniture + Electricity | Pawns sit *in* it. Comfortable enough to use as an ordinary chair. |
| Hologame pod | Spacer | Cerebral | Holographic entertainment | Trains intellectual. |
| Vista panel | Spacer | — (outdoors need) | Holographic entertainment | 3×1 wall display. Follows the local clock and eases cabin fever for the room. |
| Dreamloop holotheater | Ultra | Television | Dreamloop projection | 3×1. Projects onto a wall up to six tiles ahead. |

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
| Stand back in a watch area | `JoyGiver_WatchBuilding` | `JobDriver_WatchBuilding` / `JobDriver_WatchTelevision` | shadow theater, holotheater |
| Sit in the building itself | `JoyGiver_UseMassageChair` * | `JobDriver_UseMassageChair` * | massage chair |

\* This mod's own, because no vanilla joy giver seats a pawn in the thing it is
using — the sit-adjacent giver puts them in a *separate* chair beside it.

Powered machines are gated by the giver, which skips buildings whose
`CompPowerTrader` is off, so an unpowered cabinet is simply never chosen.

## The moving parts

Three things needed code, because vanilla has no XML-only frame animation (its
one animated graphic class, `Graphic_Flicker`, is fire) and no way to make
anything conditional on a building being in use:

- **`CompAnimatedScreen`** cycles a strip of textures over a building. It draws
  only while a pawn is actually using it and only while the thing has power,
  which is how the arcade table's maze game runs during play and stops after.
  Set `requireUser` false and it runs whenever the building is on — that is the
  shadow theater, whose drum turns on the lamp's own draught.
- **`CompWallProjection`** looks straight ahead for the first impassable
  edifice within range and throws a moving picture onto it. Face the holotheater
  at a wall and the wall becomes the screen; face it at open floor and there is
  no picture. Because it stops at the first blocker, the image never appears
  through cover.
- **`JoyGiver_UseMassageChair` / `JobDriver_UseMassageChair`** walk a pawn to the
  chair's own cell and keep them there gaining joy, which vanilla's joy givers
  cannot do.
- **`CompDayCycleDisplay`** picks a frame strip by local time of day and
  recolours the building's glower to match, so a vista panel washes the room
  amber at sunset and blue after dark.
- **`CompOutdoorsSimulator`** tops up the outdoors need of everyone sharing the
  room, but only up to a ceiling (35% by default) — enough to hold off cabin
  fever in a sealed base, never enough to replace going outside.

Frames come off the game clock, so animations hold still while the game is
paused and keep pace with the speed control.

## Layout

```
About/            mod metadata and preview image
Defs/             ThingDefs, JobDefs, JoyGiverDefs, ResearchProjectDefs
Textures/         EntertainingIdeas/Buildings/*.png
Assemblies/       EntertainingIdeas.dll (built from Source/EntertainingIdeas)
Source/           tooling and code, not loaded by the game directly
  EntertainingIdeas/  the C# above
  build.sh        fetches RimWorld reference assemblies and compiles the DLL
  validate.py     checks the defs without launching the game
  TextureGen/     regenerates every texture and the preview image
```

## Working on it

```bash
python3 Source/validate.py                     # def sanity checks
python3 Source/TextureGen/generate_textures.py # redraw all art + Preview.png
./Source/build.sh                              # rebuild Assemblies/*.dll
```

`build.sh` needs a C# compiler (`mono-devel` provides `mcs`) and pulls RimWorld's
reference assemblies from NuGet, so the DLL can be rebuilt without a copy of the
game installed. It targets 1.5 references and runs on 1.5 and 1.6.

`validate.py` catches the failures that are otherwise silent until runtime: a
recreation building no `JoyGiverDef` lists, a `texPath` with no file behind it, a
`Graphic_Multi` missing a rotation, an animation comp whose frames are missing,
XML naming a C# class the source does not define, and references to defs the mod
never defines.

The art is generated, not hand-drawn — `Source/TextureGen/` contains a small
dependency-free PNG writer and the drawing code for each building, so the
textures are reproducible and easy to restyle. They are honest placeholder
sprites; swap in hand-drawn art any time by replacing the PNGs.

## Installing

Copy the repository folder into `RimWorld/Mods/` (or symlink it) and enable
**Entertaining Ideas** in the mod list. Load order does not matter.

No overlap with Vanilla Furniture Expanded: its recreation buildings are a
roulette table, arcade cabinet, piano, dartboard, punching bag, computers,
lounger and radios, and this mod deliberately avoids all of them.
