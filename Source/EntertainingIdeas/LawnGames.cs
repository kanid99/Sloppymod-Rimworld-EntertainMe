using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// Noughts and crosses, played by throwing bean bags onto a grid pegged
    /// out on the lawn.
    ///
    /// Cornhole's throwing, with a different target: each bag lands in one of
    /// the nine squares rather than somewhere round a hole, two colours stand
    /// in for noughts and crosses, and the grid is cleared after nine throws
    /// for the next game. Flat on the ground, so it reads perfectly from above.
    /// </summary>
    public class CompProperties_NoughtsCrosses : CompProperties_CornholeGame
    {
        /// <summary>Squares a side. The building is this many tiles across.</summary>
        public int gridSize = 3;
        /// <summary>How far a bag may land off the middle of its square, in tiles.</summary>
        public float scatter = 0.14f;

        public CompProperties_NoughtsCrosses()
        {
            compClass = typeof(CompNoughtsCrosses);
        }
    }

    public class CompNoughtsCrosses : CompCornholeGame
    {
        private CompProperties_NoughtsCrosses Grid
        {
            get { return (CompProperties_NoughtsCrosses)props; }
        }

        private int Squares
        {
            get { return Grid.gridSize * Grid.gridSize; }
        }

        /// <summary>
        /// The square a throw lands in. Each game fills the squares in its own
        /// shuffled order, so no square is thrown at twice in one game.
        /// </summary>
        private int SquareFor(int throwIndex)
        {
            int squares = Squares;
            int game = throwIndex / squares;
            int turn = throwIndex % squares;
            int[] order = new int[squares];
            for (int i = 0; i < squares; i++)
            {
                order[i] = i;
            }
            Rand.PushState(parent.thingIDNumber * 131 + game * 7919);
            for (int i = squares - 1; i > 0; i--)
            {
                int j = Rand.RangeInclusive(0, i);
                int swap = order[i];
                order[i] = order[j];
                order[j] = swap;
            }
            Rand.PopState();
            return order[turn];
        }

        protected override Vector3 LandingFor(int throwIndex)
        {
            int size = Grid.gridSize;
            int square = SquareFor(throwIndex);
            float half = (size - 1) / 2f;
            Vector3 spot = parent.DrawPos;
            spot.x += (square % size) - half;
            spot.z += (square / size) - half;
            Rand.PushState(parent.thingIDNumber + throwIndex * 31);
            spot.x += Rand.Range(-Grid.scatter, Grid.scatter);
            spot.z += Rand.Range(-Grid.scatter, Grid.scatter);
            Rand.PopState();
            return spot;
        }

        /// <summary>Only this game's bags are on the grid; it is cleared between games.</summary>
        protected override bool StillLying(int index, int throwIndex)
        {
            return index / Squares == throwIndex / Squares;
        }
    }
}
