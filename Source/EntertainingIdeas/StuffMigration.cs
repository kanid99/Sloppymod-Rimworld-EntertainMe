using System.Collections.Generic;
using RimWorld;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Repairs this mod's own things in a save that predates a def becoming
    /// stuffable.
    ///
    /// A blueprint, frame or building placed while its def had no
    /// stuffCategories carries no stuff. Make the def stuffable in a later
    /// version and that null becomes illegal: CostListCalculator throws
    /// "Cannot get AdjustedCostList for ... with null Stuff" every time a
    /// hauler so much as looks at the blueprint, once per tick per pawn.
    ///
    /// Nothing in vanilla migrates that, so this fills in the default stuff on
    /// load. It touches only defs from this mod - other mods' saves are not
    /// ours to rewrite.
    /// </summary>
    public class GameComponent_StuffMigration : GameComponent
    {
        public GameComponent_StuffMigration(Game game)
        {
        }

        public override void FinalizeInit()
        {
            base.FinalizeInit();
            Repair();
        }

        private static bool Ours(Def def)
        {
            return def != null && def.defName != null && def.defName.StartsWith("EI_");
        }

        /// <summary>The def a thing will become, which is what carries the stuff rules.</summary>
        private static ThingDef StuffedDefBehind(Thing thing)
        {
            ThingDef built = thing.def.entityDefToBuild as ThingDef;
            if (built != null)
            {
                return built;         // blueprint or frame
            }
            return thing.def;         // the finished building
        }

        private static void Repair()
        {
            List<Map> maps = Find.Maps;
            if (maps == null)
            {
                return;
            }

            int repaired = 0;
            for (int m = 0; m < maps.Count; m++)
            {
                Map map = maps[m];
                foreach (ThingRequestGroup group in new[] { ThingRequestGroup.Blueprint,
                                                            ThingRequestGroup.BuildingFrame,
                                                            ThingRequestGroup.BuildingArtificial })
                {
                    // Copied, because assigning stuff can touch the lister.
                    List<Thing> things = new List<Thing>(map.listerThings.ThingsInGroup(group));
                    for (int i = 0; i < things.Count; i++)
                    {
                        Thing thing = things[i];
                        ThingDef target = StuffedDefBehind(thing);
                        if (!Ours(target) || !target.MadeFromStuff)
                        {
                            continue;
                        }

                        ThingDef fallback = GenStuff.DefaultStuffFor(target);
                        if (fallback == null)
                        {
                            continue;
                        }

                        Blueprint_Build blueprint = thing as Blueprint_Build;
                        if (blueprint != null)
                        {
                            if (blueprint.stuffToUse == null)
                            {
                                blueprint.stuffToUse = fallback;
                                repaired++;
                            }
                            continue;
                        }
                        if (thing.Stuff == null)
                        {
                            thing.SetStuffDirect(fallback);
                            repaired++;
                        }
                    }
                }
            }

            if (repaired > 0)
            {
                Log.Message("[Entertaining Ideas] Gave " + repaired + " thing(s) from an older save "
                            + "their default material, now that their def is stuffable.");
            }
        }
    }
}
