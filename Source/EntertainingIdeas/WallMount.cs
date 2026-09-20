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
    /// A display that hangs on a wall's inner face.
    ///
    /// Vanilla's wall attachments occupy the wall cell itself, and its own
    /// support for that is written for one cell: GenConstruct.GetWallAttachedTo
    /// takes a single position and rotation. A three-tile panel embedded in
    /// three wall cells is not something the game will accept.
    ///
    /// So this panel does not go inside the wall. It stands on the floor tiles
    /// in front of it - as a non-edifice with no fill, no path cost and full
    /// standability, so colonists walk straight through it - and its graphic is
    /// drawn half a tile backwards onto the wall's face. It reads as mounted,
    /// it needs no special machinery, and it works at any width.
    ///
    /// The rule this enforces: every tile of the panel must be clear, and must
    /// have wall directly behind it.
    /// </summary>
    public class PlaceWorker_MountedOnWallFace : PlaceWorker
    {
        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            // The panel faces into the room, so the wall is behind it.
            IntVec3 backwards = rot.Opposite.FacingCell;

            foreach (IntVec3 cell in GenAdj.CellsOccupiedBy(loc, rot, checkingDef.Size))
            {
                if (!cell.InBounds(map))
                {
                    return new AcceptanceReport("Must hang on a wall.");
                }

                Building blocking = cell.GetEdifice(map);
                if (blocking != null && blocking != thingToIgnore
                    && blocking.def.passability == Traversability.Impassable)
                {
                    return new AcceptanceReport("Hangs on the inside of a wall, not inside the wall itself.");
                }

                IntVec3 wallCell = cell + backwards;
                if (!wallCell.InBounds(map) || !IsWall(wallCell.GetEdifice(map), thingToIgnore))
                {
                    return new AcceptanceReport("Every tile of the panel needs wall directly behind it.");
                }
            }
            return true;
        }

        private static bool IsWall(Building edifice, Thing thingToIgnore)
        {
            return edifice != null
                   && edifice != thingToIgnore
                   && !(edifice is Building_Door)
                   && edifice.def.holdsRoof
                   && edifice.def.passability == Traversability.Impassable;
        }

        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            Map map = Find.CurrentMap;
            if (map == null)
            {
                return;
            }
            // Highlight the run of wall it will hang on, so a panel one tile
            // off the wall is obvious before you commit to it.
            IntVec3 backwards = rot.Opposite.FacingCell;
            List<IntVec3> wall = GenAdj.CellsOccupiedBy(center, rot, def.Size)
                                       .Select(cell => cell + backwards)
                                       .ToList();
            GenDraw.DrawFieldEdges(wall, ghostCol);
        }
    }
    /// <summary>
    /// A hammock hangs; it does not stand. Both ends need something solid
    /// directly beyond them to be slung from.
    ///
    /// What counts is anything that holds a roof up and is not a door - walls
    /// and columns, in other words. That is the same question the game already
    /// answers for roofs, so it needs no list of acceptable defs and it keeps
    /// working for walls and columns added by other mods.
    ///
    /// Blueprints and frames count too, so a hammock can be planned in the same
    /// breath as the columns it will hang from rather than only after they are
    /// standing.
    /// </summary>
    public class PlaceWorker_SlungBetweenSupports : PlaceWorker
    {
        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            foreach (IntVec3 anchor in AnchorsFor(checkingDef, loc, rot))
            {
                if (!Supports(map, anchor, thingToIgnore))
                {
                    return new AcceptanceReport(
                        "Needs a wall or a column at both ends to hang from.");
                }
            }
            return true;
        }

        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            Map map = Find.CurrentMap;
            if (map == null)
            {
                return;
            }
            // Colour each end for what is actually there, so a hammock one tile
            // short of its wall is obvious before you commit to it.
            foreach (IntVec3 anchor in AnchorsFor(def, center, rot))
            {
                GenDraw.DrawFieldEdges(new List<IntVec3> { anchor },
                                       Supports(map, anchor, null) ? Color.cyan : Color.red);
            }
        }

        /// <summary>
        /// The cells just beyond each end of the hammock. Written for any size,
        /// so a wider or longer version would still ask the right question.
        /// </summary>
        private static IEnumerable<IntVec3> AnchorsFor(BuildableDef def, IntVec3 loc, Rot4 rot)
        {
            IntVec3 axis = rot.FacingCell;
            List<IntVec3> cells = GenAdj.CellsOccupiedBy(loc, rot, def.Size).ToList();
            int low = int.MaxValue;
            int high = int.MinValue;
            for (int i = 0; i < cells.Count; i++)
            {
                int along = Along(cells[i], axis);
                low = Mathf.Min(low, along);
                high = Mathf.Max(high, along);
            }
            for (int i = 0; i < cells.Count; i++)
            {
                int along = Along(cells[i], axis);
                if (along == low)
                {
                    yield return cells[i] - axis;
                }
                if (along == high)
                {
                    yield return cells[i] + axis;
                }
            }
        }

        /// <summary>How far along the hammock's own long axis a cell sits.</summary>
        private static int Along(IntVec3 cell, IntVec3 axis)
        {
            return cell.x * axis.x + cell.z * axis.z;
        }

        private static bool Supports(Map map, IntVec3 cell, Thing thingToIgnore)
        {
            if (!cell.InBounds(map))
            {
                return false;
            }

            Building edifice = cell.GetEdifice(map);
            if (edifice != null && edifice != thingToIgnore && HoldsUp(edifice.def))
            {
                return true;
            }

            // A wall that is only planned still counts, so the pair can be
            // queued together.
            List<Thing> things = cell.GetThingList(map);
            for (int i = 0; i < things.Count; i++)
            {
                Thing t = things[i];
                if (t == thingToIgnore)
                {
                    continue;
                }
                if (t.def.entityDefToBuild is ThingDef && HoldsUp((ThingDef)t.def.entityDefToBuild))
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>Anything that holds a roof up and is not a door.</summary>
        private static bool HoldsUp(ThingDef def)
        {
            return def != null && def.holdsRoof && def.thingClass != typeof(Building_Door)
                   && !typeof(Building_Door).IsAssignableFrom(def.thingClass);
        }
    }
}
