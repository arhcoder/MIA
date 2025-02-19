
#? CONSTANTS:

from Data.harmony.chords import patterns, classifications
from Data.key.scales import diatonics
note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


#? METHODS:
def notes_of_scale(root: str, scale: str):
    """
        Gets the list of notes of a scale

        Parameter:
            - root [str]: Name of the root note
                It could be some of this values:
                ["C", "D", "E", "F", "G", "A", "B"]
                Or some of this values:
                ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
            - scale [str]: Name of the scale
                Only diatonic scales supported:
                    - "major"
                    - "minor"
                    - "minor harmonic"
                    - "minor melodic"
                    - "ionian"
                    - "dorian"
                    - "phrygian"
                    - "lydian"
                    - "mixolydian"
                    - "aeolian"
                    - "locrian"
        Returns:
            - [list] of strings of the notes
            NOTE: name of the note always with just sharps (#) no flats (b) notation
    """
    # Capitalize and lower case of parameters:
    root = root.capitalize()
    scale = scale.lower()

    # Flats to sharp:
    flats_to_sharps = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    if root in flats_to_sharps:
        root = flats_to_sharps[root]
    
    # Validate scale name:
    if scale not in diatonics:
        raise ValueError(f"Scale \"{scale}\" not supported.\nAvailable scales: {list(diatonics.keys())}")

    # Interval patterns:
    scale_pattern, _ = diatonics[scale]
    try:
        root_index = note_names.index(root)
    except ValueError:
        raise ValueError(f"Root note \"{root}\" not valid. Use one of {note_names}")
    
    # Returns the list of patterns:
    return [note_names[(root_index + interval) % 12] for interval in scale_pattern]


def chords_of_scale(key: str, scale: str):
    """
        Gets the list of chords from a key/scale

        Parameter:
            - key [str]: Name of the key/scale
                It could be some of this values:
                ["C", "D", "E", "F", "G", "A", "B"]
                Or some of this values:
                ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
            - scale [str]: Name of type of scale
                Only diatonic scales supported:
                    - "major"
                    - "minor"
                    - "minor harmonic"
                    - "minor melodic"
                    - "ionian"
                    - "dorian"
                    - "phrygian"
                    - "lydian"
                    - "mixolydian"
                    - "aeolian"
                    - "locrian"
        Returns:
            - [list[tuple]] where tuple has three strings: (name of the chord, type of the chord, chord degree)
              NOTE: name of the note always with just sharps (#) no flats (b) notation
    """
    # Process key to handle capitalization and flats:
    # Flats to sharp:
    flats_to_sharps = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    if key in flats_to_sharps:
        key = flats_to_sharps[key].capitalize()
    
    # Process scale to lower case:
    scale = scale.lower()
    if scale not in diatonics:
        raise ValueError(f"Scale \"{scale}\" not supported.\nAvailable scales: {list(diatonics.keys())}")
    intervals, _ = diatonics[scale]
    
    # Generate scale notes:
    try:
        key_index = note_names.index(key)
    except ValueError:
        raise ValueError(f"Invalid key: {key}")
    scale_notes = [note_names[(key_index + interval) % 12] for interval in intervals]
    
    # Generate major scale notes for accidentals comparison:
    major_scale_intervals = diatonics["major"][0]
    major_scale_notes = [note_names[(key_index + interval) % 12] for interval in major_scale_intervals]
    
    # Prepare Roman numerals:
    degrees = ["I", "II", "III", "IV", "V", "VI", "VII"]
    chords = []
    
    # Mapping from pattern names to chord types:
    # Change if can change the format of chord type:
    triad_type_mapping = {
        "": "",
        "m": "m",
        "dim": "dim",
        "aug": "aug",
        "sus2": "sus2",
        "sus4": "sus4"
    }
    
    for i in range(7):
        root = scale_notes[i]
        third_note = scale_notes[(i + 2) % 7]
        fifth_note = scale_notes[(i + 4) % 7]
        
        root_idx = note_names.index(root)
        third_idx = note_names.index(third_note)
        fifth_idx = note_names.index(fifth_note)
        
        third_semitones = (third_idx - root_idx) % 12
        fifth_semitones = (fifth_idx - root_idx) % 12
        
        triad_intervals = sorted([0, third_semitones, fifth_semitones])
        chord_pattern = None
        
        # Find the matching triad pattern:
        for pattern_name, pattern in patterns.items():
            if len(pattern) == 3 and sorted(pattern) == triad_intervals:
                chord_pattern = pattern_name
                break
        
        chord_type = triad_type_mapping.get(chord_pattern, "x")
        
        # Compute accidental:
        major_root = major_scale_notes[i]
        current_idx = note_names.index(root)
        major_idx = note_names.index(major_root)
        diff = current_idx - major_idx
        
        # Adjust diff to minimal steps:
        if diff > 6:
            diff -= 12
        elif diff < -6:
            diff += 12
        
        accidental = ""
        if diff < 0:
            accidental = "b" * abs(diff)
        elif diff > 0:
            accidental = "#" * diff
        
        # Determine Roman numeral case and notation:
        roman_base = degrees[i]
        if chord_type == "minor":
            roman_case = roman_base.lower()
        else:
            roman_case = roman_base
        
        # Add diminished symbol:
        if chord_type == "diminished":
            notation_str = f"{accidental}{roman_case.lower()}°"
        else:
            notation_str = f"{accidental}{roman_case}"
        
        chords.append((root, chord_type, notation_str))
    
    return chords


def degree_of_chord(root: str, ctype: str, key: str, scale: str):
    """
        Receives a chord and the key/scale and returns the degree (roman notation) on the key
        
        Parameters:
            - root [str]: Name of the chord root note
                It could be some of this values:
                    ["C", "D", "E", "F", "G", "A", "B"]
                    Or some of this values:
                    ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
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
            
            - key [str]: Name of the key/scale
                It could be some of this values:
                ["C", "D", "E", "F", "G", "A", "B"]
                Or some of this values:
                ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
            - scale [str]: Name of type of scale
                Only diatonic scales supported:
                    - "major"
                    - "minor"
                    - "minor harmonic"
                    - "minor melodic"
                    - "ionian"
                    - "dorian"
                    - "phrygian"
                    - "lydian"
                    - "mixolydian"
                    - "aeolian"
                    - "locrian"
        Returns:
            - [str] name of the degree in roman notation; for example: I, or "iv" or "bIII"
    """

    # Validations:
    flats_to_sharps = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    root = root.capitalize()
    key = key.capitalize()
    ctype = ctype.lower()
    if root in flats_to_sharps:
        root = flats_to_sharps[root]
    if root not in note_names:
        raise ValueError(f"\"root\" must be any from {note_names + list(flats_to_sharps.keys())}")
    
    if key in flats_to_sharps:
        key = flats_to_sharps[key]
    if key not in note_names:
        raise ValueError(f"\"key\" must be any from {note_names + list(flats_to_sharps.keys())}")
    
    scale = scale.lower()
    if scale not in diatonics:
        raise ValueError(f"Scale \"{scale}\" not supported.\nAvailable scales: {list(diatonics.keys())}")
    
    if ctype not in classifications:
        raise ValueError(f"Invalid chord type: {ctype}. Supported types: {list(classifications.keys())}")

    # Generate scale_notes:
    key_idx = note_names.index(key)
    intervals, _ = diatonics[scale]
    scale_notes = [note_names[(key_idx + interval) % 12] for interval in intervals]

    # Generate the diatonic chords for the key and scale:
    scale_chords = chords_of_scale(key, scale)
    
    # Mapping from classification to triad_type:
    triad_category_to_type = {
        "major": "",
        "minor": "m",
        "diminished": "dim",
        "augmented": "aug"
    }
    triad_category = classifications[ctype]
    triad_type = triad_category_to_type.get(triad_category)
    if triad_type is None:
        raise ValueError(f"Unsupported triad category: {triad_category}")
    
    # Search for a matching triad in the scale:
    for chord_root, chord_type, degree in scale_chords:
        if chord_root == root and chord_type == triad_type:
            if ctype == "7":
                suffix = "7"
            else:
                suffix = f" ({ctype})" if ctype not in ["", "m", "aug", "dim"] else ""
            if triad_category == "minor":
                degree = degree.lower()
            return f"{degree}{suffix}"
    
    # Check if all notes of the chord are in the scale_notes:
    root_idx = note_names.index(root)
    pattern = patterns[ctype]
    chord_notes = [note_names[(root_idx + interval) % 12] for interval in pattern]
    all_notes_in_scale = all(note in scale_notes for note in chord_notes)
    
    # Compute the notation_str:
    current_idx = note_names.index(root)
    semitone_diff = (current_idx - key_idx) % 12

    major_intervals = diatonics["major"][0]
    degrees_list = ["I", "II", "III", "IV", "V", "VI", "VII"]

    closest_i = None
    min_distance = float("inf")
    for i, interval in enumerate(major_intervals):
        distance = abs(semitone_diff - interval)
        if distance < min_distance:
            min_distance = distance
            closest_i = i
        elif distance == min_distance:
            if interval < major_intervals[closest_i]:
                closest_i = i
    i = closest_i
    diff = semitone_diff - major_intervals[i]

    if diff > 6:
        diff -= 12
    elif diff < -6:
        diff += 12

    accidental = ""
    if diff < 0:
        accidental = "b" * abs(diff)
    elif diff > 0:
        accidental = "#" * diff

    roman_base = degrees_list[i]
    if triad_category in ["minor", "diminished"]:
        roman_case = roman_base.lower()
    else:
        roman_case = roman_base

    if triad_category == "diminished":
        notation_str = f"{accidental}{roman_case}°"
        suffix = ""
    elif triad_category == "augmented":
        notation_str = f"{accidental}{roman_case}+"
        suffix = ""
    else:
        notation_str = f"{accidental}{roman_case}"
        suffix = f" ({ctype})" if ctype not in ["", "m"] else ""
    
    if all_notes_in_scale:
        return f"{notation_str}{suffix}"
    else:
        return f"*{notation_str}{suffix}"


def notes_of_chord(root: str, ctype: str, inversion: int):
    pattern = patterns[ctype]
    root_idx = note_names.index(root)
    notes = [note_names[(root_idx + interval) % 12] for interval in pattern]
    return notes[inversion:] + notes[:inversion]