using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// The two short ends of a long table, and the cells a player stands on
    /// just beyond each one.
    /// </summary>
    public static class TableEnds
    {
        /// <summary>End 0 is the back of the table, end 1 the front it faces.</summary>
        public static void Cells(Thing table, int end, List<IntVec3> into)
        {
            into.Clear();
            IntVec3 axis = table.Rotation.FacingCell;
            CellRect rect = table.OccupiedRect();
            int low = int.MaxValue;
            int high = int.MinValue;
            foreach (IntVec3 cell in rect)
            {
                int along = cell.x * axis.x + cell.z * axis.z;
                low = Mathf.Min(low, along);
                high = Mathf.Max(high, along);
            }
            foreach (IntVec3 cell in rect)
            {
                int along = cell.x * axis.x + cell.z * axis.z;
                if (end == 0 && along == low)
                {
                    into.Add(cell - axis);
                }
                else if (end == 1 && along == high)
                {
                    into.Add(cell + axis);
                }
            }
        }

        private static readonly List<IntVec3> tmp = new List<IntVec3>();

        /// <summary>Which end a cell is a playing spot for, or -1.</summary>
        public static int EndOf(Thing table, IntVec3 cell)
        {
            for (int end = 0; end < 2; end++)
            {
                Cells(table, end, tmp);
                if (tmp.Contains(cell))
                {
                    tmp.Clear();
                    return end;
                }
            }
            tmp.Clear();
            return -1;
        }
    }

    /// <summary>
    /// A ball or puck going back and forth between whoever is at the two ends.
    ///
    /// Like the cornhole sacks, drawn every rendered frame from a clock scaled
    /// to game speed rather than stepped through frames, because the whole
    /// point is watching it travel. Table tennis arcs and bounces once on the
    /// far half; air hockey slides flat and caroms off the side rails, with a
    /// mallet at each end tracking it.
    /// </summary>
    public class CompProperties_RallyGame : CompProperties
    {
        public string ballTexPath;
        public float ballSize = 0.14f;
        /// <summary>Real seconds for one shot, end to end, at normal speed.</summary>
        public float secondsPerShot = 0.9f;
        /// <summary>Table tennis: the ball lifts and bounces. Off for a puck.</summary>
        public bool arcs = true;
        /// <summary>Air hockey: some shots bank off a side rail.</summary>
        public bool banks = false;
        public string malletTexPath;
        public float malletSize = 0.26f;
        public List<ColorInt> malletColours = new List<ColorInt>();
        /// <summary>How far in from each end the ball turns round, in tiles.</summary>
        public float endInset = 0.3f;
        public float sideInset = 0.2f;
        public bool requirePower = false;
        public int recheckInterval = 30;

        public CompProperties_RallyGame()
        {
            compClass = typeof(CompRallyGame);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (ballTexPath.NullOrEmpty())
            {
                yield return "CompProperties_RallyGame needs a ballTexPath.";
            }
            if (secondsPerShot <= 0.05f)
            {
                yield return "CompProperties_RallyGame needs secondsPerShot above 0.05.";
            }
        }
    }

    public class CompRallyGame : ThingComp
    {
        private CompPowerTrader power;
        private Graphic ball;
        private Graphic shadow;
        private Graphic[] mallets;
        private float clock;
        private int nextRecheck = -99999;
        private readonly Pawn[] atEnd = new Pawn[2];

        public CompProperties_RallyGame Props
        {
            get { return (CompProperties_RallyGame)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            nextRecheck = -99999;
        }

        public bool Ready
        {
            get { return !Props.requirePower || (power != null && power.PowerOn); }
        }

        /// <summary>Who is playing at each end right now.</summary>
        public Pawn PlayerAt(int end)
        {
            Refresh(true);
            return atEnd[end];
        }

        public int PlayerCount(Pawn ignore)
        {
            Refresh(true);
            int count = 0;
            for (int end = 0; end < 2; end++)
            {
                if (atEnd[end] != null && atEnd[end] != ignore)
                {
                    count++;
                }
            }
            return count;
        }

        private static readonly List<IntVec3> tmpCells = new List<IntVec3>();

        private void Refresh(bool force)
        {
            int now = Find.TickManager.TicksGame;
            if (!force && now < nextRecheck)
            {
                return;
            }
            nextRecheck = now + Props.recheckInterval;
            atEnd[0] = atEnd[1] = null;
            if (!parent.Spawned)
            {
                return;
            }
            for (int end = 0; end < 2; end++)
            {
                TableEnds.Cells(parent, end, tmpCells);
                for (int c = 0; c < tmpCells.Count && atEnd[end] == null; c++)
                {
                    if (!tmpCells[c].InBounds(parent.Map))
                    {
                        continue;
                    }
                    List<Thing> things = tmpCells[c].GetThingList(parent.Map);
                    for (int i = 0; i < things.Count; i++)
                    {
                        Pawn pawn = things[i] as Pawn;
                        if (pawn != null && pawn.jobs != null && pawn.jobs.curDriver is JobDriver_Rally
                            && pawn.CurJob.targetA.Thing == parent)
                        {
                            atEnd[end] = pawn;
                            break;
                        }
                    }
                }
            }
            tmpCells.Clear();
        }

        private Graphic Sprite(string path, float size, Color colour, Shader shader)
        {
            return GraphicDatabase.Get<Graphic_Single>(path, shader, new Vector2(size, size), colour);
        }

        /// <summary>Where across the table shot number k is struck from.</summary>
        private float Lateral(int k, float half)
        {
            Rand.PushState(parent.thingIDNumber * 17 + k * 101);
            float lateral = Rand.Range(-half, half);
            Rand.PopState();
            return lateral;
        }

        private bool Banked(int k)
        {
            if (!Props.banks)
            {
                return false;
            }
            Rand.PushState(parent.thingIDNumber * 23 + k * 57);
            bool banked = Rand.Chance(0.45f);
            Rand.PopState();
            return banked;
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned || !Ready)
            {
                return;
            }
            Refresh(false);
            if (atEnd[0] == null && atEnd[1] == null)
            {
                return;
            }

            TickManager ticks = Find.TickManager;
            if (ticks != null && !ticks.Paused)
            {
                clock += RealTime.deltaTime * ticks.TickRateMultiplier;
            }

            // The table's own axes: along its length, and across it.
            IntVec3 facing = parent.Rotation.FacingCell;
            IntVec3 right = parent.Rotation.RighthandCell;
            Vector3 along = new Vector3(facing.x, 0f, facing.z);
            Vector3 across = new Vector3(right.x, 0f, right.z);
            IntVec2 size = parent.def.Size;
            float halfLength = size.z / 2f - Props.endInset;
            float halfWidth = Mathf.Max(0.05f, size.x / 2f - Props.sideInset);
            Vector3 centre = parent.DrawPos;

            float perShot = Mathf.Max(0.05f, Props.secondsPerShot);
            int shot = Mathf.FloorToInt(clock / perShot);
            float t = clock / perShot - shot;

            // Even shots go from end 0 to end 1, odd shots come back. With one
            // player the far end is simply the table's own return - practice.
            float fromSide = shot % 2 == 0 ? -1f : 1f;
            float a = Lateral(shot, halfWidth);
            float b = Lateral(shot + 1, halfWidth);
            float lateral;
            if (Banked(shot))
            {
                // Off the rail halfway down and back across.
                float rail = (a + b >= 0f ? -1f : 1f) * halfWidth;
                lateral = t < 0.5f ? Mathf.Lerp(a, rail, t * 2f) : Mathf.Lerp(rail, b, (t - 0.5f) * 2f);
            }
            else
            {
                lateral = Mathf.Lerp(a, b, t);
            }
            float lengthwise = fromSide * halfLength * (1f - 2f * t);
            Vector3 ground = centre + along * lengthwise + across * lateral;

            float lift = 0f;
            if (Props.arcs)
            {
                // Over the net, one bounce on the far half, up to the bat.
                lift = t < 0.7f ? Mathf.Sin(t / 0.7f * Mathf.PI) : 0.45f * Mathf.Sin((t - 0.7f) / 0.3f * Mathf.PI);
            }

            if (ball == null)
            {
                ball = Sprite(Props.ballTexPath, Props.ballSize, Color.white, ShaderDatabase.Transparent);
                shadow = Sprite(Props.ballTexPath, Props.ballSize, new Color(0f, 0f, 0f, 0.3f), ShaderDatabase.Transparent);
            }
            if (Props.arcs)
            {
                Vector3 shadowAt = ground;
                shadowAt.y = parent.DrawPos.y + 0.02f;
                Blit(shadow, shadowAt, Props.ballSize * (1f - 0.3f * lift));
            }
            Vector3 ballAt = ground;
            ballAt.z += lift * 0.3f;
            ballAt.y = AltitudeLayer.MoteOverhead.AltitudeFor();
            Blit(ball, ballAt, Props.ballSize * (1f + 0.35f * lift));

            DrawMallets(centre, along, across, halfLength, lateral, a, b, fromSide, t);
        }

        /// <summary>
        /// Air hockey only: each mallet stays at its own end and slides
        /// across to meet the puck as it comes, and back to guard as it goes.
        /// </summary>
        private void DrawMallets(Vector3 centre, Vector3 along, Vector3 across, float halfLength,
                                 float lateral, float a, float b, float fromSide, float t)
        {
            if (Props.malletTexPath.NullOrEmpty())
            {
                return;
            }
            if (mallets == null)
            {
                mallets = new Graphic[2];
                for (int end = 0; end < 2; end++)
                {
                    Color colour = Props.malletColours != null && Props.malletColours.Count > end
                        ? Props.malletColours[end].ToColor
                        : Color.white;
                    mallets[end] = Sprite(Props.malletTexPath, Props.malletSize, colour, ShaderDatabase.Transparent);
                }
            }
            for (int end = 0; end < 2; end++)
            {
                if (atEnd[end] == null)
                {
                    continue;
                }
                float side = end == 0 ? -1f : 1f;
                // Receiving: track the puck in. Having just struck: drift back to the middle.
                bool receiving = side != fromSide;
                float across01 = receiving ? Mathf.Lerp(0f, b, t) : Mathf.Lerp(a, 0f, t);
                Vector3 at = centre + along * side * (halfLength + 0.12f) + across * across01;
                at.y = parent.DrawPos.y + 0.03f;
                Blit(mallets[end], at, Props.malletSize);
            }
        }

        private static void Blit(Graphic graphic, Vector3 at, float size)
        {
            Matrix4x4 matrix = default(Matrix4x4);
            matrix.SetTRS(at, Quaternion.identity, new Vector3(size, 1f, size));
            Graphics.DrawMesh(MeshPool.plane10, matrix, graphic.MatSingle, 0);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (!Ready)
            {
                return null;
            }
            int players = PlayerCount(null);
            if (players == 0)
            {
                return "Stand at either end to play.";
            }
            return players == 1 ? "One player, practising." : "A rally under way.";
        }
    }

    /// <summary>
    /// Sends a colonist to a free end of the table - the far one, if somebody
    /// is already at the near one.
    /// </summary>
    public class JoyGiver_Rally : JoyGiver
    {
        private static readonly List<IntVec3> tmp = new List<IntVec3>();

        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                IntVec3 spot = IntVec3.Invalid;
                Thing table = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    40f,
                    t => Usable(pawn, t, def.jobDef) && TryFindSpot(pawn, t, def.jobDef, out spot));
                if (table != null && spot.IsValid)
                {
                    return JobMaker.MakeJob(def.jobDef, table, spot);
                }
            }
            return null;
        }

        private static bool Usable(Pawn pawn, Thing table, JobDef jobDef)
        {
            if (table.IsForbidden(pawn) || table.IsBurning() || !table.IsSociallyProper(pawn))
            {
                return false;
            }
            CompRallyGame game = table.TryGetComp<CompRallyGame>();
            if (game == null || !game.Ready)
            {
                return false;
            }
            // Players at the ends, or everyone already sent here if more.
            int players = System.Math.Max(game.PlayerCount(pawn), CommittedPlayers.Count(table, jobDef, pawn));
            return players < 2;
        }

        private static readonly List<Pawn> sent = new List<Pawn>();

        private static bool TryFindSpot(Pawn pawn, Thing table, JobDef jobDef, out IntVec3 spot)
        {
            spot = IntVec3.Invalid;
            CompRallyGame game = table.TryGetComp<CompRallyGame>();
            CommittedPlayers.Of(table, jobDef, pawn, sent);
            float best = float.MaxValue;
            for (int end = 0; end < 2; end++)
            {
                Pawn there = game.PlayerAt(end);
                if (there != null && there != pawn)
                {
                    continue;               // taken: go to the other end
                }
                TableEnds.Cells(table, end, tmp);
                // Someone already on their way to this end has it too.
                bool claimed = false;
                for (int s = 0; s < sent.Count && !claimed; s++)
                {
                    claimed = tmp.Contains(sent[s].CurJob.targetB.Cell);
                }
                if (claimed)
                {
                    continue;
                }
                for (int c = 0; c < tmp.Count; c++)
                {
                    IntVec3 cell = tmp[c];
                    if (!cell.InBounds(table.Map) || !cell.Standable(table.Map) || cell.IsForbidden(pawn))
                    {
                        continue;
                    }
                    if (!pawn.CanReserveAndReach(cell, PathEndMode.OnCell, Danger.Some))
                    {
                        continue;
                    }
                    float distance = cell.DistanceToSquared(pawn.Position);
                    if (distance < best)
                    {
                        best = distance;
                        spot = cell;
                    }
                }
            }
            tmp.Clear();
            sent.Clear();
            return spot.IsValid;
        }
    }

    /// <summary>Stand at an end of the table, face down it, and play.</summary>
    public class JobDriver_Rally : JobDriver
    {
        /// <summary>
        /// The "played a game" tale this job's def records on completion is a
        /// pawn-and-thing tale: the base driver passes only the pawn, and the
        /// game logs an error building it. Name the table too, as vanilla's
        /// game drivers do.
        /// </summary>
        public override object[] TaleParameters()
        {
            Thing played = job.GetTarget(TargetIndex.A).Thing;
            return new object[] { pawn, played != null ? played.def : (Def)job.def };
        }

        private Thing Table
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.ReserveSittableOrSpot(job.targetB.Cell, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            AddFailCondition(delegate
            {
                CompRallyGame game = Table == null ? null : Table.TryGetComp<CompRallyGame>();
                return game == null || !game.Ready;
            });

            yield return Toils_Goto.GotoCell(TargetIndex.B, PathEndMode.OnCell);

            Toil play = ToilMaker.MakeToil("EI_Rally");
            play.defaultCompleteMode = ToilCompleteMode.Delay;
            play.defaultDuration = job.def.joyDuration;
            play.handlingFacing = true;
            play.socialMode = RandomSocialMode.Normal;
#if RW16
            play.tickIntervalAction = delegate(int delta)
            {
                pawn.rotationTracker.FaceTarget(Table);
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#else
            play.tickAction = delegate
            {
                pawn.rotationTracker.FaceTarget(Table);
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#endif
            yield return play;
        }
    }
}
