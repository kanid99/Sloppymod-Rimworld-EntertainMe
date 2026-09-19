# Entertaining Ideas

A RimWorld mod that adds **thirteen recreation ideas — seventeen buildings** — one
for roughly each rung of the tech ladder, so a colony always has something worth
doing. A tribe gets a hide mat full of knucklebones on day one; an archotech
lounge gets a room-sized shared hallucination.

Mostly XML, plus a small assembly for the parts that move. No Harmony, no mod
dependencies. Supports RimWorld **1.5 and 1.6**, with a separate assembly built
for each — see [Versions](#versions).

## What it adds

### Neolithic and medieval — no research, no power

| Building | Size | Recreation | Notes |
|---|---|---|---|
| Knucklebone mat | 1×1 | Cerebral | Sit-adjacent, no chair needed. The one thinking game a tribe can build on day one. |
| Soaking tub | 1×1 | Solitary relaxation | Colonists get *in*. Burns wood (8/day), warms the room, steams while lit, and hides its occupant below the waterline. Holds one soak — see [water](#water). |
| Skittles lane | 1×7 | Dexterity | Nine pins in a diamond; rolled from the near end. Pins scatter when the ball lands. Trains shooting. |
| Shadow lantern theater | 2×1 | Social | Watched from 2–5 tiles by up to six colonists. The shadows walk on their own — the drum turns on the lamp's draught. |

### Industrial — powered

| Building | Size | Recreation | Power | Research |
|---|---|---|---|---|
| Pinball machine | 1×3 | Dexterity | 120W | Pinball engineering |
| Boomalope blitz pinball | 1×3 | Dexterity | 150W | Pinball engineering |
| Mech rampage pinball | 1×3 | Dexterity | 180W | + Microelectronics basics |
| Cocktail arcade table | 1×1 | Dexterity | 100W | + Microelectronics basics |
| Massage chair | 1×1 | Solitary relaxation | 90W | Complex furniture + Electricity |
| Aquarium | 2×1 | Solitary relaxation | 60W | Complex furniture + Electricity |
| Karaoke machine | 1×1 | Social | 120W | Microelectronics basics |
| Heated soaking tub | 1×1 | Solitary relaxation | 200W | Complex furniture + Electricity |

All four pinball tables share one cabinet frame and one animation; they differ in
cost, power, beauty and how much joy they give. The cocktail table seats two —
put a chair on either side.

The heated tub is the wood-fired one with the firebox swapped for an element: no
hauling and no ash, but a standing draw on the grid. The massage chair needs
power to massage anyone, and without it is simply a very comfortable chair —
colonists will still sit in it to eat and talk, they just will not book a
session.

### Spacer and ultra

| Building | Size | Recreation | Power | Research |
|---|---|---|---|---|
| Archotech dreamtable | 1×3 | Dexterity | 200W | Holographic entertainment |
| Hologame pod | 1×1 | Cerebral | 250W | Holographic entertainment |
| Vista panel | 3×1 | *(outdoors need)* | 150W | Holographic entertainment |
| Dreamloop holotheater | 3×1 | Television | 500W | Dreamloop projection |
| Gravball court | 3×3 | Dexterity | 400W | Dreamloop projection |

Three research projects chain off vanilla: **pinball engineering** (Electricity +
Complex furniture) → **holographic entertainment** (+ Microelectronics basics) →
**dreamloop projection** (+ Fabrication). Everything lands in the Recreation tab
of the architect menu.

## What the code does

Vanilla has no XML-only frame animation — its one animated graphic class,
`Graphic_Flicker`, is fire — and no way to make anything conditional on a
building being in use. These are the behaviours that needed an assembly.

**Things animate while they are being played.** `CompAnimatedScreen` cycles a
strip of textures over a building, drawing only while a pawn is actually using
it and the thing has power. The arcade table's maze game runs during play and
stops after; a pinball's ball, trail and bumper lamps do the same; skittles pins
scatter as the ball arrives; the karaoke screen scrolls; the gravball orbits.
Frames come off the game clock, so animations hold still while the game is
paused and keep pace with the speed control.

**Some things animate regardless.** Set `requireUser` false and the strip runs
whenever the building is on: the shadow theater's procession, the aquarium's
fish, the soaking tub's steam. `requireFuel` ties a strip to a refuelable parent
still burning, so a cold tub stops steaming.

**The holotheater projects onto a wall.** `CompWallProjection` looks straight
ahead for the first impassable edifice within six tiles and throws a moving
picture onto it. Face it at a wall and the wall becomes the screen; face it at
open floor and there is no picture. Because it stops at the *first* blocker, the
image never appears through cover.

**The vista panel follows the clock and eases cabin fever.**
`CompDayCycleDisplay` picks a frame strip by local time of day — night, dawn,
daylight, sunset — and recolours the building's glower to match, so the room
washes amber at sunset and blue after dark. `CompOutdoorsSimulator` tops up the
outdoors need of everyone sharing the room, but only to a ceiling (35% by
default): enough to hold off cabin fever in a sealed base, never enough to
replace going outside.

**Some furniture is sat *in*, not beside.** No vanilla joy giver does this — the
sit-adjacent giver puts a pawn in a *separate* chair next to the thing — so
`JoyGiver_SitInBuilding` / `JobDriver_SitInBuilding` walk a pawn onto the
building's own cell and keep them there gaining joy. Used by the massage chair
and both tubs, and it treats an unfuelled or unpowered building as unusable —
which is what makes the massage chair fall back to being an ordinary chair when
the power is out.

**The tub hides its occupant.** RimWorld 1.6 does have a real swimming pose, but
it swaps the pawn to a dedicated swimming graphic gated on `Pawn.Swimming` —
read-only, derived from the terrain underfoot — so a building on an ordinary
floor cannot invoke it. Instead `drawOverPawns` draws the tub's near half *above*
the pawn layer, with the waterline at chest height. Same read, and it works on
1.5 too.

**Karaoke splits the room.** The singer enjoys themselves regardless.
`CompAudienceReaction` gives everyone *else* in the room a memory, good or bad,
decided by three things: the singer's **artistic** skill (whether they can
actually hold a tune), each listener's **opinion** of them, and a **taste** value
hashed from the listener's ID, so a given colonist always reacts the same way
rather than flip-flopping. Deaf pawns are skipped.

Opinion is the heavier term on purpose, so being well liked covers for being
terrible — roughly the share of a room that enjoys it:

| singer's artistic skill | dislikes them | stranger | friendly | good friend | lover |
|---|---|---|---|---|---|
| tone deaf (0) | 0% | 20% | 48% | 76% | 100% |
| average (5) | 0% | 50% | 78% | 100% | 100% |
| good (10) | 24% | 80% | 100% | 100% | 100% |
| superb (16) | 60% | 100% | 100% | 100% | 100% |

A `JobDef` carries only one `joySkill`, so the comp also hands the performer
experience in a second skill: the job trains social, the comp adds artistic, and
a turn at the microphone builds both.

## Water

A tub holds **one soak**. When it runs dry a colonist carries more out to it —
a hauling job, a few seconds' work, and it never queues for a tub that is
already full. Both tubs start full when built, so the first soak costs nothing.

Plumb a tub in and it fills itself instead. That needs **Dubs Bad Hygiene**: the
patch below gives both tubs its pipe comp, and `CompWaterBasin` reads the
attached plumbing network to see whether there is actually water in it — a tub
on a dry or disconnected network reports as much rather than quietly working.
DBH is reached entirely by reflection, so this assembly never references it and
behaves normally without it.

## Optional mod compatibility

`Patches/DubsBadHygiene.xml` is inert unless **Dubs Bad Hygiene** is loaded. With
it:

- The **aquarium** joins DBH's plumbing network (`CompProperties_Pipe` in Sewage
  mode, the same way DBH declares its own water appliances), so the tank is
  piped in rather than filled from nowhere.
- Both **tubs** get the same pipe comp, so they can be plumbed instead of
  hand-filled, and move to DBH's `Hydrotherapy` recreation category instead of
  running a parallel one — a soak then counts as the same kind of recreation as
  its hot tub and sauna.

The tubs stay worth building alongside DBH's hot tub, which is 2×2, needs 500W
*and* plumbing, and does not heat the room. Ours are 1×1, need neither pipes nor
(for the wood-fired one) power or research, and push heat — a tribe can have a
hot soak on day one.

## How recreation is wired

A `<joyKind>` on a ThingDef is only a label — it does not make pawns use the
building. Anything usable needs a `JoyGiverDef` naming it in `<thingDefs>` plus
the `JobDef` that giver points at. Every building here is listed exactly once,
and `validate.py` fails if one is not.

| Interaction | JoyGiver | JobDriver | Used by |
|---|---|---|---|
| Sit beside it | `JoyGiver_InteractBuildingSitAdjacent` | `JobDriver_SitFacingBuilding` | knucklebone mat, cocktail table |
| Stand at its interaction cell | `JoyGiver_InteractBuildingInteractionCell` | `JobDriver_WatchBuilding` | pinball tables, hologame pod, skittles lane |
| Stand back in a watch area | `JoyGiver_WatchBuilding` | `JobDriver_WatchBuilding` / `JobDriver_WatchTelevision` | shadow theater, aquarium, karaoke, gravball, holotheater |
| Sit in the building itself | `JoyGiver_SitInBuilding` \* | `JobDriver_SitInBuilding` \* | massage chair, both tubs |

\* This mod's own; everything else is a vanilla class.

Powered machines are gated by the giver, which skips buildings whose
`CompPowerTrader` is off, so an unpowered cabinet is simply never chosen.

## Versions

One assembly cannot serve both game versions, because 1.6 changed APIs this mod
uses:

| | 1.5 | 1.6 |
|---|---|---|
| `JoyUtility.JoyTickCheckEnd` | `(Pawn, JoyTickFullJoyAction, float, Building)` | `(Pawn, **int**, JoyTickFullJoyAction, float, Building)` |
| `Toil` tick hook | `tickAction` | `tickAction`, plus `tickIntervalAction(int delta)` |

A 1.5-built assembly would throw `MissingMethodException` the moment a pawn sat
in the massage chair on 1.6. So the sources carry one `#if RW16` branch — which
also takes the opportunity to pass 1.6 the real elapsed tick count instead of
assuming a single tick — `build.sh` produces an assembly per version, and
`LoadFolders.xml` points each game version at its own folder. Defs, textures and
About are shared.

Everything else checks out on both: every class the XML names, and every vanilla
def field it sets, verified against both versions' reference assemblies.

1.6's rendering rework does not reach this mod. That work was on the *pawn*
pipeline — render trees, keyframes, animation workers — which nothing here
touches: the animations are building overlays drawn from `ThingComp.PostDraw`
via `Graphic.Draw`. The one place the two meet is the soaking tub's waterline,
which has to land above the pawn layer, and `AltitudeLayer.MoteOverhead` still
sits above `AltitudeLayer.Pawn` in both versions. The shared building base also
states `drawerType` explicitly rather than inheriting it, since a comp's
`PostDraw` only runs for things drawn in real time.

## Layout

```
About/               metadata and preview image
LoadFolders.xml      sends each game version to its own assembly
1.5/Assemblies/      built against 1.5 references
1.6/Assemblies/      the same sources built against 1.6 references
Defs/                ThingDefs, JobDefs, JoyGiverDefs, ResearchProjectDefs, ThoughtDefs
Patches/             optional compatibility, applied only if that mod is loaded
Textures/            EntertainingIdeas/Buildings/*.png
Source/              tooling and code, not loaded by the game directly
  EntertainingIdeas/ the C# described above
  build.sh           fetches reference assemblies, compiles both versions
  check_api.sh       checks XML class references against each game version
  validate.py        checks the defs without launching the game
  TextureGen/        draws every texture, the preview and the contact sheet
```

## Working on it

```bash
python3 Source/validate.py                      # def sanity checks
./Source/build.sh                               # rebuild both assemblies
./Source/check_api.sh                           # XML classes, per game version
python3 Source/TextureGen/generate_textures.py  # redraw everything (~5 min)
```

`build.sh` and `check_api.sh` need a C# compiler (`mono-devel` provides `mcs`)
and pull RimWorld's reference assemblies from NuGet, so both can run without a
copy of the game installed.

`validate.py` catches the failures that are otherwise silent until runtime: a
recreation building no `JoyGiverDef` lists, a `texPath` with no file behind it, a
`Graphic_Multi` missing a rotation, an animation comp whose frames are missing,
XML naming a C# class the source does not define, references to defs the mod
never defines, and a def declaring a comp its parent already declares — def
inheritance *appends* list entries, so that quietly gives a building two power
comps rather than replacing one.

The art is generated, not hand-drawn: `Source/TextureGen/` holds a small
dependency-free PNG writer and the drawing code for each building, so the
textures are reproducible and easy to restyle. A full redraw takes about five
minutes, so the generator takes builder names:

```bash
python3 Source/TextureGen/generate_textures.py aquarium karaoke   # seconds
python3 Source/TextureGen/build_preview.py      # refresh About/Preview.png
python3 Source/TextureGen/contact_sheet.py      # every texture on one sheet
python3 Source/TextureGen/promo_art.py          # release-post graphics -> promo/
```

`docs/release-post.md` holds the release-post copy that goes with those images.

They are honest placeholder sprites; swap in hand-drawn art any time by
replacing the PNGs.

## Installing

Copy the repository folder into `RimWorld/Mods/` (or symlink it) and enable
**Entertaining Ideas** in the mod list. Load order does not matter. Safe to add
to a running save; removing it leaves the usual missing-def warnings for
anything already built.

No overlap with Vanilla Furniture Expanded: its recreation buildings are a
roulette table, arcade cabinet, piano, dartboard, punching bag, computers,
lounger and radios, and this mod deliberately avoids all of them. (An earlier
dartboard here was dropped for exactly that reason.)

## Status

Every def is validated, both assemblies compile clean against their own game
version's references, and all 171 textures are checked for completeness — but
**none of this has been run in RimWorld yet.** Balance figures in particular
(joy factors, the karaoke curve, the outdoors ceiling) are reasoned guesses
until a colony has been let loose on them.
