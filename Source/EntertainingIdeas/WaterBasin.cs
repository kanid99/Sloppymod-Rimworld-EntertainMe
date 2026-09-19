using System;
using System.Collections.Generic;
using System.Reflection;
using RimWorld;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_JobDefOf
    {
        public static JobDef EI_FillWaterBasin;

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

    public class CompWaterBasin : ThingComp
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

    public class WorkGiver_FillWaterBasin : WorkGiver_Scanner
    {
        public override ThingRequest PotentialWorkThingRequest
        {
            get { return ThingRequest.ForGroup(ThingRequestGroup.BuildingArtificial); }
        }

        public override PathEndMode PathEndMode
        {
            get { return PathEndMode.Touch; }
        }

        public override bool HasJobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            CompWaterBasin basin = t.TryGetComp<CompWaterBasin>();
            if (basin == null || basin.Plumbed || basin.HasWater)
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
            return JobMaker.MakeJob(EI_JobDefOf.EI_FillWaterBasin, t);
        }
    }

    public class JobDriver_FillWaterBasin : JobDriver
    {
        private CompWaterBasin Basin
        {
            get
            {
                Thing thing = job.GetTarget(TargetIndex.A).Thing;
                return thing == null ? null : thing.TryGetComp<CompWaterBasin>();
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
                CompWaterBasin basin = Basin;
                return basin == null || basin.HasWater;
            });

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.Touch);

            CompProperties_WaterBasin props = null;
            Thing target = job.GetTarget(TargetIndex.A).Thing;
            if (target != null)
            {
                CompWaterBasin comp = target.TryGetComp<CompWaterBasin>();
                if (comp != null)
                {
                    props = (CompProperties_WaterBasin)comp.props;
                }
            }

            Toil fill = Toils_General.Wait(props != null ? props.fillWorkTicks : 240, TargetIndex.A);
            fill.WithProgressBarToilDelay(TargetIndex.A);
            fill.FailOnDespawnedOrNull(TargetIndex.A);
            fill.AddFinishAction(delegate
            {
                CompWaterBasin basin = Basin;
                if (basin != null)
                {
                    basin.Fill();
                }
            });
            yield return fill;
        }
    }
}
