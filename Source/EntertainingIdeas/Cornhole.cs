using System;
using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Who is currently pitching at a board, in a stable order.
    ///
    /// Shared by the giver, which needs a count to know whether the board is
    /// full, and the animation, which needs whose throw it is and what colour
    /// their sacks are. Sorted by thingIDNumber so a colonist keeps the same
    /// colour for as long as they play, however the cells happen to be walked.
    /// </summary>
    public static class CornholePlayers
    {
        private static readonly List<Pawn> counting = new List<Pawn>();
        private static readonly Comparison<Pawn> byId =
            delegate(Pawn a, Pawn b) { return a.thingIDNumber.CompareTo(b.thingIDNumber); };

        /// <summary>
        /// Fills a list the caller already has rather than handing back a new
        /// one: the giver asks this of every board a colonist might walk to,
        /// and the animation asks it of every board on screen.
        /// </summary>
        public static void At(Thing board, List<Pawn> players, Pawn ignore = null, JobDef jobDef = null)
        {
            players.Clear();
            Map map = board.Map;
            if (map == null)
            {
                return;
            }

            foreach (IntVec3 cell in WatchBuildingUtility.CalculateWatchCells(
                         board.def, board.Position, board.Rotation, map))
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                List<Thing> things = cell.GetThingList(map);
                for (int i = 0; i < things.Count; i++)
                {
                    Pawn pawn = things[i] as Pawn;
                    if (pawn == null || pawn == ignore || players.Contains(pawn))
                    {
                        continue;
                    }
                    // Any recreation job aimed at this board, unless the caller
                    // names one. Cornhole, the lawn noughts and crosses and the
                    // four-in-a-row frame all share this.
                    Job job = pawn.CurJob;
                    if (job != null && job.targetA.Thing == board
                        && (jobDef != null ? job.def == jobDef : job.def.joyKind != null))
                    {
                        players.Add(pawn);
                    }
                }
            }
            players.Sort(byId);
        }

        /// <summary>How many are pitching, when that is all the caller wants.</summary>
        public static int CountAt(Thing board, Pawn ignore, JobDef jobDef = null)
        {
            At(board, counting, ignore, jobDef);
            int count = counting.Count;
            counting.Clear();       // do not hold pawns alive between asks
            return count;
        }
    }

    /// <summary>
    /// Vanilla's watch-building giver, capped at two throwers.
    ///
    /// One board with players standing back and pitching at it is exactly the
    /// shape of vanilla horseshoes: JobDriver_PlayHorseshoes is
    /// JobDriver_WatchBuilding with a throw on a timer, and several pawns share
    /// one pin because the driver reserves the watch cell rather than the
    /// building. All of that is inherited rather than rebuilt - the throwing
    /// area, the standing spots, the reservations and the placement overlay all
    /// come from the def's watchBuilding fields.
    ///
    /// The only thing added is the cap. Cornhole is a two-player game and the
    /// throwing area holds more than two, so the third colonist along is told
    /// the board is busy. joyMaxParticipants on the JobDef does not do this:
    /// that field is declared and never read anywhere in the game's assembly.
    /// </summary>
    public class JoyGiver_Cornhole : JoyGiver_WatchBuilding
    {
        /// <summary>How many can pitch at one board at once.</summary>
        public const int MaxPlayers = 2;

        protected override bool CanInteractWith(Pawn pawn, Thing t, bool inBed)
        {
            if (!base.CanInteractWith(pawn, t, inBed))
            {
                return false;
            }
            // Everyone except this pawn: a colonist deciding to carry on playing
            // must not count as blocking their own place.
            return CornholePlayers.CountAt(t, pawn, def.jobDef) < MaxPlayers;
        }
    }

    /// <summary>
    /// The sacks.
    ///
    /// A bag in the air cannot be a frame strip: it has to leave the thrower,
    /// arc, and land on the board, and stepping that reads as teleporting. So
    /// it is drawn every rendered frame from a clock scaled to game speed, the
    /// same way the aquarium's fish are.
    ///
    /// With two players the throws alternate, each in their own colour, which
    /// is the whole of "taking turns" as far as anyone watching can tell -
    /// RimWorld gives each colonist their own job, so they are not really
    /// waiting on one another.
    /// </summary>
    public class CompProperties_CornholeGame : CompProperties
    {
        public string sackTexPath = "EntertainingIdeas/Buildings/CornholeSack";
        public float sackSize = 0.3f;
        /// <summary>Real seconds for one throw, at normal game speed.</summary>
        public float secondsPerThrow = 2.4f;
        /// <summary>How high the sack appears to go, as extra sprite scale.</summary>
        public float arcLift = 0.45f;
        /// <summary>How many landed sacks stay on the board.</summary>
        public int sacksOnBoard = 4;
        /// <summary>How often to re-check who is playing, in ticks.</summary>
        public int recheckInterval = 30;
        /// <summary>One colour per player, in the order they are listed.</summary>
        public List<ColorInt> sackColours = new List<ColorInt>();

        public CompProperties_CornholeGame()
        {
            compClass = typeof(CompCornholeGame);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (sackColours == null || sackColours.Count < JoyGiver_Cornhole.MaxPlayers)
            {
                yield return "CompProperties_CornholeGame needs a sack colour per player ("
                             + JoyGiver_Cornhole.MaxPlayers + ").";
            }
        }
    }

    public class CompCornholeGame : ThingComp
    {
        protected CompProperties_CornholeGame Props
        {
            get { return (CompProperties_CornholeGame)props; }
        }

        private readonly Dictionary<int, Graphic> sacks = new Dictionary<int, Graphic>();
        private Graphic sackShadow;
        private float clock;
        private int nextRecheckTick = -99999;
        private readonly List<Pawn> players = new List<Pawn>();

        // Where the sacks already on the board lie. Worked out once per throw
        // rather than once per frame: the scatter comes out of the seeded RNG,
        // and pushing and popping that state nine times every frame to
        // recompute numbers that had not changed was most of what this comp
        // cost to draw.
        private Vector3[] landedAt;
        private float[] landedSpin;
        private int[] landedOwner;
        private int cachedThrow = int.MinValue;
        private int cachedPlayers;

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            nextRecheckTick = -99999;
        }

        private Graphic SackFor(int player)
        {
            Graphic cached;
            if (!sacks.TryGetValue(player, out cached))
            {
                List<ColorInt> colours = Props.sackColours;
                Color colour = colours != null && colours.Count > 0
                    ? colours[player % colours.Count].ToColor
                    : Color.white;
                cached = GraphicDatabase.Get<Graphic_Single>(
                    Props.sackTexPath,
                    ShaderDatabase.TransparentPostLight,
                    new Vector2(Props.sackSize, Props.sackSize),
                    colour);
                sacks[player] = cached;
            }
            return cached;
        }

        private Graphic Shadow
        {
            get
            {
                if (sackShadow == null)
                {
                    sackShadow = GraphicDatabase.Get<Graphic_Single>(
                        Props.sackTexPath,
                        ShaderDatabase.Transparent,
                        new Vector2(Props.sackSize, Props.sackSize),
                        new Color(0f, 0f, 0f, 0.28f));
                }
                return sackShadow;
            }
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned)
            {
                return;
            }

            int now = Find.TickManager.TicksGame;
            if (now >= nextRecheckTick)
            {
                nextRecheckTick = now + Props.recheckInterval;
                CornholePlayers.At(parent, players);
            }
            if (players.Count == 0)
            {
                return;             // nobody pitching, nothing in the air
            }

            TickManager ticks = Find.TickManager;
            if (ticks != null && !ticks.Paused)
            {
                clock += RealTime.deltaTime * ticks.TickRateMultiplier;
            }

            float perThrow = Mathf.Max(0.4f, Props.secondsPerThrow);
            int throwIndex = Mathf.FloorToInt(clock / perThrow);
            float t = (clock / perThrow) - throwIndex;

            if (throwIndex != cachedThrow || players.Count != cachedPlayers)
            {
                CacheLanded(throwIndex);
            }

            DrawFlight(throwIndex, t);
            DrawLanded();
        }

        /// <summary>
        /// Where a sack comes to rest. Scattered deterministically around the
        /// board so they neither stack on one pixel nor reshuffle every frame.
        /// </summary>
        protected virtual Vector3 LandingFor(int throwIndex)
        {
            Rand.PushState(parent.thingIDNumber + throwIndex * 31);
            Vector3 spot = parent.DrawPos;
            spot.x += Rand.Range(-0.3f, 0.3f);
            spot.z += Rand.Range(-0.34f, 0.26f);
            Rand.PopState();
            return spot;
        }

        /// <summary>
        /// Whether an earlier throw is still lying on the board. Cornhole just
        /// keeps the last few; a game with rounds clears between them.
        /// </summary>
        protected virtual bool StillLying(int index, int throwIndex)
        {
            return true;
        }

        protected virtual float SpinFor(int throwIndex)
        {
            Rand.PushState(parent.thingIDNumber + throwIndex * 977);
            float spin = Rand.Range(0f, 360f);
            Rand.PopState();
            return spin;
        }

        private void DrawFlight(int throwIndex, float t)
        {
            int who = throwIndex % players.Count;
            Pawn thrower = players[who];
            if (thrower == null || !thrower.Spawned)
            {
                return;
            }

            Vector3 from = thrower.DrawPos;
            Vector3 to = LandingFor(throwIndex);

            // The last fifth of the cycle is the pause after it lands, so the
            // throw itself does not look frantic.
            float flight = Mathf.Clamp01(t / 0.8f);
            Vector3 ground = Vector3.Lerp(from, to, flight);

            // Height is faked: the sprite swells toward the middle of the arc
            // while its shadow stays on the floor and shrinks, which is how a
            // top-down camera shows something leaving the ground.
            float lift = Mathf.Sin(flight * Mathf.PI);

            Vector3 shadow = ground;
            shadow.y = AltitudeLayer.Shadows.AltitudeFor();
            Blit(Shadow, shadow, flight * 540f, Props.sackSize * (1f - 0.3f * lift));

            Vector3 sack = ground;
            sack.z += lift * 0.35f;
            sack.y = AltitudeLayer.MoteOverhead.AltitudeFor();
            Blit(SackFor(who), sack, flight * 540f,
                 Props.sackSize * (1f + Props.arcLift * lift));
        }

        /// <summary>
        /// Recomputes where the landed sacks lie. Only the newest is actually
        /// new each time, but the whole set is cheap to redo once every couple
        /// of seconds and it keeps the bookkeeping to one array index.
        /// </summary>
        private void CacheLanded(int throwIndex)
        {
            cachedThrow = throwIndex;
            cachedPlayers = players.Count;

            int want = Mathf.Max(0, Props.sacksOnBoard);
            if (landedAt == null || landedAt.Length != want)
            {
                landedAt = new Vector3[want];
                landedSpin = new float[want];
                landedOwner = new int[want];
            }

            for (int back = 1; back <= want; back++)
            {
                int index = throwIndex - back;
                int slot = back - 1;
                if (index < 0 || cachedPlayers == 0 || !StillLying(index, throwIndex))
                {
                    landedOwner[slot] = -1;
                    continue;
                }
                Vector3 spot = LandingFor(index);
                spot.y = AltitudeLayer.BuildingOnTop.AltitudeFor();
                landedAt[slot] = spot;
                landedSpin[slot] = SpinFor(index);
                landedOwner[slot] = index % cachedPlayers;
            }
        }

        /// <summary>The sacks already thrown, lying where they landed.</summary>
        private void DrawLanded()
        {
            if (landedOwner == null)
            {
                return;
            }
            for (int slot = 0; slot < landedOwner.Length; slot++)
            {
                if (landedOwner[slot] < 0)
                {
                    continue;
                }
                Blit(SackFor(landedOwner[slot]), landedAt[slot], landedSpin[slot], Props.sackSize);
            }
        }

        /// <summary>A flat sprite at a point, turned and scaled.</summary>
        private static void Blit(Graphic graphic, Vector3 at, float angle, float size)
        {
            if (graphic == null)
            {
                return;
            }
            Matrix4x4 matrix = default(Matrix4x4);
            matrix.SetTRS(at, Quaternion.Euler(0f, angle, 0f), new Vector3(size, 1f, size));
            Graphics.DrawMesh(MeshPool.plane10, matrix, graphic.MatSingle, 0);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned || players.Count == 0)
            {
                return null;
            }
            return players.Count > 1
                ? "Two players, taking turns."
                : "One player, practising.";
        }
    }
}
