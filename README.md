# SloppyMods Entertaining Ideas

A RimWorld mod that adds **nineteen recreation ideas — twenty-six buildings and
a paintable swimming pool** — one for roughly each rung of the tech ladder, so a
colony always has something worth doing. A tribe gets a hide mat full of
knucklebones on day one; an archotech lounge gets a room-sized shared
hallucination.

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
| Cornhole board | 1×2 | Dexterity | A sloped board with a hole, thrown at from a line a few tiles back. One colonist practises alone; two take turns with their own colour of sack. Wood and cloth, no power, no research. Trains shooting. |
| Hammock | 1×2 | Solitary relaxation | Rest that is not a bed: no assignment, no sleeping the night, no medical care. Recovers rest at 45% of a plain bed while a colonist lounges. Woven from cloth or leather. |
| Armillary sphere | 1×1 | Solitary relaxation | Brass rings on a tripod, turning under their own clockwork. Watched from 1–4 tiles. Beauty 16. |
| Jigsaw table | 2×2 | Cerebral | A puzzle that stays where it was left. Anyone who pulls up a chair adds pieces — as many at once as there are chairs — and it fills in visibly over several sittings. Everyone who worked on it is pleased when the last piece goes in; the finished picture is framed, boxed, and hung on a wall like a lamp (Beauty 8), and the next puzzle comes out of the box. Four pictures. Wood, metal or stone. |
| Storyteller's stump | 1×1 | Social | One colonist stands on it and tells stories beside a fire; the rest gather in front to listen, and the stories take shape in the fire's smoke — a thrumbo, a raider, a ship, a mechanoid. Everyone within earshot likes it or doesn't, by the teller's social skill and what they think of them. Needs a lit campfire (or any modded fire pit) within six tiles. Wood logs. |
| Board game table | 2×2 | Cerebral | A cupboard of games; whoever sits first picks one and the rest join in, up to four, one per chair. Colonists of the Rim, Raid!, Orbital Trader, Caravan Routes, Muffalo & Thrumbo — the board on the table shows which is on, and moves on as the game does. Wood, metal or stone. |
| Seed pit board | 1×1 | Cerebral | Seed Pits (mancala) carved for a tribe. Two players, who will sit on the ground beside it if there are no chairs. |
| Table tennis table | 2×3 | Dexterity | One player at each end; the ball arcs over the net and bounces on the far half. Alone, a colonist practises against the far end. Trains melee. |
| Lawn noughts and crosses | 3×3 | Dexterity | A rope grid pegged out on the grass. Cornhole's throwing: each bag lands in a square, two colours, cleared after nine throws. Walkable. |
| Giant four-in-a-row | 2×1 | Cerebral | An upright frame two players drop discs into. Drawn like a TV: the face from the south, an edge from the sides — face it the way the players should see it. |
| Tangle mat | 3×3 | Social | Up to three colonists step from spot to spot as the spinner calls them, and every so often one goes over. |

### Industrial — powered

| Building | Size | Recreation | Power | Research |
|---|---|---|---|---|
| Pinball machine | 1×2 | Dexterity | 120W | Electricity |
| Boomalope blitz pinball | 1×2 | Dexterity | 150W | Electricity |
| Mech rampage pinball | 1×2 | Dexterity | 180W | Microelectronics basics |
| Ore Rush arcade table | 1×1 | Dexterity | 100W | Tube television |
| Thrumbo! arcade table | 1×1 | Dexterity | 100W | Tube television |
| Infestation! arcade table | 1×1 | Dexterity | 100W | Tube television |
| Massage chair | 1×1 | Solitary relaxation | 90W | Complex furniture + Electricity |
| Aquarium | 2×1 | Solitary relaxation | 60W | Complex furniture + Electricity |
| Karaoke machine | 1×1 | Social | 120W | Microelectronics basics |
| Bowling lane | 1×7 | Dexterity | 140W | Complex furniture + Electricity |
| Heated soaking tub | 1×1 | Solitary relaxation | 200W | Complex furniture + Electricity |
| Air hockey table | 1×2 | Dexterity | 120W | Electricity |
| Pool filtration unit | 1×2 | Social | 80W + 5W/tile | Electricity |
| Tabletop orrery | 1×1 | Solitary relaxation | — | Complex furniture |
| Grand orrery | 2×2 | Solitary relaxation | — | Complex furniture |

The three arcade tables have sound: synthesised chip blips tied to the frame of
the screen animation they belong to - Ore Rush's pick and cleared rounds,
Thrumbo!'s hops and rolling rocks - and a soft jingle every couple of minutes
while idle. Everything else is silent for now. Volumes, pitch spread and range
are in `Defs/SoundDefs`, meant to be tuned by ear.

Every electric game and screen — pinball, the arcade tables, air hockey, the
hologame pod, the holotheater, karaoke, gravball and the bowling lane — can break down the way
a television does, sitting dark until a colonist repairs it with a component.
Furniture and fittings (the massage chair, heated tub, aquarium, pool pump and
vista panels) do not.

All four pinball tables share one cabinet frame and one animation; they differ in
cost, power, beauty and how much joy they give, and they sit behind a single
architect entry with a dropdown to pick one — as do the three arcade tables and the
three vista panel widths. Each has a proper backglass —
painted art over two six-digit score reels that climb while somebody is playing.

The three cocktail tables seat two apiece — put a chair on either side — and run
different games. **Ore Rush** is a maze: you work a mine shaft in a hard hat,
clearing seams of ore, while the things that live down there come along the same
corridor from the other direction. **Thrumbo!** is a climb: a colonist is
stranded at the top of a half-built scaffold and something enormous and
extremely cross is at the top of it rolling rocks down the girders at you. Left
alone, either cabinet drops into attract mode rather than sitting on a dead
screen.

The three orreries are clockwork: they turn whether or not anyone is watching
and draw no power at all. The grand one lights its own dome.

### The swimming pool

The pool is **terrain, not an object**. Paint `pool basin` tiles in whatever
shape you like, stand a filtration unit against any edge of it, and the unit
claims every basin tile joined to that one edge-to-edge. Everything then scales
with what you drew:

| | |
|---|---|
| Water it holds | 20 L per tile |
| Power it draws | 80W + 5W per tile |
| Evaporation | 0.6 L per tile per day |
| Hand-filling | 120 L per load, carried from open water |
| Going stale | 0.12 dirt per day with the pump off (murky at 0.3, foul at 0.7) |
| Clearing | 0.6 dirt per day with the pump running |
| Cap | 220 tiles per unit |

The water level drives what you see: the pool fills outward from the filter and
drains back toward it, a tile at a time, so the water line is always readable.
Power is what keeps it *clean*. Cut it, or lose the filter altogether, and the
water stays where it is but goes stale: the pool turns murky within a few days
and foul a few days after that, each stage its own water terrain. Colonists
still swim in it, and a swim in foul water has a 30% chance of a day of
swimmer's sickness. A running filter clears it again in a couple of days; water
whose filter is gone is kept by the map (`MapComponent_Pools`), and a new filter
built against it takes it over, dirt and all.

Off the plumbing, colonists carry the water in by the load, from the nearest
bank of a river, lake or marsh — never out of thin air, so a map with no open
water needs the plumbing. With Dubs Bad Hygiene installed, pipe the unit in and
it keeps itself topped up — see [water](#water). The basin is pea gravel, and
the water shows the gravel through it. On 1.6 swimmers get the game's own swimming pose, because the
job sets the flag 1.6 reads for it; on 1.5 they wade.

The heated tub is the wood-fired one with the firebox swapped for an element: no
hauling and no ash, but a standing draw on the grid. The massage chair is
upholstered from cloth, leather or synthread — its sprite is painted
near-neutral so the stuff colour carries — and needs power to massage anyone, and without it is simply a very comfortable chair —
colonists will still sit in it to eat and talk, they just will not book a
session.

### Spacer and ultra

| Building | Size | Recreation | Power | Research |
|---|---|---|---|---|
| Archotech dreamtable | 1×2 | Dexterity | 200W | Fabrication + Microelectronics |
| Hologame pod | 1×1 | Cerebral | 250W | Fabrication |
| Vista panel (1 tile) | wall | *(outdoors need)* | 60W | Flatscreen television |
| Vista panel (2 tiles) | wall | *(outdoors need)* | 105W | Flatscreen television |
| Vista panel (3 tiles) | wall | *(outdoors need)* | 150W | Flatscreen television |
| Dreamloop holotheater | 3×1 | Television | 500W | Advanced fabrication |
| Gravball court | 3×3 | Dexterity | 400W | Advanced fabrication |

**No new research.** Everything gates on projects the game already has —
Electricity for the first pinball tables, Tube television for the arcade
cabinet, Microelectronics and Flatscreen television for the screens, Fabrication
for the spacer builds and Advanced fabrication for the ultra pair — so the tree
gains twenty-six buildings and not one extra node. These are the same gates
Vanilla Furniture Expanded uses for equivalent things: its arcade machine and
industrial computer sit on Tube television, its modern computer and spacer radio
on Flatscreen television. Everything lands in the Recreation tab of the architect menu.

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

**Some things run out and need a colonist.** The tub holds one soak; the
skittles lane's pins stay where the ball leaves them. Both implement one
`IServiceable` interface, so a single work giver and job driver cover "carry
water out to it" and "walk down and stand the pins up", and a lane waiting on
somebody is not offered to anyone wanting a game. The bowling lane is the same
game with a pinsetter in it — ten pins, a ball return, and nobody walking down
the lane — which is the whole difference between the medieval version and the
industrial one.

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

A tub holds **one soak**. When it runs dry a colonist carries more out to it
from the nearest open water — a hauling job that goes to the bank first, and it
never queues for a tub that is already full or when no water is in reach. Each
unplumbed tub, and the pool filter, has a **Fill by hand** toggle; switch it off
and nobody carries water to it. A piped one gets a **Use plumbing** toggle as
well: off, it stops drawing on the network and is treated as unplumbed. Both tubs start full when built, so the first soak costs nothing.

Plumb a tub in and it fills itself instead. That needs **Dubs Bad Hygiene**: the
patch below gives both tubs and the pool filter its pipe comp. The water is
real: it comes out of the network's water towers through DBH's own
`PlumbingNet.PullWater`, the call its hot tub uses — 80 L a soak for a tub, and
up to 100 L per rare tick while a pool fills or tops up evaporation. A building
on a dry or disconnected network says so rather than quietly working. The pool
also takes on the dirt of what it draws: DBH's *untreated* water arrives a
quarter dirty and *contaminated* water foul, for the pump to clear. In DBH's
lite mode, which does not track water, it is free, as it is for DBH's fixtures.

DBH has no per-building shut-off of its own (a fixture's pipe closes only when
its power switch is off), so each piped tub and pool filter gets a **Use
plumbing** toggle. DBH is reached entirely by reflection, so this assembly never
references it and behaves normally without it.

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

`Patches/VanillaFurnitureExpanded.xml` is inert unless **Vanilla Furniture
Expanded** is loaded. With it, the massage chair, aquarium and heated tub move
from Complex furniture to VFE's own `MF_ModernFurniture`, which is where VFE
puts its piano, roulette table and lounger — so this mod's armchair-tier
comforts do not arrive noticeably earlier than VFE's equivalents. The screens
need no patch: both mods already gate those on vanilla's television research.

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
python3 Tools/validate.py                      # def sanity checks
./Tools/build.sh                               # rebuild both assemblies
./Tools/check_api.sh                           # XML classes, per game version
python3 Source/TextureGen/generate_textures.py  # redraw everything (~5 min)
python3 Source/SoundGen/generate_sounds.py     # re-synthesise the arcade sounds
```

`build.sh` and `check_api.sh` need a C# compiler (`mono-devel` provides `mcs`)
and pull RimWorld's reference assemblies from NuGet, so both can run without a
copy of the game installed.

Point `validate.py` at a copy of the game's own defs and it will also confirm
every vanilla def name the mod uses actually exists — research, joy kinds, stuff
categories, items, capacities:

```bash
RIMWORLD_CORE_DEFS="/path/to/RimWorld/Data/Core/Defs" python3 Tools/validate.py
```

That is worth running before a release: a research prerequisite that does not
resolve takes the whole building down with it. All 157 references check out
against 1.6 Core.

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
python3 Source/TextureGen/build_preview.py      # texture overview -> promo/
python3 Source/TextureGen/contact_sheet.py      # every texture on one sheet
python3 Source/TextureGen/promo_art.py          # release-post graphics -> promo/
```

`docs/release-post.md` holds the release-post copy that goes with those images.

The mod's preview image, `About/Preview.png`, is the banner in `Source/Promo/`:
a page laid out from the shipped textures and rendered to 1280x720 with
Playwright. Re-render it after changing any art it shows:

```bash
NODE_PATH=$(npm root -g) node Source/Promo/render_preview.js
```

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

## Licence

Public domain, under [CC0 1.0](LICENSE). That covers everything here - code,
textures, sounds and text. Copy it, change it, make your own version, fold it
into another mod or re-upload it: no permission or credit needed.

RimWorld belongs to Ludeon Studios, and nothing of theirs is included here.
