using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_JigsawDefOf
    {
        public static JobDef EI_DoJigsaw;
        public static JobDef EI_FrameJigsaw;
        public static ThoughtDef EI_FinishedJigsaw;

        static EI_JigsawDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_JigsawDefOf));
        }
    }

    /// <summary>One picture a puzzle can be, and what it becomes when framed.</summary>
    public class JigsawPicture
    {
        public string label;
        /// <summary>Stage textures, "&lt;framePath&gt;_0" .. "_(frameCount-1)", last one complete.</summary>
        public string framePath;
        public int frameCount = 7;
        public ThingDef framedDef;
    }

    /// <summary>
    /// A jigsaw that stays where it was left.
    ///
    /// Every other game here is over when the colonist stands up. This one is
    /// not: the puzzle on the table is shared state, anyone who sits down adds
    /// to it, and it takes several sittings to finish. When the last piece
    /// goes in, everyone who worked on it is pleased with themselves, and the
    /// finished picture can be framed and hung on a wall.
    /// </summary>
    public class CompProperties_Jigsaw : CompProperties
    {
        public List<JigsawPicture> pictures = new List<JigsawPicture>();
        /// <summary>Work to finish a puzzle, in ticks of an ordinary colonist's effort.</summary>
        public float workToFinish = 18000f;
        public int frameWorkTicks = 600;
        public Vector2 drawSize = new Vector2(2f, 2f);
        public float altitudeOffset = 0.03f;

        public CompProperties_Jigsaw()
        {
            compClass = typeof(CompJigsaw);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (pictures == null || pictures.Count == 0)
            {
                yield return "CompProperties_Jigsaw needs at least one picture.";
                yield break;
            }
            for (int i = 0; i < pictures.Count; i++)
            {
                if (pictures[i].framePath.NullOrEmpty())
                {
                    yield return "CompProperties_Jigsaw picture " + i + " has no framePath.";
                }
                if (pictures[i].frameCount < 2)
                {
                    yield return "CompProperties_Jigsaw picture " + i + " needs frameCount >= 2.";
                }
                if (pictures[i].framedDef == null)
                {
                    yield return "CompProperties_Jigsaw picture " + i + " has no framedDef.";
                }
            }
            if (workToFinish <= 0f)
            {
                yield return "CompProperties_Jigsaw needs a positive workToFinish.";
            }
        }
    }

    public class CompJigsaw : ThingComp, IServiceable
    {
        private int picture = -1;
        private float work;
        private List<Pawn> contributors = new List<Pawn>();

        // Stage textures, per picture, loaded on first draw.
        private Graphic[][] stages;
        private int drawnStage = -1;
        private Graphic drawnGraphic;

        private CompProperties_Jigsaw Props
        {
            get { return (CompProperties_Jigsaw)props; }
        }

        public JigsawPicture Picture
        {
            get { return Props.pictures[Mathf.Clamp(picture, 0, Props.pictures.Count - 1)]; }
        }

        public float Fraction
        {
            get { return Mathf.Clamp01(work / Props.workToFinish); }
        }

        public bool Finished
        {
            get { return work >= Props.workToFinish; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            if (picture < 0 || picture >= Props.pictures.Count)
            {
                // A fresh table starts on a picture of its own, so two tables
                // built side by side are not the same puzzle.
                Rand.PushState(parent.thingIDNumber);
                picture = Rand.Range(0, Props.pictures.Count);
                Rand.PopState();
            }
            drawnStage = -1;
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref picture, "EI_jigsawPicture", -1);
            Scribe_Values.Look(ref work, "EI_jigsawWork", 0f);
            Scribe_Collections.Look(ref contributors, "EI_jigsawContributors", LookMode.Reference);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (contributors == null)
                {
                    contributors = new List<Pawn>();
                }
                contributors.RemoveAll(p => p == null);
            }
        }

        /// <summary>Called by whoever is sitting at the table, every interval.</summary>
        public void AddWork(Pawn pawn, float amount)
        {
            if (Finished || amount <= 0f)
            {
                return;
            }
            work += amount;
            if (pawn != null && !contributors.Contains(pawn))
            {
                contributors.Add(pawn);
            }
            if (Finished)
            {
                OnFinished();
            }
        }

        private void OnFinished()
        {
            ThoughtDef thought = EI_JigsawDefOf.EI_FinishedJigsaw;
            for (int i = 0; i < contributors.Count; i++)
            {
                Pawn pawn = contributors[i];
                if (pawn == null || pawn.Dead || pawn.needs == null || pawn.needs.mood == null)
                {
                    continue;
                }
                pawn.needs.mood.thoughts.memories.TryGainMemory(thought);
            }
            if (parent.Spawned && parent.Faction == Faction.OfPlayer)
            {
                Messages.Message("Jigsaw finished: " + Picture.label + ". It can be framed and hung now.",
                                 new LookTargets(parent), MessageTypeDefOf.PositiveEvent);
            }
        }

        /// <summary>
        /// Which stage texture shows. The last stage is kept for a finished
        /// puzzle alone, so a table that looks complete always is.
        /// </summary>
        private int Stage
        {
            get
            {
                int count = Picture.frameCount;
                if (Finished)
                {
                    return count - 1;
                }
                return Mathf.Min(count - 2, Mathf.FloorToInt(Fraction * (count - 1)));
            }
        }

        private Graphic StageGraphic(int stage)
        {
            if (stages == null)
            {
                stages = new Graphic[Props.pictures.Count][];
            }
            int index = Mathf.Clamp(picture, 0, Props.pictures.Count - 1);
            JigsawPicture pic = Props.pictures[index];
            if (stages[index] == null)
            {
                stages[index] = new Graphic[pic.frameCount];
            }
            if (stages[index][stage] == null)
            {
                // Lit like the table it lies on, not like a screen: in a dark
                // room the puzzle is as hard to see as everything else.
                stages[index][stage] = GraphicDatabase.Get<Graphic_Single>(
                    pic.framePath + "_" + stage, ShaderDatabase.Transparent, Props.drawSize, Color.white);
            }
            return stages[index][stage];
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned)
            {
                return;
            }
            int stage = Stage;
            if (stage != drawnStage || drawnGraphic == null)
            {
                drawnStage = stage;
                drawnGraphic = StageGraphic(stage);
            }
            Vector3 at = parent.DrawPos;
            at.y += Props.altitudeOffset;
            drawnGraphic.Draw(at, Rot4.North, parent, 0f);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (Finished)
            {
                return "Puzzle: " + Picture.label + " - finished, waiting to be framed";
            }
            string line = "Puzzle: " + Picture.label + " - " + Mathf.FloorToInt(Fraction * 100f) + "% done";
            if (contributors.Count > 0)
            {
                line += " by " + contributors.Count + (contributors.Count == 1 ? " colonist" : " colonists");
            }
            return line;
        }

        // --- IServiceable: a finished puzzle is framed and a new one set out --
        public bool NeedsService
        {
            get { return Finished; }
        }

        public int ServiceWorkTicks
        {
            get { return Props.frameWorkTicks; }
        }

        public JobDef ServiceJob
        {
            get { return EI_JigsawDefOf.EI_FrameJigsaw; }
        }

        public void Service()
        {
            if (!Finished)
            {
                return;
            }
            ThingDef framedDef = Picture.framedDef;
            if (framedDef != null && parent.Spawned)
            {
                // Comes off the table boxed, like anything uninstalled, so the
                // player chooses which wall it goes on.
                Thing framed = ThingMaker.MakeThing(framedDef);
                Thing toPlace = framedDef.Minifiable ? MinifyUtility.MakeMinified(framed) : framed;
                GenPlace.TryPlaceThing(toPlace, parent.Position, parent.Map, ThingPlaceMode.Near);
            }
            // The next puzzle in the box, so a table works through all of them.
            picture = (Mathf.Max(0, picture) + 1) % Props.pictures.Count;
            work = 0f;
            contributors.Clear();
            drawnStage = -1;
        }
    }

    /// <summary>
    /// Sends a colonist to an unfinished puzzle with a free chair at it.
    ///
    /// Written out rather than borrowed from vanilla's sit-adjacent giver,
    /// because that one treats the table as the thing being reserved. Here the
    /// table is shared - as many colonists as there are chairs can work on the
    /// same puzzle at once - so only the chair is claimed.
    /// </summary>
    public class JoyGiver_Jigsaw : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }

            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                IntVec3 seat = IntVec3.Invalid;
                Thing table = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    40f,
                    t => Usable(pawn, t) && TryFindSeat(pawn, t, out seat));
                if (table != null && seat.IsValid)
                {
                    return JobMaker.MakeJob(def.jobDef, table, seat);
                }
            }
            return null;
        }

        private static bool Usable(Pawn pawn, Thing table)
        {
            if (table.IsForbidden(pawn) || table.IsBurning() || !table.IsSociallyProper(pawn))
            {
                return false;
            }
            CompJigsaw puzzle = table.TryGetComp<CompJigsaw>();
            return puzzle != null && !puzzle.Finished;
        }

        /// <summary>The nearest free chair pulled up to the table.</summary>
        public static bool TryFindSeat(Pawn pawn, Thing table, out IntVec3 seat)
        {
            return TryFindSeat(pawn, table, true, out seat);
        }

        /// <summary>
        /// The nearest free place to sit at the table. Without requireChair,
        /// bare ground beside it will do - the way a tribe sits round a board
        /// before anybody has built a stool - though a chair is still taken
        /// over the floor when there is one.
        /// </summary>
        public static bool TryFindSeat(Pawn pawn, Thing table, bool requireChair, out IntVec3 seat)
        {
            seat = IntVec3.Invalid;
            Map map = table.Map;
            float best = float.MaxValue;
            foreach (IntVec3 cell in GenAdj.CellsAdjacentCardinal(table))
            {
                if (!cell.InBounds(map) || cell.IsForbidden(pawn))
                {
                    continue;
                }
                Building edifice = cell.GetEdifice(map);
                bool chair = edifice != null && edifice.def.building != null && edifice.def.building.isSittable;
                if (!chair && (requireChair || edifice != null || !cell.Standable(map)))
                {
                    continue;
                }
                if (!pawn.CanReserveSittableOrSpot(cell) || !pawn.CanReach(cell, PathEndMode.OnCell, Danger.Some))
                {
                    continue;
                }
                // A chair always beats the floor next to it.
                float distance = cell.DistanceToSquared(pawn.Position) + (chair ? 0f : 10000f);
                if (distance < best)
                {
                    best = distance;
                    seat = cell;
                }
            }
            return seat.IsValid;
        }
    }

    /// <summary>
    /// Sit at the table and work on the puzzle. Progress belongs to the table,
    /// so leaving early loses nothing: whoever sits down next carries on.
    /// </summary>
    public class JobDriver_DoJigsaw : JobDriver
    {
        private CompJigsaw puzzle;

        private Thing Table
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        private CompJigsaw Puzzle
        {
            get
            {
                if (puzzle == null && Table != null)
                {
                    puzzle = Table.TryGetComp<CompJigsaw>();
                }
                return puzzle;
            }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            // Only the chair. The table is shared by everyone sitting at it.
            return pawn.ReserveSittableOrSpot(job.targetB.Cell, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            // Someone else placed the last piece: nothing left to do here.
            AddEndCondition(() => Puzzle == null || Puzzle.Finished
                ? JobCondition.Succeeded
                : JobCondition.Ongoing);

            yield return Toils_Goto.GotoCell(TargetIndex.B, PathEndMode.OnCell);

            Toil work = ToilMaker.MakeToil("EI_DoJigsaw");
            work.defaultCompleteMode = ToilCompleteMode.Delay;
            work.defaultDuration = job.def.joyDuration;
            work.handlingFacing = true;
            work.socialMode = RandomSocialMode.Normal;
#if RW16
            work.tickIntervalAction = delegate(int delta)
            {
                pawn.rotationTracker.FaceTarget(Table);
                Contribute(delta);
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#else
            work.tickAction = delegate
            {
                pawn.rotationTracker.FaceTarget(Table);
                Contribute(1);
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#endif
            yield return work;
        }

        /// <summary>
        /// A sharp-eyed, clever colonist gets through a puzzle faster. An
        /// average one (Intellectual 10, full sight) works at exactly 1.
        /// </summary>
        private void Contribute(int ticks)
        {
            if (Puzzle == null)
            {
                return;
            }
            float sight = pawn.health.capacities.GetLevel(PawnCapacityDefOf.Sight);
            int skill = pawn.skills == null ? 5 : pawn.skills.GetSkill(SkillDefOf.Intellectual).Level;
            float rate = Mathf.Max(0.1f, sight) * (0.6f + 0.04f * skill);
            Puzzle.AddWork(pawn, ticks * rate);
        }
    }
}
