using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Steam off hot water, and the ripples underneath it.
    ///
    /// A frame strip cannot do steam: a puff has to drift, spread and fade on
    /// its own clock, and stepping six painted frames reads as a grey blob
    /// blinking on and off. These are the game's own flecks instead - the same
    /// ones a steam geyser throws - so they drift smoothly, sit at the right
    /// altitude, and look like everything else on the map.
    /// </summary>
    public class CompProperties_SteamPlume : CompProperties
    {
        /// <summary>Average ticks between puffs. Jittered so it never pulses.</summary>
        public int puffInterval = 22;
        /// <summary>Average ticks between surface ripples. 0 turns them off.</summary>
        public int rippleInterval = 35;
        /// <summary>How far off centre effects appear, in tiles.</summary>
        public float radius = 0.34f;
        /// <summary>
        /// Where the middle of the water is, from the building's centre. A tub
        /// drawn standing shows its water up at the rim, not on the floor.
        /// </summary>
        public Vector3 surfaceOffset = Vector3.zero;
        /// <summary>
        /// How round the water looks: 1 seen straight down, less for a rim seen
        /// at the camera's slant, which reads as an ellipse.
        /// </summary>
        public float surfaceSquash = 1f;
        /// <summary>Only while a refuelable parent is lit.</summary>
        public bool requireFuel = false;
        /// <summary>Only while a powered parent is on.</summary>
        public bool requirePower = false;
        /// <summary>Only while the basin actually has water in it.</summary>
        public bool requireWater = true;

        public CompProperties_SteamPlume()
        {
            compClass = typeof(CompSteamPlume);
        }
    }

    public class CompSteamPlume : ThingComp
    {
        private static FleckDef rippleFleck;
        private static bool rippleLookedUp;

        private CompPowerTrader power;
        private CompRefuelable fuel;
        private CompWaterBasin basin;
        private int nextPuff;
        private int nextRipple;

        private CompProperties_SteamPlume Props
        {
            get { return (CompProperties_SteamPlume)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            fuel = parent.TryGetComp<CompRefuelable>();
            basin = parent.TryGetComp<CompWaterBasin>();
        }

        /// <summary>WaterRipple is a 1.6 fleck; on 1.5 there simply are no ripples.</summary>
        private static FleckDef RippleFleck
        {
            get
            {
                if (!rippleLookedUp)
                {
                    rippleLookedUp = true;
                    rippleFleck = DefDatabase<FleckDef>.GetNamedSilentFail("WaterRipple");
                }
                return rippleFleck;
            }
        }

        public bool Steaming
        {
            get
            {
                if (!parent.Spawned)
                {
                    return false;
                }
                if (Props.requirePower && (power == null || !power.PowerOn))
                {
                    return false;
                }
                if (Props.requireFuel && (fuel == null || !fuel.HasFuel))
                {
                    return false;
                }
                return !Props.requireWater || basin == null || basin.HasWater;
            }
        }

        public override void CompTick()
        {
            base.CompTick();
            if (!Steaming)
            {
                return;
            }

            Map map = parent.Map;
            if (map == null)
            {
                return;
            }

            if (--nextPuff <= 0)
            {
                nextPuff = Mathf.Max(1, (int)(Props.puffInterval * Rand.Range(0.6f, 1.5f)));
                FleckMaker.ThrowAirPuffUp(SurfacePoint(), map);
            }

            if (Props.rippleInterval > 0 && RippleFleck != null && --nextRipple <= 0)
            {
                nextRipple = Mathf.Max(1, (int)(Props.rippleInterval * Rand.Range(0.6f, 1.5f)));
                FleckMaker.Static(SurfacePoint(), map, RippleFleck, Rand.Range(0.5f, 0.9f));
            }
        }

        /// <summary>A random point on the water, not always dead centre.</summary>
        private Vector3 SurfacePoint()
        {
            Vector2 offset = Rand.InsideUnitCircle * Props.radius;
            Vector3 point = parent.DrawPos + Props.surfaceOffset;
            point.x += offset.x;
            point.z += offset.y * Props.surfaceSquash;
            return point;
        }
    }

    /// <summary>
    /// What a soak is worth beyond the recreation.
    ///
    /// Everything here is looked up by name and skipped when it is not there,
    /// so with Dubs Bad Hygiene installed a soak washes the colonist and they
    /// come out pleased about the hot water, and without it the tub behaves
    /// exactly as it did before. No hard reference either way.
    /// </summary>
    public class CompProperties_Bathing : CompProperties
    {
        /// <summary>Need raised by a soak, as a fraction of full.</summary>
        public float hygieneGain = 0.85f;
        /// <summary>Dubs Bad Hygiene's need and memories, by name.</summary>
        public string needDefName = "Hygiene";
        public string hotThoughtDefName = "HotBath";
        public string coldThoughtDefName = "ColdWater";

        public CompProperties_Bathing()
        {
            compClass = typeof(CompBathing);
        }
    }

    public class CompBathing : ThingComp
    {
        private CompRefuelable fuel;
        private CompPowerTrader power;
        private bool heatResolved;
        private NeedDef hygieneNeed;
        private bool hygieneLookedUp;

        private CompProperties_Bathing Props
        {
            get { return (CompProperties_Bathing)props; }
        }

        /// <summary>
        /// Resolved on first use rather than on every ask. The inspect pane
        /// rebuilds its text every frame the tub is selected, and walking the
        /// comp list twice a frame to answer a question whose answer cannot
        /// change is waste.
        /// </summary>
        private void ResolveHeatSource()
        {
            if (heatResolved)
            {
                return;
            }
            heatResolved = true;
            fuel = parent.TryGetComp<CompRefuelable>();
            power = parent.TryGetComp<CompPowerTrader>();
        }

        /// <summary>
        /// A wood-fired tub is hot while the firebox is lit; an electric one
        /// while it has power. A tub with neither is a barrel of cold water,
        /// which a colonist will still wash in and still complain about.
        /// </summary>
        public bool WaterIsHot
        {
            get
            {
                ResolveHeatSource();
                if (fuel != null)
                {
                    return fuel.HasFuel;
                }
                return power != null && power.PowerOn;
            }
        }

        /// <summary>
        /// Dubs Bad Hygiene's need, looked up once per tub rather than on every
        /// frame the inspect pane is open. Null when that mod is not installed,
        /// which is the case this has to stay cheap in.
        /// </summary>
        private NeedDef HygieneNeed
        {
            get
            {
                if (!hygieneLookedUp)
                {
                    hygieneLookedUp = true;
                    hygieneNeed = DefDatabase<NeedDef>.GetNamedSilentFail(Props.needDefName);
                }
                return hygieneNeed;
            }
        }

        public void OnBathed(Pawn pawn)
        {
            if (pawn == null || pawn.needs == null)
            {
                return;
            }

            NeedDef needDef = HygieneNeed;
            if (needDef != null)
            {
                Need need = pawn.needs.TryGetNeed(needDef);
                if (need != null && need.CurLevel < Props.hygieneGain)
                {
                    need.CurLevel = Props.hygieneGain;
                }
            }

            if (pawn.needs.mood == null || pawn.needs.mood.thoughts == null)
            {
                return;
            }
            string thoughtName = WaterIsHot ? Props.hotThoughtDefName : Props.coldThoughtDefName;
            ThoughtDef thought = DefDatabase<ThoughtDef>.GetNamedSilentFail(thoughtName);
            if (thought != null)
            {
                pawn.needs.mood.thoughts.memories.TryGainMemory(thought);
            }
        }

        public override string CompInspectStringExtra()
        {
            // Only worth saying when there is a hygiene need to serve.
            if (HygieneNeed == null)
            {
                return null;
            }
            return WaterIsHot ? "Water: hot" : "Water: cold - a soak will wash, but nobody will enjoy it";
        }
    }
}
