from Blocks.Melody import Melody
from Blocks.Harmony import Harmony

import random
from Selectors import lwrs, ewrs
from Key import notes_of_scale


class Melodic:

    def __init__(self, melody: Melody, harmony: Harmony):
        self.melody = melody
        self.harmony = harmony
    

    def tune_melody(self, octave: int = 4):
        """
            Having the melody and the harmony, tunes the melody using the LWRS algorithm
            [LWRS Algorithm take a list of elements and decide randomly one of them, but
            giving more probability to be selected according to the order on the list, in
            which the further up the list you are, the more likely you are to be selected]

            This is a method for Harmfirst models, because the Harmony is made first and the
            melody depends on it, so it uses the Tonal music principle of hierarchy:
            For select the frequency of a note based on the chord, the preference of selection is:

                1. Notes of the chord
                2. Notes of the key scale
                3. The rest of the notes
            
            Parameters:
                - octave [int]: Value of octave for starting to select notes (4 by default)

            Process:
                1. It uses "map_note2chords()" method to map which note sounds in which chord, this method get
                two things:
                    - a. mapping notes [list [int]]: Each element is a sound note on the melody and its value represent
                        the number of the chord that the note belongs to, for example: [-1, 0, 0, 1, 1, 2, 2, 2, 2]:}
                        This melody has 9 no-silence notes, when the note is "-1" it represent and upbeat note, so
                        use the last chord of "b. sound chords", then they are two notes of the first chord (0),
                        then two notes for second chord (1) and then 4 notes for the last chord (2)
                    - b. sound chords [list[Chord]]: List of soundable chords, where it can be possible to get from
                        each chord the variable "notes" that is a list of Notes and each note contains "note" (for
                        example "C" and "octave", for example 4)

                2. Separates which notes are for which phrase
                3. For each phrase it take the notes and the chords of it and do:
                    4. Selects randomly 50/50 if the phrase goes up or down
                    5. For each note un phrase:
                        6. If it is the first note of the phrase, it make a list using the notes of the chord
                           (taking as first the highest note) and then the notes of the scale, and select the
                           initial note of the phrase using LWRS
                        7. If not the first note of the phrase:
                            8. Make a LWRS list of [Selected direction, the other direction] and selects the
                            direction of the following note (is more probably to select the direction of the
                            initial direction decision on the phrase, but not the 100% of probability) [IN
                            TERMS OF LWRS, IT HAS THE 63% FOR USING THE SAME DIRECTION]
                            9. When the direction is already taken, it takes the notes of the chord and order
                               being first the most near note to the last note (based on the direction), then
                               add this notes to the main selection list
                            10. It takes the rest notes of the scale ignoring the notes that are already on
                                the chord and add to the list in order of how near they are to the last note
                                using also the direction (if the direction is up it takes all the up noted from
                                the last note, ordering by distance, else take the down notes
                            11. It uses the LWRS algorithm to select the note and replace with "last_note" to repeat
                                the process until finishing the notes of the phrase and start with the next phrase
                            12. Saves the note in a list "tunes" as tuple (note, octave), it has to be the same size
                                of the mapping notes list
                12. When finish with all the notes, then take the object Melody and iterate over each Note for Phrases
                    and for each note that is not silence (name="X") it changes the values of "name" and "octave" to give
                    the selected values for notes and then returns the object Melody with this modified values
        """
        # Retrieve the mapping of melody notes to chords and the list of sounding chords:
        mapping, sound_chords = self.map_note2chords()
        
        # Get the notes of the scale for the given key:
        scale_notes = notes_of_scale(self.harmony.key[0], self.harmony.key[1])
        print("\nSCALE NOTES:", scale_notes)
        
        # Chromatic scale (used for ordering and proximity):
        chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # Helper: Build a directed chromatic scale from a starting note in the given direction:
        def get_directed_chromatic(last_note: tuple, direction: str):

            # Direction == up:
            if direction == "up":
                start_idx = chromatic.index(last_note[0])
                candidates = []
                current_octave = last_note[1]
                for i in range(12):
                    idx = (start_idx + i) % 12
                    candidate_octave = current_octave + ((start_idx + i) // 12)
                    candidates.append((chromatic[idx], candidate_octave))

                # Add one extra note one octave above the start;
                # This chromatic scale ensures that only notes in a distance of an octave could be selected;
                # So, for this logic, the max intervale on melodic phrases is an octave:
                candidates.append((last_note[0], last_note[1] + 1))
            
            # Direction == down:
            else:
                start_idx = chromatic.index(last_note[0])
                candidates = []
                current_octave = last_note[1]
                for i in range(12):
                    idx = (start_idx - i) % 12
                    if i <= start_idx:
                        candidate_octave = current_octave
                    else:
                        candidate_octave = current_octave - 1
                    candidates.append((chromatic[idx], candidate_octave))
                
                # Add one extra note one octave below the start:
                candidates.append((last_note[0], last_note[1] - 1))
            print(" * Directed chromatic scale:", candidates)
            return candidates
        
        # Helper: Order the scale by degree importance:
        #// degrees 1,3,5,6,7,4,2 (indices: 0,2,4,5,6,3,1);
        # NOW JUST ORDER IT AS 1, 2, 3, 4, 5, 6 (proximity):
        def order_scale(scale: list):
            # importance_order = [0, 2, 4, 5, 6, 3, 1]
            importance_order = [0, 2, 1, 3, 4, 5, 6]
            return [scale[i] for i in importance_order if i < len(scale)]
        
        #/ Start the tuning process:
        tuned_melody = []
        mapping_index = 0

        #/ FOR EACH PHRASE:
        for phrase in self.melody.phrases:
            phrase_tuned = []
            audible_notes = [n for n in phrase.notes if n.note != "X"]
            if not audible_notes:
                continue

            #? 1. Starting Note of the Phrase:
            map_val = mapping[mapping_index]
            mapping_index += 1
            chord = sound_chords[-1] if map_val == -1 else sound_chords[map_val]
            
            #* Group a: Chord notes in reverse order (highest first) – represent as tuples using given octave:
            chord_candidates = [(n.note, octave) for n in chord.notes][::-1]

            #* Group b: Scale notes (ordered by degree importance) excluding those already in the chord:
            ordered_scale = order_scale(scale_notes)
            group_b = [(note, octave) for note in ordered_scale if note not in [n for n, _ in chord_candidates]]
            
            selection_list = chord_candidates + group_b
            print("\n[STARTING NOTE] Candidate list:")
            print(" * Group A (chord candidates, highest first):", chord_candidates)
            print(" * Group B (scale candidates, by importance):", group_b)
            selected_candidate = lwrs(selection_list)
            print(" * Selected starting note:", selected_candidate)
            last_note = selected_candidate
            phrase_tuned.append(last_note)
            
            # Determine initial direction for the phrase:
            direction = random.choice(["up", "down"])
            print("Initial direction for phrase:", direction)

            #? 2. Subsequent Notes of the Phrase:
            for _ in range(1, len(audible_notes)):
                print("\n[SUBSEQUENT NOTE] Last note:", last_note)

                #? 2a. Decide direction (using ewrs to give preference to phrase direction):
                new_direction = ewrs([direction, "up" if direction == "down" else "down"], base=1)
                print(" * Direction chosen:", new_direction)
                
                #? 2b. Get the current chord for this note:
                map_val = mapping[mapping_index]
                mapping_index += 1
                chord = sound_chords[-1] if map_val == -1 else sound_chords[map_val]
                chord_note_names = [n.note for n in chord.notes]
                print(" * Current chord:", chord_note_names)
                
                #? 2c. Build a directed chromatic scale from last_note:
                directed_chromatic = get_directed_chromatic(last_note, new_direction)
                
                #* Group A: Use the directed chromatic scale (ignoring its last element) to order chord notes;
                #* This group is the chord notes ordered by proximity to the last note:
                group_a = [candidate for candidate in directed_chromatic[:-1] if candidate[0] in chord_note_names]
                print(" * Group A:", group_a)
                
                #* Group B: From the directed chromatic scale, extract those that are in the key scale and not in Group A;
                #* This group is the scale notes ordered by proximity to the last note:
                group_b = [candidate for candidate in directed_chromatic if candidate[0] in scale_notes and candidate not in group_a]
                print(" * Group B:", group_b)
                
                #* Group C: The remaining candidates from the directed chromatic scale;
                #* This group is the rest of the chromatic scale ordered by proximity to the last note:
                group_c = [candidate for candidate in directed_chromatic if candidate not in group_a and candidate not in group_b]
                print(" * Group C (other candidates):", group_c)
                
                selection_list = group_a + group_b + group_c
                print(" * Combined selection list:", selection_list)
                next_candidate = lwrs(selection_list)
                print(" * Selected next note:", next_candidate)
                last_note = next_candidate
                phrase_tuned.append(last_note)
            
            tuned_melody.extend(phrase_tuned)
        
        #? 4. Update the melody with the tuned notes:
        tune_index = 0
        for phrase in self.melody.phrases:
            for note in phrase.notes:
                if note.note != "X":
                    note.note, note.octave = tuned_melody[tune_index]
                    tune_index += 1
                    
        return self.melody
    

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