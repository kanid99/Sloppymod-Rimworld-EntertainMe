using UnityEngine;
using Verse;

namespace EntertainingIdeas
{
    /// <summary>
    /// A strip of textures named "&lt;path&gt;_0" .. "&lt;path&gt;_(count-1)", loaded on
    /// first use and cycled off the game clock. Because the frame comes from
    /// TicksGame, animations hold still while the game is paused and keep pace
    /// with the speed control.
    /// </summary>
    public class FrameSet
    {
        private readonly string path;
        private readonly int count;
        private readonly Vector2 drawSize;
        private readonly Shader shader;
        private Graphic[] graphics;

        /// <param name="shader">
        /// Defaults to lit-from-within, which suits screens and smoke. Pass
        /// ShaderDatabase.Transparent for things that should darken with the
        /// room - a board lying on a table.
        /// </param>
        public FrameSet(string path, int count, Vector2 drawSize, Shader shader = null)
        {
            this.path = path;
            this.count = count;
            this.drawSize = drawSize;
            this.shader = shader;
        }

        public int IndexFor(int ticksPerFrame)
        {
            return Find.TickManager.TicksGame / ticksPerFrame % count;
        }

        public Graphic At(int index)
        {
            if (index < 0 || index >= count)
            {
                return null;
            }
            if (graphics == null)
            {
                graphics = new Graphic[count];
            }
            if (graphics[index] == null)
            {
                graphics[index] = GraphicDatabase.Get<Graphic_Single>(
                    path + "_" + index,
                    shader ?? ShaderDatabase.TransparentPostLight,
                    drawSize,
                    Color.white);
            }
            return graphics[index];
        }
    }
}
