Release post copy for r/RimWorld.

The four images it refers to are built by `python3 Source/TextureGen/promo_art.py`,
which writes them to `promo/` (gitignored) from the textures the game actually
loads. Image order below matches the gallery order.

TITLE
=====
[Mod] Entertaining Ideas — 13 recreation ideas across the whole tech ladder, from knucklebones to a shared hallucination [1.5/1.6]

(alternative, if posting before it's had a proper shakedown:)
[Mod/WIP] Entertaining Ideas — recreation for every tech level, looking for testers [1.5/1.6]


BODY
====

Vanilla recreation plateaus early. Horseshoes, then a chess table, then billiards
and a tube TV — and that's basically the game. A tribal start has nothing to
think with, and a colony sitting on 40,000 silver is still watching the same
television it built in year one.

So: **13 recreation ideas, 17 buildings**, roughly one per rung of the tech ladder.

*[IMAGE 1 — lineup]*

**Neolithic & medieval** — no power, no research
- **Knucklebone mat** — cerebral play a tribe can build on day one. Cast bones, argue, gamble.
- **Soaking tub** — a wood-fired barrel colonists get *into*. Warms the room, steams while lit.
- **Skittles lane** — nine pins in a diamond, seven tiles of board. The old game ten-pin bowling came from. Trains shooting.
- **Shadow lantern theater** — a lamp behind stretched linen turning a vaned drum on its own draught. Six colonists can sit and watch the shadows walk.

**Industrial**
- **Pinball machines** — 1×3 cabinets in four flavours: standard, the chemfuel-flashpot *Boomalope Blitz*, the solid-state *Mech Rampage*, and (at spacer tech) the *Archotech Dreamtable*, which projects a ball you cannot miss.
- **Cocktail arcade table** — face-up screen under glass, a joystick at each of two seats.
- **Massage chair** — colonists sit *in* it. No power, no massage — but it's still a very comfortable chair.
- **Aquarium**, **karaoke machine**, and an **electric tub** for anyone tired of hauling logs.

**Spacer & ultra**
- **Hologame pod** — a board of light tuned just past your ability. Trains intellectual.
- **Vista panel** — a 3×1 wall display showing somewhere with a horizon in it.
- **Dreamloop holotheater** — a shared waking dream the whole room can watch.
- **Gravball court** — 3×3, played from the edges by up to four. Trains melee.

---

**Things actually move**

*[IMAGE 2 — animation]*

Anything with a screen animates **while a colonist is using it**, and stops when
they leave or the power cuts. Pinball has a ball, a trail, and the bumper lamps
it just hit. The arcade table runs its maze game. Skittles pins scatter when the
ball arrives. The shadow theater and the aquarium run regardless — the lantern
turns on its own draught and the fish don't care whether anyone's watching.

Frames run off the game clock, so everything holds still when you pause and keeps
pace with the speed controls.

**A window that isn't a window**

*[IMAGE 3 — vista panel]*

The vista panel follows the local clock — grey dawn, open daylight, a long
sunset, then stars — and **recolours the light it throws** to match, so the room
washes amber at sunset and blue after dark. Colonists sharing the room hold off
cabin fever for longer, up to a ceiling well short of full. It's not a window and
nobody's fooled for long, but a base stops feeling quite so much like a hole in
the ground.

The holotheater, pointed at a wall within six tiles, turns that wall into the
screen. Point it at open floor and there's no picture.

**Karaoke splits the room**

The singer has a good time regardless. Everyone *else* forms their own view,
based on the singer's **artistic** skill, what they think of them personally, and
a fixed streak of taste — so the same colonist reacts the same way every time
instead of flip-flopping. Roughly the share of a room that enjoys it:

| singer's artistic skill | dislikes them | stranger | friendly | good friend | lover |
|---|---|---|---|---|---|
| tone deaf (0) | 0% | 20% | 48% | 76% | 100% |
| average (5) | 0% | 50% | 78% | 100% | 100% |
| good (10) | 24% | 80% | 100% | 100% | 100% |
| superb (16) | 60% | 100% | 100% | 100% | 100% |

Being well liked covers for being terrible. A turn at the mic trains artistic and
social both.

**The tub**

*[IMAGE 4 — tub]*

Colonists get in, not beside — and the tub paints its waterline back over them so
they're actually *in* the water. It holds one soak; somebody carries water out to
it between uses. If you run Dubs Bad Hygiene, plumb it in and it fills itself —
and it'll tell you if the pipes are dry.

---

**Compatibility**

- **1.5 and 1.6.** 1.6 changed the joy-tick API, so there's a separate assembly per version and `LoadFolders.xml` picks the right one.
- **No Harmony, no dependencies.** Safe to add to a running save.
- **No overlap with Vanilla Furniture Expanded** — its recreation buildings are a roulette table, arcade cabinet, piano, dartboard, punching bag, computers, lounger and radios, and this avoids all of them. (An earlier dartboard here got cut for exactly that reason.)
- **Optional Dubs Bad Hygiene patch** — inert unless DBH is loaded. With it, the aquarium and both tubs join its plumbing network, and the tubs move into its hydrotherapy category so the two mods stack instead of splitting the need.

**Art:** the sprites are procedurally generated and ship with the source that
draws them, so they're reproducible and easy to restyle — but they're honest
placeholders. If anyone fancies redrawing them by hand, the PNGs are a
drop-in swap and I'd welcome it.

[GitHub link here]
