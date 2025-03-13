from Blocks.Melody import Melody
from Blocks.Harmony import Harmony


class Melodic:

    def __init__(self, melody: Melody, harmony: Harmony):
        self.melody = melody
        self.harmony = harmony
    

    def map_note2chords(self):
        """
            Maps each audible note in the melody to the chord that is sounding at its start time
            The mapping follows these rules:
            - If both melody and harmony have anacrusis (upbeat), the first chord in harmony 
                defines the upbeat. Every note that starts before the upbeat is complete is mapped
                to -1. If a note in the upbeat overflows its available space, it is still mapped as -1,
                and the extra (overflow) is carried over into the first sound chord
            - For the remaining notes, we maintain an accumulator (current_offset) for the current
                chord’s available space. Each note is mapped according to the chord in which its start
                (the current_offset) falls. Even if a note’s full duration causes the accumulator to exceed
                the chord’s capacity, it remains mapped to that chord, and the excess is carried over
                to the next chord
            - Silence notes (with note value "X") add to the cumulative space but are not mapped
            - In the harmony, any chord with name "X" (a rest) that follows a sound chord has its
                space merged externally into that chord
            
            From self.melody and self.harmony it uses:
            self.melody: an object with attributes:
                - anacrusis [bool]
                - upbeat [int]  [not used directly; the upbeat length is taken from self.harmony.chords[0]]
                - phrases: list of Phrase objects, each with:
                    - notes: list of Note objects having:
                        - note: a string ("A" for sound, "X" for silence)
                        - space: a numeric duration
            self.harmony: an object with attributes:
                - anacrusis [bool]
                - chords: list of Chord objects, each with:
                        - name: a string ("E" or "X" for silence)
                        - space: numeric duration
                        (Any silence chord (name "X") following a sound chord is merged externally)
            
            Returns:
            [tuple]: (mapping, sound_chords) where:
                - mapping is a list of integers. Each element corresponds to an audible note 
                (notes with note != "X") in melody:
                    - If -1 means the note starts in the upbeat
                    - If 0, 1, 2, …, are the successive sound chords
                - sound_chords is a list of the Chord objects (from harmony) that are not rests,
                with their effective total durations stored externally
        """
        mapping = []
        
        # Flatten all notes from the melody phrases into one list:
        all_notes = []
        for phrase in self.melody.phrases:
            for note in phrase.notes:
                all_notes.append(note)
        
        # Phase 1: Process the Upbeat (Anacrusis) if applicable:
        i = 0
        leftover = 0
        if self.melody.anacrusis and self.harmony.anacrusis:
            upbeat_total = self.harmony.chords[0].space
            up_offset = 0
            while i < len(all_notes) and up_offset < upbeat_total:
                note = all_notes[i]
                # Even if the note overflows, if it starts in the upbeat region it is mapped as -1:
                if note.note != "X":
                    # Map audible note as part of the upbeat:
                    mapping.append(-1)
                new_up = up_offset + note.space
                # Note fits entirely within the upbeat:
                if new_up < upbeat_total:
                    up_offset = new_up
                    i += 1
                # Note overflows (or exactly fills) the upbeat;
                # It starts in the upbeat (so already mapped as -1) and the overflow is carried:
                else:
                    leftover = new_up - upbeat_total
                    up_offset = upbeat_total
                    i += 1
                    break
        else:
            leftover = 0

        # Phase 2: Build the list of sound chords and their merged spaces;
        # If anacrusis was active, skip the first chord (used for upbeat):
        chords_raw = self.harmony.chords[1:] if (self.melody.anacrusis and self.harmony.anacrusis) else self.harmony.chords[:]
        sound_chords = []
        merged_spaces = []
        for chord in chords_raw:
            if chord.name != "X":
                sound_chords.append(chord)
                merged_spaces.append(chord.space)
            # Merge the rest's space into the last sound chord's effective space:
            else:
                if merged_spaces:
                    merged_spaces[-1] += chord.space

        # Phase 3: Process the remaining notes with chord-by-chord mapping:
        # We use an accumulator (current_offset) relative to the current chord;
        # A note is assigned to the current chord if its start (current_offset) is less than that chord's capacity:
        chord_idx = 0
        current_offset = leftover
        # Process remaining notes from index i onward:
        while i < len(all_notes):
            # Ensure that if current_offset is exactly at the boundary, we advance to the next chord:
            while chord_idx < len(merged_spaces) and current_offset >= merged_spaces[chord_idx]:
                current_offset -= merged_spaces[chord_idx]
                chord_idx += 1
                # Clamp to last chord if we run out:
                if chord_idx >= len(merged_spaces):
                    chord_idx = len(merged_spaces) - 1
                    current_offset = merged_spaces[chord_idx]
                    break
            note = all_notes[i]

            # The note's start time is current_offset. If current_offset is less than the chord's capacity;
            # the note is sounding in this chord:
            if note.note != "X":
                mapping.append(chord_idx)
            new_total = current_offset + note.space

            # The note fits entirely within the current chord:
            if new_total < merged_spaces[chord_idx]:
                current_offset = new_total
            
            # The note exactly fills the current chord:
            elif new_total == merged_spaces[chord_idx]:
                current_offset = 0
                chord_idx += 1
                if chord_idx >= len(merged_spaces):
                    chord_idx = len(merged_spaces) - 1
            
            # The note spans beyond the current chord;
            # Even if it overflows, it is still mapped to the current chord because it starts here:
            else:
                # Advance to the next chord and carry the overflow:
                overflow = new_total - merged_spaces[chord_idx]
                chord_idx += 1
                if chord_idx >= len(merged_spaces):
                    chord_idx = len(merged_spaces) - 1
                    current_offset = merged_spaces[chord_idx]
                else:
                    current_offset = overflow
            i += 1

        return mapping, sound_chords