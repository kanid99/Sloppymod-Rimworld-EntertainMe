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

        static EI_TerrainDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_TerrainDefOf));
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
        /// <summary>Recount the pool's shape this often, in ticks.</summary>
        public int recountInterval = 2000;

        public CompProperties_PoolController()
        {
            compClass = typeof(CompPoolController);
        }
    }

    public class CompPoolController : ThingComp, IServiceable
    {
        private float litres;
        private CompPowerTrader power;

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

        public bool Plumbed
        {
            get { return DubsPlumbing.PipeOn(parent) != null; }
        }

        /// <summary>Powered pump plus enough water to swim in.</summary>
        public bool SwimReady
        {
            get
            {
                return cells.Count > 0
                       && (power == null || power.PowerOn)
                       && WetTileCount > 0;
            }
        }

        private int WetTileCount
        {
            get
            {
                float capacity = Capacity;
                if (capacity <= 0f)
                {
                    return 0;
                }
                return Mathf.Clamp(Mathf.RoundToInt(cells.Count * (litres / capacity)), 0, cells.Count);
            }
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
        }

#if RW16
        public override void PostDeSpawn(Map map, DestroyMode mode = DestroyMode.Vanish)
        {
            base.PostDeSpawn(map, mode);
            DrainCompletely(map);
        }
#else
        public override void PostDeSpawn(Map map)
        {
            base.PostDeSpawn(map);
            DrainCompletely(map);
        }
#endif

        /// <summary>Take the filter away and the water goes with it.</summary>
        private void DrainCompletely(Map map)
        {
            if (map == null)
            {
                return;
            }
            for (int i = 0; i < cells.Count; i++)
            {
                if (map.terrainGrid.TerrainAt(cells[i]) == EI_TerrainDefOf.EI_PoolWater)
                {
                    map.terrainGrid.SetTerrain(cells[i], EI_TerrainDefOf.EI_PoolBasin);
                }
            }
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

            ThingComp pipe = DubsPlumbing.PipeOn(parent);
            if (pipe != null && DubsPlumbing.NetHasWater(pipe))
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
        }

        private static bool IsPoolCell(Map map, IntVec3 cell)
        {
            TerrainDef terrain = map.terrainGrid.TerrainAt(cell);
            return terrain == EI_TerrainDefOf.EI_PoolBasin || terrain == EI_TerrainDefOf.EI_PoolWater;
        }

        /// <summary>
        /// Wets the first N cells and dries the rest, so the water line moves
        /// visibly as the pool fills and drains.
        /// </summary>
        private void ApplyWaterLine()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return;
            }
            int wet = WetTileCount;
            for (int i = 0; i < cells.Count; i++)
            {
                TerrainDef wanted = i < wet ? EI_TerrainDefOf.EI_PoolWater : EI_TerrainDefOf.EI_PoolBasin;
                if (map.terrainGrid.TerrainAt(cells[i]) != wanted)
                {
                    map.terrainGrid.SetTerrain(cells[i], wanted);
                }
            }
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
            if (power != null && !power.PowerOn)
            {
                return line + "\nNo power: the water is going green, and nobody will swim in it.";
            }
            int wet = WetTileCount;
            if (wet < cells.Count)
            {
                line += "\nFilling: " + wet + " of " + cells.Count + " tiles under water.";
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
    /// Sends a pawn to a pool that is filled and running. Unlike vanilla's
    /// swimming giver this does not care whether the water is outdoors or how
    /// cold the map is - an indoor heated pool is the entire point of building
    /// one - but it does refuse a pool whose pump is off.
    /// </summary>
    public class JoyGiver_Swim : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }

            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing filter = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    60f,
                    t => Usable(pawn, t));
                if (filter == null)
                {
                    continue;
                }

                IntVec3 cell;
                if (!TryFindWetCell(pawn, filter, out cell))
                {
                    continue;
                }

                Job job = JobMaker.MakeJob(def.jobDef, cell, filter);
                return job;
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
            result = IntVec3.Invalid;
            Map map = pawn.Map;
            // The pool is the water around the filter; a radial sweep finds it
            // without the comp having to hand out its cell list.
            List<IntVec3> candidates = new List<IntVec3>();
            foreach (IntVec3 cell in GenRadial.RadialCellsAround(filter.Position, 24f, true))
            {
                if (!cell.InBounds(map))
                {
                    continue;
                }
                if (map.terrainGrid.TerrainAt(cell) != EI_TerrainDefOf.EI_PoolWater)
                {
                    continue;
                }
                if (!cell.Standable(map) || cell.IsForbidden(pawn))
                {
                    continue;
                }
                if (!pawn.CanReserveAndReach(cell, PathEndMode.OnCell, Danger.None))
                {
                    continue;
                }
                candidates.Add(cell);
            }
            if (candidates.Count == 0)
            {
                return false;
            }
            result = candidates[Rand.Range(0, candidates.Count)];
            return true;
        }
    }

    /// <summary>
    /// Swim about: pick a spot, wade to it, splash around for a while, pick
    /// another. Ends when the pawn has had enough joy or the pump stops.
    /// </summary>
    public class JobDriver_Swim : JobDriver
    {
        private const int TicksPerSpot = 260;
        private int spotsLeft = 6;

        private Thing Filter
        {
            get { return job.GetTarget(TargetIndex.B).Thing; }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref spotsLeft, "EI_swimSpotsLeft", 6);
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.ReserveSittableOrSpot(job.targetA.Cell, job, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.B);
            AddFailCondition(delegate
            {
                CompPoolController pool = Filter == null ? null : Filter.TryGetComp<CompPoolController>();
                return pool == null || !pool.SwimReady;
            });

            Toil pickSpot = ToilMaker.MakeToil("EI_PickSwimSpot");
            pickSpot.initAction = delegate
            {
                IntVec3 cell;
                if (spotsLeft > 0 && Filter != null
                    && JoyGiver_Swim.TryFindWetCell(pawn, Filter, out cell))
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
            splash.initAction = MarkSwimming;
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
