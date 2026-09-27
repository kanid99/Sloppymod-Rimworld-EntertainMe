using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;
using Verse.Sound;

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
    /// <summary>A sound to play when the play loop reaches a particular frame.</summary>
    public class FrameSound
    {
        public int frame;
        public SoundDef sound;
    }

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
        /// <summary>
        /// Sounds tied to the play loop: each plays once when the loop reaches
        /// its frame, so a sound lands on the moment it belongs to - the ore
        /// vanishing, the player leaving the girder. Frames come off the game
        /// clock, so nothing plays while the game is paused.
        /// </summary>
        public List<FrameSound> frameSounds = new List<FrameSound>();
        /// <summary>
        /// Played now and then while the attract loop runs, so an idle cabinet
        /// reads as switched on. Kept rare: every idleSoundIntervalTicks.
        /// </summary>
        public SoundDef idleSound;
        public int idleSoundIntervalTicks = 3000;
        /// <summary>
        /// Only draw when the building faces one of these. For something with
        /// a front face, like a TV: the face-on animation belongs to the view
        /// that shows the face, not to the edge-on side views. Empty = always.
        /// </summary>
        public List<Rot4> drawRotations = new List<Rot4>();
        /// <summary>Turn the frames to match a rotatable building's facing.</summary>
        public bool rotateWithBuilding = false;
        /// <summary>
        /// A separately drawn set of frames for each facing, for a building
        /// whose four views are drawn rather than turned: the frames are
        /// framePath + North/East/South/West (and the same for the idle loop),
        /// and drawSize is swapped for east and west as a Graphic_Multi's is.
        /// </summary>
        public bool perFacing = false;
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
        /// <summary>
        /// Optional attract loop, shown while the building is powered but
        /// nobody is playing - a real cabinet never sits on a black screen.
        /// Leave unset and an idle building simply shows nothing.
        /// </summary>
        public string idleFramePath;
        public int idleFrameCount = 0;
        /// <summary>Attract loops run slower than play; defaults to 3x.</summary>
        public int idleTicksPerFrame = 0;

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
            if (!idleFramePath.NullOrEmpty() && idleFrameCount < 1)
            {
                yield return "CompProperties_AnimatedScreen has an idleFramePath but no idleFrameCount.";
            }
            if (idleFrameCount > 0 && idleFramePath.NullOrEmpty())
            {
                yield return "CompProperties_AnimatedScreen has an idleFrameCount but no idleFramePath.";
            }
            if (idleFrameCount > 0 && !requireUser)
            {
                yield return "CompProperties_AnimatedScreen idle frames do nothing when requireUser is false: the play loop already runs constantly.";
            }
            if (frameSounds != null)
            {
                for (int i = 0; i < frameSounds.Count; i++)
                {
                    if (frameSounds[i].sound == null)
                    {
                        yield return "CompProperties_AnimatedScreen frameSounds entry " + i + " has no sound.";
                    }
                    else if (frameSounds[i].frame < 0 || frameSounds[i].frame >= frameCount)
                    {
                        yield return "CompProperties_AnimatedScreen frameSounds entry " + i + " names frame "
                                     + frameSounds[i].frame + ", outside 0.." + (frameCount - 1) + ".";
                    }
                }
            }
            if (idleSound != null && idleSoundIntervalTicks < 60)
            {
                yield return "CompProperties_AnimatedScreen idleSoundIntervalTicks under 60 would nag.";
            }
            if (perFacing && rotateWithBuilding)
            {
                yield return "CompProperties_AnimatedScreen: perFacing frames are drawn per facing already, so rotateWithBuilding must be false.";
            }
            if (requireUser && (playJobs == null || playJobs.Count == 0))
            {
                yield return "CompProperties_AnimatedScreen needs at least one entry in playJobs when requireUser is true.";
            }
        }
    }

    public class CompAnimatedScreen : ThingComp
    {
        private static readonly string[] FacingNames = { "North", "East", "South", "West" };

        // Indexed by Rot4.AsInt; one entry, used for every facing, unless perFacing.
        private FrameSet[] frames;
        private FrameSet[] idleFrames;
        private CompPowerTrader power;
        private CompRefuelable fuel;
        private bool inUse;
        private int lastSoundFrame = -1;
        private int lastIdleBucket = -1;
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
            int sets = Props.perFacing ? 4 : 1;
            frames = new FrameSet[sets];
            idleFrames = Props.idleFrameCount > 0 ? new FrameSet[sets] : null;
            for (int i = 0; i < sets; i++)
            {
                string suffix = Props.perFacing ? FacingNames[i] : "";
                Vector2 size = Props.perFacing && new Rot4(i).IsHorizontal
                    ? new Vector2(Props.drawSize.y, Props.drawSize.x)
                    : Props.drawSize;
                frames[i] = new FrameSet(Props.framePath + suffix, Props.frameCount, size);
                if (idleFrames != null)
                {
                    idleFrames[i] = new FrameSet(Props.idleFramePath + suffix, Props.idleFrameCount, size);
                }
            }
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
            if (Props.drawRotations != null && Props.drawRotations.Count > 0
                && !Props.drawRotations.Contains(parent.Rotation))
            {
                return;
            }
            // Playing wins; otherwise fall back to the attract loop if the def
            // has one, and to nothing at all if it does not.
            int facing = Props.perFacing ? parent.Rotation.AsInt : 0;
            FrameSet playing = frames[facing];
            FrameSet set = playing;
            int ticksPerFrame = Props.ticksPerFrame;
            if (Props.requireUser && !AnyoneStillPlaying())
            {
                if (idleFrames == null)
                {
                    return;
                }
                set = idleFrames[facing];
                ticksPerFrame = Props.idleTicksPerFrame > 0
                    ? Props.idleTicksPerFrame
                    : Props.ticksPerFrame * 3;
            }

            int index = set.IndexFor(ticksPerFrame);
            if (set == playing)
            {
                PlayFrameSounds(index);
            }
            else
            {
                PlayIdleSound();
            }

            Graphic graphic = set.At(index);
            if (graphic == null)
            {
                return;
            }

            // Carries the def's own draw offset, so a screen mounted off its
            // cell (a wall panel) animates where its frame actually is.
            GraphicData data = parent.def.graphicData;
            Vector3 drawPos = parent.DrawPos
                + (data == null ? Vector3.zero : data.DrawOffsetForRot(parent.Rotation));
            drawPos.y = Props.drawOverPawns
                ? AltitudeLayer.MoteOverhead.AltitudeFor() + Props.altitudeOffset
                : drawPos.y + Props.altitudeOffset;
            float extraRotation = Props.rotateWithBuilding ? parent.Rotation.AsAngle - 180f : 0f;
            graphic.Draw(drawPos, Rot4.North, parent, extraRotation);
        }

        /// <summary>
        /// Once per frame reached, not once per rendered frame: at a hundred
        /// frames a second the same animation frame is drawn many times over.
        /// Only runs while the building is drawn, which is fine - RimWorld's
        /// map sounds come from where they happen, and one out of view would
        /// not be heard anyway.
        /// </summary>
        private void PlayFrameSounds(int index)
        {
            lastIdleBucket = -1;            // after play, wait a full interval before the jingle
            if (Props.frameSounds == null || Props.frameSounds.Count == 0 || index == lastSoundFrame)
            {
                return;
            }
            lastSoundFrame = index;
            for (int i = 0; i < Props.frameSounds.Count; i++)
            {
                FrameSound entry = Props.frameSounds[i];
                if (entry.frame == index && entry.sound != null)
                {
                    entry.sound.PlayOneShot(parent);
                }
            }
        }

        /// <summary>
        /// The attract jingle, every idleSoundIntervalTicks of game time. Each
        /// cabinet is offset by its id, so a row of them does not chime in
        /// unison, and the first interval is waited out rather than played on
        /// sight.
        /// </summary>
        private void PlayIdleSound()
        {
            lastSoundFrame = -1;
            if (Props.idleSound == null)
            {
                return;
            }
            int interval = Mathf.Max(60, Props.idleSoundIntervalTicks);
            int bucket = (Find.TickManager.TicksGame + parent.thingIDNumber * 131) / interval;
            if (lastIdleBucket >= 0 && bucket != lastIdleBucket)
            {
                Props.idleSound.PlayOneShot(parent);
            }
            lastIdleBucket = bucket;
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
            if (Props.scanRadius > 0f)
            {
                return AnyPlayerIn(map, GenRadial.RadialCellsAround(parent.Position, Props.scanRadius, true));
            }
            return AnyPlayerIn(map, GenAdj.CellsOccupiedBy(parent))
                   || AnyPlayerIn(map, GenAdj.CellsAdjacent8Way(parent));
        }

        private bool AnyPlayerIn(Map map, IEnumerable<IntVec3> cells)
        {
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
