import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



#! SAME AS TEST 7, BUT IN THE END THE GENERATION OF MIDI FOR CHORDS VOICE LEADING VERIFICATION !#



#/ INTEGRATION ---------------------------------------------------------------------- #/
print(f"{'* Importing engines':<40}", end="")
from Blocks.Melody import Melody

from Rythm import Rythm
from Progressions import GeneticProgression, build_harmony

from conf import simulated_annealing_phrases_params
from conf import genetic_progression_params
print("✅")



#/ SONG PARAMETERS -------------------------------------------------------------------- #/
key = "A"
scale = "major"
signature = (4, 4)
bars_per_sentence = 1
upbeat = 0
chords_octave = 3
tempo = 100


#/ MELODY GENERATION -----------------------------------------------------------------. /#
print("\nMELODY GENERATION")

#? LIST OF SENTENCES:
print(f"{'* Generating sentences':<40}", end="")
sentence1s = "Hey jude"
sentence1 = ["hey*", " ", "jude*"]
chords_for_s1 = 4

sentence2s = "Don't make it bad"
sentence2 = ["dont*", " ", "make'*", " ", "it'*", " ", "bad*"]
chords_for_s2 = 4

sentence3s = "Take a sad song"
sentence3 = ["take*'", " ", "a*", "sad*", " ", "song*"]
chords_for_s3 = 4

sentence4s = "And make it better"
sentence4 = ["and*", " ", "make'*", " ", "it*", " ", "be*", "tte", "e", "er*"]
chords_for_s4 = 4

sentences = [
    (sentence1s, sentence1),
    (sentence2s, sentence2),
    (sentence3s, sentence3),
    (sentence4s, sentence4)
]
print("✅")

#? RYTHM GENERATION:
#* Rythm object to fit all sentences:
print(f"{'* Generating Rythms':<40}", end="")
rythm_melody = Rythm(
    signature=signature,
    upbeat=upbeat,
    params=simulated_annealing_phrases_params
)
print("✅")

#* Melody object to append the rythmic phrases:
print(f"{'* Fitting sentences into rythm phrases':<40}", end="")
melody = Melody(
    signature=signature,
    key_name=key,
    key_type=scale,
    upbeat=upbeat
)
#* Fit method for each sentence:
for i, (sentence_str, sentence_tokens) in enumerate(sentences):
    phrase = rythm_melody.fit(
        sentence=sentence_tokens,
        bars=bars_per_sentence
    )
    #* Adding the result Phrase objecto to melody:
    melody.add_element(phrase)
print("✅")



#/ CHORDS GENERATION ------------------------------------------------------------------ /#
print("\nCHORDS PROGRESSION GENERATION")

#? SIMPLE CHORDS GENERATION:
#* Amount of chords:
amount_of_chords_list = [chords_for_s1, chords_for_s2, chords_for_s3, chords_for_s4]

#* Class GeneticProgression to get simple chord progression:
print(f"{'* Creating Genetics':<40}", end="")
progressions = GeneticProgression(
    params=genetic_progression_params
)
print("✅")

#* Creating n amount of chords for progression:
n_chords = sum(amount_of_chords_list)

#* Returns as list[tuple] in which each tuple has:
#*  - [str] Name of root note on the chord
#*  - [str] Type of the chord
#*  - [str] Degree of the chord on the key
#*  - [int] Inversion (if 0, it is fundamental state)
print(f"{'* Generating Progressios':<40}", end="")
progressions = progressions.create(
    chords=n_chords,
    key=key,
    scale=scale
)
print("✅")

#* Gives rythm to the chords:
print(f"{'* Generating Rythms':<40}", end="")
harmony = build_harmony(
    chords_per_sentence=amount_of_chords_list,
    chords_durations=[bars_per_sentence] * n_chords,
    chords_progression=progressions,
    params=simulated_annealing_phrases_params,
    signature=signature,
    upbeat=upbeat,
    key=key,
    scale=scale,
    chords_octave=chords_octave
)
print("✅")



#! MIDI RESULTS -----------------------------------------------------------------------!#

from MIDI import MIDI
midi = MIDI(
    melody=melody,
    harmony=harmony,
    tempo=tempo,
    title="HEY TEST8"
)
midi.save()

#! -------------------------------------------------------------------------------------!#