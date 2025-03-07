from Blocks.Staff import Staff
from Blocks.Chord import Chord
from Blocks.Note import get_times

class Harmony(Staff):

    def __init__(self, signature: tuple, key_name: str, key_type, upbeat=0, tuning=440):
        """
        Represents a harmony staff containing a list of Chord objects
        Inherits from Staff
        Parameters:
            - signature [tuple]: Time signature
            - key_name [str]: Name of the key
            - key_type [int]: Name of the type of scale; Example: "major", "minor", "lydian", minor melodic"
            - upbeat [int]: Times occupied by the upbeat; Default: 0 (no upbeat)
            - tuning [int | float]: Tuning frequency; Default: 440 (A4=440Hz)
        """
        super().__init__(signature, key_name, key_type, upbeat, tuning)
        if self._anacrusis:
            self._add_upbeat_chord()

    def _add_upbeat_chord(self):
        """
            Adds a silent "X" Chord to represent the upbeat.
        """
        space_required = self._upbeat * get_times(self._signature[1])[1]
        try:
            time = self._get_time_from_space(space_required)
        except ValueError as error:
            raise ValueError(f"Cannot create upbeat chord: {error}")
        
        silent_chord = Chord(
            name="X",
            ctype="",
            inversion=0,
            octave=0,
            time=time,
            dot=False,
            tuning=self._tuning
        )
        self._content.append(silent_chord)
        self._update_space()

    def add_element(self, chord: Chord):
        """
        Add a Chord to the harmony
        Parameters:
            - chord [Chord]: The Chord object to add
        """
        if not isinstance(chord, Chord):
            raise TypeError("Element must be an instance of Chord.")
        
        self._content.append(chord)
        self._update_space()

    #? Chords getter:
    @property
    def chords(self):
        return self._content
    
    
    def __repr__(self):
        return (
            "\nHarmony(\n"
            f"    signature={self._signature},\n"
            f"    key={self._key},\n"
            f"    tuning=A4[{self._tuning}Hz],\n"
            f"    upbeat={self._upbeat},\n"
            f"    anacrusis={self._anacrusis},\n"
            f"    space={self._space},\n"
            f"    bars_amount={self._bars_amount},\n"
            f"    chords=[\n\n"
            + ',\n\n'.join(['        ' + repr(chord) for chord in self._content]) + '\n\n'
            f"    ]\n"
            ")"
        )