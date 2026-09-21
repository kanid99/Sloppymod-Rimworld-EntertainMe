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
    ///
    /// Two things want this: a hammock, which needs a support beyond each end,
    /// and a cornhole set, which needs somewhere for a player to stand at each
    /// end. Written for any size so a wider or longer version still asks the
    /// right question.
    /// </summary>
    public static class BuildingEnds
    {
        /// <summary>Every cell immediately beyond the far end and the near end.</summary>
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

        /// <summary>The two ends of a spawned thing, near end first.</summary>
        public static List<IntVec3> Of(Thing thing)
        {
            return Beyond(thing.def, thing.Position, thing.Rotation).ToList();
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
    /// Sends a colonist to whichever end of the cornhole set is free.
    ///
    /// The vanilla interaction-cell giver would not do: a ThingDef gets exactly
    /// one interaction cell, and this game has two ends. Both are offered, and
    /// only the standing spot is reserved rather than the whole set, which is
    /// what lets a second colonist take the other end and makes it a game
    /// rather than a queue.
    /// </summary>
    public class JoyGiver_Cornhole : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }

            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing set = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    40f,
                    t => FreeEnd(pawn, t).IsValid);
                if (set == null)
                {
                    continue;
                }
                IntVec3 spot = FreeEnd(pawn, set);
                if (!spot.IsValid)
                {
                    continue;
                }
                return JobMaker.MakeJob(def.jobDef, set, spot);
            }
            return null;
        }

        /// <summary>An end this pawn could stand at, or an invalid cell.</summary>
        public static IntVec3 FreeEnd(Pawn pawn, Thing set)
        {
            if (set.IsForbidden(pawn) || set.IsBurning())
            {
                return IntVec3.Invalid;
            }
            Map map = set.Map;
            if (map == null)
            {
                return IntVec3.Invalid;
            }

            List<IntVec3> ends = BuildingEnds.Of(set);
            for (int i = 0; i < ends.Count; i++)
            {
                IntVec3 cell = ends[i];
                if (!cell.InBounds(map) || !cell.Standable(map) || cell.IsForbidden(pawn))
                {
                    continue;
                }
                if (!pawn.CanReserveAndReach(cell, PathEndMode.OnCell, Danger.None))
                {
                    continue;
                }
                return cell;
            }
            return IntVec3.Invalid;
        }
    }

    /// <summary>
    /// Stand at your end, throw, walk nowhere, throw again. Joy accrues as it
    /// does at any recreation building; the sacks in the air are the comp's
    /// business, not the driver's.
    /// </summary>
    public class JobDriver_PlayCornhole : JobDriver
    {
        private Thing Set
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        private IntVec3 Spot
        {
            get { return job.GetTarget(TargetIndex.B).Cell; }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            // Only the standing spot, never the set itself - reserving the set
            // would lock the second player out of the other end.
            return pawn.ReserveSittableOrSpot(Spot, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);

            yield return Toils_Goto.GotoCell(TargetIndex.B, PathEndMode.OnCell);

            Toil play = ToilMaker.MakeToil("EI_PlayCornhole");
            play.defaultCompleteMode = ToilCompleteMode.Delay;
            play.defaultDuration = job.def.joyDuration;
            play.handlingFacing = true;
#if RW16
            play.tickIntervalAction = delegate(int delta)
            {
                FaceDownTheLane();
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Set as Building);
            };
#else
            play.tickAction = delegate
            {
                FaceDownTheLane();
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Set as Building);
            };
#endif
            play.socialMode = RandomSocialMode.SuperActive;
            yield return play;
        }

        /// <summary>Look at the board you are throwing at, not off into the room.</summary>
        private void FaceDownTheLane()
        {
            if (Set != null)
            {
                pawn.rotationTracker.FaceCell(Set.Position);
            }
        }
    }

    /// <summary>
    /// The sacks.
    ///
    /// Everything visible about a game of cornhole is a bag in the air, and a
    /// bag in the air cannot be a frame strip: it has to leave one end, arc,
    /// and land, and stepping that reads as teleporting. So it is drawn every
    /// rendered frame from a clock scaled to game speed, the same way the
    /// aquarium's fish are.
    ///
    /// Who is throwing comes from who is actually standing at each end. One
    /// player throws from their end all game; two players alternate, each with
    /// their own colour, which is the whole of "taking turns" as far as anyone
    /// watching can tell - RimWorld gives each colonist their own job, so they
    /// are not really waiting on each other.
    /// </summary>
    public class CompProperties_CornholeGame : CompProperties
    {
        public string sackTexPath = "EntertainingIdeas/Buildings/CornholeSack";
        public float sackSize = 0.30f;
        /// <summary>Real seconds for one throw, at normal game speed.</summary>
        public float secondsPerThrow = 2.4f;
        /// <summary>How high the sack appears to go, as extra sprite scale.</summary>
        public float arcLift = 0.45f;
        /// <summary>How many landed sacks stay on the board.</summary>
        public int sacksOnBoard = 3;
        /// <summary>How often to re-check who is playing, in ticks.</summary>
        public int recheckInterval = 30;
        public ColorInt nearColour = new ColorInt(206, 86, 72, 255);
        public ColorInt farColour = new ColorInt(74, 118, 190, 255);

        public CompProperties_CornholeGame()
        {
            compClass = typeof(CompCornholeGame);
        }
    }

    public class CompCornholeGame : ThingComp
    {
        private CompProperties_CornholeGame Props
        {
            get { return (CompProperties_CornholeGame)props; }
        }

        private Graphic nearSack;
        private Graphic farSack;
        private Graphic sackShadow;
        private float clock;
        private int nextRecheckTick = -99999;
        private bool[] manned = new bool[2];

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            nextRecheckTick = -99999;
        }

        private Graphic SackFor(int end)
        {
            ColorInt colour = end == 0 ? Props.nearColour : Props.farColour;
            Graphic cached = end == 0 ? nearSack : farSack;
            if (cached == null)
            {
                cached = GraphicDatabase.Get<Graphic_Single>(
                    Props.sackTexPath,
                    ShaderDatabase.TransparentPostLight,
                    new Vector2(Props.sackSize, Props.sackSize),
                    colour.ToColor);
                if (end == 0)
                {
                    nearSack = cached;
                }
                else
                {
                    farSack = cached;
                }
            }
            return cached;
        }

        /// <summary>Which ends have somebody standing at them playing.</summary>
        private void Recheck()
        {
            Map map = parent.Map;
            List<IntVec3> ends = BuildingEnds.Of(parent);
            for (int i = 0; i < manned.Length; i++)
            {
                manned[i] = false;
            }
            if (map == null)
            {
                return;
            }
            for (int i = 0; i < ends.Count && i < manned.Length; i++)
            {
                if (!ends[i].InBounds(map))
                {
                    continue;
                }
                List<Thing> things = ends[i].GetThingList(map);
                for (int t = 0; t < things.Count; t++)
                {
                    Pawn pawn = things[t] as Pawn;
                    if (pawn == null || pawn.CurJob == null)
                    {
                        continue;
                    }
                    if (pawn.CurJob.def == EI_CornholeDefOf.EI_Play_Cornhole
                        && pawn.CurJob.targetA.Thing == parent)
                    {
                        manned[i] = true;
                        break;
                    }
                }
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
                Recheck();
            }
            if (!manned[0] && !manned[1])
            {
                return;             // nobody playing, nothing in the air
            }

            TickManager ticks = Find.TickManager;
            if (ticks != null && !ticks.Paused)
            {
                clock += RealTime.deltaTime * ticks.TickRateMultiplier;
            }

            List<IntVec3> ends = BuildingEnds.Of(parent);
            if (ends.Count < 2)
            {
                return;
            }

            float perThrow = Mathf.Max(0.4f, Props.secondsPerThrow);
            int throwIndex = Mathf.FloorToInt(clock / perThrow);
            float t = (clock / perThrow) - throwIndex;

            int thrower = ThrowerFor(throwIndex);
            if (thrower < 0)
            {
                return;
            }

            Vector3 from = ends[thrower].ToVector3Shifted();
            Vector3 to = ends[1 - thrower].ToVector3Shifted();
            // Land short of the far player, on the board rather than on them.
            to = Vector3.Lerp(to, from, 0.18f);

            DrawFlight(from, to, t, thrower);
            DrawLanded(ends, throwIndex, thrower);
        }

        /// <summary>
        /// Whose throw this is. One player throws every time; two alternate.
        /// </summary>
        private int ThrowerFor(int throwIndex)
        {
            if (manned[0] && manned[1])
            {
                return throwIndex % 2;
            }
            if (manned[0])
            {
                return 0;
            }
            return manned[1] ? 1 : -1;
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

        private void DrawFlight(Vector3 from, Vector3 to, float t, int thrower)
        {
            // The last fifth of the cycle is the pause after it lands, so the
            // throw itself does not look frantic.
            float flight = Mathf.Clamp01(t / 0.8f);
            Vector3 ground = Vector3.Lerp(from, to, flight);

            // Height is faked: the sprite swells toward the middle of the arc
            // and the shadow stays behind on the floor, which is how a top-down
            // camera shows something leaving the ground.
            float lift = Mathf.Sin(flight * Mathf.PI);

            Graphic graphic = SackFor(thrower);
            if (graphic == null)
            {
                return;
            }

            // The shadow stays on the floor and shrinks as the sack rises,
            // which is the other half of reading height from overhead.
            Vector3 shadow = ground;
            shadow.y = AltitudeLayer.Shadows.AltitudeFor();
            Blit(Shadow, shadow, flight * 540f, Props.sackSize * (1f - 0.3f * lift));

            Vector3 sack = ground;
            sack.z += lift * 0.35f;
            sack.y = AltitudeLayer.MoteOverhead.AltitudeFor();
            Blit(graphic, sack, flight * 540f, Props.sackSize * (1f + Props.arcLift * lift));
        }

        /// <summary>The sacks already thrown, lying where they landed.</summary>
        private void DrawLanded(List<IntVec3> ends, int throwIndex, int thrower)
        {
            for (int back = 1; back <= Props.sacksOnBoard; back++)
            {
                int index = throwIndex - back;
                if (index < 0)
                {
                    break;
                }
                int who = ThrowerFor(index);
                if (who < 0)
                {
                    continue;
                }
                Vector3 from = ends[who].ToVector3Shifted();
                Vector3 to = Vector3.Lerp(ends[1 - who].ToVector3Shifted(), from, 0.18f);

                // Scattered a little, deterministically, so they do not stack.
                Rand.PushState(parent.thingIDNumber + index * 31);
                Vector3 spot = to;
                spot.x += Rand.Range(-0.28f, 0.28f);
                spot.z += Rand.Range(-0.22f, 0.22f);
                float spin = Rand.Range(0f, 360f);
                Rand.PopState();
                spot.y = AltitudeLayer.BuildingOnTop.AltitudeFor();

                Blit(SackFor(who), spot, spin, Props.sackSize);
            }
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (manned[0] && manned[1])
            {
                return "Two players, taking turns.";
            }
            if (manned[0] || manned[1])
            {
                return "One player, practising.";
            }
            return null;
        }
    }
}
