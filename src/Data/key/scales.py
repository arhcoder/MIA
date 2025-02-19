
diatonics = {
    
    "major": ([0, 2, 4, 5, 7, 9, 11], "major"),
    "minor": ([0, 2, 3, 5, 7, 8, 10], "minor"),

    "minor harmonic": ([0, 2, 3, 5, 7, 8, 11], "minor"),
    "minor melodic": ([0, 2, 3, 5, 7, 9, 11], "minor"),

    "ionian": ([0, 2, 4, 5, 7, 9, 11], "major"),
    "dorian": ([0, 2, 3, 5, 7, 9, 10], "minor"),
    "phrygian": ([0, 1, 3, 5, 7, 8, 10], "minor"),
    "lydian": ([0, 2, 4, 6, 7, 9, 11], "major"),
    "mixolydian": ([0, 2, 4, 5, 7, 9, 10], "major"),
    "aeolian": ([0, 2, 3, 5, 7, 8, 10], "minor"),
    "locrian": ([0, 1, 3, 5, 6, 8, 10], "minor")
}


major_key_signatures = {
    "C": (0, None),
    "G": (1, "SHARPS"),
    "D": (2, "SHARPS"),
    "A": (3, "SHARPS"),
    "E": (4, "SHARPS"),
    "B": (5, "SHARPS"),
    "F#": (6, "SHARPS"),
    "C#": (7, "SHARPS"),
    "F": (1, "FLATS"),
    "Bb": (2, "FLATS"),
    "Eb": (3, "FLATS"),
    "Ab": (4, "FLATS"),
    "Db": (5, "FLATS"),
    "Gb": (6, "FLATS"),
    "Cb": (7, "FLATS")
}
minor_key_signatures = {
    "A": (0, None),
    "E": (1, "SHARPS"),
    "B": (2, "SHARPS"),
    "F#": (3, "SHARPS"),
    "C#": (4, "SHARPS"),
    "G#": (5, "SHARPS"),
    "D#": (6, "SHARPS"),
    "A#": (7, "SHARPS"),
    "D": (1, "FLATS"),
    "G": (2, "FLATS"),
    "C": (3, "FLATS"),
    "F": (4, "FLATS"),
    "Bb": (5, "FLATS"),
    "Eb": (6, "FLATS"),
    "Ab": (7, "FLATS")
}