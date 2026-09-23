using System;
using System.Collections.Generic;
using System.Reflection;
using RimWorld;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// A building that runs out of something a colonist has to top back up -
    /// the tub's water, the skittles lane's standing pins. One work giver and
    /// one job driver serve all of them.
    /// </summary>
    public interface IServiceable
    {
        bool NeedsService { get; }
        int ServiceWorkTicks { get; }
        JobDef ServiceJob { get; }
        void Service();
    }

    [DefOf]
    public static class EI_JobDefOf
    {
        public static JobDef EI_FillWaterBasin;
        public static JobDef EI_ResetPins;

        static EI_JobDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_JobDefOf));
        }
    }

    /// <summary>
    /// Dubs Bad Hygiene is a soft dependency: it is reached by reflection so
    /// this assembly never references it and works fine without it.
    /// </summary>
    public static class DubsPlumbing
    {
        private static bool lookedUp;
        private static PropertyInfo pipeNetProperty;
        private static FieldInfo pipeNetField;
        private static PropertyInfo waterStorageProperty;

        /// <summary>The DBH pipe comp on this thing, if that mod is here and it is piped.</summary>
        public static ThingComp PipeOn(ThingWithComps thing)
        {
            if (thing == null)
            {
                return null;
            }
            List<ThingComp> comps = thing.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                if (comps[i].GetType().FullName == "DubsBadHygiene.CompPipe")
                {
                    return comps[i];
                }
            }
            return null;
        }

        /// <summary>
        /// Reads DubsBadHygiene.CompPipe.pipeNet and asks its PlumbingNet what
        /// it is holding. If their internals ever move, this falls back to
        /// treating a piped building as supplied rather than breaking it.
        /// </summary>
        public static bool NetHasWater(ThingComp pipe)
        {
            if (pipe == null)
            {
                return false;
            }
            if (!lookedUp)
            {
                lookedUp = true;
                try
                {
                    Type pipeType = pipe.GetType();
                    pipeNetProperty = pipeType.GetProperty("pipeNet");
                    if (pipeNetProperty == null)
                    {
                        pipeNetField = pipeType.GetField("pipeNet");
                    }
                    Type netType = pipeNetProperty != null
                        ? pipeNetProperty.PropertyType
                        : (pipeNetField != null ? pipeNetField.FieldType : null);
                    if (netType != null)
                    {
                        waterStorageProperty = netType.GetProperty("WaterStorage");
                    }
                }
                catch (Exception ex)
                {
                    Log.Warning("[Entertaining Ideas] Could not read Dubs Bad Hygiene's "
                                + "plumbing; piped buildings will be treated as supplied. " + ex.Message);
                }
            }

            if (waterStorageProperty == null)
            {
                return true;
            }

            try
            {
                object net = pipeNetProperty != null
                    ? pipeNetProperty.GetValue(pipe, null)
                    : (pipeNetField != null ? pipeNetField.GetValue(pipe) : null);
                if (net == null)
                {
                    return false;   // piped, but not attached to anything
                }
                return Convert.ToSingle(waterStorageProperty.GetValue(net, null)) > 0f;
            }
            catch
            {
                return true;
            }
        }
    }

    /// <summary>
    /// Something that holds a tub's worth of water. A soak empties it and a
    /// colonist has to carry more, unless the building is plumbed in - which it
    /// is when Dubs Bad Hygiene is installed and its pipe reaches the tub.
    /// </summary>
    public class CompProperties_WaterBasin : CompProperties
    {
        /// <summary>Work to carry and pour one tub's worth, in ticks.</summary>
        public int fillWorkTicks = 240;
        /// <summary>Start full when built, so the first soak needs no trip.</summary>
        public bool filledOnSpawn = true;

        public CompProperties_WaterBasin()
        {
            compClass = typeof(CompWaterBasin);
        }
    }

    public class CompWaterBasin : ThingComp, IServiceable
    {
        private bool filled;

        // A thing's comps are fixed when it is constructed, so whether this tub
        // is piped never changes. Worth resolving once: NeedsService is asked
        // for every tub on the map whenever a colonist looks for work.
        private ThingComp pipe;
        private bool pipeResolved;

        private CompProperties_WaterBasin Props
        {
            get { return (CompProperties_WaterBasin)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            if (!respawningAfterLoad && Props.filledOnSpawn)
            {
                filled = true;
            }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref filled, "EI_filled", false);
        }

        private ThingComp Pipe
        {
            get
            {
                if (!pipeResolved)
                {
                    pipeResolved = true;
                    pipe = DubsPlumbing.PipeOn(parent);
                }
                return pipe;
            }
        }

        public bool Plumbed
        {
            get { return Pipe != null; }
        }

        public bool HasWater
        {
            get
            {
                ThingComp plumbing = Pipe;
                return plumbing != null ? DubsPlumbing.NetHasWater(plumbing) : filled;
            }
        }

        public void Fill()
        {
            filled = true;
        }

        // --- IServiceable: a tub off the plumbing needs carrying to ----------
        public bool NeedsService
        {
            get { return !Plumbed && !filled; }
        }

        public int ServiceWorkTicks
        {
            get { return Props.fillWorkTicks; }
        }

        public JobDef ServiceJob
        {
            get { return EI_JobDefOf.EI_FillWaterBasin; }
        }

        public void Service()
        {
            Fill();
        }

        /// <summary>A soak empties a hand-filled tub; a plumbed one refills itself.</summary>
        public void Drain()
        {
            if (!Plumbed)
            {
                filled = false;
            }
        }

        public override string CompInspectStringExtra()
        {
            if (Plumbed)
            {
                return HasWater ? "Plumbed in" : "Plumbed in, but the pipes are dry";
            }
            return filled ? "Full" : "Empty - needs filling before the next soak";
        }
    }

    /// <summary>
    /// Which defs can ever need servicing, worked out once from the comps they
    /// declare rather than kept as a hand-written list that would go stale the
    /// next time a building gains a basin.
    /// </summary>
    public static class ServiceableDefs
    {
        private static List<ThingDef> cached;

        /// <summary>
        /// Worked out on first use rather than in a field initialiser, so it
        /// cannot possibly be built before the defs it reads are loaded.
        /// </summary>
        public static List<ThingDef> All
        {
            get { return cached ?? (cached = Gather()); }
        }

        private static List<ThingDef> Gather()
        {
            List<ThingDef> found = new List<ThingDef>();
            List<ThingDef> all = DefDatabase<ThingDef>.AllDefsListForReading;
            for (int i = 0; i < all.Count; i++)
            {
                List<CompProperties> comps = all[i].comps;
                if (comps == null)
                {
                    continue;
                }
                for (int c = 0; c < comps.Count; c++)
                {
                    if (comps[c].compClass != null
                        && typeof(IServiceable).IsAssignableFrom(comps[c].compClass))
                    {
                        found.Add(all[i]);
                        break;
                    }
                }
            }
            return found;
        }
    }

    public class WorkGiver_ServiceBuilding : WorkGiver_Scanner
    {
        public override ThingRequest PotentialWorkThingRequest
        {
            get { return ThingRequest.ForGroup(ThingRequestGroup.BuildingArtificial); }
        }

        public override PathEndMode PathEndMode
        {
            get { return PathEndMode.Touch; }
        }

        /// <summary>
        /// Only this mod's serviceable buildings, rather than every artificial
        /// building on the map. The request above still says BuildingArtificial
        /// because that is what these things are, but handing the scanner an
        /// explicit set keeps a colonist looking for work from asking a
        /// thousand walls and workbenches whether they need topping up. This is
        /// how WorkGiver_FixBrokenDownBuilding narrows the same group.
        /// </summary>
        public override IEnumerable<Thing> PotentialWorkThingsGlobal(Pawn pawn)
        {
            if (pawn == null || pawn.Map == null)
            {
                yield break;
            }
            List<ThingDef> defs = ServiceableDefs.All;
            for (int i = 0; i < defs.Count; i++)
            {
                List<Thing> things = pawn.Map.listerThings.ThingsOfDef(defs[i]);
                for (int t = 0; t < things.Count; t++)
                {
                    yield return things[t];
                }
            }
        }

        /// <summary>
        /// Nothing anywhere needs filling or resetting, which is the normal
        /// state of affairs, so drop the whole work giver before it scans.
        /// </summary>
        public override bool ShouldSkip(Pawn pawn, bool forced = false)
        {
            if (pawn == null || pawn.Map == null)
            {
                return true;
            }
            List<ThingDef> defs = ServiceableDefs.All;
            for (int i = 0; i < defs.Count; i++)
            {
                List<Thing> things = pawn.Map.listerThings.ThingsOfDef(defs[i]);
                for (int t = 0; t < things.Count; t++)
                {
                    if (ServiceableOn(things[t]) != null)
                    {
                        return false;
                    }
                }
            }
            return true;
        }

        private static IServiceable ServiceableOn(Thing t)
        {
            ThingWithComps twc = t as ThingWithComps;
            if (twc == null)
            {
                return null;
            }
            List<ThingComp> comps = twc.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                IServiceable serviceable = comps[i] as IServiceable;
                if (serviceable != null && serviceable.NeedsService)
                {
                    return serviceable;
                }
            }
            return null;
        }

        public override bool HasJobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            if (ServiceableOn(t) == null)
            {
                return false;
            }
            if (t.IsForbidden(pawn) || t.IsBurning())
            {
                return false;
            }
            return pawn.CanReserve(t, 1, -1, null, forced);
        }

        public override Job JobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            IServiceable serviceable = ServiceableOn(t);
            return serviceable == null ? null : JobMaker.MakeJob(serviceable.ServiceJob, t);
        }
    }

    public class JobDriver_ServiceBuilding : JobDriver
    {
        private IServiceable Target
        {
            get
            {
                ThingWithComps thing = job.GetTarget(TargetIndex.A).Thing as ThingWithComps;
                if (thing == null)
                {
                    return null;
                }
                List<ThingComp> comps = thing.AllComps;
                for (int i = 0; i < comps.Count; i++)
                {
                    IServiceable serviceable = comps[i] as IServiceable;
                    if (serviceable != null && serviceable.ServiceJob == job.def)
                    {
                        return serviceable;
                    }
                }
                return null;
            }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            AddFailCondition(delegate
            {
                IServiceable target = Target;
                return target == null || !target.NeedsService;
            });

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.Touch);

            IServiceable serviceable = Target;
            Toil work = Toils_General.Wait(serviceable != null ? serviceable.ServiceWorkTicks : 240, TargetIndex.A);
            work.WithProgressBarToilDelay(TargetIndex.A);
            work.FailOnDespawnedOrNull(TargetIndex.A);
            yield return work;

            // Its own toil rather than a finish action on the wait. A finish
            // action runs however the toil ends, so a colonist drafted two
            // seconds into filling a tub used to leave it full anyway; this
            // toil is only reached when the work was actually done.
            Toil finish = ToilMaker.MakeToil("EI_FinishService");
            finish.initAction = delegate
            {
                IServiceable target = Target;
                if (target != null)
                {
                    target.Service();
                }
            };
            finish.defaultCompleteMode = ToilCompleteMode.Instant;
            yield return finish;
        }
    }
}
