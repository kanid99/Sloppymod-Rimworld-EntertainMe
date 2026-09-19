using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Plays a looping frame animation over a recreation building, but only
    /// while a pawn is actually using it (and only while it has power).
    ///
    /// Frames are ordinary textures named "<framePath>_0" up to
    /// "<framePath>_(frameCount-1)". They are drawn on top of the building at
    /// the same draw size, so a frame only needs to cover the part that moves.
    /// </summary>
    public class CompProperties_AnimatedScreen : CompProperties
    {
        /// <summary>Texture path without the frame index suffix.</summary>
        public string framePath;
        public int frameCount = 16;
        /// <summary>Game ticks each frame is held. 60 ticks = 1 second at normal speed.</summary>
        public int ticksPerFrame = 8;
        public Vector2 drawSize = Vector2.one;
        /// <summary>Lifts the overlay clear of the building underneath it.</summary>
        public float altitudeOffset = 0.05f;
        /// <summary>How often to re-check whether anyone is playing, in ticks.</summary>
        public int recheckInterval = 20;
        /// <summary>Jobs that count as using this building.</summary>
        public List<JobDef> playJobs = new List<JobDef>();
        /// <summary>Turn the frames to match a rotatable building's facing.</summary>
        public bool rotateWithBuilding = false;
        /// <summary>
        /// Draw above pawns instead of on the building. Used to hide the lower
        /// half of whoever is in a soaking tub.
        ///
        /// 1.6 does render swimmers properly, but it does it by swapping the
        /// pawn to a dedicated swimming graphic, gated on Pawn.Swimming, which
        /// is read-only and derived from the terrain the pawn is standing in.
        /// A building on an ordinary floor can never set it, so a waterline
        /// painted over the occupant is the portable way to get the look - and
        /// unlike the real pose it also works on 1.5.
        /// </summary>
        public bool drawOverPawns = false;
        /// <summary>Only draw while a refuelable parent still has fuel.</summary>
        public bool requireFuel = false;
        /// <summary>
        /// How far to look for someone using this, in cells. 0 checks the
        /// building's own cells and the ring around them, which covers
        /// interaction cells and adjacent chairs.
        /// </summary>
        public float scanRadius = 0f;
        /// <summary>
        /// When false the animation runs whenever the building is on, instead
        /// of only while a pawn is using it. Suits things that move under their
        /// own steam, like a lantern that turns on its own draught.
        /// </summary>
        public bool requireUser = true;

        public CompProperties_AnimatedScreen()
        {
            compClass = typeof(CompAnimatedScreen);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (framePath.NullOrEmpty())
            {
                yield return "CompProperties_AnimatedScreen needs a framePath.";
            }
            if (frameCount < 1)
            {
                yield return "CompProperties_AnimatedScreen needs frameCount >= 1.";
            }
            if (ticksPerFrame < 1)
            {
                yield return "CompProperties_AnimatedScreen needs ticksPerFrame >= 1.";
            }
            if (requireUser && (playJobs == null || playJobs.Count == 0))
            {
                yield return "CompProperties_AnimatedScreen needs at least one entry in playJobs when requireUser is true.";
            }
        }
    }

    public class CompAnimatedScreen : ThingComp
    {
        private FrameSet frames;
        private CompPowerTrader power;
        private CompRefuelable fuel;
        private bool inUse;
        private int nextRecheckTick = -99999;

        private CompProperties_AnimatedScreen Props
        {
            get { return (CompProperties_AnimatedScreen)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            fuel = parent.TryGetComp<CompRefuelable>();
            frames = new FrameSet(Props.framePath, Props.frameCount, Props.drawSize);
            nextRecheckTick = -99999;
        }

        public override void PostDraw()
        {
            base.PostDraw();

            if (!parent.Spawned)
            {
                return;
            }
            if (power != null && !power.PowerOn)
            {
                return;
            }
            if (Props.requireFuel && fuel != null && !fuel.HasFuel)
            {
                return;
            }
            if (Props.requireUser && !AnyoneStillPlaying())
            {
                return;
            }

            Graphic graphic = frames.At(frames.IndexFor(Props.ticksPerFrame));
            if (graphic == null)
            {
                return;
            }

            Vector3 drawPos = parent.DrawPos;
            drawPos.y = Props.drawOverPawns
                ? AltitudeLayer.MoteOverhead.AltitudeFor() + Props.altitudeOffset
                : drawPos.y + Props.altitudeOffset;
            float extraRotation = Props.rotateWithBuilding ? parent.Rotation.AsAngle - 180f : 0f;
            graphic.Draw(drawPos, Rot4.North, parent, extraRotation);
        }

        /// <summary>
        /// Cached because PostDraw runs every rendered frame but the answer can
        /// only change every few ticks.
        /// </summary>
        private bool AnyoneStillPlaying()
        {
            int now = Find.TickManager.TicksGame;
            if (now >= nextRecheckTick)
            {
                nextRecheckTick = now + Props.recheckInterval;
                inUse = ScanForPlayer();
            }
            return inUse;
        }

        private bool ScanForPlayer()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return false;
            }

            // A user may stand on the interaction cell, sit in a chair beside
            // the building, sit in the building itself, or - for things a crowd
            // gathers around - stand a few tiles back.
            IEnumerable<IntVec3> cells = Props.scanRadius > 0f
                ? GenRadial.RadialCellsAround(parent.Position, Props.scanRadius, true)
                : GenAdj.CellsOccupiedBy(parent).Concat(GenAdj.CellsAdjacent8Way(parent));
            foreach (IntVec3 cell in cells)
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                List<Thing> things = cell.GetThingList(map);
                for (int i = 0; i < things.Count; i++)
                {
                    Pawn pawn = things[i] as Pawn;
                    if (pawn == null)
                    {
                        continue;
                    }
                    Job job = pawn.CurJob;
                    if (job == null || !Props.playJobs.Contains(job.def))
                    {
                        continue;
                    }
                    if (JobTargetsParent(job))
                    {
                        return true;
                    }
                }
            }
            return false;
        }

        private bool JobTargetsParent(Job job)
        {
            if (job.targetA.Thing == parent || job.targetB.Thing == parent || job.targetC.Thing == parent)
            {
                return true;
            }
            // Some joy givers record only cells; an adjacent pawn running one of
            // our play jobs is this building's player either way.
            return job.targetA.Thing == null && job.targetB.Thing == null && job.targetC.Thing == null;
        }
    }
}
