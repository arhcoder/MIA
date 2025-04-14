from Blocks.Melody import Melody
from Blocks.Harmony import Harmony

import random
from Selectors import lwrs, ewrs
from Key import notes_of_scale


class Melodic:
    
    def __init__(self, melody: Melody, harmony: Harmony):
        self.melody = melody
        self.harmony = harmony

    def tune_melody(self, shapes: list, octave: int = 4, max_jump: int = 12, verbose: bool = False):
        """
            Tunes the melody based on a revised hierarchical LWRS algorithm that considers
            contextual importance of each note within a phrase and its harmonic context

            [LWRS Algorithm takes a list of elements and randomly selects one of them, giving
            higher probability to items at the top of the list]

            This function is intended for Harmfirst models, where harmony is generated first
            and melody adapts to it. The process takes tonal music principles of hierarchy
            and classifies the notes of the melody by importances:
                - Structural
                - Main
                - Important
                - Step

            Notes are classified based on their context within a phrase using 4 properties:
                - "long": note duration is >= 50% of the bar size
                - "strong": note begins exactly when a chord changes
                - "first_of_phrase": is the first note of a phrase
                - "last_of_phrase": is the last note of a phrase

            The classification hierarchy:
                1. Structural: if ("strong" and "long") or ("strong" and "first") or ("long" and "last")
                    - LWRS Selection list: [Chord notes], ordered with highest pitch first

                2. Main: if only "strong", or ("strong" and "last")
                    - LWRS Selection list: [Chord notes + Scale notes excluding duplicates]

                3. Important: if only "long" or only "first" or only "last"
                    - LWRS Selection list: [Chord notes + Scale notes excluding chord tones]

                4. Step: all others
                    - LWRS Selection list: [Chord notes + Scale notes excluding chord tones +
                      Rest of notes not in chromatic scale]
            
            Additionally, on the selection it order the elements on the list to favor the proximity to the
            objective notes, trying to give the direction according to a "shape" that could be:
                - "arch": up-down-up
                - "valley": down-up-down
                - "rise": up-up-up
                - "fall": down-down-down
                - "random": Choose one of the previous shapes randomly

            Parameters:
                - shapes [list[str]]: List of shape names for each phrase: With possible values:
                    "arch", "valley", "rise", "fall"
                    NOTE: The length of this list must be equal to the number of phrases in the melody
                - octave [int]: Initial octave for starting melody generation (default is 4)
                - max_jump [int]: Maximum allowed interval jump (default is 12 semitones)
                - verbose [bool]: If True, prints additional information during processing (default is False)

            Process:
                1. Uses "map_note2chords()" to map melody notes to their corresponding chords:
                    a. mapping_notes [list[int]]: Index list where each entry maps a melody note to a chord index,
                        [-1, 0, 0, 1, 1] means the first note is upbeat (maps to last chord), next two to chord 0, etc
                    b. sound_chords [list[Chord]]: Chord objects for each segment with access to .notes (pitch and octave)

                2. Groups notes by phrases

                3. For each phrase:

                    4. For each note:
                        a. Calculates its context using properties: strong, long, first_of_phrase, last_of_phrase
                        b. Classifies it into one of four categories based on these features
                        c. Builds selection list using the rules above and sorts items based on pitch distance and direction

                        d. Applies optional pitch constraints:
                            - Adjusts target octave relative to prior note to keep within melodic shape
                            - Applies max jump limit
                        
                        e. Uses LWRS to select a note from the list
                        f. Appends selected (note, octave) tuple to final tune list

                5. After all phrases:
                    - Iterates over melody notes in the Melody object
                    - Assigns each selected (note, octave) to replace original values (skipping silences)

                Returns:
                    - [Melody]: Modified Melody object with tuned note names and octaves applied
        """

        #? 1. Map each melody note to its corresponding chord:
        mapping, sound_chords = self.map_note2chords()

        #* Prepare scale and chromatic lookup tables:
        scale_tones = notes_of_scale(self.harmony.key[0], self.harmony.key[1])
        chromatic_scale = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        semitone_index = {name: idx for idx, name in enumerate(chromatic_scale)}

        #* Helper functions:
        def get_directed_chromatic_scale(last_pitch: tuple, direction: str):
            """
                Builda a chromatic list of (note_name, octave) stepping from last_pitch
                in "up" or "down" direction, spanning one octave
            """
            note_name, note_octave = last_pitch
            start_idx = chromatic_scale.index(note_name)
            directed = []
            if direction == "up":
                for step in range(13):
                    idx = (start_idx + step) % 12
                    octave_shift = (start_idx + step) // 12
                    directed.append((chromatic_scale[idx], note_octave + octave_shift))
            else:
                for step in range(13):
                    idx = (start_idx - step) % 12
                    # floor‑division on a negative numerator gives you -1 once you cross zero:
                    octave_shift = (start_idx - step) // 12
                    directed.append((chromatic_scale[idx], note_octave + octave_shift))
            return directed

        def semitone_distance(pitch_a: tuple, pitch_b: tuple):
            """
                Compute absolute semitone distance between two pitches
            """
            index_a = pitch_a[1] * 12 + semitone_index[pitch_a[0]]
            index_b = pitch_b[1] * 12 + semitone_index[pitch_b[0]]
            return abs(index_a - index_b)
        
        
        def clamp(pitch: tuple):
            """
                Ensures notes are always in a limit of octaves
                Between octaves 2 and 7
            """
            name, octv = pitch
            return (name, max(2, min(7, octv)))

        #? 2. Phrase context metadata for two-pass processing:
        mapping_index = 0
        phrases_info = []
        for phrase in self.melody.phrases:

            # Gather only audible (non-rest) notes:
            audible_notes = [n for n in phrase.notes if n.note != "X"]
            if not audible_notes:

                # No audible notes: still record for alignment:
                phrases_info.append({
                    "phrase": phrase,
                    "audible_notes": [],
                    "chord_sequence": [],
                    "note_indices": []
                })
                continue

            chord_sequence = []
            note_indices = []
            for _ in audible_notes:
                chord_idx = mapping[mapping_index]
                chord_obj = sound_chords[-1] if chord_idx == -1 else sound_chords[chord_idx]
                chord_sequence.append(chord_obj)
                note_indices.append(mapping_index)
                mapping_index += 1

            phrases_info.append({
                "phrase": phrase,
                "audible_notes": audible_notes,
                "chord_sequence": chord_sequence,
                "note_indices": note_indices
            })

        #? 3. Making pitches for each phrase:
        all_selected_pitches = []
        for i, phrase_data in enumerate(phrases_info):
            audible_notes = phrase_data["audible_notes"]
            if not audible_notes:
                continue
            num_notes = len(audible_notes)

            #? 4. For each audible note:
            note_roles = []
            for idx, note_obj in enumerate(audible_notes):

                #* a. Determine characteristics:
                is_first = (idx == 0)
                is_last = (idx == num_notes - 1)
                bar_space = self.melody.space / self.melody.bars_amount
                is_long = (note_obj.space / bar_space >= 0.5)
                map_idx = phrase_data["note_indices"][idx]
                prev_map = mapping[map_idx - 1] if map_idx > 0 else None
                is_strong = (prev_map is None or mapping[map_idx] != prev_map)

                #* b. Classify each note's role based on context:
                if (is_strong and is_long) or (is_strong and is_first) or (is_long and is_last):
                    note_roles.append("structural")
                elif is_strong or (is_strong and is_last):
                    note_roles.append("principal")
                elif is_long or is_first or is_last:
                    note_roles.append("important")
                else:
                    note_roles.append("step")
            
            #* Shape of the phrase: 
            if shapes[i] == "random":
                contour_shape = random.choice(["arch", "valley", "rise", "fall"])
            else:
                contour_shape = shapes[i]

            #* Identify indices of structural notes:
            structural_indices = [i for i, role in enumerate(note_roles) if role == "structural"]

            #* PASS 1: Place structural anchors according to contour:
            structural_anchors = {}
            if structural_indices:
                for rank, pos in enumerate(structural_indices):
                    chord_obj = phrase_data["chord_sequence"][pos]

                    # Build chord-tone candidates across allowed octaves:
                    chord_tone_candidates = [
                        (tone.note, octv)
                        for tone in chord_obj.notes
                        for octv in [octave]
                    ]
                    # Sort by absolute pitch:
                    chord_tone_candidates.sort(key=lambda p: p[1] * 12 + semitone_index[p[0]])

                    # Relative position along the phrase (0=start .. 1=end):
                    rel_pos = rank / (len(structural_indices) - 1) if len(structural_indices) > 1 else 0

                    # Map rel_pos to contour height:
                    if contour_shape == "arch":
                        height = 4 * rel_pos * (1 - rel_pos)
                    elif contour_shape == "valley":
                        height = 1 - 4 * rel_pos * (1 - rel_pos)
                    elif contour_shape == "rise":
                        height = rel_pos
                    # Fall:
                    else:
                        height = 1 - rel_pos

                    # Select the anchor pitch at the computed height:
                    idx_choice = int(round(height * (len(chord_tone_candidates) - 1)))
                    structural_anchors[pos] = chord_tone_candidates[idx_choice]

            #* PASS 2: Fill in the remaining notes:
            phrase_selection = [None] * num_notes

            # Place structural anchors first:
            for pos, pitch in structural_anchors.items():
                phrase_selection[pos] = pitch

            # Fill segments between anchors:
            boundary_positions = [-1] + structural_indices + [num_notes]
            for seg_idx in range(len(boundary_positions) - 1):
                start_pos = boundary_positions[seg_idx]
                end_pos = boundary_positions[seg_idx + 1]
                for j in range(start_pos + 1, end_pos):
                    if phrase_selection[j] is not None:
                        continue

                    # Determine last placed pitch:
                    if j - 1 >= 0 and phrase_selection[j - 1] is not None:
                        last_pitch = phrase_selection[j - 1]
                    # First filler: choose from chord-tones then scale-tones:
                    else:
                        chord_obj = phrase_data["chord_sequence"][j]
                        chord_candidates = [(t.note, octave) for t in chord_obj.notes]
                        scale_candidates = [
                            (tone, octave)
                            for tone in scale_tones
                            if tone not in [c for c,_ in chord_candidates]
                        ]
                        candidate_list = chord_candidates + scale_candidates
                        selected = lwrs(candidate_list)
                        phrase_selection[j] = selected
                        last_pitch = selected
                        continue

                    # Find next structural anchor as target (if any):
                    next_anchor = None
                    for pos in structural_indices:
                        if pos > j:
                            next_anchor = phrase_selection[pos]
                            break

                    # Choose direction, biasing toward next anchor if present:
                    if next_anchor:
                        sem_diff = (
                            next_anchor[1] * 12 + semitone_index[next_anchor[0]]
                            - (last_pitch[1] * 12 + semitone_index[last_pitch[0]])
                        )
                        preferred_dir = "up" if sem_diff > 0 else "down"
                        direction = ewrs([preferred_dir, "up" if preferred_dir == "down" else "down"], base=2)
                    else:
                        direction = random.choice(["up", "down"])

                    # Build directed chromatic scale from last_pitch:
                    directed_chromatic_scale = get_directed_chromatic_scale(last_pitch, direction)

                    # Possible candidates on the list:
                    chord_tone_names = [t.note for t in phrase_data["chord_sequence"][j].notes]
                    chord_candidates = [p for p in directed_chromatic_scale if p[0] in chord_tone_names]
                    scale_candidates = [p for p in directed_chromatic_scale if p[0] in scale_tones and p not in chord_candidates]
                    chromatic_candidates = [p for p in directed_chromatic_scale if p not in chord_candidates and p not in scale_candidates]

                    #* c. Builds selection list with candidates, according to note classification:
                    role = note_roles[j]
                    if role == "principal":
                        candidate_list = chord_candidates + scale_candidates + chord_candidates
                    elif role == "important":
                        candidate_list = chord_candidates + scale_candidates
                    else:
                        candidate_list = chord_candidates + scale_candidates + chromatic_candidates

                    #* d. Enforces maximum interval jump:
                    filtered_candidates = [p for p in candidate_list if semitone_distance(p, last_pitch) <= max_jump]

                    #* e. Selects pitch using LWRS:
                    selected = lwrs(filtered_candidates)
                    selected = clamp(selected)
                    if verbose:
                        print(f"\nPhrase {i}, Note {j} - {role.upper()}:\n - Last pitch: {last_pitch}\n - Selection list: {filtered_candidates}\n - Selected: {selected}")
                        print(f" - Is strong: {is_strong}\n - Is long: {is_long}\n - Is first: {is_first}\n - Is last: {is_last}")
                    
                    #* f. Append selected pitch:
                    phrase_selection[j] = selected
                    last_pitch = selected

            # Append this phrase's selected pitches:
            all_selected_pitches.extend(phrase_selection)

        #? 5. Writes back into Melody object:
        write_idx = 0
        for phrase in self.melody.phrases:
            for note_obj in phrase.notes:
                if note_obj.note != "X":
                    note_obj.note, note_obj.octave = all_selected_pitches[write_idx]
                    write_idx += 1

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