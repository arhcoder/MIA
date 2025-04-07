import os
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from NLP.Grammar import Grammar
from Blocks.Melody import Melody
from Rythm import Rythm
from Progressions import GeneticProgression, build_harmony
from Melodic import Melodic
from conf import simulated_annealing_phrases_params
from conf import genetic_progression_params


#/ SONG PARAMETERS -------------------------------------------------------------------- #/
key = "A"
scale = "major"
signature = (4, 4)
upbeat = 0
harmony_octave = 3
melody_octave = 4
tempo = 110
tuning = 440

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

#* Sentence 1:
sentence1s, sentence1 = grammar.generate()
bars.append(2)
chords.append(1)
patterns.append(0)

#* Sentence 2:
grammar.sentence_type = random.randint(1, 4)
sentence2s, sentence2 = grammar.generate()
bars.append(2)
chords.append(1)
patterns.append(1)

#* Sentence 3:
#/ SAME SENTENCE AND RYTHM AS 1:
sentence3s, sentence3 = sentence1s, sentence1
bars.append(2)
chords.append(1)
patterns.append((0, "sentence"))

#* Sentence 4:
#/ SAME SENTENCE AS 2, BUT DIFFERENT RYTHM:
sentence4s, sentence4 = sentence2s, sentence2
bars.append(2)
chords.append(2)
patterns.append((1, "rythm"))

sentences = [
    (sentence1s, sentence1),
    (sentence2s, sentence2),
    (sentence3s, sentence3),
    (sentence4s, sentence4)
]

#? RYTHM:
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
phrases = []
for i, (sentence_str, sentence_syll) in enumerate(sentences):

    #? If patterns[i] is not a tuple, it is an original phrase;
    #? If patterns[i] is a tuple and it is a sentence repetition;
    #? In this case it will just generate an original rythm:
    if not isinstance(patterns[i], tuple) or patterns[i][1] == "sentence":
        phrase = rythm_melody.fit(
            sentence=sentence_syll,
            bars=bars[i]
        )
        phrases.append(phrase)
    
    #? If patterns[i] is a tuple and it is a rythm repetition;
    #? It recycle the respective phrase:
    elif patterns[i][1] == "rythm":
        phrases.append(phrases[patterns[i][0]])
    
    else:
        print("WARNING: Pattern not recognized on phrases structure")
        # Creates an original phrase for avoid errors:
        phrase = rythm_melody.fit(
            sentence=sentence_syll,
            bars=bars[i]
        )
        phrases.append(phrase)

for phrase in phrases:
    melody.add_element(phrase)

#/ ------------------------------------------------------------------------------------ #/


#/ HARMONY GENERATION ----------------------------------------------------------------- /#

#? SIMPLE CHORDS GENERATION:
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
print("Creating progression...")
progressions = progressions.create(
    chords=n_chords,
    key=key,
    scale=scale
)
print("Progression create :3")

#* Gives rythm to the chords:
harmony = build_harmony(
    chords_per_sentence=chords,
    chords_durations=bars,
    chords_progression=progressions,
    params=simulated_annealing_phrases_params,
    signature=signature,
    upbeat=upbeat,
    key=key,
    scale=scale,
    chords_octave=harmony_octave,
    tuning=tuning
)


#/ MELODIC GENERATION ------------------------------------------------------------------!#

melodic = Melodic(melody, harmony)
tunned_melody = melodic.tune_melody(melody_octave, verbose=True)

#/ ------------------------------------------------------------------------------------ #/


#/ MIDI GENERATION -------------------------------------------------------------------- #/

# Logs to understand the structure of the song:
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