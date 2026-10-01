using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Pins that stay where the ball leaves them. After a few games somebody
    /// has to walk down and stand them back up, which is the whole difference
    /// between a skittles alley and a bowling lane with a pinsetter in it.
    /// </summary>
    public class CompProperties_PinDeck : CompProperties
    {
        public int gamesPerReset = 3;
        public int resetWorkTicks = 300;

        public CompProperties_PinDeck()
        {
            compClass = typeof(CompPinDeck);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (gamesPerReset < 1)
            {
                yield return "CompProperties_PinDeck needs gamesPerReset >= 1.";
            }
        }
    }

    public class CompPinDeck : ThingComp, IServiceable
    {
        private int gamesLeft = -1;

        private CompProperties_PinDeck Props
        {
            get { return (CompProperties_PinDeck)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            if (gamesLeft < 0)
            {
                gamesLeft = Props.gamesPerReset;
            }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref gamesLeft, "EI_gamesLeft", -1);
        }

        public void Notify_GamePlayed()
        {
            if (gamesLeft > 0)
            {
                gamesLeft--;
            }
        }

        public bool NeedsService
        {
            get { return gamesLeft <= 0; }
        }

        public int ServiceWorkTicks
        {
            get { return Props.resetWorkTicks; }
        }

        public JobDef ServiceJob
        {
            get { return EI_JobDefOf.EI_ResetPins; }
        }

        public void Service()
        {
            gamesLeft = Props.gamesPerReset;
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            return NeedsService
                ? "Pins down - somebody needs to set them up"
                : "Pins standing: " + gamesLeft + " more game" + (gamesLeft == 1 ? "" : "s");
        }
    }

    /// <summary>
    /// Vanilla's interaction-cell giver, plus a check that the building is not
    /// waiting on somebody. Stops colonists queueing up at a lane whose pins
    /// are all lying down.
    /// </summary>
    public class JoyGiver_InteractBuildingServiceable : JoyGiver_InteractBuildingInteractionCell
    {
        protected override bool CanInteractWith(Pawn pawn, Thing t, bool inBed)
        {
            if (!base.CanInteractWith(pawn, t, inBed))
            {
                return false;
            }
            ThingWithComps thing = t as ThingWithComps;
            if (thing == null)
            {
                return true;
            }
            List<ThingComp> comps = thing.AllComps;
            for (int i = 0; i < comps.Count; i++)
            {
                IServiceable serviceable = comps[i] as IServiceable;
                if (serviceable != null && serviceable.NeedsService)
                {
                    return false;
                }
            }
            return true;
        }
    }

    /// <summary>
    /// Vanilla's watch-building job with one addition: playing knocks the pins
    /// over. The count comes off when the session ends, however it ends.
    /// </summary>
    public class JobDriver_PlayAtPinDeck : JobDriver_WatchBuilding
    {
        protected override IEnumerable<Toil> MakeNewToils()
        {
            AddFinishAction(delegate
            {
                // Only a game actually played: a colonist called away on the
                // way to the lane never reached their spot and rolled nothing.
                Thing thing = job.GetTarget(TargetIndex.A).Thing;
                if (thing != null && pawn.Spawned && pawn.Position == job.GetTarget(TargetIndex.B).Cell)
                {
                    CompPinDeck deck = thing.TryGetComp<CompPinDeck>();
                    if (deck != null)
                    {
                        deck.Notify_GamePlayed();
                    }
                }
            });
            foreach (Toil toil in base.MakeNewToils())
            {
                yield return toil;
            }
        }
    }
}
