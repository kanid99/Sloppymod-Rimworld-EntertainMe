using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Looks for a wall in front of the building and, if one is close enough,
    /// throws a moving picture onto it. Used by the dreamloop holotheater: park
    /// it facing a wall and the wall becomes the screen.
    /// </summary>
    public class CompProperties_WallProjection : CompProperties
    {
        public string framePath;
        public int frameCount = 12;
        public int ticksPerFrame = 10;
        /// <summary>Size of the projected image, in cells, as seen facing south.</summary>
        public Vector2 drawSize = new Vector2(3f, 1f);
        /// <summary>How many cells ahead to look for something to project onto.</summary>
        public int projectionRange = 6;
        public float altitudeOffset = 0.06f;
        /// <summary>Walls rarely move, so the search is cached between checks.</summary>
        public int recheckInterval = 60;

        public CompProperties_WallProjection()
        {
            compClass = typeof(CompWallProjection);
        }

        public override System.Collections.Generic.IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (framePath.NullOrEmpty())
            {
                yield return "CompProperties_WallProjection needs a framePath.";
            }
            if (frameCount < 1 || ticksPerFrame < 1)
            {
                yield return "CompProperties_WallProjection needs frameCount and ticksPerFrame >= 1.";
            }
            if (projectionRange < 1)
            {
                yield return "CompProperties_WallProjection needs projectionRange >= 1.";
            }
        }
    }

    public class CompWallProjection : ThingComp
    {
        private FrameSet frames;
        private CompPowerTrader power;
        private IntVec3 wallCell = IntVec3.Invalid;
        private int nextRecheckTick = -99999;

        private CompProperties_WallProjection Props
        {
            get { return (CompProperties_WallProjection)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
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

            RefreshWallIfDue();
            if (!wallCell.IsValid)
            {
                return;
            }

            Graphic graphic = frames.At(frames.IndexFor(Props.ticksPerFrame));
            if (graphic == null)
            {
                return;
            }

            Vector3 drawPos = wallCell.ToVector3Shifted();
            drawPos.y = parent.DrawPos.y + Props.altitudeOffset;
            // Frames are drawn as they look from a south-facing emitter, so turn
            // the image to match whichever way this one is pointed.
            graphic.Draw(drawPos, Rot4.North, parent, parent.Rotation.AsAngle - 180f);
        }

        private void RefreshWallIfDue()
        {
            int now = Find.TickManager.TicksGame;
            if (now < nextRecheckTick)
            {
                return;
            }
            nextRecheckTick = now + Props.recheckInterval;
            wallCell = FindWall();
        }

        /// <summary>
        /// First impassable edifice straight ahead within range. Scanning
        /// outward and stopping at the first one means anything blocking the
        /// beam becomes the screen, so the picture never appears through cover.
        /// </summary>
        private IntVec3 FindWall()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return IntVec3.Invalid;
            }

            IntVec3 facing = parent.Rotation.FacingCell;
            for (int distance = 1; distance <= Props.projectionRange; distance++)
            {
                IntVec3 cell = parent.Position + facing * distance;
                if (!cell.InBounds(map))
                {
                    return IntVec3.Invalid;
                }
                Building edifice = cell.GetEdifice(map);
                if (edifice != null && edifice.def.passability == Traversability.Impassable)
                {
                    return cell;
                }
            }
            return IntVec3.Invalid;
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (power != null && !power.PowerOn)
            {
                return null;
            }
            return wallCell.IsValid
                ? "Projecting onto wall ahead."
                : "No surface ahead to project onto.";
        }
    }
}
