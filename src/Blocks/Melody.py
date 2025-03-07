from Blocks.Staff import Staff
from Blocks.Phrase import Phrase

class Melody(Staff):

    def __init__(self, signature: tuple, key_name: str, key_type, upbeat=0, tuning=440):
        """
            Represents a melody staff containing a list of Phrase objects
            Inherits from Staff
            Parameters:
                - signature [tuple]: Time signature
                - key_name [str]: Name of the key
                - key_type [str]: Name of the type of scale; Example: "major", "minor", "lydian", minor melodic"
                - upbeat [int]: Times occupied by the upbeat; Default: 0 (no upbeat)
                - tuning [int | float]: Tuning frequency; Default: 440 (A4=440Hz)
        """
        super().__init__(signature, key_name, key_type, upbeat, tuning)
    
    def add_element(self, phrase: Phrase):
        """
        Add a Phrase to the melody
        Parameters:
            - phrase [Phrase]: The Phrase object to add
        """
        if not isinstance(phrase, Phrase):
            raise TypeError("Element must be an instance of Phrase")
        
        self._content.append(phrase)
        self._update_space()
    

    #? Phrases getter:
    @property
    def phrases(self):
        return self._content
    
    def __repr__(self):
        return (
            "\nMelody(\n"
            f"    signature={self._signature},\n"
            f"    key={self._key},\n"
            f"    tuning=A4[{self._tuning}Hz],\n"
            f"    upbeat={self._upbeat},\n"
            f"    anacrusis={self._anacrusis},\n"
            f"    space={self._space},\n"
            f"    bars_amount={self._bars_amount},\n"
            f"    phrases=[\n"
            + ',\n'.join(['        ' + repr(phrase) for phrase in self._content]) + '\n'
            f"    ]\n"
            ")"
        )
