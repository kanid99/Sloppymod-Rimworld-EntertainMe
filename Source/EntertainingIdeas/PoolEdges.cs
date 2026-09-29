using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    [StaticConstructorOnStartup]
    internal static class PoolEdgeMats
    {
        private const string Dir = "EntertainingIdeas/Terrain/PoolEdge/";

        public static readonly Material Coping = Mat("PoolCoping");
        public static readonly Material CornerOuter = Mat("PoolCopingCornerOuter");
        public static readonly Material CornerInner = Mat("PoolCopingCornerInner");
        public static readonly Material WallFace = Mat("PoolWallFace");
        public static readonly Material WallFaceSkimmer = Mat("PoolWallFaceSkimmer");
        public static readonly Material WallFaceJet = Mat("PoolWallFaceJet");
        public static readonly Material WallSide = Mat("PoolWallSide");
        public static readonly Material Drain = Mat("PoolDrain");
        public static readonly Material DrainWet = Mat("PoolDrainWet");
        public static readonly Material Ladder = Mat("PoolLadder");

        private static Material Mat(string name)
        {
            return MaterialPool.MatFrom(Dir + name, ShaderDatabase.Transparent);
        }
    }

    /// <summary>
    /// Gives a painted pool a proper rim. Terrain alone can only blend into
    /// its neighbours, so this layer draws over it: a stone coping along every
    /// side of the pool that meets anything that is not pool, the far (north)
    /// wall showing under its coping because the pool is sunk, a glimpse of
    /// the side walls, and the fittings - a floor drain here and there, a
    /// skimmer or a return jet in the far wall, a ladder on the near side.
    ///
    /// Everything is decided from the cell and its neighbours alone, so any
    /// shape the player paints gets a sensible rim, and it redraws with the
    /// terrain: the game makes one of these per map section, finds it by
    /// reflection like its own layers, and rebuilds it whenever terrain in or
    /// next to the section changes - including the water line moving.
    /// </summary>
    public class SectionLayer_PoolEdges : SectionLayer
    {
        /// <summary>Coping width inside the pool's edge, and how far it laps over the neighbour.</summary>
        private const float Cope = 0.16f;
        private const float Lap = 0.06f;
        /// <summary>How much of the far wall shows below its coping.</summary>
        private const float Wall = 0.2f;
        private const float SideWall = 0.07f;

        public SectionLayer_PoolEdges(Section section) : base(section)
        {
            relevantChangeTypes = MapMeshFlagDefOf.Terrain;
        }

        private static bool IsPool(Map map, IntVec3 c)
        {
            return c.InBounds(map) && PoolWater.IsPool(map.terrainGrid.TerrainAt(c));
        }

        private static float Hash(IntVec3 c, int salt)
        {
            unchecked
            {
                uint h = 2166136261;
                h = (h ^ (uint)c.x) * 16777619;
                h = (h ^ (uint)c.z) * 16777619;
                h = (h ^ (uint)salt) * 16777619;
                h ^= h >> 13;
                h *= 1274126177;
                h ^= h >> 16;
                return h / 4294967295f;
            }
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            Map map = Map;
            TerrainGrid grid = map.terrainGrid;
            float y = AltitudeLayer.TerrainScatter.AltitudeFor();

            foreach (IntVec3 c in section.CellRect)
            {
                TerrainDef here = grid.TerrainAt(c);
                if (!PoolWater.IsPool(here))
                {
                    continue;
                }
                bool n = !IsPool(map, c + IntVec3.North);
                bool s = !IsPool(map, c + IntVec3.South);
                bool e = !IsPool(map, c + IntVec3.East);
                bool w = !IsPool(map, c + IntVec3.West);
                float x0 = c.x, x1 = c.x + 1f, z0 = c.z, z1 = c.z + 1f;

                // Walls first, so the coping lies over their top edges.
                if (n)
                {
                    float r = Hash(c, 3);
                    Material face = r < 0.3f ? PoolEdgeMats.WallFaceSkimmer
                                  : r < 0.55f ? PoolEdgeMats.WallFaceJet
                                  : PoolEdgeMats.WallFace;
                    Rect(face, y, x0, z1 - Cope - Wall, x1, z1 - Cope, 0);
                }
                if (w)
                {
                    Rect(PoolEdgeMats.WallSide, y, x0 + Cope, z0, x0 + Cope + SideWall, z1, 0);
                }
                if (e)
                {
                    Rect(PoolEdgeMats.WallSide, y, x1 - Cope - SideWall, z0, x1 - Cope, z1, 2);
                }

                // A drain on roughly one cell in six that is pool all round.
                if (!n && !s && !e && !w && Surrounded(map, c) && Hash(c, 7) < 0.18f)
                {
                    if (here == EI_TerrainDefOf.EI_PoolBasin)
                    {
                        Rect(PoolEdgeMats.Drain, y + 0.001f, c.x + 0.28f, c.z + 0.33f, c.x + 0.72f, c.z + 0.67f, 0);
                    }
                    else if (here == EI_TerrainDefOf.EI_PoolWater)
                    {
                        Rect(PoolEdgeMats.DrainWet, y + 0.001f, c.x + 0.28f, c.z + 0.33f, c.x + 0.72f, c.z + 0.67f, 0);
                    }
                    // Murky and foul water hide the floor altogether.
                }

                // Coping: outer edge of the texture toward the outside.
                float yc = y + 0.002f;
                if (n) Rect(PoolEdgeMats.Coping, yc, x0, z1 - Cope, x1, z1 + Lap, 0);
                if (s) Rect(PoolEdgeMats.Coping, yc, x0, z0 - Lap, x1, z0 + Cope, 2);
                if (e) Rect(PoolEdgeMats.Coping, yc, x1 - Cope, z0, x1 + Lap, z1, 1);
                if (w) Rect(PoolEdgeMats.Coping, yc, x0 - Lap, z0, x0 + Cope, z1, 3);

                // Corners: capped outside where two sides meet, filled inside
                // where the pool turns a corner around something.
                float yk = y + 0.003f;
                if (n && w) Rect(PoolEdgeMats.CornerOuter, yk, x0 - Lap, z1 - Cope, x0 + Cope, z1 + Lap, 0);
                if (n && e) Rect(PoolEdgeMats.CornerOuter, yk, x1 - Cope, z1 - Cope, x1 + Lap, z1 + Lap, 1);
                if (s && e) Rect(PoolEdgeMats.CornerOuter, yk, x1 - Cope, z0 - Lap, x1 + Lap, z0 + Cope, 2);
                if (s && w) Rect(PoolEdgeMats.CornerOuter, yk, x0 - Lap, z0 - Lap, x0 + Cope, z0 + Cope, 3);
                if (!n && !w && !IsPool(map, c + IntVec3.North + IntVec3.West))
                    Rect(PoolEdgeMats.CornerInner, yk, x0, z1 - Cope, x0 + Cope, z1, 0);
                if (!n && !e && !IsPool(map, c + IntVec3.North + IntVec3.East))
                    Rect(PoolEdgeMats.CornerInner, yk, x1 - Cope, z1 - Cope, x1, z1, 1);
                if (!s && !e && !IsPool(map, c + IntVec3.South + IntVec3.East))
                    Rect(PoolEdgeMats.CornerInner, yk, x1 - Cope, z0, x1, z0 + Cope, 2);
                if (!s && !w && !IsPool(map, c + IntVec3.South + IntVec3.West))
                    Rect(PoolEdgeMats.CornerInner, yk, x0, z0, x0 + Cope, z0 + Cope, 3);

                // A ladder at the start of each run of near-side edge three
                // tiles or longer: rails over the coping, rungs into the pool.
                if (s && !n && LadderHere(map, c))
                {
                    Rect(PoolEdgeMats.Ladder, y + 0.004f, c.x + 0.22f, c.z - 0.08f, c.x + 0.78f, c.z + 0.72f, 0);
                }
            }
            FinalizeMesh(MeshParts.All);
        }

        private static bool Surrounded(Map map, IntVec3 c)
        {
            for (int i = 0; i < 8; i++)
            {
                if (!IsPool(map, c + GenAdj.AdjacentCells[i]))
                {
                    return false;
                }
            }
            return true;
        }

        private static bool NearEdge(Map map, IntVec3 c)
        {
            return IsPool(map, c) && !IsPool(map, c + IntVec3.South);
        }

        private static bool LadderHere(Map map, IntVec3 c)
        {
            return !NearEdge(map, c + IntVec3.West)
                   && NearEdge(map, c + IntVec3.East)
                   && NearEdge(map, c + IntVec3.East + IntVec3.East);
        }

        /// <summary>
        /// One textured quad over the world rect, with the texture turned by
        /// quarter turns clockwise so its top (the outer edge, for coping)
        /// faces north (0), east (1), south (2) or west (3).
        /// </summary>
        private void Rect(Material mat, float y, float x0, float z0, float x1, float z1, int turns)
        {
            LayerSubMesh sm = GetSubMesh(mat);
            int start = sm.verts.Count;
            sm.verts.Add(new Vector3(x0, y, z0));
            sm.verts.Add(new Vector3(x0, y, z1));
            sm.verts.Add(new Vector3(x1, y, z1));
            sm.verts.Add(new Vector3(x1, y, z0));
            // Texture corners in the same order (bottom-left, top-left,
            // top-right, bottom-right), rotated to face the chosen side.
            Vector3[] uv = { new Vector3(0f, 0f, 0f), new Vector3(0f, 1f, 0f),
                             new Vector3(1f, 1f, 0f), new Vector3(1f, 0f, 0f) };
            for (int i = 0; i < 4; i++)
            {
                sm.uvs.Add(uv[(i + 4 - (turns & 3)) % 4]);
                sm.colors.Add(new Color32(255, 255, 255, 255));
            }
            sm.tris.Add(start);
            sm.tris.Add(start + 1);
            sm.tris.Add(start + 2);
            sm.tris.Add(start);
            sm.tris.Add(start + 2);
            sm.tris.Add(start + 3);
        }
    }
}
