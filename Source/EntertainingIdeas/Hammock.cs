using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Rest that is not sleep.
    ///
    /// A bed in RimWorld is a whole institution: colonists are assigned to it,
    /// they sleep the night in it, doctors treat them in it, and it wants a
    /// bedroom around it. A hammock is none of that. A colonist gets into one
    /// to do nothing for a while, comes out having had some recreation, and
    /// happens to be a little less tired than they went in. It never competes
    /// with a real bed, because as far as the game is concerned it is not one.
    /// </summary>
    public class CompProperties_Lounger : CompProperties
    {
        /// <summary>
        /// Rest recovered per tick, as a multiple of what a pawn gets lying in
        /// a plain bed. Deliberately well under 1: an afternoon in a hammock is
        /// not a night's sleep, and should never be worth skipping one for.
        /// </summary>
        public float restEffectiveness = 0.45f;

        public CompProperties_Lounger()
        {
            compClass = typeof(CompLounger);
        }
    }

    public class CompLounger : ThingComp
    {
        public float RestEffectiveness
        {
            get { return ((CompProperties_Lounger)props).restEffectiveness; }
        }

        public override string CompInspectStringExtra()
        {
            return "Not a bed: colonists lounge here, they do not sleep here.";
        }
    }

    /// <summary>
    /// Climb in, lie back, and do nothing on purpose. Joy accrues as it would
    /// in any recreation building; rest trickles back at the lounger's rate.
    /// </summary>
    public class JobDriver_Lounge : JobDriver
    {
        private Thing Lounger
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

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.OnCell);

            Toil lounge = ToilMaker.MakeToil("EI_Lounge");
            lounge.initAction = delegate
            {
                pawn.jobs.posture = PawnPosture.LayingOnGroundNormal;
            };
            lounge.defaultCompleteMode = ToilCompleteMode.Delay;
            lounge.defaultDuration = job.def.joyDuration;
            lounge.handlingFacing = true;
#if RW16
            lounge.tickIntervalAction = delegate(int delta)
            {
                Lounge(delta);
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Lounger as Building);
            };
#else
            lounge.tickAction = delegate
            {
                Lounge(1);
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Lounger as Building);
            };
#endif
            lounge.AddFinishAction(delegate
            {
                pawn.jobs.posture = PawnPosture.Standing;
            });
            lounge.socialMode = RandomSocialMode.Quiet;
            yield return lounge;
        }

        private void Lounge(int delta)
        {
            pawn.jobs.posture = PawnPosture.LayingOnGroundNormal;

            Need_Rest rest = pawn.needs == null ? null : pawn.needs.rest;
            if (rest == null || Lounger == null)
            {
                return;
            }
            CompLounger lounger = Lounger.TryGetComp<CompLounger>();
            if (lounger == null)
            {
                return;
            }
            // TickResting expects to be called once per tick, so on 1.6's
            // variable intervals it is called for each tick that elapsed.
            for (int i = 0; i < delta; i++)
            {
                rest.TickResting(lounger.RestEffectiveness);
            }
        }
    }
}
