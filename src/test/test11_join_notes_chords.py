import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


#! SAME AS TEST 7, BUT IN THE END IT TESTS THE RECOGNITION OF WHICH NOTE IS FOR EACH CHORD !#


from Blocks.Melody import Melody
from Rythm import Rythm
from Progressions import GeneticProgression, build_harmony
from Melodic import Melodic
from conf import simulated_annealing_phrases_params
from conf import genetic_progression_params


#/ SONG PARAMETERS -------------------------------------------------------------------- #/
key = "A"
scale = "major"
signature = (9, 8)
bars_per_sentence = 6
upbeat = 3
chords_octave = 3
tempo = 150
tuning = 440

#/ MELODY GENERATION -----------------------------------------------------------------. /#

sentence1s = "Hey jude"
sentence1 = ["hey*", " ", "jude*"]
chords_for_s1 = 1

sentence2s = "Don't make it bad"
sentence2 = ["dont*", " ", "make'*", " ", "it'*", " ", "bad*"]
chords_for_s2 = 1

sentence3s = "Take a sad song"
sentence3 = ["take*'", " ", "a*", "sad*", " ", "song*"]
chords_for_s3 = 2

sentence4s = "And make it better"
sentence4 = ["and*", " ", "make'*", " ", "it*", " ", "be*", "tte", "e", "er*"]
chords_for_s4 = 4

sentences = [
    (sentence1s, sentence1),
    (sentence2s, sentence2),
    (sentence3s, sentence3),
    (sentence4s, sentence4)
]

#? RYTHM GENERATION:
#* Rythm object to fit all sentences:
rythm_melody = Rythm(
    signature=signature,
    upbeat=upbeat,
    params=simulated_annealing_phrases_params,
    tuning=tuning
)

#* Melody object to append the rythmic phrases:
melody = Melody(
    signature=signature,
    key_name=key,
    key_type=scale,
    upbeat=upbeat,
    tuning=tuning
)
#* Fit method for each sentence:
for i, (sentence_str, sentence_tokens) in enumerate(sentences):
    phrase = rythm_melody.fit(
        sentence=sentence_tokens,
        bars=bars_per_sentence
    )
    #* Adding the result Phrase objecto to melody:
    melody.add_element(phrase)

#/ CHORDS GENERATION ------------------------------------------------------------------ /#

#? SIMPLE CHORDS GENERATION:
#* Amount of chords:
amount_of_chords_list = [chords_for_s1, chords_for_s2, chords_for_s3, chords_for_s4]

#* Class GeneticProgression to get simple chord progression:
progressions = GeneticProgression(
    params=genetic_progression_params
)

#* Creating n amount of chords for progression:
n_chords = sum(amount_of_chords_list)

#* Returns as list[tuple] in which each tuple has:
#*  - [str] Name of root note on the chord
#*  - [str] Type of the chord
#*  - [str] Degree of the chord on the key
#*  - [int] Inversion (if 0, it is fundamental state)
print("Creating progression...")
progressions = progressions.create(
    chords=n_chords,
    key=key,
    scale=scale
)
print("Progression create :3")

#* Gives rythm to the chords:
harmony = build_harmony(
    chords_per_sentence=amount_of_chords_list,
    chords_durations=[bars_per_sentence] * n_chords,
    chords_progression=progressions,
    params=simulated_annealing_phrases_params,
    signature=signature,
    upbeat=upbeat,
    key=key,
    scale=scale,
    chords_octave=chords_octave,
    tuning=tuning
)

#! TEST MELODIC NOTE AND CHORD JOINNING ------------------------------------------------!#

# Join the notes and chords:
melodic = Melodic(melody, harmony)
mapping, map_chords = melodic.map_note2chords()

print("\nNotes mapping:", mapping)
print("\nChords:")
for chordx in map_chords:
    print(" *", chordx)

# Exports the MIDI to evaluate:
from MIDI import MIDI
midi = MIDI(
    melody=melody,
    harmony=harmony,
    tempo=tempo,
    title="MELODIC test 11"
)
midi.save()

#! -------------------------------------------------------------------------------------!#