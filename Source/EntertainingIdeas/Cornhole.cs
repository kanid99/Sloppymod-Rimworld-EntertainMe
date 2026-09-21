using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// The cells just past each end of a long building, along its own length.
    /// Used by the hammock, which needs a support beyond each end.
    /// </summary>
    public static class BuildingEnds
    {
        public static IEnumerable<IntVec3> Beyond(BuildableDef def, IntVec3 loc, Rot4 rot)
        {
            IntVec3 axis = rot.FacingCell;
            List<IntVec3> cells = GenAdj.CellsOccupiedBy(loc, rot, def.Size).ToList();
            int low = int.MaxValue;
            int high = int.MinValue;
            for (int i = 0; i < cells.Count; i++)
            {
                int along = Along(cells[i], axis);
                low = Mathf.Min(low, along);
                high = Mathf.Max(high, along);
            }
            for (int i = 0; i < cells.Count; i++)
            {
                int along = Along(cells[i], axis);
                if (along == low)
                {
                    yield return cells[i] - axis;
                }
                if (along == high)
                {
                    yield return cells[i] + axis;
                }
            }
        }

        /// <summary>How far along the building's own length a cell sits.</summary>
        public static int Along(IntVec3 cell, IntVec3 axis)
        {
            return cell.x * axis.x + cell.z * axis.z;
        }
    }

    [DefOf]
    public static class EI_CornholeDefOf
    {
        public static JobDef EI_Play_Cornhole;

        static EI_CornholeDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_CornholeDefOf));
        }
    }

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
        public static List<Pawn> At(Thing board, Pawn ignore = null)
        {
            List<Pawn> players = new List<Pawn>();
            Map map = board.Map;
            if (map == null)
            {
                return players;
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
                    Job job = pawn.CurJob;
                    if (job != null && job.def == EI_CornholeDefOf.EI_Play_Cornhole
                        && job.targetA.Thing == board)
                    {
                        players.Add(pawn);
                    }
                }
            }
            players.Sort((a, b) => a.thingIDNumber.CompareTo(b.thingIDNumber));
            return players;
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
            return CornholePlayers.At(t, pawn).Count < MaxPlayers;
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
        private CompProperties_CornholeGame Props
        {
            get { return (CompProperties_CornholeGame)props; }
        }

        private readonly Dictionary<int, Graphic> sacks = new Dictionary<int, Graphic>();
        private Graphic sackShadow;
        private float clock;
        private int nextRecheckTick = -99999;
        private List<Pawn> players = new List<Pawn>();

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
                players = CornholePlayers.At(parent);
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

            DrawFlight(throwIndex, t);
            DrawLanded(throwIndex);
        }

        /// <summary>
        /// Where a sack comes to rest. Scattered deterministically around the
        /// board so they neither stack on one pixel nor reshuffle every frame.
        /// </summary>
        private Vector3 LandingFor(int throwIndex)
        {
            Rand.PushState(parent.thingIDNumber + throwIndex * 31);
            Vector3 spot = parent.DrawPos;
            spot.x += Rand.Range(-0.3f, 0.3f);
            spot.z += Rand.Range(-0.34f, 0.26f);
            Rand.PopState();
            return spot;
        }

        private float SpinFor(int throwIndex)
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

        /// <summary>The sacks already thrown, lying where they landed.</summary>
        private void DrawLanded(int throwIndex)
        {
            for (int back = 1; back <= Props.sacksOnBoard; back++)
            {
                int index = throwIndex - back;
                if (index < 0)
                {
                    break;
                }
                Vector3 spot = LandingFor(index);
                spot.y = AltitudeLayer.BuildingOnTop.AltitudeFor();
                Blit(SackFor(index % players.Count), spot, SpinFor(index), Props.sackSize);
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
