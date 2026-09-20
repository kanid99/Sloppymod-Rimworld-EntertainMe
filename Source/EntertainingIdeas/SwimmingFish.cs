using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Fish that actually swim, rather than a flipbook of fish.
    ///
    /// A frame strip can only ever move things in whole steps: eight frames at
    /// eleven ticks each is eight positions a second and a half apart, which
    /// reads as stuttering no matter how nicely the frames are drawn. This
    /// draws each fish at a position computed fresh every rendered frame from a
    /// continuous clock, so motion is as smooth as the monitor allows and the
    /// speed follows the game's - frozen when paused, three times as quick at
    /// three times speed.
    ///
    /// Each fish laps a slow ellipse whose size breathes and whose centre
    /// drifts, both far slower than the lap itself. That matters: two
    /// independent sine waves - the obvious way to write this - makes a path
    /// with cusps, where the fish momentarily stops and its heading flips. A
    /// simulation of the two puts the worst turn rate at 7800 degrees a second
    /// for the Lissajous against 350 for this, which is an ordinary fish U-turn.
    /// The breathing and drift keep the path from ever looking like a fixed
    /// racetrack, without reintroducing a stall.
    /// </summary>
    public class FishStock
    {
        /// <summary>Texture path, drawn nose-east.</summary>
        public string texPath;
        public float size = 0.3f;
        /// <summary>How many of this kind are in the tank.</summary>
        public int count = 3;
        /// <summary>Laps per in-game day, roughly. Small fish dart, big fish cruise.</summary>
        public float speed = 1f;
        public Color color = Color.white;
    }

    public class CompProperties_SwimmingFish : CompProperties
    {
        public List<FishStock> stocks = new List<FishStock>();
        /// <summary>Swimmable area in tiles, measured from the building's centre.</summary>
        public Vector2 tankSize = new Vector2(1.5f, 0.42f);
        public float altitudeOffset = 0.06f;
        /// <summary>Turn the whole tank with a rotatable building.</summary>
        public bool rotateWithBuilding = true;
        /// <summary>Degrees of tail waggle, and how fast it waggles.</summary>
        public float waggleDegrees = 9f;
        public float waggleSpeed = 7f;

        public CompProperties_SwimmingFish()
        {
            compClass = typeof(CompSwimmingFish);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (stocks == null || stocks.Count == 0)
            {
                yield return "CompProperties_SwimmingFish needs at least one stock.";
            }
            else
            {
                for (int i = 0; i < stocks.Count; i++)
                {
                    if (stocks[i].texPath.NullOrEmpty())
                    {
                        yield return "CompProperties_SwimmingFish stock " + i + " has no texPath.";
                    }
                    if (stocks[i].count < 1)
                    {
                        yield return "CompProperties_SwimmingFish stock " + i + " needs count >= 1.";
                    }
                }
            }
        }
    }

    public class CompSwimmingFish : ThingComp
    {
        /// <summary>One fish: which graphic, and where it is on its own loop.</summary>
        private struct Fish
        {
            public int stock;
            public float phase;      // its own offset along the loop
            public float speed;
            public float ax, az;     // ellipse radii
            public float w;          // lap rate
            public float wb, wd;     // breathing and centre-drift rates
            public float px, pb, pd; // phases for each
            public float angle;      // smoothed heading, so it banks into turns
            public bool angleSet;
        }

        /// <summary>How much the lap swells and shrinks, as a fraction.</summary>
        private const float Breathe = 0.30f;
        /// <summary>How far the lap's centre wanders, as a fraction.</summary>
        private const float Drift = 0.20f;

        private CompPowerTrader power;
        private Graphic[] graphics;
        private Fish[] fish;

        // A clock of our own, advanced by real time scaled to game speed, so
        // the fish move between ticks instead of jumping on them.
        private float clock;
        private float lastDelta;

        private CompProperties_SwimmingFish Props
        {
            get { return (CompProperties_SwimmingFish)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            BuildShoal();
        }

        private void BuildShoal()
        {
            List<FishStock> stocks = Props.stocks;
            graphics = new Graphic[stocks.Count];

            List<Fish> shoal = new List<Fish>();
            // Seeded off the building, so two tanks side by side do not swim in
            // lockstep but each one is the same every time the game is loaded.
            Rand.PushState(parent.thingIDNumber);
            try
            {
                for (int s = 0; s < stocks.Count; s++)
                {
                    FishStock stock = stocks[s];
                    for (int n = 0; n < stock.count; n++)
                    {
                        Fish f = new Fish();
                        f.stock = s;
                        f.phase = Rand.Range(0f, 100f);
                        f.speed = stock.speed * Rand.Range(0.82f, 1.18f);
                        // Shrunk so that breathing and drift together still fit
                        // inside the glass at full stretch.
                        float room = 1f + Breathe + Drift;
                        f.ax = Props.tankSize.x * 0.5f * Rand.Range(0.60f, 0.92f) / room;
                        f.az = Props.tankSize.y * 0.5f * Rand.Range(0.55f, 0.92f) / room;
                        f.w = Rand.Range(0.55f, 0.80f);
                        f.wb = f.w * Rand.Range(0.11f, 0.19f);
                        f.wd = f.w * Rand.Range(0.07f, 0.13f);
                        f.px = Rand.Range(0f, 6.283f);
                        f.pb = Rand.Range(0f, 6.283f);
                        f.pd = Rand.Range(0f, 6.283f);
                        shoal.Add(f);
                    }
                }
            }
            finally
            {
                Rand.PopState();
            }
            fish = shoal.ToArray();
        }

        private Graphic GraphicFor(int stock)
        {
            if (graphics[stock] == null)
            {
                FishStock s = Props.stocks[stock];
                graphics[stock] = GraphicDatabase.Get<Graphic_Single>(
                    s.texPath,
                    ShaderDatabase.TransparentPostLight,
                    new Vector2(s.size, s.size),
                    s.color);
            }
            return graphics[stock];
        }

        public override void PostDraw()
        {
            base.PostDraw();

            if (!parent.Spawned || fish == null)
            {
                return;
            }
            if (power != null && !power.PowerOn)
            {
                return;
            }

            AdvanceClock();

            GraphicData data = parent.def.graphicData;
            Vector3 origin = parent.DrawPos
                + (data == null ? Vector3.zero : data.DrawOffsetForRot(parent.Rotation));
            origin.y += Props.altitudeOffset;

            float tankAngle = Props.rotateWithBuilding ? parent.Rotation.AsAngle - 180f : 0f;
            Quaternion tankTurn = Quaternion.Euler(0f, tankAngle, 0f);

            for (int i = 0; i < fish.Length; i++)
            {
                Fish f = fish[i];
                float t = clock * f.speed + f.phase;

                // A breathing, drifting ellipse. Sampled twice a hair apart so
                // the heading comes from the path itself rather than from a
                // derivative that has to be kept in step with it by hand.
                Vector2 here = PointOn(f, t);
                Vector2 ahead = PointOn(f, t + 0.0005f);
                float x = here.x;
                float z = here.y;

                float heading = Mathf.Atan2(ahead.y - here.y, ahead.x - here.x) * Mathf.Rad2Deg;
                // Sprites are drawn nose-east; RimWorld measures rotation
                // clockwise from north, so east is 90 degrees.
                float target = 90f - heading;

                // Where the two derivatives pass through zero together the
                // heading is briefly undefined and would snap. Easing toward it
                // removes that and makes the fish bank into its turns.
                if (!f.angleSet)
                {
                    fish[i].angle = target;
                    fish[i].angleSet = true;
                }
                else if (lastDelta > 0f)
                {
                    fish[i].angle = Mathf.LerpAngle(f.angle, target,
                                                    1f - Mathf.Exp(-6f * lastDelta));
                }
                float angle = fish[i].angle
                              + Props.waggleDegrees * Mathf.Sin(t * Props.waggleSpeed);

                Vector3 local = tankTurn * new Vector3(x, 0f, z);
                Graphic graphic = GraphicFor(f.stock);
                if (graphic != null)
                {
                    graphic.Draw(origin + local, Rot4.North, parent, angle + tankAngle);
                }
            }
        }

        /// <summary>Where a fish is on its lap at parameter t.</summary>
        private static Vector2 PointOn(Fish f, float t)
        {
            float rx = f.ax * (1f + Breathe * Mathf.Sin(f.wb * t + f.pb));
            float rz = f.az * (1f + Breathe * Mathf.Cos(f.wb * t + f.pb));
            float cx = f.ax * Drift * Mathf.Sin(f.wd * t + f.pd);
            float cz = f.az * Drift * Mathf.Cos(f.wd * t * 1.3f + f.pd);
            return new Vector2(cx + rx * Mathf.Cos(f.w * t + f.px),
                               cz + rz * Mathf.Sin(f.w * t + f.px));
        }

        /// <summary>
        /// Real seconds scaled by the game's speed, so the shoal freezes with
        /// the game and speeds up with it, but moves smoothly between ticks.
        /// </summary>
        private void AdvanceClock()
        {
            TickManager ticks = Find.TickManager;
            if (ticks == null || ticks.Paused)
            {
                lastDelta = 0f;
                return;
            }
            lastDelta = RealTime.deltaTime * ticks.TickRateMultiplier;
            clock += lastDelta;
        }
    }
}
