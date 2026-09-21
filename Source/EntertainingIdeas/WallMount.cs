using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Points the thing being placed a different way.
    ///
    /// Designator_Place.placingRot is protected, so this reaches it by
    /// reflection and quietly gives up if it ever moves - the player can still
    /// rotate by hand, so the worst case is a cosmetic loss.
    /// </summary>
    internal static class PlacingRotation
    {
        private static FieldInfo field;
        private static bool lookedUp;

        public static void SnapTo(Rot4 wanted, Rot4 current)
        {
            if (wanted == current)
            {
                return;
            }
            if (!lookedUp)
            {
                lookedUp = true;
                field = typeof(Designator_Place).GetField(
                    "placingRot", BindingFlags.Instance | BindingFlags.NonPublic);
            }
            if (field == null || Find.DesignatorManager == null)
            {
                return;
            }
            Designator_Place designator = Find.DesignatorManager.SelectedDesignator as Designator_Place;
            if (designator == null)
            {
                return;
            }
            try
            {
                field.SetValue(designator, wanted);
            }
            catch
            {
                field = null;       // stop trying
            }
        }
    }

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

            int range = RangeOf(def);
            List<IntVec3> beam;
            IntVec3 wall;

            if (!TryCastBeam(map, center, rot, range, out wall, out beam))
            {
                // This way misses. Turn to a direction that does not, if there
                // is one - a projector aimed at nothing is the single thing
                // players get wrong with this building. Only ever corrects a
                // facing that is already useless: a valid aim is left alone,
                // because which wall to use is the player's call.
                Rot4 better;
                if (TryFindAWall(map, center, range, rot, out better))
                {
                    PlacingRotation.SnapTo(better, rot);
                    return;
                }
                GenDraw.DrawFieldEdges(beam, new Color(1f, 0.4f, 0.4f, 0.35f));
                return;
            }

            GenDraw.DrawFieldEdges(new List<IntVec3>
            {
                wall, wall + rot.RighthandCell, wall - rot.RighthandCell
            }, Color.cyan);
        }

        private static int RangeOf(ThingDef def)
        {
            CompProperties_WallProjection props = def.GetCompProperties<CompProperties_WallProjection>();
            return props != null ? props.projectionRange : 6;
        }

        /// <summary>
        /// Walks the beam out until it meets something solid. Reports the wall
        /// it hit, or the cells it crossed on its way to hitting nothing.
        /// </summary>
        private static bool TryCastBeam(Map map, IntVec3 center, Rot4 rot, int range,
                                        out IntVec3 wall, out List<IntVec3> beam)
        {
            IntVec3 facing = rot.FacingCell;
            beam = new List<IntVec3>();
            wall = IntVec3.Invalid;

            for (int distance = 1; distance <= range; distance++)
            {
                IntVec3 cell = center + facing * distance;
                if (!cell.InBounds(map))
                {
                    return false;
                }
                Building edifice = cell.GetEdifice(map);
                if (edifice != null && edifice.def.passability == Traversability.Impassable)
                {
                    wall = cell;
                    return true;
                }
                beam.Add(cell);
            }
            return false;
        }

        private static bool TryFindAWall(Map map, IntVec3 center, int range, Rot4 skip, out Rot4 result)
        {
            result = skip;
            IntVec3 wall;
            List<IntVec3> ignored;
            for (int i = 0; i < 4; i++)
            {
                Rot4 rot = new Rot4(i);
                if (rot == skip)
                {
                    continue;
                }
                if (TryCastBeam(map, center, rot, range, out wall, out ignored))
                {
                    result = rot;
                    return true;
                }
            }
            return false;
        }
    }

    /// <summary>
    /// A display that lives in the wall itself and hangs no wider than it.
    ///
    /// It used to take the floor tiles in front of the wall. That placed fine,
    /// but it meant the panel owned three tiles of room, so anything already
    /// standing there - a shelf, an armchair - was marked for removal to make
    /// space for a picture on the wall behind it. Wrong trade.
    ///
    /// So the panel is one cell now, sitting in the wall cell the way a wall
    /// lamp does, and the picture is simply drawn three tiles wide across the
    /// neighbouring wall. Vanilla's wall-attachment support is single-cell -
    /// GenConstruct.GetWallAttachedTo takes one position - and one cell is all
    /// this needs. Nothing in the room is touched.
    ///
    /// What is checked: the cell is wall, the wall runs far enough either side
    /// to carry the width of the picture, and the side it faces is open.
    /// </summary>
    public class PlaceWorker_WallMountedDisplay : PlaceWorker
    {
        /// <summary>How many cells either side the drawn picture reaches.</summary>
        private static int ReachFor(BuildableDef def)
        {
            ThingDef thingDef = def as ThingDef;
            if (thingDef == null || thingDef.graphicData == null)
            {
                return 0;
            }
            return Mathf.Max(0, (Mathf.RoundToInt(thingDef.graphicData.drawSize.x) - 1) / 2);
        }

        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            if (!IsWall(map, loc, thingToIgnore))
            {
                return new AcceptanceReport("Must be mounted in a wall.");
            }

            // The picture is wider than the cell, so the wall has to keep going
            // or it would hang over open air.
            IntVec3 across = rot.RighthandCell;
            int reach = ReachFor(checkingDef);
            for (int i = 1; i <= reach; i++)
            {
                if (!IsWall(map, loc + across * i, thingToIgnore)
                    || !IsWall(map, loc - across * i, thingToIgnore))
                {
                    return new AcceptanceReport(
                        "Needs " + (reach * 2 + 1) + " tiles of unbroken wall to span.");
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

            // Auto-orient, the way a wall lamp does: face whichever side of the
            // wall is actually a room. Done here rather than at spawn alone so
            // the ghost shows the truth while it is being placed.
            SnapPlacingRotation(map, center, rot);

            List<IntVec3> run = new List<IntVec3> { center };
            IntVec3 across = rot.RighthandCell;
            for (int i = 1; i <= ReachFor(def); i++)
            {
                run.Add(center + across * i);
                run.Add(center - across * i);
            }
            GenDraw.DrawFieldEdges(run, ghostCol);
            GenDraw.DrawFieldEdges(new List<IntVec3> { center + rot.FacingCell }, Color.cyan);
        }

        private static void SnapPlacingRotation(Map map, IntVec3 center, Rot4 current)
        {
            Rot4 wanted;
            if (TryFindOpenSide(map, center, current, out wanted))
            {
                PlacingRotation.SnapTo(wanted, current);
            }
        }

        /// <summary>
        /// The side of this wall cell a room is on. A side already facing one
        /// wins, so a wall with rooms on both faces leaves the player's choice
        /// alone.
        /// </summary>
        public static bool TryFindOpenSide(Map map, IntVec3 cell, Rot4 current, out Rot4 result)
        {
            result = current;
            if (Faces(map, cell, current))
            {
                return false;
            }
            for (int i = 0; i < 4; i++)
            {
                Rot4 rot = new Rot4(i);
                if (Faces(map, cell, rot))
                {
                    result = rot;
                    return true;
                }
            }
            return false;
        }

        /// <summary>Is there somewhere to look at the picture from, this way?</summary>
        private static bool Faces(Map map, IntVec3 cell, Rot4 rot)
        {
            IntVec3 front = cell + rot.FacingCell;
            if (!front.InBounds(map))
            {
                return false;
            }
            Building edifice = front.GetEdifice(map);
            return edifice == null || edifice.def.passability != Traversability.Impassable;
        }

        private static bool IsWall(Map map, IntVec3 cell, Thing thingToIgnore)
        {
            if (!cell.InBounds(map))
            {
                return false;
            }
            Building edifice = cell.GetEdifice(map);
            return edifice != null
                   && edifice != thingToIgnore
                   && !(edifice is Building_Door)
                   && edifice.def.holdsRoof
                   && edifice.def.passability == Traversability.Impassable;
        }
    }

    /// <summary>
    /// Turns a wall-mounted thing to face the room when it is built, so a
    /// blueprint placed the wrong way round still ends up pointing inward.
    /// </summary>
    public class CompProperties_FaceOpenSide : CompProperties
    {
        public CompProperties_FaceOpenSide()
        {
            compClass = typeof(CompFaceOpenSide);
        }
    }

    public class CompFaceOpenSide : ThingComp
    {
        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            if (respawningAfterLoad || parent.Map == null)
            {
                return;
            }
            Rot4 wanted;
            if (PlaceWorker_WallMountedDisplay.TryFindOpenSide(
                    parent.Map, parent.Position, parent.Rotation, out wanted))
            {
                parent.Rotation = wanted;
            }
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
