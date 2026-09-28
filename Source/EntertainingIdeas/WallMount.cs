using System.Collections.Generic;
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
    /// Auto-aiming that gives way to the player.
    ///
    /// A place worker's ghost is redrawn every frame, so a worker that simply
    /// turns the ghost to its preferred side turns it back every frame too -
    /// press rotate and it snaps straight back, which is what made placing a
    /// vista panel feel like a fight. This makes the auto-aim a first guess
    /// only: it is offered when the cursor reaches a new cell, and as soon as
    /// the rotation changes to anything it did not set, the player has turned
    /// it themselves and it stops for the rest of that placement.
    /// </summary>
    internal static class AutoTurn
    {
        private static Designator session;
        private static IntVec3 lastCell = IntVec3.Invalid;
        private static Rot4 expected;
        private static bool playerTurned;

        /// <summary>
        /// True when the auto-aim may suggest a facing for this cell: a new
        /// cell, and the player has not turned the ghost by hand. Call
        /// Suggested with whatever was chosen, or with the current rotation
        /// when there was nothing better.
        /// </summary>
        public static bool MaySuggest(IntVec3 cell, Rot4 current)
        {
            Designator designator = Find.DesignatorManager == null ? null : Find.DesignatorManager.SelectedDesignator;
            if (designator != session)
            {
                // A fresh placement: forget the last one's choices.
                session = designator;
                lastCell = IntVec3.Invalid;
                playerTurned = false;
            }
            if (playerTurned)
            {
                return false;
            }
            if (lastCell.IsValid && current != expected)
            {
                playerTurned = true;
                return false;
            }
            if (cell == lastCell)
            {
                return false;
            }
            lastCell = cell;
            expected = current;
            return true;
        }

        public static void Suggested(Rot4 wanted, Rot4 current)
        {
            PlacingRotation.SnapTo(wanted, current);
            expected = wanted;
        }
    }

    /// <summary>
    /// Draws, while placing, the wall the projector will actually hit - or the
    /// beam running off into nothing if there is no wall in range. Aiming a
    /// projector you cannot see the aim of is guesswork otherwise.
    /// </summary>
    public class PlaceWorker_ProjectionTarget : PlaceWorker
    {
        // DrawGhost runs every rendered frame while a projector is on the
        // cursor, so the cells it needs are held in lists that are cleared and
        // refilled rather than allocated afresh sixty times a second.
        private static readonly List<IntVec3> beamCells = new List<IntVec3>();
        private static readonly List<IntVec3> probeCells = new List<IntVec3>();
        private static readonly List<IntVec3> highlight = new List<IntVec3>();

        public override void DrawGhost(ThingDef def, IntVec3 center, Rot4 rot, Color ghostCol, Thing thing = null)
        {
            Map map = Find.CurrentMap;
            if (map == null)
            {
                return;
            }

            int range = RangeOf(def);
            IntVec3 wall;

            if (!TryCastBeam(map, center, rot, range, beamCells, out wall))
            {
                // This way misses. Turn to a direction that does not, if there
                // is one - a projector aimed at nothing is the single thing
                // players get wrong with this building. Only ever corrects a
                // facing that is already useless: a valid aim is left alone,
                // because which wall to use is the player's call.
                Rot4 better;
                if (AutoTurn.MaySuggest(center, rot) && TryFindAWall(map, center, range, rot, out better))
                {
                    AutoTurn.Suggested(better, rot);
                    return;
                }
                GenDraw.DrawFieldEdges(beamCells, new Color(1f, 0.4f, 0.4f, 0.35f));
                return;
            }

            highlight.Clear();
            highlight.Add(wall);
            highlight.Add(wall + rot.RighthandCell);
            highlight.Add(wall - rot.RighthandCell);
            GenDraw.DrawFieldEdges(highlight, Color.cyan);
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
                                        List<IntVec3> beam, out IntVec3 wall)
        {
            IntVec3 facing = rot.FacingCell;
            beam.Clear();
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
            for (int i = 0; i < 4; i++)
            {
                Rot4 rot = new Rot4(i);
                if (rot == skip)
                {
                    continue;
                }
                if (TryCastBeam(map, center, rot, range, probeCells, out wall))
                {
                    result = rot;
                    return true;
                }
            }
            return false;
        }
    }

    /// <summary>
    /// A display hung on a wall from the floor tile in front of it, the way a
    /// picture is hung - and the way vanilla's wall lamps are placed.
    ///
    /// History, because this has gone round twice. It first took the floor
    /// tiles in front of the wall as a 3x1 edifice, which marked a shelf or an
    /// armchair standing there for removal. It then moved into the wall cell
    /// itself (canPlaceOverWall), which left the floor alone but meant the
    /// cursor had to be on the wall: pointing at the floor in front - which
    /// is what everyone does - drew the picture on the wall above and then
    /// refused to place it.
    ///
    /// So now: one floor tile, not an edifice (it takes no room from
    /// furniture), with the picture drawn one tile back on the wall's face and
    /// as wide as the def says. Its rotation is the way the picture faces, so
    /// the wall is behind it: at Position - Rotation.FacingCell.
    ///
    /// Deliberately not a vanilla attachment (isAttachment): vanilla re-aims
    /// those every frame, so in a corner the player could never pick the
    /// other wall. This aims once per cell and then leaves it to the player.
    /// </summary>
    public class PlaceWorker_WallMountedDisplay : PlaceWorker
    {
        /// <summary>
        /// The cells of wall the drawn picture covers, as offsets along the
        /// wall from the one directly behind the panel.
        ///
        /// Read off the def rather than hard-coded, because the picture is not
        /// always centred: a two-tile panel hangs over its neighbour on one
        /// side only, so the span is asymmetric. Deriving it from drawSize and
        /// the def's own draw offset keeps the check right for any width.
        /// </summary>
        private static void SpanFor(BuildableDef def, Rot4 rot, out int low, out int high)
        {
            low = 0;
            high = 0;
            ThingDef thingDef = def as ThingDef;
            if (thingDef == null || thingDef.graphicData == null)
            {
                return;
            }

            float half = thingDef.graphicData.drawSize.x / 2f;

            // The wall runs left to right as the panel sees it, so that is the
            // right-hand axis; the rest of the offset is depth onto the wall's
            // face and does not matter here.
            Vector3 offset = thingDef.graphicData.DrawOffsetForRot(rot);
            IntVec3 across = rot.RighthandCell;
            float lateral = offset.x * across.x + offset.z * across.z;

            // A cell counts as covered when the picture reaches its centre.
            // Ceil and floor rather than rounding, so a width that lands
            // exactly on a cell boundary cannot fall foul of the
            // round-half-to-even the rounding helpers use.
            low = Mathf.CeilToInt(lateral - half);
            high = Mathf.FloorToInt(lateral + half);
        }

        /// <summary>The wall cell directly behind a panel hung here.</summary>
        public static IntVec3 WallBehind(IntVec3 loc, Rot4 rot)
        {
            return loc - rot.FacingCell;
        }

        // Both AllowsPlacing and DrawGhost want the run, both are called every
        // frame while the panel is on the cursor, and they are never in flight
        // at the same time, so one reused list serves both.
        private static readonly List<IntVec3> wallRun = new List<IntVec3>();
        private static readonly List<IntVec3> spot = new List<IntVec3>();

        private static List<IntVec3> WallRun(BuildableDef def, IntVec3 loc, Rot4 rot)
        {
            int low, high;
            SpanFor(def, rot, out low, out high);
            IntVec3 behind = WallBehind(loc, rot);
            IntVec3 across = rot.RighthandCell;
            wallRun.Clear();
            for (int k = low; k <= high; k++)
            {
                wallRun.Add(behind + across * k);
            }
            return wallRun;
        }

        private static bool WallRunComplete(BuildableDef def, Map map, IntVec3 loc, Rot4 rot, Thing ignore)
        {
            List<IntVec3> run = WallRun(def, loc, rot);
            for (int i = 0; i < run.Count; i++)
            {
                if (!IsWall(map, run[i], ignore))
                {
                    return false;
                }
            }
            return true;
        }

        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            if (IsWall(map, loc, thingToIgnore))
            {
                return new AcceptanceReport("Hang it from the floor in front of the wall, not on the wall itself.");
            }
            Building edifice = loc.GetEdifice(map);
            if (edifice is Building_Door)
            {
                return new AcceptanceReport("Cannot hang anything in a doorway.");
            }
            if (edifice != null && edifice != thingToIgnore && edifice.def.passability == Traversability.Impassable)
            {
                return new AcceptanceReport("Needs open floor in front of the wall.");
            }

            // The picture can be wider than the tile, so the wall behind has to
            // keep going or it would hang over open air.
            if (!WallRunComplete(checkingDef, map, loc, rot, thingToIgnore))
            {
                int span = WallRun(checkingDef, loc, rot).Count;
                return new AcceptanceReport(span <= 1
                    ? "Needs a wall behind it. Rotate it so its back is to the wall."
                    : "Needs " + span + " tiles of unbroken wall behind it.");
            }

            // One picture per spot: two would draw over each other.
            List<Thing> here = loc.GetThingList(map);
            for (int i = 0; i < here.Count; i++)
            {
                Thing other = here[i];
                if (other == thingToIgnore || other == thing)
                {
                    continue;
                }
                ThingDef otherDef = other.def.entityDefToBuild as ThingDef ?? other.def;
                if (otherDef.PlaceWorkers != null && otherDef.PlaceWorkers.Exists(w => w is PlaceWorker_WallMountedDisplay)
                    && (other.Rotation == rot))
                {
                    return new AcceptanceReport("Something is already hanging here.");
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

            // Aim the back at a wall, the way a wall lamp does - but only as a
            // first guess at each new cell, never over the top of the player
            // turning it themselves, so in a corner either wall can be chosen.
            SnapPlacingRotation(def, map, center, rot);

            GenDraw.DrawFieldEdges(WallRun(def, center, rot), ghostCol);
            spot.Clear();
            spot.Add(center);
            GenDraw.DrawFieldEdges(spot, Color.cyan);
        }

        private static void SnapPlacingRotation(ThingDef def, Map map, IntVec3 center, Rot4 current)
        {
            if (!AutoTurn.MaySuggest(center, current))
            {
                return;
            }
            Rot4 wanted;
            if (TryFindWallBehind(def, map, center, current, out wanted))
            {
                AutoTurn.Suggested(wanted, current);
            }
        }

        /// <summary>
        /// A facing that puts a whole run of wall behind this cell. The
        /// current one wins if it already works, so a corner leaves the
        /// player's choice alone.
        /// </summary>
        public static bool TryFindWallBehind(BuildableDef def, Map map, IntVec3 cell, Rot4 current, out Rot4 result)
        {
            result = current;
            if (WallRunComplete(def, map, cell, current, null))
            {
                return false;
            }
            for (int i = 0; i < 4; i++)
            {
                Rot4 rot = new Rot4(i);
                if (rot != current && WallRunComplete(def, map, cell, rot, null))
                {
                    result = rot;
                    return true;
                }
            }
            return false;
        }

        public static bool HasWallBehind(Thing thing)
        {
            return thing.Spawned && IsWall(thing.Map, WallBehind(thing.Position, thing.Rotation), thing);
        }

        public static bool IsWall(Map map, IntVec3 cell, Thing thingToIgnore)
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
    /// Looks after a hung display once it is up.
    ///
    /// A panel from before 0.9.83 sits inside its wall cell; the first rare
    /// tick after loading steps it out onto the floor tile it faces, keeping
    /// its facing, so it looks the same as it did and is placed the way new
    /// ones are. If that tile is taken, it is taken down and left boxed beside
    /// the wall rather than wiping whatever is standing there.
    ///
    /// And when the wall behind a panel goes - deconstructed, blown up - the
    /// panel comes down with it, boxed, rather than hanging on nothing.
    /// </summary>
    public class CompProperties_FaceOpenSide : CompProperties
    {
        public CompProperties_FaceOpenSide()
        {
            compClass = typeof(CompFaceOpenSide);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            // Vanilla re-aims isAttachment things at a wall every frame, which
            // takes the choice of wall in a corner away from the player.
            if (parentDef != null && parentDef.building != null && parentDef.building.isAttachment)
            {
                yield return "CompProperties_FaceOpenSide on " + parentDef.defName
                             + ": leave isAttachment off. PlaceWorker_WallMountedDisplay aims the panel "
                             + "itself; vanilla's attachment handling re-aims it every frame.";
            }
            if (parentDef != null && parentDef.tickerType != TickerType.Rare)
            {
                yield return "CompProperties_FaceOpenSide on " + parentDef.defName
                             + " needs tickerType Rare: it checks the wall behind on the rare tick.";
            }
        }
    }

    public class CompFaceOpenSide : ThingComp
    {
        public override void CompTickRare()
        {
            base.CompTickRare();
            if (!parent.Spawned)
            {
                return;
            }
            Map map = parent.Map;

            if (PlaceWorker_WallMountedDisplay.IsWall(map, parent.Position, parent))
            {
                StepOutOfWall(map);
                return;
            }
            if (!PlaceWorker_WallMountedDisplay.HasWallBehind(parent))
            {
                TakeDown("The wall behind " + parent.LabelShort + " is gone, so it has been taken down.");
            }
        }

        /// <summary>Old in-wall placement: onto the floor tile it faces.</summary>
        private void StepOutOfWall(Map map)
        {
            Rot4 rot = parent.Rotation;
            IntVec3 target = parent.Position + rot.FacingCell;
            if (!FloorIsFree(map, target))
            {
                TakeDown(parent.LabelShort + " was hung inside the wall, the old way, and the floor in front of it "
                         + "is taken - it has been taken down to hang again.");
                return;
            }
            parent.DeSpawn();
            GenSpawn.Spawn(parent, target, map, rot);
        }

        private bool FloorIsFree(Map map, IntVec3 cell)
        {
            if (!cell.InBounds(map) || !cell.Standable(map))
            {
                return false;
            }
            List<Thing> things = cell.GetThingList(map);
            for (int i = 0; i < things.Count; i++)
            {
                if (things[i] != parent && things[i].def.category == ThingCategory.Building)
                {
                    return false;
                }
            }
            return true;
        }

        private void TakeDown(string why)
        {
            if (!parent.def.Minifiable)
            {
                return;
            }
            Thing boxed = MinifyUtility.Uninstall(parent);
            if (parent.Faction == Faction.OfPlayer)
            {
                Messages.Message(why, boxed, MessageTypeDefOf.NeutralEvent);
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
        // Refilled rather than reallocated: both callers run every frame while
        // a hammock is on the cursor.
        private static readonly List<IntVec3> anchors = new List<IntVec3>();
        private static readonly List<IntVec3> oneCell = new List<IntVec3>();

        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            AnchorsFor(checkingDef, loc, rot, anchors);
            for (int i = 0; i < anchors.Count; i++)
            {
                if (!Supports(map, anchors[i], thingToIgnore))
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
            AnchorsFor(def, center, rot, anchors);
            for (int i = 0; i < anchors.Count; i++)
            {
                oneCell.Clear();
                oneCell.Add(anchors[i]);
                GenDraw.DrawFieldEdges(oneCell,
                                       Supports(map, anchors[i], null) ? Color.cyan : Color.red);
            }
        }

        /// <summary>
        /// The cells just beyond each end of the hammock. Written for any size,
        /// so a wider or longer version would still ask the right question.
        /// </summary>
        private static void AnchorsFor(BuildableDef def, IntVec3 loc, Rot4 rot, List<IntVec3> into)
        {
            into.Clear();
            IntVec3 axis = rot.FacingCell;
            CellRect occupied = GenAdj.OccupiedRect(loc, rot, def.Size);
            int low = int.MaxValue;
            int high = int.MinValue;
            foreach (IntVec3 cell in occupied)
            {
                int along = Along(cell, axis);
                low = Mathf.Min(low, along);
                high = Mathf.Max(high, along);
            }
            foreach (IntVec3 cell in occupied)
            {
                int along = Along(cell, axis);
                if (along == low)
                {
                    into.Add(cell - axis);
                }
                if (along == high)
                {
                    into.Add(cell + axis);
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
