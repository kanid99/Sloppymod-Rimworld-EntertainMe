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

        // Dubs Bad Hygiene is a soft dependency: it is reached by reflection so
        // this assembly never references it and works fine without it.
        private static bool dbhLookedUp;
        private static PropertyInfo pipeNetProperty;
        private static FieldInfo pipeNetField;
        private static PropertyInfo waterStorageProperty;

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

        /// <summary>The DBH pipe comp, if that mod is here and this is piped.</summary>
        private ThingComp PipeComp
        {
            get
            {
                List<ThingComp> comps = parent.AllComps;
                for (int i = 0; i < comps.Count; i++)
                {
                    if (comps[i].GetType().FullName == "DubsBadHygiene.CompPipe")
                    {
                        return comps[i];
                    }
                }
                return null;
            }
        }

        public bool Plumbed
        {
            get { return PipeComp != null; }
        }

        public bool HasWater
        {
            get
            {
                ThingComp pipe = PipeComp;
                return pipe != null ? NetHasWater(pipe) : filled;
            }
        }

        /// <summary>
        /// Reads DubsBadHygiene.CompPipe.pipeNet and asks its PlumbingNet what
        /// it is holding. If their internals ever move, this falls back to
        /// treating a piped tub as supplied rather than breaking the building.
        /// </summary>
        private static bool NetHasWater(ThingComp pipe)
        {
            if (!dbhLookedUp)
            {
                dbhLookedUp = true;
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
                                + "plumbing; piped tubs will be treated as supplied. " + ex.Message);
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
            work.AddFinishAction(delegate
            {
                IServiceable target = Target;
                if (target != null)
                {
                    target.Service();
                }
            });
            yield return work;
        }
    }
}
