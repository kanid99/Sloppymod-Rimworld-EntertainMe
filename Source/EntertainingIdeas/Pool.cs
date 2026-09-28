using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_TerrainDefOf
    {
        public static TerrainDef EI_PoolBasin;
        public static TerrainDef EI_PoolWater;
        public static TerrainDef EI_PoolWaterMurky;
        public static TerrainDef EI_PoolWaterFoul;

        static EI_TerrainDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_TerrainDefOf));
        }
    }

    /// <summary>
    /// What pool water looks like at a given dirtiness, and the water line
    /// shared by a pool with a filter and one whose filter is gone.
    /// </summary>
    public static class PoolWater
    {
        /// <summary>Dirt at which the water turns visibly murky.</summary>
        public const float MurkyAt = 0.3f;
        /// <summary>Dirt at which it is foul, and swimming in it can make a pawn ill.</summary>
        public const float FoulAt = 0.7f;

        public static bool IsWater(TerrainDef terrain)
        {
            return terrain != null
                   && (terrain == EI_TerrainDefOf.EI_PoolWater
                       || terrain == EI_TerrainDefOf.EI_PoolWaterMurky
                       || terrain == EI_TerrainDefOf.EI_PoolWaterFoul);
        }

        public static bool IsPool(TerrainDef terrain)
        {
            return terrain == EI_TerrainDefOf.EI_PoolBasin || IsWater(terrain);
        }

        public static TerrainDef For(float dirt)
        {
            if (dirt >= FoulAt)
            {
                return EI_TerrainDefOf.EI_PoolWaterFoul;
            }
            return dirt >= MurkyAt ? EI_TerrainDefOf.EI_PoolWaterMurky : EI_TerrainDefOf.EI_PoolWater;
        }

        public static int WetCount(int cellCount, float litres, float litresPerTile)
        {
            float capacity = cellCount * litresPerTile;
            if (capacity <= 0f)
            {
                return 0;
            }
            return Mathf.Clamp(Mathf.RoundToInt(cellCount * (litres / capacity)), 0, cellCount);
        }

        /// <summary>
        /// Wets the first N cells and dries the rest, so the water line moves
        /// visibly as the pool fills and drains; the wet ones take the colour
        /// of how dirty the water is.
        /// </summary>
        public static void ApplyWaterLine(Map map, List<IntVec3> cells, int wet, float dirt)
        {
            if (map == null)
            {
                return;
            }
            TerrainDef water = For(dirt);
            for (int i = 0; i < cells.Count; i++)
            {
                TerrainDef wanted = i < wet ? water : EI_TerrainDefOf.EI_PoolBasin;
                if (map.terrainGrid.TerrainAt(cells[i]) != wanted)
                {
                    map.terrainGrid.SetTerrain(cells[i], wanted);
                }
            }
        }

        public static string Describe(float dirt)
        {
            if (dirt >= FoulAt)
            {
                return "foul (" + dirt.ToStringPercent() + " dirty) - swimmers may fall ill";
            }
            if (dirt >= MurkyAt)
            {
                return "murky (" + dirt.ToStringPercent() + " dirty)";
            }
            return dirt > 0.05f ? "clear (" + dirt.ToStringPercent() + " dirty)" : "clear";
        }
    }

    /// <summary>
    /// The water left behind when a pool's filter is torn down, sold or
    /// destroyed. It stays where it is and goes stale, slowly evaporating,
    /// until a new filter is built beside it and takes it back over.
    /// </summary>
    public class OrphanPool : IExposable
    {
        public List<IntVec3> cells = new List<IntVec3>();
        public float litres;
        public float dirt;
        public float litresPerTile = 20f;
        public float litresLostPerTilePerDay = 0.6f;
        public float dirtPerDay = 0.12f;

        public int WetTileCount
        {
            get { return PoolWater.WetCount(cells.Count, litres, litresPerTile); }
        }

        public void ExposeData()
        {
            Scribe_Collections.Look(ref cells, "cells", LookMode.Value);
            Scribe_Values.Look(ref litres, "litres", 0f);
            Scribe_Values.Look(ref dirt, "dirt", 0f);
            Scribe_Values.Look(ref litresPerTile, "litresPerTile", 20f);
            Scribe_Values.Look(ref litresLostPerTilePerDay, "litresLostPerTilePerDay", 0.6f);
            Scribe_Values.Look(ref dirtPerDay, "dirtPerDay", 0.12f);
            if (cells == null)
            {
                cells = new List<IntVec3>();
            }
        }
    }

    /// <summary>
    /// Keeps the orphaned pools on a map. Found by the game on its own:
    /// every MapComponent subclass is added to every map, old saves included.
    /// </summary>
    public class MapComponent_Pools : MapComponent
    {
        private const int Interval = 250;
        private List<OrphanPool> orphans = new List<OrphanPool>();

        public MapComponent_Pools(Map map) : base(map)
        {
        }

        public List<OrphanPool> Orphans
        {
            get { return orphans; }
        }

        public static MapComponent_Pools On(Map map)
        {
            return map == null ? null : map.GetComponent<MapComponent_Pools>();
        }

        public void Add(OrphanPool pool)
        {
            orphans.Add(pool);
        }

        public void Remove(OrphanPool pool)
        {
            orphans.Remove(pool);
        }

        public OrphanPool OrphanAt(IntVec3 cell)
        {
            for (int i = 0; i < orphans.Count; i++)
            {
                if (orphans[i].cells.Contains(cell))
                {
                    return orphans[i];
                }
            }
            return null;
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Collections.Look(ref orphans, "EI_orphanPools", LookMode.Deep);
            if (orphans == null)
            {
                orphans = new List<OrphanPool>();
            }
        }

        public override void MapComponentTick()
        {
            base.MapComponentTick();
            if (orphans.Count == 0 || Find.TickManager.TicksGame % Interval != 0)
            {
                return;
            }

            float days = Interval / 60000f;
            for (int i = orphans.Count - 1; i >= 0; i--)
            {
                OrphanPool pool = orphans[i];

                // Forget any tile the player has since floored over.
                pool.cells.RemoveAll(c => !c.InBounds(map) || !PoolWater.IsPool(map.terrainGrid.TerrainAt(c)));
                float capacity = pool.cells.Count * pool.litresPerTile;
                pool.litres = Mathf.Min(pool.litres, capacity)
                              - pool.cells.Count * pool.litresLostPerTilePerDay * days;
                pool.dirt = Mathf.Min(1f, pool.dirt + pool.dirtPerDay * days);

                if (pool.litres <= 0f || pool.cells.Count == 0)
                {
                    pool.litres = 0f;
                    PoolWater.ApplyWaterLine(map, pool.cells, 0, 0f);
                    orphans.RemoveAt(i);
                    continue;
                }
                PoolWater.ApplyWaterLine(map, pool.cells, pool.WetTileCount, pool.dirt);
            }
        }
    }

    /// <summary>
    /// Runs a pool of whatever shape the player painted.
    ///
    /// Dubs Bad Hygiene's pool is a fixed-size object; this one is terrain. The
    /// player lays basin tiles wherever they like and the filtration unit
    /// claims every basin tile connected to it, so the pool's size - and with
    /// it the water it holds and the power it draws - is whatever they drew.
    /// </summary>
    public class CompProperties_PoolController : CompProperties
    {
        /// <summary>A hard stop, so one painted tile too many cannot eat a tick.</summary>
        public int maxTiles = 220;
        public float litresPerTile = 20f;
        public float basePowerConsumption = 80f;
        public float powerPerTile = 5f;
        /// <summary>How much one hauled load adds.</summary>
        public float litresPerLoad = 120f;
        public int fillWorkTicks = 320;
        /// <summary>Evaporation and splash-out, per tile of open water per day.</summary>
        public float litresLostPerTilePerDay = 0.6f;
        /// <summary>How fast standing water goes bad with no pump running, per day (0 clean, 1 foul).</summary>
        public float dirtPerDay = 0.12f;
        /// <summary>How fast a running pump clears it again, per day.</summary>
        public float cleanPerDay = 0.6f;
        /// <summary>Recount the pool's shape this often, in ticks.</summary>
        public int recountInterval = 2000;

        public CompProperties_PoolController()
        {
            compClass = typeof(CompPoolController);
        }
    }

    public class CompPoolController : ThingComp, IServiceable, ICarriedWater
    {
        private float litres;
        private float dirt;
        private CompPowerTrader power;

        // Resolved once: a thing's comps are fixed when it is constructed, so
        // whether this building is piped cannot change while it exists. Plumbed
        // is asked on the work-giver scan and again every frame the pool is
        // selected, and each ask used to walk every comp comparing type names.
        private ThingComp pipe;
        private bool pipeResolved;

        // The pool's cells, in the order the flood fill reached them, so the
        // pool fills outward from the filter and drains back toward it.
        private List<IntVec3> cells = new List<IntVec3>();
        private int nextRecountTick;

        private CompProperties_PoolController Props
        {
            get { return (CompProperties_PoolController)props; }
        }

        public int TileCount
        {
            get { return cells.Count; }
        }

        public float Capacity
        {
            get { return cells.Count * Props.litresPerTile; }
        }

        private ThingComp Pipe
        {
            get
            {
                if (!pipeResolved)
                {
                    pipeResolved = true;
                    pipe = DubsPlumbing.PipeOn(parent);
                }
                return pipe;
            }
        }

        public bool Plumbed
        {
            get { return Pipe != null; }
        }

        /// <summary>
        /// The pool's own tiles, in fill order. Handed out so the swimming
        /// giver can look at the pool itself rather than sweeping every cell
        /// within twenty-four tiles of the filter hunting for water.
        /// </summary>
        public List<IntVec3> Cells
        {
            get { return cells; }
        }

        /// <summary>
        /// Enough water to swim in. The pump does not have to be running:
        /// with it off the water goes bad, and colonists swim in it anyway
        /// until it makes somebody ill.
        /// </summary>
        public bool SwimReady
        {
            get { return cells.Count > 0 && WetTileCount > 0; }
        }

        public float Dirt
        {
            get { return dirt; }
        }

        private bool Pumping
        {
            get { return power == null || power.PowerOn; }
        }

        private int WetTileCount
        {
            get { return PoolWater.WetCount(cells.Count, litres, Props.litresPerTile); }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            Recount();
            nextRecountTick = Find.TickManager.TicksGame + Props.recountInterval;
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref litres, "EI_poolLitres", 0f);
            Scribe_Values.Look(ref dirt, "EI_poolDirt", 0f);
        }

#if RW16
        public override void PostDeSpawn(Map map, DestroyMode mode = DestroyMode.Vanish)
        {
            base.PostDeSpawn(map, mode);
            LeaveWaterBehind(map);
        }
#else
        public override void PostDeSpawn(Map map)
        {
            base.PostDeSpawn(map);
            LeaveWaterBehind(map);
        }
#endif

        /// <summary>
        /// Take the filter away and the water stays, with nothing keeping it
        /// clean. The map looks after it from here, and a new filter built
        /// beside it takes it back. The comp keeps nothing, so a filter that
        /// was only uninstalled does not arrive at its new spot still full.
        /// </summary>
        private void LeaveWaterBehind(Map map)
        {
            MapComponent_Pools pools = MapComponent_Pools.On(map);
            if (pools != null && cells.Count > 0 && litres > 0f)
            {
                OrphanPool orphan = new OrphanPool
                {
                    cells = new List<IntVec3>(cells),
                    litres = litres,
                    dirt = dirt,
                    litresPerTile = Props.litresPerTile,
                    litresLostPerTilePerDay = Props.litresLostPerTilePerDay,
                    dirtPerDay = Props.dirtPerDay
                };
                pools.Add(orphan);
            }
            litres = 0f;
            dirt = 0f;
            cells.Clear();
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            if (!parent.Spawned)
            {
                return;
            }

            if (Find.TickManager.TicksGame >= nextRecountTick)
            {
                nextRecountTick = Find.TickManager.TicksGame + Props.recountInterval;
                Recount();
            }

            // A bigger pool is a bigger pump.
            if (power != null)
            {
                power.PowerOutput = power.PowerOn
                    ? -(Props.basePowerConsumption + Props.powerPerTile * cells.Count)
                    : 0f;
            }

            ThingComp plumbing = Pipe;
            if (plumbing != null && DubsPlumbing.NetHasWater(plumbing))
            {
                litres = Capacity;              // plumbed in: it tops itself up
            }
            else
            {
                // 250 ticks is one rare tick; 60000 is a day.
                litres -= cells.Count * Props.litresLostPerTilePerDay * (250f / 60000f);
                if (litres < 0f)
                {
                    litres = 0f;
                }
            }
            if (litres > Capacity)
            {
                litres = Capacity;
            }

            // Standing water goes bad; a running pump clears it. An empty
            // pool has nothing to go bad, so it refills clean.
            float days = 250f / 60000f;
            dirt = Pumping
                ? Mathf.Max(0f, dirt - Props.cleanPerDay * days)
                : Mathf.Min(1f, dirt + Props.dirtPerDay * days);
            if (litres <= 0f)
            {
                dirt = 0f;
            }

            ApplyWaterLine();
        }

        /// <summary>
        /// Flood-fills basin and water terrain outward from the cells around
        /// the filter. Four-way, so two pools that only touch at a corner stay
        /// separate pools.
        /// </summary>
        private void Recount()
        {
            cells.Clear();
            Map map = parent.Map;
            if (map == null)
            {
                return;
            }

            HashSet<IntVec3> seen = new HashSet<IntVec3>();
            Queue<IntVec3> queue = new Queue<IntVec3>();
            foreach (IntVec3 adjacent in GenAdj.CellsAdjacent8Way(parent))
            {
                if (adjacent.InBounds(map) && IsPoolCell(map, adjacent) && seen.Add(adjacent))
                {
                    queue.Enqueue(adjacent);
                }
            }

            while (queue.Count > 0 && cells.Count < Props.maxTiles)
            {
                IntVec3 cell = queue.Dequeue();
                cells.Add(cell);
                for (int i = 0; i < 4; i++)
                {
                    IntVec3 next = cell + GenAdj.CardinalDirections[i];
                    if (next.InBounds(map) && IsPoolCell(map, next) && seen.Add(next))
                    {
                        queue.Enqueue(next);
                    }
                }
            }

            TakeOverOrphans(map);
        }

        /// <summary>
        /// Water left standing by an earlier filter becomes this one's, dirt
        /// and all - which is how a pool gone foul is rescued: build a filter
        /// beside it, power it, and wait for the pump to clear it.
        /// </summary>
        private void TakeOverOrphans(Map map)
        {
            MapComponent_Pools pools = MapComponent_Pools.On(map);
            if (pools == null || pools.Orphans.Count == 0 || cells.Count == 0)
            {
                return;
            }
            HashSet<IntVec3> mine = new HashSet<IntVec3>(cells);
            List<OrphanPool> orphans = pools.Orphans;
            for (int i = orphans.Count - 1; i >= 0; i--)
            {
                OrphanPool orphan = orphans[i];
                if (!orphan.cells.Exists(c => mine.Contains(c)))
                {
                    continue;
                }
                float total = litres + orphan.litres;
                if (total > 0f)
                {
                    dirt = (dirt * litres + orphan.dirt * orphan.litres) / total;
                }
                litres = Mathf.Min(Capacity, total);
                pools.Remove(orphan);
            }
            ApplyWaterLine();
        }

        private static bool IsPoolCell(Map map, IntVec3 cell)
        {
            return PoolWater.IsPool(map.terrainGrid.TerrainAt(cell));
        }

        private void ApplyWaterLine()
        {
            PoolWater.ApplyWaterLine(parent.Map, cells, WetTileCount, dirt);
        }

        // --- IServiceable: a pool off the plumbing is filled by the bucket ---
        public bool NeedsService
        {
            get { return !Plumbed && cells.Count > 0 && litres < Capacity - 0.01f; }
        }

        public int ServiceWorkTicks
        {
            get { return Props.fillWorkTicks; }
        }

        public JobDef ServiceJob
        {
            get { return EI_PoolJobDefOf.EI_FillPool; }
        }

        public void Service()
        {
            litres = Mathf.Min(Capacity, litres + Props.litresPerLoad);
            ApplyWaterLine();
        }

        public override string CompInspectStringExtra()
        {
            if (cells.Count == 0)
            {
                return "No pool attached: lay pool basin next to this unit.";
            }

            string line = cells.Count + " tiles, "
                          + Mathf.RoundToInt(litres) + " / " + Mathf.RoundToInt(Capacity) + "L";
            if (Plumbed)
            {
                line += " (plumbed in)";
            }
            if (litres > 0f)
            {
                line += "\nWater: " + PoolWater.Describe(dirt);
            }
            if (!Pumping)
            {
                line += "\nNo power: the pump is off and the water is going stale.";
            }
            int wet = WetTileCount;
            if (wet < cells.Count)
            {
                line += "\nFilling: " + wet + " of " + cells.Count + " tiles under water.";
                if (!Plumbed && !WaterSources.MapHasWater(parent.Map))
                {
                    line += "\nNo open water on this map to carry from.";
                }
            }
            return line;
        }
    }

    [DefOf]
    public static class EI_PoolJobDefOf
    {
        public static JobDef EI_FillPool;
        public static JobDef EI_Swim;

        static EI_PoolJobDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_PoolJobDefOf));
        }
    }

    /// <summary>
    /// Sends a pawn to a pool with water in it. Unlike vanilla's swimming
    /// giver this does not care whether the water is outdoors or how cold the
    /// map is - an indoor heated pool is the entire point of building one. It
    /// does not care how clean the water is either, which is the risk of
    /// letting the pump stand idle.
    /// </summary>
    public class JoyGiver_Swim : JoyGiver
    {
        private const float MaxDistance = 60f;

        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }

            IntVec3 cell;
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing filter = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    MaxDistance,
                    t => Usable(pawn, t));
                if (filter != null && TryFindWetCell(pawn, filter, out cell))
                {
                    return JobMaker.MakeJob(def.jobDef, cell, filter);
                }
            }

            // A pool whose filter is gone still holds water, and will be
            // swum in until it has gone bad enough to make somebody ill.
            MapComponent_Pools pools = MapComponent_Pools.On(pawn.Map);
            if (pools != null)
            {
                List<OrphanPool> orphans = pools.Orphans;
                for (int i = 0; i < orphans.Count; i++)
                {
                    List<IntVec3> cells = orphans[i].cells;
                    if (cells.Count == 0 || !cells[0].InHorDistOf(pawn.Position, MaxDistance))
                    {
                        continue;
                    }
                    if (TryFindWetCell(pawn, cells, out cell))
                    {
                        return JobMaker.MakeJob(def.jobDef, cell);
                    }
                }
            }
            return null;
        }

        private static bool Usable(Pawn pawn, Thing thing)
        {
            if (thing.IsForbidden(pawn) || thing.IsBurning())
            {
                return false;
            }
            CompPoolController pool = thing.TryGetComp<CompPoolController>();
            return pool != null && pool.SwimReady;
        }

        public static bool TryFindWetCell(Pawn pawn, Thing filter, out IntVec3 result)
        {
            CompPoolController pool = filter.TryGetComp<CompPoolController>();
            if (pool == null)
            {
                result = IntVec3.Invalid;
                return false;
            }
            return TryFindWetCell(pawn, pool.Cells, out result);
        }

        /// <summary>
        /// A random wet, standable, reachable tile of the given pool. The pool
        /// knows its own tiles, so this looks only at those rather than
        /// sweeping the area around it.
        /// </summary>
        public static bool TryFindWetCell(Pawn pawn, List<IntVec3> cells, out IntVec3 result)
        {
            result = IntVec3.Invalid;
            Map map = pawn.Map;
            if (map == null || cells == null)
            {
                return false;
            }

            scratch.Clear();
            for (int i = 0; i < cells.Count; i++)
            {
                IntVec3 cell = cells[i];
                if (!PoolWater.IsWater(map.terrainGrid.TerrainAt(cell)))
                {
                    continue;       // the shallow end of a half-filled pool
                }
                if (!cell.Standable(map) || cell.IsForbidden(pawn))
                {
                    continue;
                }
                scratch.Add(cell);
            }
            if (scratch.Count == 0)
            {
                return false;
            }

            // Reachability is the expensive part, so it is left until a cell
            // has been picked. Walking a shuffled list rather than testing them
            // all means the usual case costs one check instead of one per tile,
            // while a pool that is genuinely cut off still gets ruled out.
            for (int i = scratch.Count - 1; i > 0; i--)
            {
                int j = Rand.RangeInclusive(0, i);
                IntVec3 swap = scratch[i];
                scratch[i] = scratch[j];
                scratch[j] = swap;
            }
            for (int i = 0; i < scratch.Count; i++)
            {
                if (pawn.CanReserveAndReach(scratch[i], PathEndMode.OnCell, Danger.None))
                {
                    result = scratch[i];
                    scratch.Clear();
                    return true;
                }
            }
            scratch.Clear();
            return false;
        }

        /// <summary>Reused between calls; job giving is single-threaded.</summary>
        private static readonly List<IntVec3> scratch = new List<IntVec3>();
    }

    [DefOf]
    public static class EI_HediffDefOf
    {
        public static HediffDef EI_SwimmersSickness;

        static EI_HediffDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_HediffDefOf));
        }
    }

    /// <summary>
    /// Swim about: pick a spot, wade to it, splash around for a while, pick
    /// another. Ends when the pawn has had enough joy or the water is gone.
    /// A swim in foul water can leave the swimmer ill.
    /// </summary>
    public class JobDriver_Swim : JobDriver
    {
        private const int TicksPerSpot = 260;
        /// <summary>Chance a swim in foul water makes the swimmer ill.</summary>
        private const float SicknessChance = 0.3f;

        private int spotsLeft = 6;
        private bool swamInFoul;

        private Thing Filter
        {
            get { return job.GetTarget(TargetIndex.B).Thing; }
        }

        /// <summary>Swimming in a pool whose filter has gone.</summary>
        private bool Orphaned
        {
            get { return !job.targetB.HasThing; }
        }

        private List<IntVec3> PoolCells()
        {
            if (!Orphaned)
            {
                CompPoolController pool = Filter == null ? null : Filter.TryGetComp<CompPoolController>();
                return pool == null ? null : pool.Cells;
            }
            MapComponent_Pools pools = MapComponent_Pools.On(pawn.Map);
            OrphanPool orphan = pools == null ? null : pools.OrphanAt(job.targetA.Cell);
            return orphan == null ? null : orphan.cells;
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref spotsLeft, "EI_swimSpotsLeft", 6);
            Scribe_Values.Look(ref swamInFoul, "EI_swamInFoul", false);
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.ReserveSittableOrSpot(job.targetA.Cell, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            if (!Orphaned)
            {
                this.EndOnDespawnedOrNull(TargetIndex.B);
            }
            AddFailCondition(delegate
            {
                if (Orphaned)
                {
                    return PoolCells() == null
                           || !PoolWater.IsWater(pawn.Map.terrainGrid.TerrainAt(job.targetA.Cell));
                }
                CompPoolController pool = Filter == null ? null : Filter.TryGetComp<CompPoolController>();
                return pool == null || !pool.SwimReady;
            });
            AddFinishAction(delegate
            {
                if (swamInFoul)
                {
                    MaybeFallIll();
                }
            });

            Toil pickSpot = ToilMaker.MakeToil("EI_PickSwimSpot");
            pickSpot.initAction = delegate
            {
                IntVec3 cell;
                if (spotsLeft > 0 && JoyGiver_Swim.TryFindWetCell(pawn, PoolCells(), out cell))
                {
                    spotsLeft--;
                    job.SetTarget(TargetIndex.A, cell);
                }
                else
                {
                    EndJobWith(JobCondition.Succeeded);
                }
            };
            pickSpot.defaultCompleteMode = ToilCompleteMode.Instant;
            yield return pickSpot;

            yield return Toils_Goto.GotoCell(TargetIndex.A, PathEndMode.OnCell);

            Toil splash = ToilMaker.MakeToil("EI_Splash");
            splash.initAction = delegate
            {
                MarkSwimming();
                if (pawn.Map.terrainGrid.TerrainAt(pawn.Position) == EI_TerrainDefOf.EI_PoolWaterFoul)
                {
                    swamInFoul = true;
                }
            };
            splash.defaultCompleteMode = ToilCompleteMode.Delay;
            splash.defaultDuration = TicksPerSpot;
            splash.handlingFacing = true;
#if RW16
            splash.tickIntervalAction = delegate(int delta)
            {
                MarkSwimming();
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Filter as Building);
            };
#else
            splash.tickAction = delegate
            {
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Filter as Building);
            };
#endif
            splash.socialMode = RandomSocialMode.Normal;
            yield return splash;

            yield return Toils_Jump.JumpIf(pickSpot, () => spotsLeft > 0);
        }

        /// <summary>
        /// Once per swim, not once per mouthful: a long session in foul water
        /// is no worse than a short one, so there is no reason to keep rolling.
        /// </summary>
        private void MaybeFallIll()
        {
            swamInFoul = false;
            if (pawn.Dead || pawn.health == null || !pawn.RaceProps.IsFlesh)
            {
                return;
            }
            HediffDef sickness = EI_HediffDefOf.EI_SwimmersSickness;
            if (pawn.health.hediffSet.HasHediff(sickness) || !Rand.Chance(SicknessChance))
            {
                return;
            }
            pawn.health.AddHediff(HediffMaker.MakeHediff(sickness, pawn));
            if (pawn.Faction == Faction.OfPlayer)
            {
                Messages.Message(pawn.LabelShort + " swallowed foul pool water and has fallen ill.",
                                 pawn, MessageTypeDefOf.NegativeHealthEvent);
            }
        }

        /// <summary>
        /// 1.6 draws a pawn with the swimming graphic while its job says it is
        /// swimming, so this gets the real pose rather than a painted waterline.
        /// On 1.5 there is no such flag and the pawn simply wades.
        /// </summary>
        private void MarkSwimming()
        {
#if RW16
            job.swimming = true;
#endif
        }
    }
}
