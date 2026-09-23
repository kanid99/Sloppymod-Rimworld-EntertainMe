using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// A spotted mat, a spinner, and up to three colonists getting in each
    /// other's way.
    ///
    /// A colonist cannot be posed into a knot without Harmony, so the game is
    /// played with what a pawn can do: the spinner turns, every player steps
    /// to another spot on the mat, and every so often somebody goes over and
    /// has to lie there a moment before getting back up. Stood still on the
    /// mat it would just be people waiting; moving about it, it is a game.
    /// </summary>
    public class JoyGiver_Tangle : JoyGiver
    {
        public const int MaxPlayers = 3;

        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing mat = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.OnCell,
                    TraverseParms.For(pawn),
                    40f,
                    t => !t.IsForbidden(pawn) && !t.IsBurning() && t.IsSociallyProper(pawn)
                         && pawn.CanReserve(t, MaxPlayers, 0));
                if (mat != null)
                {
                    return JobMaker.MakeJob(def.jobDef, mat);
                }
            }
            return null;
        }
    }

    public class JobDriver_PlayTangle : JobDriver
    {
        private const int MinHold = 150;
        private const int MaxHold = 320;
        private const float FallChance = 0.12f;
        private const int FallTicks = 110;

        private int played;
        private bool fallen;

        private Thing Mat
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref played, "EI_tanglePlayed", 0);
            Scribe_Values.Look(ref fallen, "EI_tangleFallen", false);
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            // Shared: up to three on one mat. A stack count of 0 is what lets
            // several colonists hold a reservation on the same thing at once.
            return pawn.Reserve(job.targetA, job, JoyGiver_Tangle.MaxPlayers, 0, null, errorOnFailed);
        }

        /// <summary>A spot on the mat, preferring one nobody is standing on.</summary>
        private IntVec3 PickSpot()
        {
            Thing mat = Mat;
            List<IntVec3> free = new List<IntVec3>();
            List<IntVec3> any = new List<IntVec3>();
            foreach (IntVec3 cell in mat.OccupiedRect())
            {
                if (cell == pawn.Position || !cell.Standable(mat.Map))
                {
                    continue;
                }
                any.Add(cell);
                if (cell.GetFirstPawn(mat.Map) == null)
                {
                    free.Add(cell);
                }
            }
            List<IntVec3> from = free.Count > 0 ? free : any;
            return from.Count > 0 ? from[Rand.Range(0, from.Count)] : mat.Position;
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            AddFinishAction(delegate
            {
                pawn.jobs.posture = PawnPosture.Standing;
            });

            // Spin: somewhere else on the mat.
            Toil spin = ToilMaker.MakeToil("EI_TangleSpin");
            spin.initAction = delegate
            {
                job.SetTarget(TargetIndex.B, PickSpot());
            };
            spin.defaultCompleteMode = ToilCompleteMode.Instant;
            yield return spin;

            yield return Toils_Goto.GotoCell(TargetIndex.B, PathEndMode.OnCell);

            // Hold it - or go over.
            Toil hold = ToilMaker.MakeToil("EI_TangleHold");
            hold.initAction = delegate
            {
                fallen = Rand.Chance(FallChance);
                ticksLeftThisToil = fallen ? FallTicks : Rand.RangeInclusive(MinHold, MaxHold);
                pawn.jobs.posture = fallen ? PawnPosture.LayingOnGroundNormal : PawnPosture.Standing;
                pawn.Rotation = Rot4.Random;
            };
            hold.defaultCompleteMode = ToilCompleteMode.Delay;
            hold.defaultDuration = MaxHold;
            hold.handlingFacing = true;
            hold.socialMode = RandomSocialMode.SuperActive;
#if RW16
            hold.tickIntervalAction = delegate(int delta)
            {
                played += delta;
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Mat as Building);
            };
#else
            hold.tickAction = delegate
            {
                played++;
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Mat as Building);
            };
#endif
            hold.AddFinishAction(delegate
            {
                pawn.jobs.posture = PawnPosture.Standing;
            });
            yield return hold;

            // Round again until the session is over.
            yield return Toils_Jump.JumpIf(spin, () => played < job.def.joyDuration);
        }
    }
}
