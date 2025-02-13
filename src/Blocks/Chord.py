from Blocks.Note import Note, get_times
from Data.harmony.chords import patterns

class Chord:

    def __init__(self, name: str, ctype: str, inversion: int, octave: int, time: int, dot: bool = False, degree: str = "", tuning: int = 440):
        """
            Paremeters:
            - name [str]: Indicates the name of the chord based on the root note.
                It could be some of this values:
                ["C", "D", "E", "F", "G", "A", "B"]
                Or some of this values:
                ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
                "X" value represents a silent chords.
            - ctype [str]: The type of the chord. It could be:
                
                Value       | Description
                ------------|-----------------------------------------
                ""          | Major chord (empty string)
                "m"         | Minor chord
                "7"         | Dominant 7th chord
                "maj7"      | Major 7th chord
                "m7"        | Minor 7th chord
                "mmaj7"     | Minor Major 7th chord
                "aug"       | Augmented chord
                "dim"       | Diminished chord
                "sus2"      | Suspended 2nd chord
                "sus4"      | Suspended 4th chord
                "9"         | Dominant 9th chord
                "maj9"      | Major 9th chord
                "m9"        | Minor 9th chord
                "11"        | Dominant 11th chord
                "maj11"     | Major 11th chord
                "m11"       | Minor 11th chord
                "13"        | Dominant 13th chord
                "maj13"     | Major 13th chord
                "m13"       | Minor 13th chord
                "dim7"      | Diminished 7th chord
                "m7b5"      | Half-Diminished 7th chord (Minor 7 flat 5)
                "add9"      | Add 9 chord
                "madd9"     | Minor Add 9 chord
                "6"         | Major 6th chord
                "m6"        | Minor 6th chord
                "aug7"      | Augmented 7th chord
                "7b9"       | Dominant 7 flat 9 chord
                "7#9"       | Dominant 7 sharp 9 chord
                "7b5"       | Dominant 7 flat 5 chord
                "7#5"       | Dominant 7 sharp 5 chord
                "9#11"      | Dominant 9 sharp 11 chord

            - inversion [int] Indicates if the chord has an inversion (only between 0 and 3):
                - If 0, it will be in fundamental state.
                - If 1, 2 or 3, it will be applied the inversions.
            - octave [int]: Octave of the chord root (before apply an inversion).
            - time [int]: Base time value for the chord:

                Time   | Figure Name
                -------|-------------------
                1      | Whole
                2      | Half
                4      | Quarter
                8      | Eighth
                16     | Sixteenth
                32     | Thirty-second
                64     | Sixty-fourth
                3      | Half Triplet
                6      | Quarter Triplet
                12     | Eighth Triplet
                24     | Sixteenth Triplet

        """

        #/ ATTRIBUTES:
        #? Chord name:
        naturals = ["C", "D", "E", "F", "G", "A", "B", "X"]
        sharps = ["C#", "D#", "F#", "G#", "A#"]
        flats = ["Db", "Eb", "Gb", "Ab", "Bb"]
        name = name.capitalize()
        if name in flats:
            name = sharps[flats.index(name)]
        if name not in naturals + sharps + flats:
            raise ValueError(f"\"name\" must be one of {naturals + sharps + flats}, but given {name}")
        self._name = name
        
        #? Chord type:
        ctype = ctype.lower()
        if ctype not in [*patterns.keys()]:
            raise ValueError(f"\"ctype\" must be one of {[*patterns.keys()]}, but given {ctype}")
        self._ctype = ctype

        #? Chord inversion:
        if inversion < 0 or inversion > 3 or not isinstance(inversion, int):
            raise ValueError(f"\"inversion\" must be an integer between 0 and 3, but given {inversion}")
        self._inversion = inversion

        #? Root octave:
        if octave < 0 or octave > 8 or not isinstance(octave, int):
            raise ValueError(f"\"octave\" must be an integer between 0 and 8, but given {octave}")
        self._octave = octave

        #? Chord time:
        if time not in [1, 2, 4, 8, 16, 32, 64, 3, 6, 12, 24]:
            raise ValueError(f"\"time\" must be one of: [1, 2, 4, 8, 16, 32, 64] or for tripletes: [3, 6, 12, 24], but given {time}")
        self._time = time

        #? Existance of Dot in the note:
        if not isinstance(dot, bool):
            raise TypeError(f"\"dot\" has to be boolean (True or False), but given {dot}")
        self._dot = dot

        #? Chord tuning:
        if tuning not in [440, 432]:
            raise ValueError(f"\"tuning\" must be either 440 or 432, but given {tuning}")
        self._tuning = tuning

        #? Calculated:
        self._degree = degree
        self._notes = None
        self._notes_str = None
        self._space = 0
        self._calculate_notes()
    

    #/ METHODS:
    def _calculate_notes(self):

        # If silent chord, ignore the rest:
        if self._name == "X":
            self._ctype = None
            self._inversion = None
            self._octave = None
            self._notes = [Note(self._time, "X", 0, self._dot, self._tuning)]
            self._notes_str = []
            _, space = get_times(self._time)
            self._space = space
            return

        #? Constants:
        scale = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        # Gets the root and the intervals:
        root_index = scale.index(self._name)
        intervals = patterns[self._ctype]
        notes = []
        notes_obj = []
        notes_str = []
        current_octave = self._octave

        # Get each note of the chord:
        for _, interval in enumerate(intervals):
            note_index = (root_index + interval) % len(scale)
            note_name = scale[note_index]

            # Adjust the octave:
            if root_index + interval >= len(scale):
                current_octave += 1

            notes.append({"note": note_name, "octave": current_octave})

        # Apply inversions:
        for _ in range(self._inversion):
            inverted_note = notes.pop(0)
            inverted_note["octave"] += 1
            notes.append(inverted_note)
        

        # Creates two lists for notes:
        for note in notes:
            # Append the note using class Note:
            notes_obj.append(Note(self._time, note["note"], note["octave"], self._dot, self._tuning))

            # Generates also a easy lecture of the chord notes:
            notes_str.append(f'{note["note"]}{note["octave"]}')
        
        # Saves the chords lists:
        self._notes = notes_obj
        self._notes_str = notes_str

        # Calculates the space:
        _, space = get_times(self._time)
        self._space = space
    

    #/ SETTERS:
    #? NAME:
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value: str):
        naturals = ["C", "D", "E", "F", "G", "A", "B", "X"]
        sharps = ["C#", "D#", "F#", "G#", "A#"]
        flats = ["Db", "Eb", "Gb", "Ab", "Bb"]
        value = value.capitalize()
        if value in flats:
            value = sharps[flats.index(value)]
        if value not in naturals + sharps + flats:
            raise ValueError(f"\"name\" must be one of {naturals + sharps + flats}, but given {value}")
        if value != self._name:
            self._name = value
            self._calculate_notes()
    
    #? CTYPE:
    @property
    def ctype(self):
        return self._ctype
    
    @ctype.setter
    def ctype(self, value: str):
        value = value.lower()
        if value not in patterns:
            raise ValueError(f"\"value\" must be one of {patterns}, but given {value}")
        if value != self._ctype:
            self._ctype = value
            self._calculate_notes()
    
    #? CHORD INVERSION:
    @property
    def inversion(self):
        return self._inversion
    
    @inversion.setter
    def inversion(self, value: int):
        if value < 0 or value > 3 or not isinstance(value, int):
            raise ValueError(f"\"inversion\" must be an integer between 0 and 3, but given {value}")
        if value != self._inversion:
            self._inversion = value
            self._calculate_notes()
    
    #? OCTAVE:
    @property
    def octave(self):
        return self._octave

    @octave.setter
    def octave(self, value: int):
        if value < 0 or value > 8 or not isinstance(value, int):
            raise ValueError(f"\"octave\" must be an integer between 0 and 8, but given {value}")
        if value != self._octave:
            self._octave = value
            self._calculate_notes()

    #? TIME:
    @property
    def time(self):
        return self._time
    
    @time.setter
    def time(self, value: int):
        if value not in [1, 2, 4, 8, 16, 32, 64, 3, 6, 12, 24]:
            raise ValueError(f"\"time\" must be one of: [1, 2, 4, 8, 16, 32, 64] or for tripletes: [3, 6, 12, 24], but given {value}")
        if value != self._time:
            self._time = value
            self._calculate_notes()
    
    #? DOT:
    @property
    def dot(self):
        return self._dot

    @dot.setter
    def dot(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError(f"\"dot\" has to be boolean (True or False), but given {value}")
        if value != self._dot:
            self._dot = value
            self._calculate_notes()
    
    #? TUNING:
    @property
    def tuning(self):
        return self._tuning

    @tuning.setter
    def tuning(self, value: int):
        if value not in [440, 432]:
            raise ValueError(f"\"tuning\" must be either 440 or 432, but given {value}")
        if value != self._tuning:
            self._tuning = value
            self._calculate_notes()
    
    #? DEGREE:
    #* Given by external sources;
    #* Says which is the function of the chord in a reference key:
    @property
    def degree(self):
        return self._degree
    
    def degree(self, degree: str):
        if not isinstance(degree, str):
            raise TypeError("\"degree\" must be a string")
        self._degree = degree
    
    #? SPACE:
    @property
    def space(self):
        return self._space
    
    @property
    def notes(self):
        return self._notes
    

    def __repr__(self):
        return (
            f"Chord(name={self._name}, ctype={self._ctype}, inversion={self._inversion}, octave={self._octave}, degree={self._degree}, "
            f"time={self._time}, space={self._space} dot={self._dot} notes={self._notes}, notes_str={self._notes_str})"
        )