import os
import re
import math
import datetime
from midiutil import MIDIFile # type: ignore
from midiutil.MidiFile import SHARPS, FLATS, MAJOR, MINOR # type: ignore

from Blocks.Melody import Melody
from Blocks.Harmony import Harmony
from Data.key.scales import diatonics, major_key_signatures, minor_key_signatures


class MIDI:

    #? CONSTRUCTOR:
    def __init__(self, melody: Melody, harmony: Harmony, tempo: int, title: str = "Untitled", logs: str = "No logs."):
        """
            To convert a song in melody/harmony MIA classes notation into a MIDI file

            Parameters:
                - melody [Melody]: Instance of Melody (with attributes such as .phrases, .signature, .upbeat, .key)
                - harmony [Harmony]: Instance of Harmony (with attributes such as .chords, .signature, .upbeat)
                - tempo [int]: Tempo in BPM
                - title [str]: Title for the song
                - logs [str]: Texto to add into the txt to understand the structure of the piece
            
            Methods:
                - save (directory [str]): Receives a directory path and saves the song as MIDI file and a TXT
                  with song printing representation of melody and harmony data
        """
        self.melody = melody
        self.harmony = harmony
        self.tempo = tempo
        self.title = title
        self.logs = logs
    
    #? SAVE:
    def save(self, directory="songs/"):

        #* If directory exists:
        if not os.path.exists(directory):
            os.makedirs(directory)
        

        #? File attributes:
        # Build a clean file name based on title: replace spaces with "_" and remove special characters:
        replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "ñ": "n", "Ñ": "n", "ü": "u", "Ü": "u"}
        base_title = self.title
        for old, new in replacements.items():
            base_title = base_title.replace(old, new)
        base_title = re.sub(r"[^A-Za-z0-9 ]+", "", base_title)
        file_title = base_title.replace(" ", "_")
        

        filename = os.path.join(directory, f"{file_title}.mid")
        counter = 1
        while os.path.exists(filename):
            filename = os.path.join(directory, f"{file_title}_{counter}.mid")
            counter += 1
        

        #? MIDI Object:
        #* Tracks:
        # Track 0: Melody, Track 1: Harmony:
        midi = MIDIFile(2)

        #* Tuning:
        # Note 69 is A4:
        midi.changeNoteTuning(0, [(69, self.melody.tuning)])
        midi.changeNoteTuning(1, [(69, self.harmony.tuning)])

        #* Tempo:
        midi.addTempo(0, 0, self.tempo)
        midi.addTempo(1, 0, self.tempo)

        #* Instruments:
        # Set instruments using General MIDI program numbers (0-based);
        # Oboe is program 68 and Acoustic Grand Piano is program 0:
        melody_instrument = 68
        harmony_instrument = 0
        midi.addProgramChange(0, 0, 0, melody_instrument)
        midi.addProgramChange(1, 1, 0, harmony_instrument)

        #* Metadata:
        # Title:
        midi.addText(0, 0, f"Title: {self.title}")
        midi.addText(1, 0, f"Title: {self.title}")
        # Composer:
        midi.addText(0, 0, f"Composer: ARH MIA")
        midi.addText(1, 0, f"Composer: ARH MIA")
        # Date:
        date = datetime.datetime.now().strftime("%d/%m/%Y")
        midi.addText(0, 0, f"Date: {date}")
        midi.addText(1, 0, f"Date: {date}")

        # Copyright:
        midi.addCopyright(0, 0, "@arhcoder")
        midi.addCopyright(1, 0, "@arhcoder")

        #* Time Signature:
        # MIDIUtil expects the denominator as a power of 2;
        # For 4/4, numerator=4, denominator=int(log2(4)) = 2):
        num, denom = self.melody.signature
        midi_denominator = int(math.log(denom, 2))
        clocks_per_tick = 24
        notes_per_quarter = 8
        midi.addTimeSignature(0, 0, num, midi_denominator, clocks_per_tick, notes_per_quarter)
        midi.addTimeSignature(1, 0, num, midi_denominator, clocks_per_tick, notes_per_quarter)

        #* Key signature:
        key_name, key_type = self.melody.key

        # Determine if key scale (key_type) is major or minor:
        key_type = key_type.lower()
        
        # Determine mode and accidentals based on key_type
        if key_type in [k for k, (_, t) in diatonics.items() if t == "major"]:
            accidentals, acc_type_str = major_key_signatures.get(key_name, (0, None))
            mode = MAJOR
        elif key_type in [k for k, (_, t) in diatonics.items() if t == "minor"]:
            accidentals, acc_type_str = minor_key_signatures.get(key_name, (0, None))
            mode = MINOR
        else:
            accidentals, acc_type_str = (0, None)
            mode = MAJOR
        
        # Gets the type of accidentals:
        if acc_type_str == "SHARPS":
            accidental_type = SHARPS
        elif acc_type_str == "FLATS":
            accidental_type = FLATS
        else:
            accidental_type = SHARPS

        midi.addKeySignature(0, 0, accidentals, accidental_type, mode)
        midi.addKeySignature(1, 0, accidentals, accidental_type, mode)


        #? UPBEAT AND FREE INITIAL BARS:
        beats_per_bar = num * (4.0 / denom)
        upbeat = self.melody.upbeat
        free_bars = math.ceil(upbeat / beats_per_bar) if upbeat > 0 else 1

        # The first actual note starts at:
        start_offset = free_bars * beats_per_bar - upbeat


        #? MELODY ON TRACK 0:
        # Units: quarter note = 16 units = 1 beat:
        def add_melody(start_time: int):
            current_time = start_time
            for phrase in self.melody.phrases:
                for note in phrase.notes:
                    duration = note.space / 16.0

                    # If the note name is "X", it is a rest:
                    if note.note != "X":
                        pitch = self.note_to_midi(note.note, note.octave)
                        midi.addNote(track=0, channel=0, pitch=pitch,
                                     time=current_time, duration=duration,
                                     volume=100)
                    current_time += duration
            return current_time
        

        #? HARMONY ON TRACK 1:
        def add_harmony(start_time, ignore_leading_silence=False):
            current_time = start_time
            non_silent_encountered = False
            for chord in self.harmony.chords:
                # Determine if the chord is completely silent:
                is_silent = all(note.note == "X" for note in chord.notes)
                if ignore_leading_silence and not non_silent_encountered:
                    if is_silent:
                        continue
                    else:
                        non_silent_encountered = True
                duration = chord.space / 16.0
                for i, note in enumerate(chord.notes):
                    if note.note == "X":
                        continue  # skip silent notes
                    pitch = self.note_to_midi(note.note, note.octave)
                    annotation = None

                    # For the lowest note (first non-silent note) add an annotation with chord.degree:
                    if i == 0:
                        annotation = getattr(chord, "degree", None)
                    midi.addNote(track=1, channel=1, pitch=pitch,
                                 time=current_time, duration=duration,
                                 volume=100, annotation=annotation)
                current_time += duration
            return current_time
        

        #? MELODY and HARMONY ADDING TWICE:
        melody_iter_start = start_offset
        harmony_iter_start = start_offset

        #* First time:
        melody_end = add_melody(melody_iter_start)
        harmony_end = add_harmony(harmony_iter_start, ignore_leading_silence=False)

        #* Second time:
        second_melody_start = melody_end
        second_harmony_start = harmony_end
        add_melody(second_melody_start)
        add_harmony(second_harmony_start, ignore_leading_silence=True)


        #? SAVES THE MIDI FILE:
        with open(filename, "wb") as outf:
            midi.writeFile(outf)
        
        
        #? SAVES TXT FILE:
        with open(filename.replace(".mid", ".txt"), "w", encoding="utf-8") as f:
            f.write("\nMIA Harmfirst b.0.3.0 COMPOSITION\n")
            date_str = datetime.datetime.now().strftime("%d/%m/%Y at %H:%M:%S")
            f.write(f"Date: {date_str}\n\n")
            f.write(f"Title: {self.title}\n")
            f.write(f"Composer: ARH MIA\n\n")
            f.write(str(self.melody))
            f.write(str(self.harmony))
            f.write("\nLOGS:\n")
            f.write(self.logs)
            print(f"\nText file saved as {filename.replace('.mid', '.txt')}")

        print(f"MIDI file saved as {filename}")
    

    #? Helper function to translate notes into midi id format:
    def note_to_midi(self, note_name, octave):
        note_map = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,"B": 11}
        semitone = note_map.get(note_name, 0)
        midi_number = (octave + 1) * 12 + semitone
        return midi_number