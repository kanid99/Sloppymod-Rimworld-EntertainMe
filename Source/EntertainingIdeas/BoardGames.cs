using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace EntertainingIdeas
{
    /// <summary>One game in the cupboard, and the board drawn for it.</summary>
    public class BoardGameEntry
    {
        public string label;
        /// <summary>Board textures "&lt;framePath&gt;_0" .. "_(frameCount-1)", cycled as moves are made.</summary>
        public string framePath;
        public int frameCount = 3;
    }

    /// <summary>
    /// A table with a cupboard of games.
    ///
    /// Whoever sits down first picks a game - never the one that was played
    /// last - and anyone who joins plays that. The board is drawn over the
    /// table while it is being played, so a glance says which game is on, and
    /// it is packed away when the last player gets up.
    /// </summary>
    public class CompProperties_BoardGame : CompProperties
    {
        public List<BoardGameEntry> games = new List<BoardGameEntry>();
        /// <summary>Shown when nobody is playing: the boxes, stacked.</summary>
        public string idleTexPath;
        public int maxPlayers = 4;
        /// <summary>False lets players sit on the ground beside it, for a tribe's first boards.</summary>
        public bool requireChair = true;
        /// <summary>Ticks between the board changing - roughly, a move.</summary>
        public int ticksPerFrame = 300;
        public Vector2 drawSize = new Vector2(2f, 2f);
        public float altitudeOffset = 0.03f;

        public CompProperties_BoardGame()
        {
            compClass = typeof(CompBoardGame);
        }

        public override IEnumerable<string> ConfigErrors(ThingDef parentDef)
        {
            foreach (string error in base.ConfigErrors(parentDef))
            {
                yield return error;
            }
            if (games == null || games.Count == 0)
            {
                yield return "CompProperties_BoardGame needs at least one game.";
            }
            if (maxPlayers < 1)
            {
                yield return "CompProperties_BoardGame needs maxPlayers >= 1.";
            }
        }
    }

    public class CompBoardGame : ThingComp
    {
        private int current = -1;
        private int last = -1;
        private FrameSet[] boards;
        private Graphic idle;
        private int nextTidyTick;
        private static readonly List<Pawn> tmpPlayers = new List<Pawn>();

        public CompProperties_BoardGame Props
        {
            get { return (CompProperties_BoardGame)props; }
        }

        public BoardGameEntry Current
        {
            get { return current >= 0 && current < Props.games.Count ? Props.games[current] : null; }
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Values.Look(ref current, "EI_boardGame", -1);
            Scribe_Values.Look(ref last, "EI_boardGameLast", -1);
        }

        /// <summary>Everyone sitting at this table playing it, into a list the caller owns.</summary>
        public void Players(List<Pawn> into, Pawn ignore = null)
        {
            into.Clear();
            if (!parent.Spawned)
            {
                return;
            }
            foreach (IntVec3 cell in GenAdj.CellsAdjacentCardinal(parent))
            {
                if (!cell.InBounds(parent.Map))
                {
                    continue;
                }
                List<Thing> things = cell.GetThingList(parent.Map);
                for (int i = 0; i < things.Count; i++)
                {
                    Pawn pawn = things[i] as Pawn;
                    if (pawn == null || pawn == ignore || into.Contains(pawn))
                    {
                        continue;
                    }
                    if (pawn.jobs != null && pawn.jobs.curDriver is JobDriver_PlayBoardGame
                        && pawn.CurJob.targetA.Thing == parent)
                    {
                        into.Add(pawn);
                    }
                }
            }
        }

        public int PlayerCount(Pawn ignore = null)
        {
            Players(tmpPlayers, ignore);
            int count = tmpPlayers.Count;
            tmpPlayers.Clear();
            return count;
        }

        /// <summary>A player sits down. The first one picks the game.</summary>
        public void Join(Pawn pawn)
        {
            if (current >= 0)
            {
                return;
            }
            int count = Props.games.Count;
            if (count == 1)
            {
                current = 0;
                return;
            }
            // Anything but what was played last, so an evening at the table is
            // not the same game over and over.
            int pick = Rand.Range(0, count - (last >= 0 ? 1 : 0));
            if (last >= 0 && pick >= last)
            {
                pick++;
            }
            current = pick;
        }

        /// <summary>A player gets up. The last one out packs the game away.</summary>
        public void Leave(Pawn pawn)
        {
            if (current >= 0 && PlayerCount(pawn) == 0)
            {
                last = current;
                current = -1;
            }
        }

        public override void PostDraw()
        {
            base.PostDraw();
            if (!parent.Spawned)
            {
                return;
            }

            // A game left out by a save made mid-session, or a player who was
            // drafted away without the job finishing cleanly: tidy it up.
            int now = Find.TickManager.TicksGame;
            if (current >= 0 && now >= nextTidyTick)
            {
                nextTidyTick = now + 250;
                if (PlayerCount() == 0)
                {
                    last = current;
                    current = -1;
                }
            }

            Graphic graphic = null;
            if (current >= 0)
            {
                if (boards == null)
                {
                    boards = new FrameSet[Props.games.Count];
                }
                if (boards[current] == null)
                {
                    BoardGameEntry game = Props.games[current];
                    boards[current] = new FrameSet(game.framePath, game.frameCount, Props.drawSize, ShaderDatabase.Transparent);
                }
                graphic = boards[current].At(boards[current].IndexFor(Props.ticksPerFrame));
            }
            else if (!Props.idleTexPath.NullOrEmpty())
            {
                if (idle == null)
                {
                    idle = GraphicDatabase.Get<Graphic_Single>(Props.idleTexPath, ShaderDatabase.Transparent,
                                                               Props.drawSize, Color.white);
                }
                graphic = idle;
            }
            if (graphic == null)
            {
                return;
            }
            Vector3 at = parent.DrawPos;
            at.y += Props.altitudeOffset;
            // The table stays upright (drawRotated false); what is on it turns
            // with the facing, drawn as it is when the table faces south.
            graphic.Draw(at, Rot4.North, parent, 180f - parent.Rotation.AsAngle);
        }

        public override string CompInspectStringExtra()
        {
            if (!parent.Spawned)
            {
                return null;
            }
            BoardGameEntry game = Current;
            if (game == null)
            {
                return Props.games.Count == 1
                    ? "Nobody playing " + Props.games[0].label + "."
                    : Props.games.Count + " games in the cupboard. Nobody playing.";
            }
            int players = PlayerCount();
            return "Playing " + game.label + " (" + players + (players == 1 ? " player)" : " players)");
        }
    }

    /// <summary>
    /// Sends a colonist to a table with a free chair and room in the game.
    /// Only the chair is claimed, as at the jigsaw table, so several can play.
    /// </summary>
    public class JoyGiver_BoardGame : JoyGiver
    {
        public override Job TryGiveJob(Pawn pawn)
        {
            if (def.thingDefs == null || pawn.Map == null)
            {
                return null;
            }
            for (int i = 0; i < def.thingDefs.Count; i++)
            {
                IntVec3 seat = IntVec3.Invalid;
                Thing table = GenClosest.ClosestThingReachable(
                    pawn.Position,
                    pawn.Map,
                    ThingRequest.ForDef(def.thingDefs[i]),
                    PathEndMode.Touch,
                    TraverseParms.For(pawn),
                    40f,
                    t => Usable(pawn, t, def.jobDef)
                         && JoyGiver_Jigsaw.TryFindSeat(pawn, t, RequiresChair(t), out seat));
                if (table != null && seat.IsValid)
                {
                    return JobMaker.MakeJob(def.jobDef, table, seat);
                }
            }
            return null;
        }

        private static bool RequiresChair(Thing table)
        {
            CompBoardGame game = table.TryGetComp<CompBoardGame>();
            return game == null || game.Props.requireChair;
        }

        private static bool Usable(Pawn pawn, Thing table, JobDef jobDef)
        {
            if (table.IsForbidden(pawn) || table.IsBurning() || !table.IsSociallyProper(pawn))
            {
                return false;
            }
            CompBoardGame game = table.TryGetComp<CompBoardGame>();
            if (game == null)
            {
                return false;
            }
            // Seated players, or everyone already sent here if more: the
            // ones still walking to a chair count too.
            int players = System.Math.Max(game.PlayerCount(pawn), CommittedPlayers.Count(table, jobDef, pawn));
            return players < game.Props.maxPlayers;
        }
    }

    public class JobDriver_PlayBoardGame : JobDriver
    {
        /// <summary>
        /// The "played a game" tale this job's def records on completion is a
        /// pawn-and-thing tale: the base driver passes only the pawn, and the
        /// game logs an error building it. Name the table too, as vanilla's
        /// game drivers do.
        /// </summary>
        public override object[] TaleParameters()
        {
            Thing played = job.GetTarget(TargetIndex.A).Thing;
            return new object[] { pawn, played != null ? played.def : (Def)job.def };
        }

        private Thing Table
        {
            get { return job.GetTarget(TargetIndex.A).Thing; }
        }

        private CompBoardGame Game
        {
            get { return Table == null ? null : Table.TryGetComp<CompBoardGame>(); }
        }

        public override bool TryMakePreToilReservations(bool errorOnFailed)
        {
            return pawn.ReserveSittableOrSpot(job.targetB.Cell, job, errorOnFailed);
        }

        public override string GetReport()
        {
            CompBoardGame game = Game;
            BoardGameEntry current = game == null ? null : game.Current;
            return current == null ? base.GetReport() : "playing " + current.label + ".";
        }

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.EndOnDespawnedOrNull(TargetIndex.A);
            this.FailOnForbidden(TargetIndex.A);

            yield return Toils_Goto.GotoCell(TargetIndex.B, PathEndMode.OnCell);

            Toil play = ToilMaker.MakeToil("EI_PlayBoardGame");
            play.initAction = delegate
            {
                CompBoardGame game = Game;
                if (game != null)
                {
                    game.Join(pawn);
                }
            };
            play.AddFinishAction(delegate
            {
                CompBoardGame game = Game;
                if (game != null)
                {
                    game.Leave(pawn);
                }
            });
            play.defaultCompleteMode = ToilCompleteMode.Delay;
            play.defaultDuration = job.def.joyDuration;
            play.handlingFacing = true;
            play.socialMode = RandomSocialMode.Normal;
#if RW16
            play.tickIntervalAction = delegate(int delta)
            {
                pawn.rotationTracker.FaceTarget(Table);
                JoyUtility.JoyTickCheckEnd(pawn, delta, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#else
            play.tickAction = delegate
            {
                pawn.rotationTracker.FaceTarget(Table);
                JoyUtility.JoyTickCheckEnd(pawn, JoyTickFullJoyAction.EndJob, 1f, Table as Building);
            };
#endif
            yield return play;
        }
    }
}
