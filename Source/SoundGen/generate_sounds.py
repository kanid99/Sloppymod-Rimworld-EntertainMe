#!/usr/bin/env python3
"""Synthesises the mod's sound effects, the way generate_textures.py draws its art.

Only for things whose real sound is synthetic anyway - arcade cabinets bleeped
because they were built from oscillators - so a generated sound is the
authentic one rather than a stand-in. Anything organic (a bag landing, water,
a voice) wants either one of vanilla's own sounds or a recording instead.

Standard library only: square and triangle oscillators, a noise source, and a
short fade at each end of every sound so none of them clicks. Every file is
checked after it is written - peak level, DC offset, and that it starts and
ends at silence - and the script fails if any check does.

Usage: python3 Source/SoundGen/generate_sounds.py
"""

import math
import os
import random
import struct
import sys
import wave

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Sounds", "EntertainingIdeas", "Arcade")
RATE = 22050                 # plenty for chip sounds, and half the file size
PEAK = 0.6                   # normalise to about -4.4 dBFS: loud enough, never clips


# --- oscillators ------------------------------------------------------------

def square(phase, duty=0.5):
    return 1.0 if (phase % 1.0) < duty else -1.0


def triangle(phase):
    p = phase % 1.0
    return 4.0 * p - 1.0 if p < 0.5 else 3.0 - 4.0 * p


def tone(freq_at, seconds, wave_fn, duty=0.5):
    """A tone whose frequency may change over time: freq_at(t) in Hz."""
    out, phase = [], 0.0
    for i in range(int(seconds * RATE)):
        t = i / float(RATE)
        phase += freq_at(t) / RATE
        out.append(wave_fn(phase, duty) if wave_fn is square else wave_fn(phase))
    # A pulse narrower than half sits off-centre. Centre each tone here, before
    # its fades go on: correcting the whole file afterwards moves the silence
    # at either end off zero, and the sound clicks every time it plays.
    mean = sum(out) / float(len(out) or 1)
    return [v - mean for v in out]


def envelope(samples, attack=0.002, release=0.02, decay=None):
    """Fade in and out so nothing clicks; optionally decay exponentially."""
    n = len(samples)
    a, r = int(attack * RATE), int(release * RATE)
    out = []
    for i, s in enumerate(samples):
        g = 1.0
        if i < a:
            g *= i / float(max(1, a))
        if i > n - r:
            g *= max(0.0, (n - i) / float(max(1, r)))
        if decay:
            g *= math.exp(-i / float(RATE) / decay)
        out.append(s * g)
    return out


def join(*parts, gap=0.0):
    out = []
    for k, p in enumerate(parts):
        out.extend(p)
        if gap and k < len(parts) - 1:
            out.extend([0.0] * int(gap * RATE))
    return out


def lowpass(samples, cutoff):
    """One-pole low-pass, to take the fizz off noise."""
    k = 1.0 - math.exp(-2 * math.pi * cutoff / RATE)
    out, y = [], 0.0
    for s in samples:
        y += k * (s - y)
        out.append(y)
    return out


def mix(a, b, gb=1.0):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0.0) + gb * (b[i] if i < len(b) else 0.0) for i in range(n)]


def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


# --- the sounds ---------------------------------------------------------------

def ore_rush_dig():
    """Two quick steps down: the miner's pick taking a piece of ore."""
    a = envelope(tone(lambda t: 760.0, 0.032, square, 0.25), release=0.006)
    b = envelope(tone(lambda t: 570.0, 0.034, square, 0.25), release=0.012)
    return join(a, b)


def ore_rush_seam():
    """A rising arpeggio: a rich seam cleared."""
    notes = [note(n) for n in (76, 79, 83, 88)]           # E5 G5 B5 E6
    parts = [envelope(tone(lambda t, f=f: f, 0.05, square, 0.5), release=0.01) for f in notes[:-1]]
    parts.append(envelope(tone(lambda t: notes[-1], 0.16, square, 0.5), release=0.1, decay=0.12))
    return join(*parts)


def thrumbo_jump():
    """A springy upward sweep: the player hopping."""
    f0, f1, d = 330.0, 900.0, 0.12
    return envelope(tone(lambda t: f0 * (f1 / f0) ** (t / d), d, square, 0.5), release=0.03)


def thrumbo_roll():
    """A low rolling rumble: a rock set off down the girders."""
    d = 0.3
    rng = random.Random(7)
    body = tone(lambda t: 72.0 - 18.0 * t / d, d, triangle)
    noise = lowpass([rng.uniform(-1, 1) for _ in range(int(d * RATE))], 420.0)
    rolled = [s * (0.65 + 0.35 * math.sin(2 * math.pi * 13.0 * i / RATE))
              for i, s in enumerate(mix(body, noise, 1.6))]
    return envelope(rolled, attack=0.01, release=0.08)


def arcade_attract():
    """Four soft notes: the cabinet reminding the room it is switched on."""
    notes = [note(n) for n in (72, 76, 79, 84)]           # C5 E5 G5 C6
    parts = [envelope(tone(lambda t, f=f: f, 0.085, triangle), release=0.02) for f in notes[:-1]]
    parts.append(envelope(tone(lambda t: notes[-1], 0.22, triangle), release=0.12, decay=0.2))
    return join(*parts, gap=0.012)


def infest_shot():
    """INFESTATION!: the mini-turret's shot - a quick falling zap."""
    f0, f1, d = 1500.0, 420.0, 0.09
    return envelope(tone(lambda t: f0 * (f1 / f0) ** (t / d), d, square, 0.3), release=0.03)


def infest_splat():
    """INFESTATION!: a bug popping - a wet burst over a low drop."""
    d = 0.2
    rng = random.Random(11)
    body = tone(lambda t: 220.0 * (70.0 / 220.0) ** (t / d), d, triangle)
    noise = lowpass([rng.uniform(-1, 1) for _ in range(int(d * RATE))], 1400.0)
    squelch = [s * (1.0 - i / float(len(noise))) ** 2 for i, s in enumerate(noise)]
    return envelope(mix(body, squelch, 1.3), attack=0.002, release=0.07)


SOUNDS = {
    "OreRushDig": ore_rush_dig,
    "OreRushSeam": ore_rush_seam,
    "ThrumboJump": thrumbo_jump,
    "ThrumboRoll": thrumbo_roll,
    "ArcadeAttract": arcade_attract,
    "InfestShot": infest_shot,
    "InfestSplat": infest_splat,
}


# --- writing and checking -------------------------------------------------------

def normalise(samples):
    """Scale to the target peak. Scaling only: every tone is already centred."""
    peak = max(abs(s) for s in samples) or 1.0
    return [s * PEAK / peak for s in samples]


def write(name, samples):
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(round(s * 32767))) for s in samples))
    return path


def check(path):
    """Read the file back and prove it is sound to ship."""
    problems = []
    with wave.open(path, "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, RATE):
            problems.append("unexpected format")
        raw = w.readframes(w.getnframes())
    s = [v / 32767.0 for v in struct.unpack("<%dh" % (len(raw) // 2), raw)]
    peak = max(abs(v) for v in s)
    dc = sum(s) / len(s)
    edge = max(abs(s[0]), abs(s[-1]))
    if peak > 0.95:
        problems.append("clips (peak %.2f)" % peak)
    if abs(dc) > 0.01:
        problems.append("DC offset %.3f" % dc)
    if edge > 0.02:
        problems.append("does not start and end at silence (%.3f) - it will click" % edge)
    rms = math.sqrt(sum(v * v for v in s) / len(s))
    return problems, len(s) / float(RATE), peak, rms


def main():
    os.makedirs(OUT, exist_ok=True)
    failed = False
    for name, make in SOUNDS.items():
        path = write(name, normalise(make()))
        problems, seconds, peak, rms = check(path)
        status = "ok" if not problems else "FAILED: " + "; ".join(problems)
        failed |= bool(problems)
        print("  %-14s %5.0f ms  peak %.2f  rms %.2f  %s"
              % (name + ".wav", seconds * 1000, peak, rms, status))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
