# Entertaining Ideas

A RimWorld mod that adds thirteen recreation ideas, one for roughly each rung of
the tech ladder, so a colony always has something worth doing — from a hide mat
full of knucklebones to a room-sized shared hallucination.

Mostly XML, plus a small assembly for the moving parts. No Harmony, no mod
dependencies. Targets RimWorld 1.5 and 1.6, with a separate assembly built for
each — see [Versions](#versions).

## What it adds

| Building | Tech | Recreation type | Research | Notes |
|---|---|---|---|---|
| Knucklebone mat | Neolithic | Cerebral | — | Sit-adjacent, no chair needed. The one cerebral game a tribe can build on day one. |
| Soaking tub | Medieval | Solitary relaxation | — | Pawns get in. Wood-fired, warms the room, steams while lit. |
| Skittles lane | Medieval | Dexterity | — | 1×5. Rolled from the near end; pins scatter in play. Trains shooting. |
| Shadow lantern theater | Medieval | Social | — | 2×1, watched from 2–5 tiles by up to six colonists. The shadows walk on their own. |
| Pinball machine | Industrial | Dexterity | Pinball engineering | 1×3 cabinet, player stands at the flipper end. |
| Boomalope blitz pinball | Industrial | Dexterity | Pinball engineering | Chemfuel flash pots; rowdier and prettier, more power. |
| Mech rampage pinball | Industrial | Dexterity | + Microelectronics basics | Solid-state scoring, highest joy of the wired tables. |
| Archotech dreamtable | Spacer | Dexterity | Holographic entertainment | Projected ball, glows, absurdly expensive. |
| Cocktail arcade table | Industrial | Dexterity | + Microelectronics basics | 1×1, seats two — put a chair on either side. Screen animates in play. |
| Aquarium | Industrial | Solitary relaxation | Complex furniture + Electricity | 2×1. Fish swim whether or not anyone is watching. High beauty. |
| Karaoke machine | Industrial | Social | Microelectronics basics | A crowd of up to five. Trains social. The room forms opinions — see below. |
| Massage chair | Industrial | Solitary relaxation | Complex furniture + Electricity | Pawns sit *in* it. Comfortable enough to use as an ordinary chair. |
| Hologame pod | Spacer | Cerebral | Holographic entertainment | Trains intellectual. |
| Vista panel | Spacer | — (outdoors need) | Holographic entertainment | 3×1 wall display. Follows the local clock and eases cabin fever for the room. |
| Dreamloop holotheater | Ultra | Television | Dreamloop projection | 3×1. Projects onto a wall up to six tiles ahead. |
| Gravball court | Ultra | Dexterity | Dreamloop projection | 3×3, played from the edges by up to four. Trains melee. |

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
| Sit in the building itself | `JoyGiver_SitInBuilding` * | `JobDriver_SitInBuilding` * | massage chair, soaking tub |

\* This mod's own, because no vanilla joy giver seats a pawn in the thing it is
using — the sit-adjacent giver puts them in a *separate* chair beside it.

Powered machines are gated by the giver, which skips buildings whose
`CompPowerTrader` is off, so an unpowered cabinet is simply never chosen.

## The moving parts

These needed code, because vanilla has no XML-only frame animation (its one
animated graphic class, `Graphic_Flicker`, is fire) and no way to make anything
conditional on a building being in use:

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
- **`drawOverPawns`** on the animation comp draws above the pawn layer, which
  is how the soaking tub hides its occupant below the waterline. RimWorld 1.6
  does have a real swimming pose, but it swaps the pawn to a dedicated swimming
  graphic gated on `Pawn.Swimming` — read-only, and derived from the terrain
  underfoot — so a building standing on an ordinary floor cannot invoke it. The
  painted waterline gets the same read and works on 1.5 as well.
- **`CompAudienceReaction`** gives everyone *else* in the room a memory while
  someone is performing. The singer enjoys themselves regardless; the audience
  is a mixed bag, decided by the performer's social skill (a good singer wins
  the room), each listener's opinion of them (friends are forgiving), and a
  taste value hashed from the listener's ID so the same colonist reacts the
  same way every time instead of flip-flopping. Deaf pawns are skipped.
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
  build.sh        fetches reference assemblies and compiles both versions
  check_api.sh    checks XML class references against each game version
  validate.py     checks the defs without launching the game
  TextureGen/     regenerates every texture and the preview image
```

## Working on it

```bash
python3 Source/validate.py                     # def sanity checks
python3 Source/TextureGen/generate_textures.py # redraw all art + Preview.png
./Source/build.sh                              # rebuild both assemblies
./Source/check_api.sh                          # check XML classes per version
```

`build.sh` needs a C# compiler (`mono-devel` provides `mcs`) and pulls RimWorld's
reference assemblies from NuGet, so the assemblies can be rebuilt without a copy
of the game installed.

## Versions

One assembly cannot serve both versions. 1.6 changed APIs this mod uses:

| | 1.5 | 1.6 |
|---|---|---|
| `JoyUtility.JoyTickCheckEnd` | `(Pawn, JoyTickFullJoyAction, float, Building)` | `(Pawn, int, JoyTickFullJoyAction, float, Building)` |
| `Toil` tick hook | `tickAction` | `tickAction`, plus `tickIntervalAction(int delta)` |

A 1.5-built assembly would throw `MissingMethodException` the moment a pawn sat
in the massage chair on 1.6. So the sources carry one `#if RW16` branch, which
also takes the opportunity to pass 1.6 the real elapsed tick count rather than
assuming one tick has passed, `build.sh` produces an assembly per version, and
`LoadFolders.xml` loads the right one. Defs, textures and About are shared.

Everything else checks out on both: every class the XML names, and every vanilla
def field it sets, verified against both versions' reference assemblies.

`validate.py` catches the failures that are otherwise silent until runtime: a
recreation building no `JoyGiverDef` lists, a `texPath` with no file behind it, a
`Graphic_Multi` missing a rotation, an animation comp whose frames are missing,
XML naming a C# class the source does not define, references to defs the mod
never defines, and a def declaring a comp its parent already declares — def
inheritance *appends* list entries, so that quietly gives a building two power
comps rather than replacing one.

`generate_textures.py` takes builder names, so a tweak costs seconds instead of
the five minutes a full redraw takes:

```bash
python3 Source/TextureGen/generate_textures.py aquarium karaoke
python3 Source/TextureGen/build_preview.py     # then refresh the preview
python3 Source/TextureGen/contact_sheet.py     # every texture on one sheet
```

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
