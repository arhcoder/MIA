import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from Progressions import GeneticProgression, build_harmony
from conf import genetic_progression_params, simulated_annealing_phrases_params

#? Generates a random progression:
chords_per_sentence = [2, 2, 4, 4]
chords_durations = [1, 1, 1, 1]
progressions = GeneticProgression(
    params=genetic_progression_params
)
chords = progressions.create(
    chords=sum(chords_per_sentence),
    key="G",
    scale="minor"
)
harmony = build_harmony(
    chords_per_sentence=chords_per_sentence,
    chords_durations=chords_durations,
    chords_progression=chords,
    params=simulated_annealing_phrases_params,
    signature=(4, 4),
    upbeat=0,
    key="G",
    scale="minor",
    chords_octave=3
)

#? See the chords notes:
for chord in harmony.chords:
    print(f"\n{chord.name}{chord.ctype}:\tInversion:{chord.inversion}\tOctave:{chord.octave}:")
    for note in chord.notes:
        print(f"\t- {note.note}{note.octave}")