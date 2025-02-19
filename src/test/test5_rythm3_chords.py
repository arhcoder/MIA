import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Rythm import Rythm
from Data.rythm.times import TIMES
from conf import simulated_annealing_phrases_params


#! USING TO GET CHORDS RYTHM !#

# Sentences in english and chords:
sentence1s = "Find my self in times of trubles"
sentence1 = ["X", "X"]

sentence2s = "Mother marry comes to me"
sentence2 = ["X", "X", "X"]

sentence3s = "Speaking words of wisdom"
sentence3 = ["X", "X"]

sentence4s = "Let it be"
sentence4 = ["X", "X", "X", "X"]

sentences = [
    (sentence1s, sentence1),
    (sentence2s, sentence2),
    (sentence3s, sentence3),
    (sentence4s, sentence4)
]
signature = (4, 4)
bars_per_sentence = 2
upbeat = 0

rythm_instance = Rythm(signature=signature, upbeat=upbeat, params=simulated_annealing_phrases_params, for_chords=True)
for i, (sentence_str, sentence_tokens) in enumerate(sentences):

    rythm_results = rythm_instance.fit(sentence_tokens, bars=bars_per_sentence)
    initial_rest, syllable_figures, final_rest, extra_silences, dots = rythm_results

    processed_syllables = rythm_instance.preprocess_syllables(sentence_tokens)
    
    full_notes = [initial_rest] + syllable_figures + [final_rest]
    full_syllables = ["(rest)"] + processed_syllables + ["(rest)"]
    full_dots = dots

    print(f"\nSentence {i+1}:")
    print(f"\n * {sentence_str}")
    print()
    for j in range(len(full_notes)):
        note_val = full_notes[j]
        dot_flag = full_dots[j]
        label = full_syllables[j]
        note_id_str = f"{note_val}•" if dot_flag else f"{note_val}"
        note_name_str = f"{TIMES.get(note_val, 'x')[0]}•" if dot_flag else TIMES.get(note_val, 'x')[0]
        print(f"    - {label}\t{note_id_str}\t{note_name_str}")