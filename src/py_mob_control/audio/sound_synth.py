"""Procedural sound synthesis using NumPy and Pygame mixer.

Generates 100% self-contained organic SFX without requiring any external audio files.
"""

from typing import Optional
import numpy as np
import pygame

SAMPLE_RATE = 44100


def _to_stereo_sound(samples: np.ndarray) -> Optional[pygame.mixer.Sound]:
    """Convert a 1D float32 numpy array [-1.0, 1.0] to a stereo 16-bit pygame.mixer.Sound."""
    if not pygame.mixer.get_init():
        return None
    try:
        # Clip to prevent distortion
        clipped = np.clip(samples, -1.0, 1.0)
        pcm16 = (clipped * 32767).astype(np.int16)
        # Duplicate for stereo (L, R) interleaved
        stereo = np.column_stack((pcm16, pcm16)).ravel()
        return pygame.mixer.Sound(buffer=stereo.tobytes())
    except Exception:
        return None


def synth_mob_pop(freq_start: float = 480.0, freq_end: float = 160.0, duration: float = 0.07) -> Optional[pygame.mixer.Sound]:
    """Generates a snappy bubble/pop sound when a mob is fired."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(freq_start, freq_end, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = np.exp(-t * 55.0)
    samples = np.sin(phase) * envelope * 0.4
    return _to_stereo_sound(samples)


def synth_gate_chime(frequency: float = 440.0, duration: float = 0.22) -> Optional[pygame.mixer.Sound]:
    """Generates a luminous bell/chime sound for multiplier gates."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    envelope = np.exp(-t * 14.0)
    # Fundamental + shimmering harmonics
    tone = (
        0.6 * np.sin(2 * np.pi * frequency * t)
        + 0.3 * np.sin(2 * np.pi * frequency * 2.0 * t)
        + 0.15 * np.sin(2 * np.pi * frequency * 3.01 * t)
    )
    samples = tone * envelope * 0.35
    return _to_stereo_sound(samples)


def synth_mob_clash(duration: float = 0.05) -> Optional[pygame.mixer.Sound]:
    """Soft cartoon pop when friendly and enemy mobs cancel each other out."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(350.0, 90.0, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    noise = np.random.uniform(-0.15, 0.15, len(t))
    envelope = np.exp(-t * 70.0)
    samples = (np.sin(phase) + noise) * envelope * 0.25
    return _to_stereo_sound(samples)


def synth_champion_summon(duration: float = 0.45) -> Optional[pygame.mixer.Sound]:
    """Dramatic brass/bass chord when a champion is summoned."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    envelope = np.minimum(t * 20.0, 1.0) * np.exp(-t * 5.0)
    # Power chord: Root (110Hz), Fifth (165Hz), Octave (220Hz)
    chord = (
        0.5 * np.sin(2 * np.pi * 110.0 * t)
        + 0.3 * np.sin(2 * np.pi * 165.0 * t)
        + 0.25 * np.sin(2 * np.pi * 220.0 * t)
    )
    samples = chord * envelope * 0.55
    return _to_stereo_sound(samples)


def synth_champion_stomp(duration: float = 0.2) -> Optional[pygame.mixer.Sound]:
    """Sub-bass thud when a champion crushes an obstacle or enemy group."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(120.0, 35.0, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = np.exp(-t * 22.0)
    samples = np.sin(phase) * envelope * 0.6
    return _to_stereo_sound(samples)


def synth_brick_chip(duration: float = 0.08) -> Optional[pygame.mixer.Sound]:
    """Crisp crunch/chip sound when mobs break bricks off enemy buildings."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    noise = np.random.uniform(-0.5, 0.5, len(t))
    tone = 0.4 * np.sin(2 * np.pi * 880.0 * t)
    envelope = np.exp(-t * 60.0)
    samples = (tone + noise) * envelope * 0.35
    return _to_stereo_sound(samples)


def synth_coin(duration: float = 0.15) -> Optional[pygame.mixer.Sound]:
    """High bright pickup chime."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    half = len(t) // 2
    f1 = 987.77   # B5
    f2 = 1318.51  # E6
    freq = np.concatenate([np.full(half, f1), np.full(len(t) - half, f2)])
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = np.exp(-t * 18.0)
    samples = np.sin(phase) * envelope * 0.3
    return _to_stereo_sound(samples)


def synth_win_fanfare(duration: float = 0.8) -> Optional[pygame.mixer.Sound]:
    """Triumphant ascending arpeggio upon level victory."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    samples = np.zeros_like(t)
    step_len = len(t) // len(notes)
    for i, freq in enumerate(notes):
        start = i * step_len
        end = start + step_len if i < len(notes) - 1 else len(t)
        sub_t = t[start:end] - t[start]
        env = np.exp(-sub_t * 6.0)
        samples[start:end] = (
            np.sin(2 * np.pi * freq * sub_t)
            + 0.3 * np.sin(2 * np.pi * freq * 2.0 * sub_t)
        ) * env * 0.45
    return _to_stereo_sound(samples)


def synth_game_over(duration: float = 0.6) -> Optional[pygame.mixer.Sound]:
    """Downward sad slide upon defeat."""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(340.0, 110.0, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = np.exp(-t * 5.0)
    samples = np.sin(phase) * envelope * 0.4
    return _to_stereo_sound(samples)
