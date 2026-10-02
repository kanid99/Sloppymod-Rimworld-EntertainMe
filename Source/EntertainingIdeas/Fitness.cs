using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_FitnessDefOf
    {
        public static ThoughtDef EI_WorkedOut;
        /// <summary>Vanilla's bruise; HediffDefOf only carries it in 1.6.</summary>
        public static HediffDef Bruise;

        static EI_FitnessDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_FitnessDefOf));
        }
    }

    public enum ExerciseMotion
    {
        Bounce,
        Punch,
        Lift,
        Pedal,
        Climb
    }

    /// <summary>
    /// A piece of fitness equipment: how it is used, and where the colonist
    /// using it is drawn.
    ///
    /// The art for these is modelled in 3D and drawn from RimWorld's camera
    /// (Source/TextureGen/fitness.py), so a point on the model lands on screen
    /// at (x, 0.8 * depth + 0.6 * height) tiles from the building's centre.
    /// The colonist is moved about with the job's body offset - the same hook
    /// vanilla's dancing uses - to sit on the saddle, lie on the bench, climb
    /// the holds or bounce, without Harmony.
    /// </summary>
    public class CompProperties_Exercise : CompProperties
    {
        public ExerciseMotion motion = ExerciseMotion.Bounce;
        /// <summary>
        /// True for things used by getting on them (trampoline, bench, bike);
        /// false for things used from the interaction cell (bag, wall).
        /// </summary>
        public bool onBuilding = false;
        /// <summary>
        /// Where the colonist's body goes, on the south-facing model: x across,
        /// y depth (north), z height, in tiles from the centre.
        /// </summary>
        public Vector3 bodyAt = Vector3.zero;
        /// <summary>One bounce, in ticks. Must match the mat's sag frames.</summary>
        public int bounceTicks = 64;
        public float bounceHeight = 0.55f;
        /// <summary>Chance per session of a bruise, for a colonist who moves perfectly.</summary>
        public float bruiseChance = 0f;
        /// <summary>Joy gain for children, who like this sort of thing more.</summary>
        public float childJoyFactor = 1f;
        /// <summary>How long a session must run to count as a workout.</summary>
        public int workoutTicks = 900;
        /// <summary>
        /// Given after a workout: a short-lived boost to the stats the
        /// equipment trains. A new workout replaces it, so it never stacks.
        /// </summary>
        public HediffDef workoutBuff;
        /// <summary>Skills trained while using it, on top of the JobDef's joySkill.</summary>
        public List<ExerciseSkillXp> trainSkills = new List<ExerciseSkillXp>();

        public CompProperties_Exercise()
        {
            compClass = typeof(CompExercise);
        }
    }

    public class ExerciseSkillXp
    {
        public SkillDef skill;
        public float xpPerTick;
    }

    public class CompExercise : ThingComp
    {
        private int lastUsedTick = -99999;

        public CompProperties_Exercise Props
        {
            get { return (CompProperties_Exercise)props; }
        }

        /// <summary>Somebody is on it right now.</summary>
        public bool InUse
        {
            get { return Find.TickManager.TicksGame - lastUsedTick <= 30; }
        }

        public void MarkUsed()
        {
            lastUsedTick = Find.TickManager.TicksGame;
        }

        /// <summary>
        /// A point on the south-facing model, turned with the building, as a
        /// world position.
        /// </summary>
        public Vector3 ModelToWorld(Vector3 model)
        {
            float x = model.x, y = model.y;
            switch (parent.Rotation.AsInt)
            {
                case 1: x = -model.y; y = model.x; break;   // east
                case 0: x = -model.x; y = -model.y; break;  // north
                case 3: x = model.y; y = -model.x; break;   // west
            }
            Vector3 centre = parent.TrueCenter();
            return new Vector3(centre.x + x, 0f, centre.z + 0.8f * y + 0.6f * model.z);
        }

        /// <summary>
        /// The inverse, for a point on the ground: where on the model a cell
        /// is, such that ModelToWorld puts it straight back.
        /// </summary>
        public Vector3 WorldToModel(Vector3 world)
        {
            Vector3 centre = parent.TrueCenter();
            float dx = world.x - centre.x, dz = (world.z - centre.z) / 0.8f;
            switch (parent.Rotation.AsInt)
            {
                case 1: return new Vector3(dz, -dx, 0f);    // east
                case 0: return new Vector3(-dx, -dz, 0f);   // north
                case 3: return new Vector3(-dz, dx, 0f);    // west
            }
            return new Vector3(dx, dz, 0f);
        }

        /// <summary>Where a colonist stands to use it.</summary>
        public IntVec3 UseCell
        {
            get { return Props.onBuilding ? parent.Position : parent.InteractionCell; }
        }
    }

    /// <summary>
    /// A pedal generator: the bike feeds its rated power into the grid while
    /// somebody is riding it, and nothing while nobody is.
    /// </summary>
    public class CompPowerPlantPedal : CompPowerPlant
    {
        private CompExercise exercise;

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            exercise = parent.TryGetComp<CompExercise>();
        }

        protected override float DesiredPowerOutput
        {
            get { return exercise != null && exercise.InUse ? base.DesiredPowerOutput : 0f; }
        }

        public override string CompInspectStringExtra()
        {
            string text = base.CompInspectStringExtra();
            string riding = exercise != null && exercise.InUse ? "Someone is pedalling." : "Needs a rider to make power.";
            return text.NullOrEmpty() ? riding : text + "\n" + riding;
        }
    }

    /// <summary>
    /// The punching bag's bag: a pendulum hanging from the arm, drawn as one of
    /// a grid of pre-drawn swing positions. Punches knock it about; it circles
    /// and settles on its own. Purely a picture, so nothing is saved - a
    /// loaded game starts with the bag hanging still.
    /// </summary>
    public class CompProperties_PunchingBag : CompProperties
    {
        public string bagPath = "EntertainingIdeas/Buildings/PunchingBag";
        public string postNorthPath = "EntertainingIdeas/Buildings/PunchingBagPostNorth";
        public int gridHalf = 3;
        /// <summary>Tiles of swing at the bag's foot between one sprite and the next.</summary>
        public float gridStep = 0.08f;
        /// <summary>The arm's tip on the south-facing model.</summary>
        public Vector3 pivot = new Vector3(0f, 0.04f, 1.85f);
        /// <summary>The sprite's centre below the pivot, in tiles on screen.</summary>
        public float spriteDrop = 0.625f;
        public Vector2 spriteSize = new Vector2(1.25f, 1.75f);
        public float stiffness = 22f;
        public float damping = 1.2f;

        public CompProperties_PunchingBag()
        {
            compClass = typeof(CompPunchingBag);
        }
    }

    public class CompPunchingBag : ThingComp
    {
        private float x, y, vx, vy;
        private int lastTick = -1;
        private Graphic[] sprites;
        private Graphic postNorth;
        private CompExercise exercise;

        private CompProperties_PunchingBag Props
        {
            get { return (CompProperties_PunchingBag)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            exercise = parent.TryGetComp<CompExercise>();
        }

        /// <summary>A punch from the colonist standing at `from`.</summary>
        public void Punch(Pawn from, float strength)
        {
            Vector3 d = parent.TrueCenter() - from.DrawPos;
            d.y = 0f;
            if (d.sqrMagnitude < 0.0001f)
            {
                d = Vector3.forward;
            }
            d.Normalize();
            Vector3 side = new Vector3(d.z, 0f, -d.x);
            float roll = Rand.Value;
            Vector3 kick;
            if (roll < 0.6f)
            {
                kick = d * Rand.Range(1.4f, 1.9f) + side * Rand.Range(-0.4f, 0.4f);     // jab
            }
            else if (roll < 0.85f)
            {
                kick = side * (Rand.Bool ? 1f : -1f) * Rand.Range(1.3f, 1.7f) + d * 0.5f; // hook
            }
            else
            {
                kick = d * 2.3f;                                                        // cross
            }
            kick *= strength;
            vx += kick.x;
            vy += kick.z;
        }

        private void Step()
        {
            int now = Find.TickManager.TicksGame;
            if (lastTick < 0 || now < lastTick)
            {
                lastTick = now;
                return;
            }
            int steps = Mathf.Min(now - lastTick, 120);
            lastTick = now;
            const float dt = 1f / 60f;
            for (int i = 0; i < steps; i++)
            {
                float ax = -Props.stiffness * x - Props.damping * vx;
                float ay = -Props.stiffness * y - Props.damping * vy;
                vx += ax * dt;
                vy += ay * dt;
                x += vx * dt;
                y += vy * dt;
            }
            if (Mathf.Abs(x) + Mathf.Abs(y) + Mathf.Abs(vx) + Mathf.Abs(vy) < 0.002f)
            {
                x = y = vx = vy = 0f;
            }
        }

        private Graphic Sprite(int i, int j)
        {
            int n = Props.gridHalf * 2 + 1;
            if (sprites == null)
            {
                sprites = new Graphic[n * n];
            }
            int k = (i + Props.gridHalf) * n + (j + Props.gridHalf);
            if (sprites[k] == null)
            {
                sprites[k] = GraphicDatabase.Get<Graphic_Single>(
                    Props.bagPath + "_" + (i + Props.gridHalf) + "_" + (j + Props.gridHalf),
                    ShaderDatabase.Cutout, Props.spriteSize, Color.white);
            }
            return sprites[k];
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned)
            {
                return;
            }
            Step();
            int h = Props.gridHalf;
            int i = Mathf.Clamp(Mathf.RoundToInt(x / Props.gridStep), -h, h);
            int j = Mathf.Clamp(Mathf.RoundToInt(y / Props.gridStep), -h, h);

            Vector3 pivot = exercise != null
                ? exercise.ModelToWorld(Props.pivot)
                : parent.TrueCenter() + new Vector3(0f, 0f, 0.6f * Props.pivot.z);
            Vector3 at = new Vector3(pivot.x, parent.DrawPos.y + 0.03f, pivot.z - Props.spriteDrop);
            Sprite(i, j).Draw(at, Rot4.North, parent);

            // Facing north the post is between the camera and the bag.
            if (parent.Rotation == Rot4.North)
            {
                if (postNorth == null)
                {
                    postNorth = GraphicDatabase.Get<Graphic_Single>(
                        Props.postNorthPath, ShaderDatabase.Cutout, parent.def.graphicData.drawSize, Color.white);
                }
                Vector3 post = parent.DrawPos + parent.def.graphicData.DrawOffsetForRot(parent.Rotation);
                post.y = parent.DrawPos.y + 0.04f;
                postNorth.Draw(post, Rot4.North, parent);
            }
        }
    }

    /// <summary>
    /// Sends a colonist to a free piece of fitness equipment: onto it, or to
    /// its interaction cell.
    /// </summary>
    public class JoyGiver_Exercise : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            Thing best = null;
            float bestDistance = float.MaxValue;
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing candidate = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    40f,
                    t => Usable(pawn, t));
                if (candidate == null)
                {
                    continue;
                }
                float distance = candidate.Position.DistanceToSquared(pawn.Position);
                if (distance < bestDistance)
                {
                    best = candidate;
                    bestDistance = distance;
                }
            }
            return best == null ? null : JobMaker.MakeJob(def.jobDef, best);
        }

        private static bool Usable(Pawn pawn, Thing thing)
        {
            if (thing.IsForbidden(pawn) || thing.IsBurning()
                || !thing.IsSociallyProper(pawn) || !thing.IsPoliticallyProper(pawn))
            {
                return false;
            }
            CompExercise exercise = thing.TryGetComp<CompExercise>();
            if (exercise == null || !pawn.CanReserve(thing))
            {
                return false;
            }
            IntVec3 cell = exercise.UseCell;
            return cell.InBounds(thing.Map) && pawn.CanReach(cell, PathEndMode.OnCell, Danger.Some)
                   && !cell.IsForbidden(pawn);
        }
    }

    /// <summary>
    /// Use a piece of fitness equipment: get on it (or up to it), and work at
    /// it until the pawn has had enough fun. The motion comes from the
    /// equipment's CompExercise; a proper session leaves a "worked out" mood.
    /// </summary>
    public class JobDriver_Exercise : JobDriver
    {
        private const int ClimbCycle = 900;

        private int played;
        private bool exercising;
        private int nextPunchTick;
        private int lastBounce = -1;

        private Thing Equipment
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        private CompExercise Exercise
        {
            get { return Equipment == null ? null : Equipment.TryGetComp<CompExercise>(); }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref played, "EI_exercisePlayed", 0);
            Scribe_Values.Look(ref exercising, "EI_exercising", false);
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }

        public override object[] TaleParameters()
        {
            Thing used = Equipment;
            return new object[] { pawn, used != null ? used.def : (Def)job.def };
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);

            Toil walk = ToilMaker.MakeToil("EI_ExerciseWalk");
            walk.initAction = delegate
            {
                CompExercise exercise = Exercise;
                IntVec3 cell = exercise != null ? exercise.UseCell : Equipment.Position;
                pawn.pather.StartPath(cell, PathEndMode.OnCell);
            };
            walk.defaultCompleteMode = ToilCompleteMode.PatherArrival;
            yield return walk;

            Toil work = ToilMaker.MakeToil("EI_Exercise");
            work.initAction = delegate
            {
                exercising = true;
                nextPunchTick = Find.TickManager.TicksGame + Rand.Range(20, 50);
                Settle();
            };
            work.defaultCompleteMode = ToilCompleteMode.Delay;
            work.defaultDuration = job.def.joyDuration;
            work.handlingFacing = true;
            work.socialMode = RandomSocialMode.Normal;
#if RW16
            work.tickIntervalAction = delegate(int delta)
            {
                Work(delta);
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, JoyFactor(), Equipment as Building);
            };
#else
            work.tickAction = delegate
            {
                Work(1);
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, JoyFactor(), Equipment as Building);
            };
#endif
            work.AddFinishAction(Finish);
            yield return work;
        }

        private float JoyFactor()
        {
            CompExercise exercise = Exercise;
            if (exercise != null && exercise.Props.childJoyFactor != 1f
                && pawn.DevelopmentalStage.Child())
            {
                return exercise.Props.childJoyFactor;
            }
            return 1f;
        }

        /// <summary>Posture and facing for the whole session.</summary>
        private void Settle()
        {
            CompExercise exercise = Exercise;
            if (exercise == null)
            {
                return;
            }
            switch (exercise.Props.motion)
            {
                case ExerciseMotion.Lift:
                    pawn.jobs.posture = PawnPosture.LayingOnGroundNormal;
                    pawn.Rotation = Equipment.Rotation;
                    break;
                case ExerciseMotion.Pedal:
                    pawn.Rotation = Equipment.Rotation;
                    break;
                case ExerciseMotion.Punch:
                case ExerciseMotion.Climb:
                    pawn.Rotation = Equipment.Rotation.Opposite;
                    break;
                default:
                    pawn.Rotation = Rot4.South;
                    break;
            }
        }

        private void Work(int delta)
        {
            played += delta;
            CompExercise exercise = Exercise;
            if (exercise == null)
            {
                return;
            }
            exercise.MarkUsed();
            if (pawn.skills != null)
            {
                List<ExerciseSkillXp> training = exercise.Props.trainSkills;
                for (int i = 0; i < training.Count; i++)
                {
                    if (training[i].skill != null)
                    {
                        pawn.skills.Learn(training[i].skill, training[i].xpPerTick * delta);
                    }
                }
            }
            ExerciseMotion motion = exercise.Props.motion;
            if (motion == ExerciseMotion.Lift)
            {
                pawn.jobs.posture = PawnPosture.LayingOnGroundNormal;
            }
            if (motion == ExerciseMotion.Punch && Find.TickManager.TicksGame >= nextPunchTick)
            {
                nextPunchTick = Find.TickManager.TicksGame + Rand.Range(35, 70);
                CompPunchingBag bag = Equipment.TryGetComp<CompPunchingBag>();
                if (bag != null)
                {
                    float melee = pawn.skills == null ? 5f : pawn.skills.GetSkill(SkillDefOf.Melee).Level;
                    bag.Punch(pawn, 0.8f + melee / 40f);
                }
            }
            // A bounce now and then turns the jumper round.
            if (motion == ExerciseMotion.Bounce)
            {
                int bounce = Find.TickManager.TicksGame / exercise.Props.bounceTicks;
                if (bounce != lastBounce)
                {
                    if (lastBounce >= 0 && Rand.Chance(0.2f))
                    {
                        pawn.Rotation = Rot4.Random;
                    }
                    lastBounce = bounce;
                }
            }
        }

        private void Finish()
        {
            exercising = false;
            pawn.jobs.posture = PawnPosture.Standing;
            CompExercise exercise = Exercise;
            if (exercise == null)
            {
                return;
            }
            if (played >= exercise.Props.workoutTicks)
            {
                if (pawn.needs != null && pawn.needs.mood != null)
                {
                    pawn.needs.mood.thoughts.memories.TryGainMemory(EI_FitnessDefOf.EI_WorkedOut);
                }
                GiveBuff(exercise.Props.workoutBuff);
            }
            if (exercise.Props.bruiseChance > 0f && played > 300)
            {
                MaybeBruise(exercise.Props.bruiseChance);
            }
        }

        /// <summary>Starts the buff afresh, replacing one still running.</summary>
        private void GiveBuff(HediffDef buff)
        {
            if (buff == null || pawn.health == null || pawn.Dead)
            {
                return;
            }
            Hediff running = pawn.health.hediffSet.GetFirstHediffOfDef(buff);
            if (running != null)
            {
                pawn.health.RemoveHediff(running);
            }
            pawn.health.AddHediff(HediffMaker.MakeHediff(buff, pawn));
        }

        /// <summary>
        /// Somebody came down wrong. Rare for anyone who moves well, less rare
        /// for the slow, the hurt and the clumsy.
        /// </summary>
        private void MaybeBruise(float baseChance)
        {
            if (pawn.health == null || pawn.Dead)
            {
                return;
            }
            float moving = Mathf.Max(0.25f, pawn.health.capacities.GetLevel(PawnCapacityDefOf.Moving));
            if (!Rand.Chance(baseChance / (moving * moving)))
            {
                return;
            }
            List<BodyPartRecord> legs = new List<BodyPartRecord>();
            foreach (BodyPartRecord part in pawn.health.hediffSet.GetNotMissingParts())
            {
                if (part.def.tags != null && (part.def.tags.Contains(BodyPartTagDefOf.MovingLimbCore)
                                              || part.def.tags.Contains(BodyPartTagDefOf.MovingLimbSegment)))
                {
                    legs.Add(part);
                }
            }
            if (legs.Count == 0)
            {
                return;
            }
            BodyPartRecord hurt = legs.RandomElement();
            Hediff bruise = HediffMaker.MakeHediff(EI_FitnessDefOf.Bruise, pawn, hurt);
            bruise.Severity = Rand.Range(1.5f, 3f);
            pawn.health.AddHediff(bruise, hurt);
            if (pawn.Faction == Faction.OfPlayer)
            {
                Messages.Message(pawn.LabelShort + " came down badly on the " + Equipment.LabelShort
                                 + " and bruised their " + hurt.Label + ".",
                                 pawn, MessageTypeDefOf.NegativeHealthEvent);
            }
        }

        /// <summary>
        /// Where the colonist is drawn: on the equipment's model, turned with
        /// it, relative to the cell they are standing in.
        /// </summary>
        public override Vector3 ForcedBodyOffset
        {
            get
            {
                if (!exercising)
                {
                    return Vector3.zero;
                }
                CompExercise exercise = Exercise;
                if (exercise == null || Equipment == null || !Equipment.Spawned)
                {
                    return Vector3.zero;
                }
                CompProperties_Exercise p = exercise.Props;
                Vector3 body = p.bodyAt;
                switch (p.motion)
                {
                    case ExerciseMotion.Bounce:
                        body.z += BounceHeight(p);
                        break;
                    case ExerciseMotion.Climb:
                        body = ClimbPoint(exercise.WorldToModel(pawn.Position.ToVector3Shifted()));
                        break;
                    case ExerciseMotion.Punch:
                        return Vector3.zero;
                }
                Vector3 target = exercise.ModelToWorld(body);
                Vector3 here = pawn.Position.ToVector3Shifted();
                return new Vector3(target.x - here.x, 0f, target.z - here.z);
            }
        }

        /// <summary>
        /// Height above the mat, in tiles, off the game clock - the mat's sag
        /// frames run on the same clock, so it dips as they land.
        /// </summary>
        private static float BounceHeight(CompProperties_Exercise p)
        {
            float phase = (float)(Find.TickManager.TicksGame % p.bounceTicks) / p.bounceTicks;
            if (phase < 0.2f)
            {
                return -0.06f * Mathf.Sin(Mathf.PI * phase / 0.2f);          // pressing into the mat
            }
            float u = (phase - 0.2f) / 0.8f;
            return p.bounceHeight * 4f * u * (1f - u);
        }

        /// <summary>
        /// Up the wall, a pause at the top, a drop to the mat, a breather, and
        /// again - drifting across the face from one climb to the next.
        /// </summary>
        private Vector3 ClimbPoint(Vector3 start)
        {
            int t = (Find.TickManager.TicksGame + pawn.thingIDNumber * 37) % ClimbCycle;
            int round = (Find.TickManager.TicksGame + pawn.thingIDNumber * 37) / ClimbCycle;
            float lane = ((round * 7919 + pawn.thingIDNumber) % 5 - 2) * 0.3f;
            float up;
            if (t < 560)
            {
                float f = t / 560f;
                // hand over hand: rises in steps, not a smooth glide
                up = (Mathf.Floor(f * 8f) + Mathf.SmoothStep(0f, 1f, f * 8f - Mathf.Floor(f * 8f))) / 8f;
            }
            else if (t < 680)
            {
                up = 1f;
            }
            else if (t < 720)
            {
                float f = (t - 680) / 40f;
                up = 1f - f * f;
            }
            else
            {
                up = 0f;
            }
            float height = 1.5f * up;
            // the panel leans back: from y -0.2 at its foot, 0.217 further per tile of height
            float onFace = -0.3f + 0.217f * height;
            float y = Mathf.Lerp(start.y, onFace, Mathf.Clamp01(up * 4f));
            float x = Mathf.Lerp(start.x, lane, Mathf.Clamp01(up * 2f));
            return new Vector3(x, y, height);
        }
    }
}
