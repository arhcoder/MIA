from Blocks.Melody import Melody
from Blocks.Harmony import Harmony
from Data.harmony.chords import patterns, classifications

import random
from Selectors import lwrs, ewrs
from Key import notes_of_scale


class Melodic:

    def __init__(self, melody: Melody, harmony: Harmony):
        self.melody = melody
        self.harmony = harmony
    

    def tune_melody(self, octave: int = 4, verbose: bool = False):
        """
            Having the melody and the harmony, tunes the melody using the LWRS algorithm
            [LWRS Algorithm take a list of elements and decide randomly one of them, but
            giving more probability to be selected according to the order on the list, in
            which the further up the list you are, the more likely you are to be selected]

            This is a method for Harmfirst models, because the Harmony is made first and the
            melody depends on it, so it uses the Tonal music principle of hierarchy
            For select the frequency of a note based on the chord, the steps are:

            1. Preprocessing:
                - Retrieves a mapping between each audible note and its corresponding chord index 
                    using "map_note2chords()", along with a list of "sound chords" from the harmony
                - Obtains the diatonic scale for the current key via "notes_of_scale"
                - Defines a chromatic scale (12 semitones) to be used for proximity and stepwise motion

            2. Helper Functions:
                - get_directed_chromatic(last_note, direction):
                    Builds a directed chromatic sequence from a starting note in a given direction 
                    ("up" or "down"), ensuring candidate notes remain within an octave (plus one extra note)
                - order_scale(scale):
                    Orders the diatonic scale tones by a predefined functional importance
                - common_tones(chord1, chord2):
                    Determines the common note names between two chords for smoother voice-leading

            3. Segmentation of the Melody:
                - Groups the melody's audible notes into segments based on the chord mapping
                - Each segment is characterized by its chord index, the start and end indices in the mapping,
                    and the "density" (number of notes played over that chord)
                - Notes that start a new segment are flagged as chord-boundary notes, important for transition

            4. Notes Loop: For each audible note in each phrase:
            
                a. Determine Context:
                    - Identify the current chord from the mapping. For an anacrusis note (mapping value -1), 
                        the last chord is used
                    - Identify if the note is a chord-boundary note (the first note in a segment)
                    - Retrieve previous and next chord objects if available to support voice-leading across chords
                    - Retrieve the last assigned note (if any) for proximity considerations

                b. Build the candidates List:
                    The candidates list is built in four groups, then concatenated and passed to the 
                    weighted random selection function (lwrs):

                    - Group A: Current Chord Tones:
                        * Consists of all tones from the current chord, ordered by proximity relative to 
                        the last note (if available) using a directed chromatic scale
                        * For the first note of phrase, an ordering of highest first is used

                    - Group B: Adjacent Chord Context:
                        * Includes common tones between the previous chord and the current chord, if available
                        * For chord-boundary notes, also includes common tones between the current and next chord,
                        inserted at the beginning of this group to ensure smooth transitions

                    - Group C: Diatonic Scale Tones:
                        * Contains scale tones from the current key, ordered by functional importance and excluding
                        any candidates already present in Groups A and B

                    - Group D: Chromatic Fillers:
                        * Supplements with additional candidates from a directed chromatic scale
                        * These fillers are filtered by a maximum allowed leap, which is set more restrictively, so
                        when the chord density is high (favoring stepwise motion) and more liberally when density is low

                c. Direction Decision:
                    - A decision on whether the melodic motion should continue upward or downward is made,
                        potentially using an enhanced version of ewrs to favor continuity or voice-leading cues

                d. Final Selection:
                    - The fully assembled candidate list is passed to lwrs, which selects one note based on a logarithmic
                        weighting favoring candidates at the top of the list
                    - The selected candidate (a (note, octave) tuple) is then assigned to the current note

            5. Updating the Melody:
            - Once all phrases and their audible notes have been processed, the melody object is updated with the newly
                assigned note names and octaves, replacing the original pitches

            Returns:
             - [Melody]: The updated melody object with tunned notes acoording to the harmony
        """

        #? 1. Preprocessing: Get chord mapping and sound chords, and the key’s scale:
        mapping, sound_chords = self.map_note2chords()
        scale_notes = notes_of_scale(self.harmony.key[0], self.harmony.key[1])
        if verbose:
            print("\nSCALE NOTES:", scale_notes)
        
        # Define a standard chromatic scale:
        chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        #? Helpef functions:
        #* Directed chromatic scale from a starting note in a given direction:
        def get_directed_chromatic(last_note: tuple, direction: str):
            start_idx = chromatic.index(last_note[0])
            candidates = []
            current_octave = last_note[1]
            for i in range(12):
                if direction == "up":
                    idx = (start_idx + i) % 12
                    candidate_octave = current_octave + ((start_idx + i) // 12)
                else:
                    idx = (start_idx - i) % 12
                    candidate_octave = current_octave - (1 if i > start_idx else 0)
                candidates.append((chromatic[idx], candidate_octave))
            # Cap the movement: add one extra note one octave away:
            if direction == "up":
                candidates.append((last_note[0], last_note[1] + 1))
            else:
                candidates.append((last_note[0], last_note[1] - 1))
            return candidates

        #* Order scale tones by functional importance:
        def order_scale(scale: list):
            # ORDER: tonic (0), mediant (2), supertonic (1), subdominant (3), dominant (4), submediant (5), leading-tone (6):
            importance_order = [0, 2, 1, 3, 4, 5, 6]
            return [scale[i] for i in importance_order if i < len(scale)]
        
        #* Determine common tones between two chords:
        def common_tones(chord1, chord2):
            tones1 = [n.note for n in chord1.notes]
            tones2 = [n.note for n in chord2.notes]
            return list(set(tones1) & set(tones2))
        
        #? 2. Tuning Process:
        # Group notes by chord segments using the mapping:
        # Creating a list of segments, each segment is (chord_idx, start_index, end_index, density):
        segments = []
        current_chord = None
        start = 0
        for i, m in enumerate(mapping):
            if i == 0:
                current_chord = m
            if m != current_chord:
                segments.append((current_chord, start, i, i - start))
                current_chord = m
                start = i
        # Append final segment:
        segments.append((current_chord, start, len(mapping), len(mapping) - start))
        
        tuned_melody = []
        mapping_index = 0
        
        # Process each phrase:
        for phrase in self.melody.phrases:
            phrase_tuned = []
            # Extract only audible notes (ignoring rests "X"):
            audible_notes = [n for n in phrase.notes if n.note != "X"]
            if not audible_notes:
                continue

            # Process each note in the phrase using its global mapping index:
            for note_idx, note_obj in enumerate(audible_notes):
                # Identify current segment by matching mapping_index:
                # Also get density for current chord:
                current_segment = None
                for seg in segments:
                    if seg[1] <= mapping_index < seg[2]:
                        current_segment = seg
                        break
                
                # Determine the current chord from mapping:
                map_val = mapping[mapping_index]
                
                # If map_val == -1, it's an anacrusis note: assign last chord:
                current_chord_obj = sound_chords[-1] if map_val == -1 else sound_chords[map_val]
                
                # Decide if this note is at a chord boundary:
                is_boundary = False
                if mapping_index == current_segment[1]:
                    # First note in the segment is a chord entry note:
                    is_boundary = True
                
                # Determine previous chord and next chord contexts (if available):
                previous_chord_obj = None
                next_chord_obj = None

                # For previous chord: if not the first segment:
                seg_index = segments.index(current_segment)
                if seg_index > 0:
                    prev_seg = segments[seg_index - 1]
                    prev_map = prev_seg[0]
                    previous_chord_obj = sound_chords[-1] if prev_map == -1 else sound_chords[prev_map]
                
                # For next chord: if not the last segment:
                if seg_index < len(segments) - 1:
                    next_seg = segments[seg_index + 1]
                    next_map = next_seg[0]
                    next_chord_obj = sound_chords[-1] if next_map == -1 else sound_chords[next_map]
                
                # For the very first note in the melody or phrase;
                # if there is no last note, we choose a candidate from current chord tones directly:
                if phrase_tuned:
                    last_note = phrase_tuned[-1]
                else:
                    last_note = None
                candidate_list = []

                #? Candidate Group A: Primary current chord tones:
                chord_candidates = [(n.note, octave) for n in current_chord_obj.notes]
                # Order by proximity if a last_note exists; otherwise, use default order (highest first):
                if last_note:
                    # Build a directed chromatic scale from last_note (in the prevailing direction):
                    # For initial note, choose direction based on a simple random pick:
                    direction = random.choice(["up", "down"])
                    directed = get_directed_chromatic(last_note, direction)
                    
                    # Reorder chord_candidates based on their appearance in the directed list:
                    ordered_chord = []
                    for candidate in directed[:-1]:
                        if candidate in chord_candidates and candidate not in ordered_chord:
                            ordered_chord.append(candidate)
                    
                    # If some chord tones were not encountered in the directed scale, append them at end:
                    for c in chord_candidates:
                        if c not in ordered_chord:
                            ordered_chord.append(c)
                    chord_candidates = ordered_chord
                else:
                    chord_candidates = chord_candidates[:-1]
                candidate_list.extend(chord_candidates)
                
                #? Candidate Group B: Adjacent chord context (common tones):
                adjacent_candidates = []
                if previous_chord_obj:
                    prev_common = common_tones(previous_chord_obj, current_chord_obj)
                    # Include these tones in the candidate list, if not already present:
                    for tone in prev_common:
                        cand = (tone, octave)
                        if cand not in candidate_list and cand not in adjacent_candidates:
                            adjacent_candidates.append(cand)
                if is_boundary and next_chord_obj:
                    next_common = common_tones(current_chord_obj, next_chord_obj)
                    for tone in next_common:
                        cand = (tone, octave)
                        # Bump boundary notes: these should be highly favored:
                        if cand not in candidate_list and cand not in adjacent_candidates:
                            # Insert at the beginning of this group:
                            adjacent_candidates.insert(0, cand)
                # Insert adjacent candidates at the top (but after any explicit boundary treatment):
                candidate_list = adjacent_candidates + candidate_list
                
                #? Candidate Group C: Diatonic scale tones:
                ordered_scale = order_scale(scale_notes)
                scale_candidates = [(n, octave) for n in ordered_scale if (n, octave) not in candidate_list]
                candidate_list.extend(scale_candidates)
                
                #? Candidate Group D: Chromatic fillers (with adjustments based on density):
                # Determine maximum allowed leap: if the chord density is high (many notes), allow only small intervals:
                density = current_segment[3] if current_segment else 1
                if density > 3:
                    # Steps only (a whole tone at most):
                    max_leap = 2
                else:
                    # Allow larger leaps if fewer notes to be played:
                    max_leap = 5
                
                # If is there a last note, get a directed chromatic scale based on the last note and an enhanced direction:
                if last_note:
                    # Use ewrs to favor continuation of the previous direction:
                    # In absence of an explicit previous direction, choose randomly:
                    direction = random.choice(["up", "down"]) if last_note is None else ewrs([direction, "up" if direction == "down" else "down"], base=1)
                    chroma_seq = get_directed_chromatic(last_note, direction)
                    # Filter chromatic fillers: only include those within the max_leap:
                    filtered = []
                    # Compute interval steps based on position in the chromatic list:
                    for i, cand in enumerate(chroma_seq):
                        if i <= max_leap and cand not in candidate_list:
                            filtered.append(cand)
                    candidate_list.extend(filtered)
                else:
                    # For the very first note, if no last note exists, add full chromatic fillers:
                    candidate_list.extend([(c, octave) for c in chromatic if (c, octave) not in candidate_list])
                
                # Debug: show candidate list for this note:
                if verbose:
                    print(f"\n[NOTE {mapping_index}] Candidate list:")
                    print(" * Group A (current chord tones):", chord_candidates)
                    if adjacent_candidates:
                        print(" * Group B (adjacent chord common tones):", adjacent_candidates)
                    print(" * Group C (scale tones):", scale_candidates)
                    print(" * Group D (chromatic fillers, limited by leap):", candidate_list[-len(filtered):] if last_note else "N/A")
                
                #? Final Selection: Use lwrs on the assembled candidate list:
                selected_candidate = lwrs(candidate_list)
                phrase_tuned.append(selected_candidate)

                if verbose:
                    print(" * Selected note:", selected_candidate)
                
                mapping_index += 1
            
            tuned_melody.extend(phrase_tuned)
        
        # Update the melody notes with the newly tuned notes:
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
                # Note overflows (or exactly fills) the upbeat;:
                # It starts in the upbeat (so already mapped as -1) and the overflow is carried:
                else:
                    leftover = new_up - upbeat_total
                    up_offset = upbeat_total
                    i += 1
                    break
        else:
            leftover = 0

        # Phase 2: Build the list of sound chords and their merged spaces;:
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
        # We use an accumulator (current_offset) relative to the current chord;:
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

            # The note's start time is current_offset. If current_offset is less than the chord's capacity;:
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
            
            # The note spans beyond the current chord;:
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