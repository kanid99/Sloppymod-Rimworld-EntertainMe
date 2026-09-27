using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>One look the display can wear, keyed to a point in the day.</summary>
    public class DayCyclePhase
    {
        public string label = "day";
        /// <summary>Start of this phase as a fraction of the local day, 0-1.</summary>
        public float startDayPercent;
        public string framePath;
        public int frameCount = 6;
        public ColorInt glowColor = new ColorInt(240, 230, 200, 0);
    }

    /// <summary>
    /// Shows a view of outside that follows the local clock: dawn, daylight,
    /// dusk and night, each its own animated strip, with the building's glow
    /// recoloured to match whatever it is currently showing.
    /// </summary>
    public class CompProperties_DayCycleDisplay : CompProperties
    {
        public List<DayCyclePhase> phases = new List<DayCyclePhase>();
        public int ticksPerFrame = 12;
        public Vector2 drawSize = new Vector2(3f, 1f);
        public float altitudeOffset = 0.05f;
        public bool rotateWithBuilding = true;
        /// <summary>
        /// Only show the view when the building faces one of these. A panel on
        /// a wall's north, east or west face is seen edge-on or over the top
        /// of the wall, and its own texture draws that; the view belongs to
        /// the south face. Empty = every facing.
        /// </summary>
        public List<Rot4> drawRotations = new List<Rot4>();

        public CompProperties_DayCycleDisplay()
        {
            compClass = typeof(CompDayCycleDisplay);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (phases == null || phases.Count == 0)
            {
                yield return "CompProperties_DayCycleDisplay needs at least one phase.";
            }
            else
            {
                for (int i = 0; i < phases.Count; i++)
                {
                    if (phases[i].framePath.NullOrEmpty())
                    {
                        yield return "CompProperties_DayCycleDisplay phase " + i + " has no framePath.";
                    }
                    if (i > 0 && phases[i].startDayPercent < phases[i - 1].startDayPercent)
                    {
                        yield return "CompProperties_DayCycleDisplay phases must be ordered by startDayPercent.";
                    }
                }
            }
            if (parentDef != null && parentDef.tickerType == TickerType.Never)
            {
                yield return "CompProperties_DayCycleDisplay needs a tickerType of Rare or Normal to follow the clock.";
            }
        }
    }

    public class CompDayCycleDisplay : ThingComp
    {
        private CompPowerTrader power;
        private CompGlower glower;
        private FrameSet[] sets;
        private int phase = -1;
        private int ticksToPulse;

        private CompProperties_DayCycleDisplay Props
        {
            get { return (CompProperties_DayCycleDisplay)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
            glower = parent.TryGetComp<CompGlower>();
            sets = new FrameSet[Props.phases.Count];
            for (int i = 0; i < Props.phases.Count; i++)
            {
                DayCyclePhase p = Props.phases[i];
                sets[i] = new FrameSet(p.framePath, p.frameCount, Props.drawSize);
            }
            phase = -1;
            UpdatePhase();
        }

        // Works whether the def ticks Normal or Rare.
        public override void CompTick()
        {
            if (--ticksToPulse <= 0)
            {
                ticksToPulse = 250;
                UpdatePhase();
            }
        }

        public override void CompTickRare()
        {
            UpdatePhase();
        }

        private void UpdatePhase()
        {
            if (!parent.Spawned)
            {
                return;
            }
            int now = PhaseAt(GenLocalDate.DayPercent(parent));
            if (now == phase)
            {
                return;
            }
            phase = now;
            if (glower != null)
            {
                // Recolouring the glower re-lights the room in the new colour,
                // so a night scene washes the room blue and a noon scene white.
                glower.GlowColor = Props.phases[phase].glowColor;
            }
        }

        private int PhaseAt(float dayPercent)
        {
            int result = Props.phases.Count - 1;
            for (int i = 0; i < Props.phases.Count; i++)
            {
                if (dayPercent >= Props.phases[i].startDayPercent)
                {
                    result = i;
                }
            }
            return result;
        }

        private Vector3 DrawOffset()
        {
            GraphicData data = parent.def.graphicData;
            return data == null ? Vector3.zero : data.DrawOffsetForRot(parent.Rotation);
        }

        public override void PostDraw()
        {
            base.PostDraw();

            if (!parent.Spawned || sets == null)
            {
                return;
            }
            if (power != null && !power.PowerOn)
            {
                return;
            }
            if (Props.drawRotations != null && Props.drawRotations.Count > 0
                && !Props.drawRotations.Contains(parent.Rotation))
            {
                return;
            }
            if (phase < 0)
            {
                UpdatePhase();
                if (phase < 0)
                {
                    return;
                }
            }

            FrameSet set = sets[phase];
            Graphic graphic = set.At(set.IndexFor(Props.ticksPerFrame));
            if (graphic == null)
            {
                return;
            }

            // A wall-mounted panel is drawn half a tile off its own cell so it
            // sits on the face the room can see. DrawPos does not carry that
            // offset, so without this the picture and its frame come apart.
            Vector3 drawPos = parent.DrawPos + DrawOffset();
            drawPos.y += Props.altitudeOffset;
            float extraRotation = Props.rotateWithBuilding ? parent.Rotation.AsAngle - 180f : 0f;
            graphic.Draw(drawPos, Rot4.North, parent, extraRotation);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned || phase < 0)
            {
                return null;
            }
            if (power != null && !power.PowerOn)
            {
                return null;
            }
            return "Showing: " + Props.phases[phase].label;
        }
    }

    /// <summary>
    /// Takes the edge off cabin fever for everyone in the room. It tops the
    /// outdoors need up toward a ceiling well below full, so a windowless base
    /// stays liveable without ever being as good as actually going outside.
    /// </summary>
    public class CompProperties_OutdoorsSimulator : CompProperties
    {
        /// <summary>Never pushes the need above this. Deliberately partial.</summary>
        public float maxNeedLevel = 0.35f;
        /// <summary>Added per 250-tick pulse while a pawn is in the room.</summary>
        public float gainPerPulse = 0.018f;

        public CompProperties_OutdoorsSimulator()
        {
            compClass = typeof(CompOutdoorsSimulator);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (maxNeedLevel <= 0f || maxNeedLevel > 1f)
            {
                yield return "CompProperties_OutdoorsSimulator needs a maxNeedLevel between 0 and 1.";
            }
            if (parentDef != null && parentDef.tickerType == TickerType.Never)
            {
                yield return "CompProperties_OutdoorsSimulator needs a tickerType of Rare or Normal.";
            }
        }
    }

    public class CompOutdoorsSimulator : ThingComp
    {
        private CompPowerTrader power;
        private int ticksToPulse;
        private int servedLastPulse;

        private CompProperties_OutdoorsSimulator Props
        {
            get { return (CompProperties_OutdoorsSimulator)props; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            power = parent.TryGetComp<CompPowerTrader>();
        }

        public override void CompTick()
        {
            if (--ticksToPulse <= 0)
            {
                ticksToPulse = 250;
                Pulse();
            }
        }

        public override void CompTickRare()
        {
            Pulse();
        }

        private void Pulse()
        {
            servedLastPulse = 0;

            if (!parent.Spawned)
            {
                return;
            }
            if (power != null && !power.PowerOn)
            {
                return;
            }

            Room room = RoomServed();
            if (room == null || room.PsychologicallyOutdoors)
            {
                return;
            }

            List<Pawn> pawns = parent.Map.mapPawns.FreeColonistsAndPrisonersSpawned;
            for (int i = 0; i < pawns.Count; i++)
            {
                Pawn pawn = pawns[i];
                if (pawn.needs == null || pawn.GetRoom() != room)
                {
                    continue;
                }
                Need_Outdoors need = pawn.needs.TryGetNeed<Need_Outdoors>();
                if (need == null || need.CurLevel >= Props.maxNeedLevel)
                {
                    continue;
                }
                need.CurLevel = Mathf.Min(Props.maxNeedLevel, need.CurLevel + Props.gainPerPulse);
                servedLastPulse++;
            }
        }

        /// <summary>
        /// Mounted in a wall, the panel's own cell belongs to no room, so the
        /// room it serves is the one it faces.
        /// </summary>
        private Room RoomServed()
        {
            Map map = parent.Map;
            if (map == null)
            {
                return null;
            }
            IntVec3 front = parent.Position + parent.Rotation.FacingCell;
            Room room = front.InBounds(map) ? front.GetRoom(map) : null;
            return room ?? parent.GetRoom();
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            if (power != null && !power.PowerOn)
            {
                return "Outdoors simulation: off";
            }
            Room room = RoomServed();
            if (room != null && room.PsychologicallyOutdoors)
            {
                return "Outdoors simulation: not needed here";
            }
            return servedLastPulse > 0
                ? "Easing cabin fever for " + servedLastPulse + " colonist(s) in this room"
                : "Outdoors simulation: on";
        }
    }
}
