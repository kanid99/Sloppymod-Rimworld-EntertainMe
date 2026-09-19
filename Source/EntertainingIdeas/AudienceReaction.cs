using System.Collections.Generic;
using RimWorld;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// While someone is using this building, everyone else in the room forms an
    /// opinion about it. Whether they enjoy it depends on how good the user is,
    /// what they think of them, and a fixed streak of taste that makes some
    /// colonists reliable fans and others reliable sufferers. Being well liked
    /// carries a bad performer: affection is weighted heavily enough to cover
    /// the whole skill penalty and then some.
    ///
    /// Also hands the performer experience in a second skill, since a JobDef
    /// only carries one joySkill and singing is practice at two things.
    /// </summary>
    public class CompProperties_AudienceReaction : CompProperties
    {
        /// <summary>Jobs at this building that produce the performance.</summary>
        public List<JobDef> userJobs = new List<JobDef>();
        public ThoughtDef goodThought;
        public ThoughtDef badThought;
        /// <summary>How often listeners form a fresh memory, in ticks.</summary>
        public int intervalTicks = 1250;
        /// <summary>How far to look for the performer.</summary>
        public float scanRadius = 5f;
        /// <summary>Skill that decides whether the performance is any good.</summary>
        public SkillDef performanceSkill;
        /// <summary>Skill level at which a performance is a coin flip.</summary>
        public float neutralSkill = 8f;
        public float skillWeight = 4f;
        public float opinionWeight = 0.4f;
        /// <summary>How far personal taste can swing the verdict either way.</summary>
        public float tasteSpread = 25f;
        public bool requiresHearing = true;
        /// <summary>Second skill the performer practises, beyond the job's joySkill.</summary>
        public SkillDef performerSkill;
        public float performerXpPerPulse = 0f;

        public CompProperties_AudienceReaction()
        {
            compClass = typeof(CompAudienceReaction);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (goodThought == null || badThought == null)
            {
                yield return "CompProperties_AudienceReaction needs both goodThought and badThought.";
            }
            if (userJobs == null || userJobs.Count == 0)
            {
                yield return "CompProperties_AudienceReaction needs at least one entry in userJobs.";
            }
            if (intervalTicks < 1)
            {
                yield return "CompProperties_AudienceReaction needs intervalTicks >= 1.";
            }
            if (parentDef != null && parentDef.tickerType == TickerType.Never)
            {
                yield return "CompProperties_AudienceReaction needs a tickerType of Rare or Normal.";
            }
        }
    }

    public class CompAudienceReaction : ThingComp
    {
        private CompPowerTrader power;
        private int ticksToPulse;
        private int lastPleased;
        private int lastAnnoyed;

        private CompProperties_AudienceReaction Props
        {
            get { return (CompProperties_AudienceReaction)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
        }

        public override void CompTick()
        {
            if (--ticksToPulse <= 0)
            {
                ticksToPulse = Props.intervalTicks;
                Pulse();
            }
        }

        public override void CompTickRare()
        {
            ticksToPulse -= 250;
            if (ticksToPulse <= 0)
            {
                ticksToPulse = Props.intervalTicks;
                Pulse();
            }
        }

        private void Pulse()
        {
            lastPleased = 0;
            lastAnnoyed = 0;

            if (!parent.Spawned || (power != null && !power.PowerOn))
            {
                return;
            }

            Pawn performer = FindPerformer();
            if (performer == null)
            {
                return;
            }

            // The performer practises whether or not anyone is listening.
            if (Props.performerSkill != null && Props.performerXpPerPulse > 0f
                && performer.skills != null)
            {
                performer.skills.Learn(Props.performerSkill, Props.performerXpPerPulse);
            }

            Room room = parent.GetRoom();
            if (room == null)
            {
                return;
            }

            List<Pawn> pawns = parent.Map.mapPawns.FreeColonistsAndPrisonersSpawned;
            for (int i = 0; i < pawns.Count; i++)
            {
                Pawn listener = pawns[i];
                if (listener == performer || listener.GetRoom() != room)
                {
                    continue;
                }
                if (listener.needs == null || listener.needs.mood == null)
                {
                    continue;
                }
                if (Props.requiresHearing
                    && !listener.health.capacities.CapableOf(PawnCapacityDefOf.Hearing))
                {
                    continue;
                }

                bool enjoyed = Verdict(listener, performer);
                listener.needs.mood.thoughts.memories.TryGainMemory(
                    enjoyed ? Props.goodThought : Props.badThought, performer);
                if (enjoyed)
                {
                    lastPleased++;
                }
                else
                {
                    lastAnnoyed++;
                }
            }
        }

        /// <summary>
        /// Above the halfway mark they liked it. Skill pushes the whole room one
        /// way, opinion of the performer pulls each listener individually, and
        /// taste is fixed per pawn so the same colonist reacts the same way
        /// every time rather than flip-flopping.
        ///
        /// Opinion is deliberately the heavier term. A hopeless singer their
        /// friends are fond of still goes down well; the same performance in
        /// front of strangers does not.
        /// </summary>
        private bool Verdict(Pawn listener, Pawn performer)
        {
            float score = 50f;

            if (Props.performanceSkill != null && performer.skills != null)
            {
                SkillRecord skill = performer.skills.GetSkill(Props.performanceSkill);
                if (skill != null)
                {
                    score += (skill.Level - Props.neutralSkill) * Props.skillWeight;
                }
            }
            if (listener.relations != null)
            {
                score += listener.relations.OpinionOf(performer) * Props.opinionWeight;
            }
            score += Taste(listener);
            return score >= 50f;
        }

        private float Taste(Pawn listener)
        {
            // Stable per pawn: same colonist, same opinion of the noise, always.
            int hash = Gen.HashCombineInt(listener.thingIDNumber, 0x5EA5017);
            float unit = (hash & 0x7FFFFFFF) % 1000 / 1000f;
            return (unit * 2f - 1f) * Props.tasteSpread;
        }

        private Pawn FindPerformer()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return null;
            }
            foreach (IntVec3 cell in GenRadial.RadialCellsAround(parent.Position, Props.scanRadius, true))
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                List<Thing> things = cell.GetThingList(map);
                for (int i = 0; i < things.Count; i++)
                {
                    Pawn pawn = things[i] as Pawn;
                    if (pawn == null || pawn.CurJob == null)
                    {
                        continue;
                    }
                    if (Props.userJobs.Contains(pawn.CurJob.def))
                    {
                        return pawn;
                    }
                }
            }
            return null;
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned || (lastPleased == 0 && lastAnnoyed == 0))
            {
                return null;
            }
            return "Audience: " + lastPleased + " enjoying it, " + lastAnnoyed + " enduring it";
        }
    }
}
