using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    [DefOf]
    public static class EI_IceFishingDefOf
    {
        public static JobDef EI_IceFish;
        public static ThoughtDef EI_CaughtFish;
        public static ThoughtDef EI_LandedRecordFish;

        static EI_IceFishingDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(EI_IceFishingDefOf));
        }
    }

    /// <summary>One kind of fish that can come up through the hole.</summary>
    public class IceFishSpecies
    {
        public string label;
        public float minKg = 0.2f;
        public float maxKg = 1f;
        /// <summary>How often this one bites, relative to the others.</summary>
        public float commonality = 1f;
        /// <summary>Tints the fish sprite, which is painted near-white for it.</summary>
        public ColorInt colour = new ColorInt(200, 200, 200);
    }

    public class CompProperties_IceFishing : CompProperties
    {
        /// <summary>Ice this thick or more holds a colonist and a bucket.</summary>
        public float safeThicknessCm = 10f;
        public float maxThicknessCm = 60f;
        /// <summary>Centimetres gained per day per degree below freezing.</summary>
        public float freezeCmPerDegreeDay = 0.5f;
        /// <summary>Centimetres lost per day per degree above freezing. Ice goes faster than it comes.</summary>
        public float meltCmPerDegreeDay = 1f;
        /// <summary>
        /// A hole built in the middle of a winter does not start on open
        /// water: it starts as thick as that season would have made it, this
        /// many centimetres per degree the season sits below freezing.
        /// </summary>
        public float startCmPerSeasonalDegree = 3f;

        /// <summary>Ticks between chances of a bite while someone is jigging.</summary>
        public int biteIntervalTicks = 600;
        public float catchChance = 0.3f;
        /// <summary>Added to catchChance per level of the angler's Animals skill.</summary>
        public float catchChancePerSkill = 0.015f;

        public List<IceFishSpecies> species = new List<IceFishSpecies>();

        /// <summary>The line jigging over the hole, drawn while someone fishes.</summary>
        public string framePath;
        public int frameCount = 8;
        public int ticksPerFrame = 12;
        /// <summary>Two tiles tall, centred on the hole, so the rod reaches the angler's hands.</summary>
        public Vector2 drawSize = new Vector2(1f, 2f);
        public string fishTexPath;
        public string bucketTexPath;
        /// <summary>How long a catch flaps on the ice before it goes back down, in ticks.</summary>
        public int flopTicks = 420;
        /// <summary>How often to look for the angler again, in ticks.</summary>
        public int recheckInterval = 30;

        public CompProperties_IceFishing()
        {
            compClass = typeof(CompIceFishing);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (species == null || species.Count == 0)
            {
                yield return "CompProperties_IceFishing needs at least one species.";
            }
            else
            {
                for (int i = 0; i < species.Count; i++)
                {
                    if (species[i].maxKg < species[i].minKg || species[i].minKg <= 0f)
                    {
                        yield return "CompProperties_IceFishing species " + species[i].label
                                     + " needs 0 < minKg <= maxKg.";
                    }
                }
            }
            if (ticksPerFrame < 1)
            {
                yield return "CompProperties_IceFishing needs ticksPerFrame >= 1.";
            }
            if (!parentDef.hasInteractionCell)
            {
                yield return "CompProperties_IceFishing needs an interaction cell to fish from.";
            }
            if (parentDef.tickerType != TickerType.Rare)
            {
                yield return "CompProperties_IceFishing needs tickerType Rare, or the ice never changes.";
            }
        }
    }

    /// <summary>
    /// A hole cut through the ice, and the ice around it.
    ///
    /// RimWorld's water never freezes, so the ice is this comp's own: a
    /// thickness that grows through cold days and melts through warm ones, off
    /// the map's outdoor temperature. Nobody goes out until it will hold them.
    /// On terrain that is already ice - a sea-ice map, an ice sheet - it is
    /// always thick enough.
    ///
    /// Everything caught goes back down the hole. What stays is the story:
    /// how many, and the biggest, and who landed it.
    /// </summary>
    public class CompIceFishing : ThingComp
    {
        private float thicknessCm;
        private int catches;
        private float bestKg;
        private string bestSpecies;
        private string bestAngler;

        // The fish on the ice right now, if any. Not saved: it is only ever
        // there for a few seconds.
        private int lastCatchTick = -99999;
        private int lastCatchSpecies;
        private float lastCatchKg;

        private FrameSet jig;
        private Graphic bucket;
        private readonly Dictionary<int, Graphic> fishGraphics = new Dictionary<int, Graphic>();
        private Graphic fishShadow;
        private Pawn angler;
        private int nextRecheckTick = -99999;

        public CompProperties_IceFishing Props
        {
            get { return (CompProperties_IceFishing)props; }
        }

        /// <summary>Terrain a hole can be cut into.</summary>
        public static bool Fishable(TerrainDef terrain)
        {
            return terrain != null && (terrain.IsWater || IsIce(terrain));
        }

        private static bool IsIce(TerrainDef terrain)
        {
            return terrain != null && terrain.defName == "Ice";
        }

        private bool PermanentIce
        {
            get { return parent.Spawned && IsIce(parent.Position.GetTerrain(parent.Map)); }
        }

        public float ThicknessCm
        {
            get { return PermanentIce ? Props.maxThicknessCm : thicknessCm; }
        }

        public bool SafeToFish
        {
            get { return parent.Spawned && ThicknessCm >= Props.safeThicknessCm; }
        }

        public override void PostSpawnSetup(bool respawningAfterLoad)
        {
            base.PostSpawnSetup(respawningAfterLoad);
            jig = Props.framePath.NullOrEmpty()
                ? null
                : new FrameSet(Props.framePath, Props.frameCount, Props.drawSize, ShaderDatabase.Transparent);
            nextRecheckTick = -99999;
            if (!respawningAfterLoad)
            {
                float seasonal = parent.Map.mapTemperature.SeasonalTemp;
                thicknessCm = Mathf.Clamp(-seasonal * Props.startCmPerSeasonalDegree, 0f, Props.maxThicknessCm);
            }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref thicknessCm, "EI_iceCm", 0f);
            Scribe_Values.Look(ref catches, "EI_iceCatches", 0);
            Scribe_Values.Look(ref bestKg, "EI_iceBestKg", 0f);
            Scribe_Values.Look(ref bestSpecies, "EI_iceBestSpecies");
            Scribe_Values.Look(ref bestAngler, "EI_iceBestAngler");
        }

        public override void CompTickRare()
        {
            base.CompTickRare();
            if (!parent.Spawned || PermanentIce)
            {
                return;
            }
            float temperature = parent.Map.mapTemperature.OutdoorTemp;
            float days = GenTicks.TickRareInterval / (float)GenDate.TicksPerDay;
            float rate = temperature < 0f ? Props.freezeCmPerDegreeDay : Props.meltCmPerDegreeDay;
            thicknessCm = Mathf.Clamp(thicknessCm - temperature * rate * days, 0f, Props.maxThicknessCm);
        }

        /// <summary>
        /// Called by the angler's job every bite interval. Most of the time
        /// nothing is down there.
        /// </summary>
        public void TryBite(Pawn pawn)
        {
            int skill = SkillOf(pawn);
            if (Rand.Chance(Props.catchChance + Props.catchChancePerSkill * skill))
            {
                Land(pawn, skill);
            }
        }

        private static int SkillOf(Pawn pawn)
        {
            SkillRecord record = pawn.skills == null ? null : pawn.skills.GetSkill(SkillDefOf.Animals);
            return record == null || record.TotallyDisabled ? 0 : record.Level;
        }

        private void Land(Pawn pawn, int skill)
        {
            int index = PickSpecies();
            IceFishSpecies fish = Props.species[index];
            // Mostly small ones. Someone who knows animals is likelier to be
            // patient enough for a big one.
            float exponent = Mathf.Lerp(2.4f, 1.2f, skill / 20f);
            float kg = Mathf.Lerp(fish.minKg, fish.maxKg, Mathf.Pow(Rand.Value, exponent));
            kg = Mathf.Round(kg * 10f) / 10f;

            bool record = catches > 0 && kg > bestKg;
            catches++;
            if (kg > bestKg)
            {
                bestKg = kg;
                bestSpecies = fish.label;
                bestAngler = pawn.LabelShort;
            }

            lastCatchTick = Find.TickManager.TicksGame;
            lastCatchSpecies = index;
            lastCatchKg = kg;

            MoteMaker.ThrowText(parent.DrawPos, parent.Map, kg.ToString("0.0") + " kg " + fish.label, 4f);

            if (pawn.needs != null && pawn.needs.mood != null)
            {
                pawn.needs.mood.thoughts.memories.TryGainMemory(
                    record ? EI_IceFishingDefOf.EI_LandedRecordFish : EI_IceFishingDefOf.EI_CaughtFish);
            }
            if (record && parent.Faction == Faction.OfPlayer)
            {
                Messages.Message(pawn.LabelShort + " has pulled a " + kg.ToString("0.0") + " kg " + fish.label
                                 + " up through the ice - the biggest this hole has seen. It went back down.",
                                 new LookTargets(parent), MessageTypeDefOf.PositiveEvent);
            }
        }

        private int PickSpecies()
        {
            List<IceFishSpecies> list = Props.species;
            float total = 0f;
            for (int i = 0; i < list.Count; i++)
            {
                total += Mathf.Max(0f, list[i].commonality);
            }
            float roll = Rand.Value * total;
            for (int i = 0; i < list.Count; i++)
            {
                roll -= Mathf.Max(0f, list[i].commonality);
                if (roll <= 0f)
                {
                    return i;
                }
            }
            return list.Count - 1;
        }

        /// <summary>
        /// Whoever is jigging at the hole. Only the interaction cell is looked
        /// at, so this is cheap enough to ask while drawing.
        /// </summary>
        private Pawn FindAngler()
        {
            IntVec3 seat = parent.InteractionCell;
            if (!seat.InBounds(parent.Map))
            {
                return null;
            }
            List<Thing> things = seat.GetThingList(parent.Map);
            for (int i = 0; i < things.Count; i++)
            {
                Pawn pawn = things[i] as Pawn;
                if (pawn == null)
                {
                    continue;
                }
                Job job = pawn.CurJob;
                if (job != null && job.def == EI_IceFishingDefOf.EI_IceFish && job.targetA.Thing == parent)
                {
                    return pawn;
                }
            }
            return null;
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned)
            {
                return;
            }

            DrawBucket();

            int now = Find.TickManager.TicksGame;
            if (now >= nextRecheckTick)
            {
                nextRecheckTick = now + Props.recheckInterval;
                angler = FindAngler();
            }

            float turn = parent.Rotation.AsAngle - 180f;
            if (angler != null && jig != null)
            {
                Graphic frame = jig.At(jig.IndexFor(Props.ticksPerFrame));
                if (frame != null)
                {
                    Vector3 at = parent.DrawPos;
                    at.y += 0.05f;
                    frame.Draw(at, Rot4.North, parent, turn);
                }
            }

            int age = now - lastCatchTick;
            if (age >= 0 && age < Props.flopTicks)
            {
                DrawCatch(age / (float)Props.flopTicks, turn);
            }
        }

        /// <summary>The upturned bucket the angler sits on.</summary>
        private void DrawBucket()
        {
            if (Props.bucketTexPath.NullOrEmpty())
            {
                return;
            }
            if (bucket == null)
            {
                bucket = GraphicDatabase.Get<Graphic_Single>(
                    Props.bucketTexPath, ShaderDatabase.Cutout, new Vector2(0.6f, 0.6f), Color.white);
            }
            Vector3 at = parent.InteractionCell.ToVector3Shifted();
            at.y = AltitudeLayer.BuildingOnTop.AltitudeFor();
            bucket.Draw(at, Rot4.North, parent, 0f);
        }

        /// <summary>
        /// The fish, flapping on the ice beside the hole, then slid back in.
        /// Driven off the game clock, so it holds still while paused.
        /// </summary>
        private void DrawCatch(float t, float turn)
        {
            if (Props.fishTexPath.NullOrEmpty() || lastCatchSpecies >= Props.species.Count)
            {
                return;
            }
            // Out to the side of the hole, away from the angler's seat.
            Vector3 side = Quaternion.Euler(0f, turn, 0f) * new Vector3(0.42f, 0f, -0.05f);
            Vector3 hole = parent.DrawPos;
            Vector3 at = hole + side;

            float size = 0.26f + 0.16f * Mathf.Sqrt(lastCatchKg);
            float flap = Mathf.Sin(t * 70f) * 28f * (1f - t);
            float hop = Mathf.Abs(Mathf.Sin(t * 35f)) * 0.08f * (1f - t);

            // The last fifth: slid back to the hole and let go.
            if (t > 0.8f)
            {
                float back = (t - 0.8f) / 0.2f;
                at = Vector3.Lerp(at, hole, back);
                size *= 1f - 0.6f * back;
                flap = 0f;
                hop = 0f;
            }

            float angle = turn + flap;

            Vector3 shadow = at;
            shadow.y = AltitudeLayer.Shadows.AltitudeFor();
            Blit(Shadow, shadow, angle, size);

            Vector3 body = at;
            body.z += hop;
            body.y = AltitudeLayer.MoteLow.AltitudeFor();
            Blit(FishGraphic(lastCatchSpecies), body, angle, size);
        }

        private Graphic FishGraphic(int index)
        {
            Graphic cached;
            if (!fishGraphics.TryGetValue(index, out cached))
            {
                cached = GraphicDatabase.Get<Graphic_Single>(
                    Props.fishTexPath, ShaderDatabase.Transparent, Vector2.one, Props.species[index].colour.ToColor);
                fishGraphics[index] = cached;
            }
            return cached;
        }

        private Graphic Shadow
        {
            get
            {
                if (fishShadow == null)
                {
                    fishShadow = GraphicDatabase.Get<Graphic_Single>(
                        Props.fishTexPath, ShaderDatabase.Transparent, Vector2.one, new Color(0f, 0f, 0f, 0.25f));
                }
                return fishShadow;
            }
        }

        private static void Blit(Graphic graphic, Vector3 at, float angle, float size)
        {
            Matrix4x4 matrix = default(Matrix4x4);
            matrix.SetTRS(at, Quaternion.Euler(0f, angle, 0f), new Vector3(size, 1f, size));
            Graphics.DrawMesh(MeshPool.plane10, matrix, graphic.MatSingle, 0);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            string ice;
            if (PermanentIce)
            {
                ice = "Solid ice - always safe to fish.";
            }
            else if (thicknessCm < 0.5f)
            {
                ice = "Open water. It wants a hard freeze before anyone goes out.";
            }
            else if (SafeToFish)
            {
                ice = "Ice: " + Mathf.RoundToInt(thicknessCm) + " cm - safe to fish.";
            }
            else
            {
                ice = "Ice: " + thicknessCm.ToString("0.#") + " cm - too thin to go out on (needs "
                      + Mathf.RoundToInt(Props.safeThicknessCm) + ").";
            }
            if (catches == 0)
            {
                return ice + "\nNothing caught here yet.";
            }
            return ice + "\nCaught here: " + catches + ". Biggest: " + bestKg.ToString("0.0") + " kg "
                   + bestSpecies + ", by " + bestAngler + ".";
        }
    }

    /// <summary>
    /// A hole can only be cut into water or ice, with somewhere to sit beside
    /// it - the shore, the shallows, or more ice.
    /// </summary>
    public class PlaceWorker_IceFishingHole : PlaceWorker
    {
        public override AcceptanceReport AllowsPlacing(BuildableDef checkingDef, IntVec3 loc, Rot4 rot,
                                                       Map map, Thing thingToIgnore = null, Thing thing = null)
        {
            if (!CompIceFishing.Fishable(loc.GetTerrain(map)))
            {
                return new AcceptanceReport("Must be cut into water or ice.");
            }
            ThingDef def = checkingDef as ThingDef;
            if (def != null && def.hasInteractionCell)
            {
                IntVec3 seat = ThingUtility.InteractionCellWhenAt(def, loc, rot, map);
                if (!seat.InBounds(map) || !seat.Walkable(map))
                {
                    return new AcceptanceReport(
                        "Needs somewhere to sit beside the hole: the shore, the shallows or the ice.");
                }
            }
            return true;
        }
    }

    /// <summary>
    /// Someone wrapped up warm enough for the weather goes out to a hole whose
    /// ice will hold them and nobody else is at.
    /// </summary>
    public class JoyGiver_IceFishing : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            // Vanilla's own test for a walk or a sky-gaze: comfortable in this
            // temperature in what they are wearing, and not a storm.
            if (!JoyUtility.EnjoyableOutsideNow(pawn))
            {
                return null;
            }
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                Thing hole = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.InteractionCell,
                    TraverseParms.For(pawn),
                    // Lakes are rarely next to the barracks.
                    100f,
                    t => Usable(pawn, t));
                if (hole != null)
                {
                    return JobMaker.MakeJob(def.jobDef, hole);
                }
            }
            return null;
        }

        private static bool Usable(Pawn pawn, Thing hole)
        {
            if (hole.IsForbidden(pawn) || hole.IsBurning() || !pawn.CanReserve(hole))
            {
                return false;
            }
            CompIceFishing comp = hole.TryGetComp<CompIceFishing>();
            return comp != null && comp.SafeToFish;
        }
    }

    /// <summary>
    /// Sit on the bucket, face the hole, jig the line. Every so often
    /// something takes it.
    /// </summary>
    public class JobDriver_IceFishing : JobDriver
    {
        private int ticksToBite;
        private int ticksToWeatherCheck;

        /// <summary>How often the angler asks whether it has got too cold to stay out.</summary>
        private const int WeatherCheckInterval = 250;

        private Thing Hole
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        private CompIceFishing Comp
        {
            get { return Hole == null ? null : Hole.TryGetComp<CompIceFishing>(); }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref ticksToBite, "EI_ticksToBite", 0);
            Scribe_Values.Look(ref ticksToWeatherCheck, "EI_ticksToWeatherCheck", 0);
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.Reserve(job.targetA, job, 1, -1, null, errorOnFailed);
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);
            // A thaw: off the ice.
            AddFailCondition(delegate
            {
                CompIceFishing comp = Comp;
                return comp == null || !comp.SafeToFish;
            });

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.InteractionCell);

            Toil fish = ToilMaker.MakeToil("EI_IceFish");
            fish.initAction = delegate
            {
                ResetBite();
                ticksToWeatherCheck = WeatherCheckInterval;
            };
            fish.defaultCompleteMode = ToilCompleteMode.Delay;
            fish.defaultDuration = job.def.joyDuration;
            fish.handlingFacing = true;
#if RW16
            fish.tickIntervalAction = delegate(int delta)
            {
                if (Jig(delta))
                {
                    JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Hole as Building);
                }
            };
#else
            fish.tickAction = delegate
            {
                if (Jig(1))
                {
                    JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Hole as Building);
                }
            };
#endif
            fish.socialMode = RandomSocialMode.Quiet;
            yield return fish;
        }

        private void ResetBite()
        {
            CompIceFishing comp = Comp;
            int interval = comp == null ? 600 : comp.Props.biteIntervalTicks;
            ticksToBite = Mathf.RoundToInt(interval * Rand.Range(0.6f, 1.4f));
        }

        /// <summary>One stretch of jigging. False when the angler has packed up.</summary>
        private bool Jig(int delta)
        {
            if (Hole != null)
            {
                pawn.rotationTracker.FaceCell(Hole.Position);
            }
            // The weather turning, or the cold getting through: pack up and go in.
            ticksToWeatherCheck -= delta;
            if (ticksToWeatherCheck <= 0)
            {
                ticksToWeatherCheck = WeatherCheckInterval;
                if (!JoyUtility.EnjoyableOutsideNow(pawn))
                {
                    EndJobWith(JobCondition.Succeeded);
                    return false;
                }
            }
            ticksToBite -= delta;
            if (ticksToBite > 0)
            {
                return true;
            }
            ResetBite();
            CompIceFishing comp = Comp;
            if (comp != null)
            {
                comp.TryBite(pawn);
            }
            return true;
        }
    }
}
