using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Sends a pawn to sit in the building itself. The vanilla sit-adjacent
    /// giver seats pawns in a *separate* chair beside the thing they are using,
    /// which is wrong for furniture you get into, so this one targets the
    /// building's own cell. Used by the massage chair and the soaking tub.
    /// </summary>
    public class JoyGiver_SitInBuilding : JoyGiver
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
                    PathEndMode.OnCell,
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
            if (thing.IsForbidden(pawn) || thing.IsBurning())
            {
                return false;
            }
            if (!pawn.CanReserve(thing))
            {
                return false;
            }
            CompPowerTrader power = thing.TryGetComp<CompPowerTrader>();
            if (power != null && !power.PowerOn)
            {
                return false;
            }
            // A tub with a cold firebox is just a tub.
            CompRefuelable fuel = thing.TryGetComp<CompRefuelable>();
            return fuel == null || fuel.HasFuel;
        }
    }

    /// <summary>
    /// Walk to it, settle in, and soak up joy until the pawn has had enough or
    /// something interrupts.
    /// </summary>
    public class JobDriver_SitInBuilding : JobDriver
    {
        private Thing Seat
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);
            AddFailCondition(delegate
            {
                CompPowerTrader power = Seat == null ? null : Seat.TryGetComp<CompPowerTrader>();
                return power != null && !power.PowerOn;
            });

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.OnCell);

            Toil relax = new Toil();
            relax.defaultCompleteMode = ToilCompleteMode.Delay;
            relax.defaultDuration = job.def.joyDuration;
            relax.handlingFacing = true;
            relax.tickAction = delegate
            {
                // Face the way the furniture does, so pawns sit in it rather
                // than standing on it at some random angle.
                if (Seat != null)
                {
                    pawn.rotationTracker.FaceCell(pawn.Position + Seat.Rotation.FacingCell);
                }
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Seat as Building);
            };
            relax.socialMode = RandomSocialMode.Quiet;
            yield return relax;
        }
    }
}
