using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_StoryDefOf
    {
        public static JobDef EI_TellStory;
        public static JobDef EI_ListenToStory;

        static EI_StoryDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_StoryDefOf));
        }
    }

    /// <summary>
    /// What counts as a fire to tell stories by.
    ///
    /// Anything that draws a proper flame - vanilla's campfire, and the fire
    /// pits and braziers other mods add - rather than a hand-kept list of
    /// defNames. RimWorld marks those with a fire overlay comp, and its size
    /// separates a campfire from a wall torch. Campfire itself is accepted by
    /// name as well, so this still works if its overlay size ever changes.
    /// </summary>
    public static class StoryFire
    {
        private static readonly Dictionary<ThingDef, bool> isFire = new Dictionary<ThingDef, bool>();

        public static bool IsFireDef(ThingDef def, float minSize)
        {
            bool cached;
            if (isFire.TryGetValue(def, out cached))
            {
                return cached;
            }
            bool result = def.defName == "Campfire";
            if (!result && def.comps != null)
            {
                for (int i = 0; i < def.comps.Count; i++)
                {
                    CompProperties_FireOverlay overlay = def.comps[i] as CompProperties_FireOverlay;
                    if (overlay != null && overlay.fireSize >= minSize)
                    {
                        result = true;
                        break;
                    }
                }
            }
            isFire[def] = result;
            return result;
        }

        /// <summary>A fire thing that is burning right now.</summary>
        public static bool IsLit(Thing thing)
        {
            CompRefuelable fuel = thing.TryGetComp<CompRefuelable>();
            return fuel == null || fuel.HasFuel;
        }

        /// <summary>The nearest fire within range, lit or not.</summary>
        public static Thing Nearest(Map map, IntVec3 center, float radius, float minSize, bool mustBeLit)
        {
            Thing best = null;
            float bestDistance = float.MaxValue;
            foreach (IntVec3 cell in GenRadial.RadialCellsAround(center, radius, true))
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                Building building = cell.GetFirstBuilding(map);
                if (building == null || !IsFireDef(building.def, minSize))
                {
                    continue;
                }
                if (mustBeLit && !IsLit(building))
                {
                    continue;
                }
                float distance = cell.DistanceToSquared(center);
                if (distance < bestDistance)
                {
                    best = building;
                    bestDistance = distance;
                }
            }
            return best;
        }
    }

    public class StoryMotif
    {
        public string framePath;
        public int frameCount = 10;
    }

    public class CompProperties_Storyteller : CompProperties
    {
        /// <summary>How far from the stump a fire can be and still count.</summary>
        public float fireRadius = 6f;
        public float minFireSize = 0.5f;
        /// <summary>How often to look for the fire again, in ticks.</summary>
        public int recheckInterval = 250;
        public List<StoryMotif> motifs = new List<StoryMotif>();
        public int ticksPerFrame = 20;
        public Vector2 drawSize = new Vector2(1f, 1.5f);
        /// <summary>Where over the fire the smoke shapes sit, so they rise out of the flame.</summary>
        public Vector3 smokeOffset = new Vector3(0f, 0f, 0.95f);

        public CompProperties_Storyteller()
        {
            compClass = typeof(CompStoryteller);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (motifs == null || motifs.Count == 0)
            {
                yield return "CompProperties_Storyteller needs at least one motif.";
            }
            if (ticksPerFrame < 1)
            {
                yield return "CompProperties_Storyteller needs ticksPerFrame >= 1.";
            }
        }
    }

    /// <summary>
    /// A stump to stand on and tell stories from, beside a fire.
    ///
    /// A colonist cannot be posed without Harmony, so the teller just stands
    /// there talking. The show is in the smoke: while a story is under way,
    /// shapes out of it rise from the nearest fire and fade - a thrumbo, a
    /// raider, a ship, a mechanoid - one after another.
    /// </summary>
    public class CompStoryteller : ThingComp
    {
        private FrameSet[] motifs;
        private Thing fire;
        private int nextFireCheck = -99999;

        private CompProperties_Storyteller Props
        {
            get { return (CompProperties_Storyteller)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            motifs = new FrameSet[Props.motifs.Count];
            for (int i = 0; i < motifs.Length; i++)
            {
                motifs[i] = new FrameSet(Props.motifs[i].framePath, Props.motifs[i].frameCount, Props.drawSize);
            }
            nextFireCheck = -99999;
        }

        /// <summary>A burning fire close enough to tell stories by, or null.</summary>
        public Thing LitFire
        {
            get
            {
                if (!parent.Spawned)
                {
                    return null;
                }
                int now = Find.TickManager.TicksGame;
                if (now >= nextFireCheck || (fire != null && (!fire.Spawned || !StoryFire.IsLit(fire))))
                {
                    nextFireCheck = now + Props.recheckInterval;
                    fire = StoryFire.Nearest(parent.Map, parent.Position, Props.fireRadius,
                                             Props.minFireSize, true);
                }
                return fire;
            }
        }

        /// <summary>
        /// Whoever is standing on the stump telling a story. Only the stump's
        /// own cell is looked at, so this is cheap enough to ask every frame.
        /// </summary>
        public Pawn Teller
        {
            get
            {
                if (!parent.Spawned)
                {
                    return null;
                }
                List<Thing> things = parent.Position.GetThingList(parent.Map);
                for (int i = 0; i < things.Count; i++)
                {
                    Pawn pawn = things[i] as Pawn;
                    if (pawn == null)
                    {
                        continue;
                    }
                    Job job = pawn.CurJob;
                    if (job != null && job.def == EI_StoryDefOf.EI_TellStory && job.targetA.Thing == parent)
                    {
                        return pawn;
                    }
                }
                return null;
            }
        }

        public bool StoryUnderway
        {
            get { return Teller != null && LitFire != null; }
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (motifs == null || motifs.Length == 0 || Teller == null)
            {
                return;
            }
            Thing flame = LitFire;
            if (flame == null)
            {
                return;
            }
            // Each pass of the strip is the next story, so the shapes change
            // over the course of an evening rather than repeating one.
            int loop = Props.ticksPerFrame * Props.motifs[0].frameCount;
            int index = (Find.TickManager.TicksGame / Mathf.Max(1, loop)) % motifs.Length;
            FrameSet set = motifs[index];
            Graphic graphic = set.At(set.IndexFor(Props.ticksPerFrame));
            if (graphic == null)
            {
                return;
            }
            Vector3 at = flame.DrawPos + Props.smokeOffset;
            at.y = AltitudeLayer.MoteOverhead.AltitudeFor();
            graphic.Draw(at, Rot4.North, parent, 0f);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (LitFire == null)
            {
                return "No lit fire within " + Mathf.RoundToInt(Props.fireRadius)
                       + " tiles - stories want a campfire.";
            }
            Pawn teller = Teller;
            return teller != null
                ? teller.LabelShort + " is telling a story."
                : "Beside a fire, waiting for someone with a story to tell.";
        }
    }

    /// <summary>
    /// While placing, the ring the fire has to be inside, and a line to the
    /// fire the stump would use - or nothing, which says there is none yet.
    /// </summary>
    public class PlaceWorker_StoryFire : PlaceWorker
    {
        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            Map map = Find.CurrentMap;
            CompProperties_Storyteller props = def.GetCompProperties<CompProperties_Storyteller>();
            if (map == null || props == null)
            {
                return;
            }
            GenDraw.DrawRadiusRing(center, props.fireRadius);
            Thing fire = StoryFire.Nearest(map, center, props.fireRadius, props.minFireSize, false);
            if (fire != null)
            {
                GenDraw.DrawLineBetween(center.ToVector3Shifted(), fire.TrueCenter());
            }
        }
    }

    /// <summary>Someone steps up onto a stump that has a fire beside it and nobody on it.</summary>
    public class JoyGiver_TellStory : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing stump = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.OnCell,
                    TraverseParms.For(pawn),
                    40f,
                    t => Usable(pawn, t));
                if (stump != null)
                {
                    return JobMaker.MakeJob(def.jobDef, stump);
                }
            }
            return null;
        }

        private static bool Usable(Pawn pawn, Thing stump)
        {
            if (stump.IsForbidden(pawn) || stump.IsBurning() || !stump.IsSociallyProper(pawn))
            {
                return false;
            }
            CompStoryteller comp = stump.TryGetComp<CompStoryteller>();
            return comp != null && comp.Teller == null && comp.LitFire != null
                   && pawn.CanReserveSittableOrSpot(stump.Position);
        }
    }

    /// <summary>
    /// Stand on the stump and talk, facing the audience. The sit-in-building
    /// job already does going there and facing the way the stump faces; this
    /// changes what is claimed and when it stops.
    /// </summary>
    public class JobDriver_TellStory : JobDriver_SitInBuilding
    {
        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            // The stump's cell, not the stump. Listeners find the stump through
            // vanilla's watch-building giver, which is not written to expect
            // the thing they watch to be reserved by someone else.
            return pawn.ReserveSittableOrSpot(job.targetA.Thing.Position, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            // The fire went out: the evening is over.
            AddFailCondition(delegate
            {
                Thing stump = job.targetA.Thing;
                CompStoryteller comp = stump == null ? null : stump.TryGetComp<CompStoryteller>();
                return comp == null || comp.LitFire == null;
            });
            foreach (Toil toil in base.MakeNewToils())
            {
                yield return toil;
            }
        }
    }

    /// <summary>Gather round - but only while somebody is actually telling one.</summary>
    public class JoyGiver_ListenToStory : JoyGiver_WatchBuilding
    {
        protected override bool CanInteractWith(Pawn pawn, Thing t, bool inBed)
        {
            if (!base.CanInteractWith(pawn, t, inBed))
            {
                return false;
            }
            CompStoryteller comp = t.TryGetComp<CompStoryteller>();
            if (comp == null || !comp.StoryUnderway)
            {
                return false;
            }
            return comp.Teller != pawn;
        }
    }

    /// <summary>Vanilla watching, ended when the story is.</summary>
    public class JobDriver_ListenToStory : JobDriver_WatchBuilding
    {
        protected override IEnumerable<Toil> MakeNewToils()
        {
            AddEndCondition(delegate
            {
                Thing stump = job.targetA.Thing;
                CompStoryteller comp = stump == null ? null : stump.TryGetComp<CompStoryteller>();
                return comp != null && comp.StoryUnderway ? JobCondition.Ongoing : JobCondition.Succeeded;
            });
            foreach (Toil toil in base.MakeNewToils())
            {
                yield return toil;
            }
        }
    }
}
