import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


#! STRUCTURE abab' !#
# Phrase A and Phrase B with progression C
# Phrase A and Phrase B variation with progression C


from NLP.Grammar import Grammar
from Blocks.Melody import Melody
from Rythm import Rythm
from Progressions import GeneticProgression, build_harmony
from Melodic import Melodic
from conf import simulated_annealing_phrases_params
from conf import genetic_progression_params


#/ SONG PARAMETERS -------------------------------------------------------------------- #/
key = "G"
scale = "major"
signature = (4, 4)
upbeat = 1
harmony_octave = 2
melody_octave = 4
tempo = 94
tuning = 440

rythm_best_of = 20

#/ ------------------------------------------------------------------------------------ #/


#/ MELODY GENERATION ----------------------------------------------------------------- /#

#? SENTENCES:
grammar = Grammar(random.randint(1, 4))

#! "patterns" will save the indexes for phrases and repetitions as format:
# [
#   0,                  If it is just an integer, it is an original phrase with it's index
#   1,                  Orignal phrase
#   (0, "sentence")     It is a tuple, so it is a repetition (in this case of phrase 0); The type "sentence" says it is a repetition of just the sentence
#   (1, "rythm")        Repetition "Rythm" means a repetition of sentence and rythm. In this case of sentence 1
# ]
#? This means in this case: 2 first phrases are original, the third is a repetition of sentence but not the rythm of the first and the
#? last one is a complete repetition (sentence and rythm) of the second sentence.
patterns = []

bars = []
chords = []
shapes = []

#* Sentence 1:
sentence1s, sentence1 = grammar.generate()
bars.append(2)
chords.append(2)
patterns.append(0)
shapes.append("rise")

#* Sentence 2:
grammar.sentence_type = random.randint(1, 4)
sentence2s, sentence2 = grammar.generate()
bars.append(2)
chords.append(2)
patterns.append(1)
shapes.append("rise")

#* Sentence 3:
#/ SAME SENTENCE AND RYTHM AS 1:
sentence3s, sentence3 = sentence1s, sentence1
bars.append(2)

#! NO MORE CHORDS !#
# chords.append(2)

patterns.append((0, "rythm"))
shapes.append("rise")

#* Sentence 4:
sentence4s, sentence4 = sentence2s, sentence2
bars.append(2)

#! NO MORE CHORDS !#
# chords.append(2)

patterns.append((0, "sentence"))
shapes.append("rise")

sentences = [
    (sentence1s, sentence1),
    (sentence2s, sentence2),
    (sentence3s, sentence3),
    (sentence4s, sentence4)
]

#? RYTHM:
#* Rythm object to fit all sentences:

#* Melody object to append the rythmic phrases:
melody = Melody(
    signature=signature,
    key_name=key,
    key_type=scale,
    upbeat=upbeat,
    tuning=tuning
)
#* Fit method for each sentence:
phrases = []
for i, (sentence_str, sentence_syll) in enumerate(sentences):

    #? If patterns[i] is not a tuple, it is an original phrase;
    #? If patterns[i] is a tuple and it is a sentence repetition;
    #? In this case it will just generate an original rythm:
    if not isinstance(patterns[i], tuple) or patterns[i][1] == "sentence":

        # Create n rythms and takes the best one:
        rythms = []
        for _ in range(rythm_best_of):
            #* Create a rythm candidate:
            rythm_melody = Rythm(
                signature=signature,
                upbeat=upbeat,
                params=simulated_annealing_phrases_params,
                tuning=tuning
            )
            phrase = rythm_melody.fit(
                sentence=sentence_syll,
                bars=bars[i]
            )
            #* Append the rythm candidate to the list:
            rythms.append((phrase, rythm_melody.score))
            # print(f" * Rythm candidate {candidate + 1}/{rythm_best_of} score: {rythm_melody.score}")

        # Gets the better phrase from rythms:
        best_rythm = max(rythms, key=lambda x: x[1])
        phrase = best_rythm[0]
        # print(f" * Best rythm candidate score: {best_rythm[1]}")
        phrases.append(phrase)
    
    #? If patterns[i] is a tuple and it is a rythm repetition;
    #? It recycle the respective phrase:
    elif patterns[i][1] == "rythm":
        phrases.append(phrases[patterns[i][0]])
    
    else:
        raise ValueError("Pattern not recognized on phrases structure")

for phrase in phrases:
    melody.add_element(phrase)

#/ ------------------------------------------------------------------------------------ #/


#/ HARMONY GENERATION ----------------------------------------------------------------- /#

#? SIMPLE CHORDS GENERATION:

#! CONSTRUCT THE FIRST VERSION OF CHORD PROGRESSION !#:

#* Class GeneticProgression to get simple chord progression:
progressions = GeneticProgression(
    params=genetic_progression_params
)

#* Creating n amount of chords for progression:
n_chords = sum(chords)

#* Returns as list[tuple] in which each tuple has:
#*  - [str] Name of root note on the chord
#*  - [str] Type of the chord
#*  - [str] Degree of the chord on the key
#*  - [int] Inversion (if 0, it is fundamental state)

#! FOR PROGRESSION 1 ---------------------------------------------
print("Creating progression 1...")
progressions_1 = progressions.create(
    chords=n_chords,
    key=key,
    scale=scale
)
print("Progression create :3")
#! ---------------------------------------------------------------

#! FOR PROGRESSION 2 ---------------------------------------------
print("Improving progression 1 into progression 2...")
progressions_2 = progressions.create(
    chords=n_chords,
    key=key,
    scale=scale,
    restart=False
)
print("Progression improved :3")
#! ---------------------------------------------------------------


#* Gives rythm to the chords:
#! FOR PROGRESSION 1 ---------------------------------------------
harmony = build_harmony(
    chords_per_sentence=chords,
    chords_durations=bars,
    chords_progression=progressions_1,
    params=simulated_annealing_phrases_params,
    signature=signature,
    upbeat=upbeat,
    key=key,
    scale=scale,
    chords_octave=harmony_octave,
    tuning=tuning,
    best_rythm_of=rythm_best_of
)
#! ---------------------------------------------------------------

#! FOR PROGRESSION 2 ---------------------------------------------

harmony2 = build_harmony(
    chords_per_sentence=chords,
    chords_durations=bars,
    chords_progression=progressions_2,
    params=simulated_annealing_phrases_params,
    signature=signature,
    upbeat=upbeat,
    key=key,
    scale=scale,
    chords_octave=harmony_octave,
    tuning=tuning,
    best_rythm_of=rythm_best_of
)

#! ---------------------------------------------------------------

#! APPEND THE HARMONY 2 CHORDS TO ORIGINAL HARMONY:
anacrusis_passed = False
for chord in harmony2.chords:
    if harmony2.upbeat != 0 and not anacrusis_passed:
        if chord.name == "X":
            pass
        else:
            anacrusis_passed = True
            harmony.add_element(chord)
    else:
        harmony.add_element(chord)


#/ MELODIC GENERATION ------------------------------------------------------------------!#

melodic = Melodic(melody, harmony)
tunned_melody = melodic.tune_melody(shapes, melody_octave, verbose=False)

#/ ------------------------------------------------------------------------------------ #/


#/ MIDI GENERATION -------------------------------------------------------------------- #/

# Logs to understand the structure of the song:
chords.append(chords[0])
chords.append(chords[1])
logs = ""
logs += "SENTENCES:\n"
for i, sentence in enumerate(sentences):
    logs += f"[{i + 1}]: {sentence[0]}\n"
    logs += f"  - {sentence[1]}\n"
    if not isinstance(patterns[i], tuple):
        logs += f"  - [ORIGINAL]\n"
    elif patterns[i][1] == "sentence":
        logs += f"  - [REPETITION OF SENTENCE {patterns[i][0]}]\n"
    elif patterns[i][1] == "rythm":
        logs += f"  - [REPETITION OF RYTHM {patterns[i][0]}]\n"
    logs += f"  - Bars: {bars[i]}\n"
    logs += f"  - Chords: {chords[i]}\n"
    logs += f"  - Shape: {shapes[i]}\n"
    logs += "\n"

# Exports the MIDI to evaluate:
from MIDI import MIDI
midi = MIDI(
    melody=tunned_melody,
    harmony=harmony,
    tempo=tempo,
    title=" ".join(sentence1s.split()[:2]),
    logs=logs
)
midi.save()

#/ -------------------------------------------------------------------------------------!#