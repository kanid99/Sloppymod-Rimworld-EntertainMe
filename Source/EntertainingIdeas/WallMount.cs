using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Draws, while placing, the wall the projector will actually hit - or the
    /// beam running off into nothing if there is no wall in range. Aiming a
    /// projector you cannot see the aim of is guesswork otherwise.
    /// </summary>
    public class PlaceWorker_ProjectionTarget : PlaceWorker
    {
        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            Map map = Find.CurrentMap;
            if (map == null)
            {
                return;
            }

            CompProperties_WallProjection props = def.GetCompProperties<CompProperties_WallProjection>();
            int range = props != null ? props.projectionRange : 6;
            IntVec3 facing = rot.FacingCell;

            List<IntVec3> beam = new List<IntVec3>();
            for (int distance = 1; distance <= range; distance++)
            {
                IntVec3 cell = center + facing * distance;
                if (!cell.InBounds(map))
                {
                    break;
                }
                Building edifice = cell.GetEdifice(map);
                if (edifice != null && edifice.def.passability == Traversability.Impassable)
                {
                    List<IntVec3> screen = new List<IntVec3>
                    {
                        cell, cell + rot.RighthandCell, cell - rot.RighthandCell
                    };
                    GenDraw.DrawFieldEdges(screen, Color.cyan);
                    return;
                }
                beam.Add(cell);
            }
            // Nothing in range: show how far it looked, so the miss is obvious.
            GenDraw.DrawFieldEdges(beam, new Color(1f, 0.4f, 0.4f, 0.35f));
        }
    }

    /// <summary>
    /// Vanilla's wall attachments are all one cell, and its own place worker
    /// checks accordingly. A three-tile display has to have wall under all of
    /// it, or it ends up half mounted and half hanging in the room.
    /// </summary>
    public class PlaceWorker_AttachedToWallWide : PlaceWorker
    {
        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            foreach (IntVec3 cell in GenAdj.CellsOccupiedBy(loc, rot, checkingDef.Size))
            {
                if (!cell.InBounds(map))
                {
                    return new AcceptanceReport("Must be placed on a wall.");
                }
                Building edifice = cell.GetEdifice(map);
                if (edifice == null || edifice == thingToIgnore)
                {
                    return new AcceptanceReport("Must be placed on a wall.");
                }
                if (edifice is Building_Door || !edifice.def.holdsRoof
                    || edifice.def.passability != Traversability.Impassable)
                {
                    return new AcceptanceReport("Must be placed on a wall, not a door.");
                }
            }
            return true;
        }

        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            // Show which way it will face, since it is drawn off its own cell.
            GenDraw.DrawFieldEdges(GenAdj.CellsOccupiedBy(center, rot, def.Size).ToList(), ghostCol);
        }
    }
}
