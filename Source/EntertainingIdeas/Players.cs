using System.Collections.Generic;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>
    /// Who has been sent to play at something, whether or not they have got
    /// there yet. Counting only the colonists already at their places let
    /// several be sent in the same few ticks - each saw the others still
    /// walking, not playing - so a four-player table sat five.
    /// </summary>
    public static class CommittedPlayers
    {
        /// <summary>Colonists running jobDef on target, apart from `ignore`.</summary>
        public static void Of(Thing target, JobDef jobDef, Pawn ignore, List<Pawn> into)
        {
            into.Clear();
            Map map = target.Map;
            if (map == null || jobDef == null)
            {
                return;
            }
            IReadOnlyList<Pawn> pawns = map.mapPawns.AllPawnsSpawned;
            for (int i = 0; i < pawns.Count; i++)
            {
                Pawn pawn = pawns[i];
                if (pawn == ignore)
                {
                    continue;
                }
                Job job = pawn.CurJob;
                if (job != null && job.def == jobDef && job.targetA.Thing == target)
                {
                    into.Add(pawn);
                }
            }
        }

        private static readonly List<Pawn> scratch = new List<Pawn>();

        public static int Count(Thing target, JobDef jobDef, Pawn ignore)
        {
            Of(target, jobDef, ignore, scratch);
            int count = scratch.Count;
            scratch.Clear();
            return count;
        }
    }
}
