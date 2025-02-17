import random
import math
import copy

from Blocks.Note import Note
from Blocks.Phrase import Phrase
from Data.rythm.times import TIMES
from Selectors import ewrs


class Rythm:

    def __init__(self, signature: tuple, upbeat: int, params: dict, for_chords: bool = False):
        """

            This class allows to create an object that fits sentences (divided by syllables),
            into bars, giving ryhtmic figures to each syllable

            Parameters:
                - signature [tuple]: Time signature on the phrase. For example: (4, 4)
                - upbeat: [int]: Space occupied by the upbeat (anacrusis)

                - params [dict]: Dictionary containing the configuration parameters for the Simulated Annealing
                  algorithm and the fitting rules. The name of the variables are the name of the key:

                    Simulated Annealing Configuration:
                    -----------------------------------
                    - "initial_temperature" [float]:
                        Starting temperature for the annealing process
                        Higher values allow greater exploration of the solution space
                    
                    - "cooling_rate" [float]:
                        Rate at which the temperature decreases. 
                        Should be between 0 and 1. A value closer to 1 slows down cooling, allowing more exploration
                    
                    - "iterations" [int]:
                        Number of iterations to perform at each temperature level
                    
                    - "selection_bias" [int]:
                        Bias of selecting large notes over small notes (BASED ON THE ORDER OF NOTES)
                        THIS BIAS GET MORE WEIGTH OF SELECTION ACCORDING TO THE ORDER INTO "TIMES" of Data.rythm.times:
                        DEFAULT PREFERENCE TOP:
                        - "Whole"
                        - "Half"
                        - "Quarter"
                        - "Eighth"

                        - "Sixteenth"

                        - "Quarter Triplet"
                        - "Half Triplet"
                        - "Eighth Triplet"

                        - "Thirty-second"
                        
                        - "Sixteenth Triplet"
                        - "Sixty-fourth"

                        THIS BIAS PPARAMETER is int between 1 and 10
                            - 1: The bias between based on the order (Preference among the firsts towards the latests) is low
                            - 5: The bias between based on the order (Preference among the firsts towards the latests) is high
                            - 10: The bias between based on the order (Preference among the firsts towards the latests) is the highest
                    
                    - "dot_probability" [float]:
                        Probability of assigning a dotted rhythm to a note
                        Should be between 0 and 1

                    Importance Weights:
                    -------------------
                    These parameters determine the importance of each characteristic when evaluating a solution
                    They must be set between -100 and 100, following these guidelines:
                        - 0: The parameter is inactive and does not affect the evaluation
                        - -100: Maximally penalizes the characteristic, discouraging its presence
                        - 100: Maximally rewards the characteristic, encouraging its presence
                    
                    - "correct_fitting_importance" [int]:
                        Importance of fitting the syllables" durations exactly to the expected size
                    
                    - "beat_on_strong_beats_reward" [int]:
                        Reward for aligning syllables with strong beats:
                            - If stressed hits a strong beat, the double (no, 10 times) of reward
                            - If stressed hits semi-strong beat, the reward
                            - If not, not
                    
                    - "initial_rest_duration_reward" [int]:
                        Reward for having an initial rest before the first syllable
                    
                    - "initial_rest_anacrusis_penalty" [int]:
                        Penalty for an initial rest that creates an anacrusis (upbeat)
                    
                    - "final_rest_duration_reward" [int]:
                        Reward for ending with a rest, enhancing the cadence
                    
                    - "large_last_note_reward" [int]:
                        Reward for using a long duration for the last syllable (e.g., to emphasize the end)

                    Probabilities:
                    --------------
                    These probabilities control certain rhythmic choices and must be set between 0 and 100:

                    - "probability_find_initial_rest" [int]:
                        Probability of introducing an initial rest before the first syllable
                    
                    - "probability_find_final_rest" [int]:
                        Probability of adding a rest at the end of the phrase
                    
                    Uniformity:
                    -----------
                    - "uniformity" [int]:
                        Controls the repetitiveness of note durations
                            - 0: Maximum variety in note durations
                            - 100: Maximum uniformity, with repetitive note durations
                
                - for_chords [bool]: If true, do the logic of find the durations, but for chords. This logic
                  is too much easier and use basic parameters

                  FOR CHORDS RECOMENDATION WHILE USING METHOD "fit":
                    1. "sentence" should be a list of strings "X" for wich each "X"
                        is the amount of chords for each phrase. For example, if
                        there are 4 phrases, and 6 chords, and the distribution is:
                            - Phrase 1: 2 chords
                            - Phrase 2: 1 chord
                            - Phrase 3: 2 chords
                            - Phrase 4: 1 chord
                        And each phrase size is "4 bars", in order to get the
                        durations of each chord for the 6 chords progression,
                        then execute this method 4 times (1 for each phrase),
                        and, in each one pass as "sentences" a list of "X" based
                        on the amount of chords for each phrase
                    2. "bars" has to be the same length of "bars" used on each phrase
        """
        self.signature = signature
        self.upbeat = upbeat
        self.params = params
        self.TIMES = TIMES
        self.triplet_types = {3, 6, 12, 24}
        self.for_chords = for_chords

        # If it is for chords, some params are simplier:
        if for_chords:
            self.params["selection_bias"] = 5
            self.params["correct_fitting_importance"] = 100
            self.params["beat_on_strong_beats_reward"] = 100
            self.params["initial_rest_duration_reward"] = -100
            self.params["initial_rest_anacrusis_penalty"] = -100
            self.params["final_rest_duration_reward"] = -100
            self.params["large_last_note_reward"] = 0
            self.params["probability_find_initial_rest"] = 0
            self.params["probability_find_final_rest"] = 0
            self.params["uniformity"] = 80
    

    def preprocess_syllables(self, sentence: list):
        """
        Preprocess the sentence to apply synalepha. In this context the sentence is a list of tokens,
        where " " indicates a word boundary. Synalepha is applied as follows:
        
            - For each word (a sequence of tokens separated by " "), check whether the last character
              (ignoring the stress marker "*") of the last syllable of the previous word is a vowel and
              the first character of the first syllable of the current word is also a vowel
            - If so, merge these two syllables. If either syllable was stressed (contains "*"),
              ensure the merged syllable is marked as stressed
        
        Returns:
            [list]: Processed syllable strings (with synalepha applied)
        """
        vowels = set("aeiouAEIOU")
        words = []
        current_word = []
        for token in sentence:
            if token == " ":
                if current_word:
                    words.append(current_word)
                    current_word = []
            else:
                current_word.append(token)
        if current_word:
            words.append(current_word)

        processed_syllables = []
        for syl in words[0]:
            processed_syllables.append(syl)

        # For subsequent words, apply synalepha between the last syllable of the previous word
        # and the first syllable of the current word:
        for word in words[1:]:
            first_syl = word[0]
            prev_text = processed_syllables[-1]

            # Remove stress marker for checking vowels:
            prev_clean = prev_text.replace("*", "")
            first_clean = first_syl.replace("*", "")
            if prev_clean and first_clean and (prev_clean[-1] in vowels) and (first_clean[0] in vowels):
                merged = prev_text + first_syl
                if ("*" in prev_text) or ("*" in first_syl):
                    if "*" not in merged:
                        merged = "*" + merged
                processed_syllables[-1] = merged
            else:
                processed_syllables.append(first_syl)
            for syl in word[1:]:
                processed_syllables.append(syl)
        return processed_syllables
    

    def fit(self, sentence: list, bars: int):
        """
            Fits a sentence into an amount of bars using Simulated Annealing

            Parameters:
                - sentence [list[str]]: Sentence in wich each element is a syllable
                    - A " " (space) element means an empty space between words
                    - A syllable with a "*" means it is stressed (tonic syllable)
                - bars [int]: Amount of bars in which the sentence must be fitted

            Returns:

                IF Rythm.for_chords is TRUE:
                    - [Phrase]: Object Phrase, built by a grupo of Objects [Note] in which each note
                      has the setted time duration and a default note A of octave 4.
                
                IF Rythm.for_chords is FALSE:
                    - [tuple]: (initial_rest, syllable_figures, final_rest, dots)
                        - initial_rest [int]: Figure time id number of the silence before the phrase
                        - syllable_figures [list]: Note IDs (integers) assigned to each syllable (non-space)
                        - final_rest [int]: Figure id number of the silence after the phrase
                        - dots [list[bool]]: For each syllable, True if the note is dotted, else False
                            (The first and last entries correspond to the rests)
                
                    NOTE: FOR FIGURE TIME ID NUMBERS:

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

        # Preprocess sentence (apply synalepha):
        syllables = self.preprocess_syllables(sentence)
        num_syllables = len(syllables)

        # Calculate the total available "space" in our time system:
        denom = self.signature[1]
        if denom not in self.TIMES:
            raise ValueError(f"Wrong Time Signature: Denom {denom} must be one of {list(TIMES.keys())}")
        base_duration = self.TIMES[denom][1]
        beats_per_bar = self.signature[0]
        bar_space = beats_per_bar * base_duration
        total_space = bars * bar_space

        # Generate an initial candidate solution:
        candidate = self._generate_initial_solution(num_syllables)

        # Run simulated annealing:
        best_candidate = self._simulated_annealing(candidate, syllables, total_space)

        # Here best_candidate is a tuple: (notes, dots):
        notes, dots = best_candidate

        # Ensures the size of the phrase is not exceding:
        notes, dots, extra_silences = self._adjust_phrase_size((notes, dots), total_space)
        
        #/ If for chords return as simple list of strings:
        if self.for_chords:

            # Here notes[0] is the initial rest, notes[1:-1] are the syllable notes, notes[-1] is the final rest:
            return (notes[0], notes[1:-1], notes[-1], dots)

        #/ If not for chords returns as Phrase clase:
        else:
            phrase = Phrase()

            # Process the initial rest (index 0);
            # Use "X" in octave 0:
            if notes[0] != 0:
                note_obj = Note(time=notes[0], note="X", octave=0, dot=dots[0])
                phrase.add_end(note_obj)
            
            # Process the syllable notes (indices 1 to len(notes)-2)
            # Use "A" in octave 4 as default (because is just rythmic, not melodic yet):
            for idx in range(1, len(notes) - 1):
                note_obj = Note(time=notes[idx], note="A", octave=4, dot=dots[idx])
                phrase.add_end(note_obj)
            
            # Process the final rest (last index);
            # For rests, use "X" in octave 0:
            if notes[-1] != 0:
                note_obj = Note(time=notes[-1], note="X", octave=0, dot=dots[-1])
                phrase.add_end(note_obj)
            
            # Process the extra silence coins:
            for fig, dot in extra_silences:
                note_obj = Note(time=fig, note="X", octave=0, dot=dot)
                phrase.add_end(note_obj)
            
            return phrase
    

    def _generate_initial_solution(self, num_syllables: int):
        """
            Generates an initial candidate solution

            Returns a tuple (notes, dots) where:
                - notes [list]: List of length num_syllables + 2 (positions 0 and -1 are rests)
                - dots [list]: List of booleans of the same length, where each entry indicates if that note is dotted
            
            Each note is chosen using the exponential selection function. For syllable notes, a dot flag
            is assigned with probability given by self.params["dot_probability"]. For rests, dot is always False
        """

        allowed = list(self.TIMES.keys())
        x_param = self.params["selection_bias"]
        dot_prob = self.params["dot_probability"]

        notes = []
        dots = []

        # Generate initial rest:
        if random.random() > (self.params["probability_find_initial_rest"] / 100.0):
            initial_rest = 0
            dots.append(False)
        else:
            initial_rest = ewrs(allowed, x_param)
            dots.append(random.random() < dot_prob)
        notes.append(initial_rest)

        # Generate syllable notes:
        for _ in range(num_syllables):
            note = ewrs(allowed, x_param)
            notes.append(note)
            dots.append(random.random() < dot_prob)

        # Generate final rest:
        if random.random() > (self.params["probability_find_final_rest"] / 100.0):
            final_rest = 0
            dots.append(False)
        else:
            final_rest = ewrs(allowed, x_param)
            dots.append(random.random() < dot_prob)
        notes.append(final_rest)

        return (notes, dots)
    

    def _simulated_annealing(self, candidate: tuple, syllables: list, total_space: int):
        """
            Runs the simulated annealing loop
            The candidate is represented as a tuple: (notes, dots)
        """

        current = candidate
        current_score = self.rate(current, syllables, total_space)
        best = copy.deepcopy(current)
        best_score = current_score

        T = self.params["initial_temperature"]
        cooling_rate = self.params["cooling_rate"]
        iterations = self.params["iterations"]

        for _ in range(iterations):
            neighbor = self._neighbor(current)
            score = self.rate(neighbor, syllables, total_space)
            if score > current_score or random.uniform(0, 1) < math.exp((score - current_score) / T):
                current = neighbor
                current_score = score
                if score > best_score:
                    best = copy.deepcopy(neighbor)
                    best_score = score
            T *= cooling_rate

        print("Best:", best_score)
        return best
    

    def _neighbor(self, candidate: tuple):
        """
            Returns a neighboring candidate solution by randomly changing one element
            Candidate is a tuple (notes, dots)
        
            A random index is selected from 0 to len(notes)-1. For rests (indices 0 and -1),
            only the note ID is updated (the dot flag remains False). For a syllable note,
            both its note ID and dot flag are updated. Additionally, if the new note is a
            triplet type and there are at least two following syllable notes, the neighbor
            forces the next two syllable notes (and their dot flags) to match

            Returns:
                tuple: The neighbor candidate (notes, dots)
        """

        notes, dots = candidate
        new_notes = notes.copy()
        new_dots = dots.copy()

        index = random.randint(0, len(new_notes) - 1)
        allowed = list(self.TIMES.keys())
        x_param = self.params["selection_bias"]
        dot_prob = self.params["dot_probability"]

        # Possible 0 value for rest:
        if index == 0:
            # For initial rest, check probability:
            if random.random() > (self.params["probability_find_initial_rest"] / 100.0):
                new_notes[index] = 0
                new_dots[index] = False
            else:
                new_notes[index] = ewrs(allowed, x_param)
                new_dots[index] = random.random() < dot_prob
        
        elif index == len(new_notes) - 1:
            # For final rest, check probability:
            if random.random() > (self.params["probability_find_final_rest"] / 100.0):
                new_notes[index] = 0
                new_dots[index] = False
            else:
                new_notes[index] = ewrs(allowed, x_param)
                new_dots[index] = random.random() < dot_prob
        else:
            new_value = ewrs(allowed, x_param)
            new_notes[index] = new_value
            new_dots[index] = (random.random() < dot_prob)
            if new_value in self.triplet_types and (index <= len(new_notes) - 3):
                new_notes[index + 1] = new_value
                new_notes[index + 2] = new_value
                new_dots[index + 1] = new_dots[index]
                new_dots[index + 2] = new_dots[index]
        
        return (new_notes, new_dots)
    

    def _generate_compound_subdivisions(self, total: int):
        """
            Finds a random combination of duples, triples and quadruples meters
            to compund special times signatures as 5/4, 7/4, etc
        """
        parts = [2, 3, 4]
        partitions = []

        def rec(remaining, current):
            if remaining == 0:
                partitions.append(current.copy())
            else:
                for p in parts:
                    if p <= remaining:
                        current.append(p)
                        rec(remaining - p, current)
                        current.pop()
        rec(total, [])
        if partitions:
            return random.choice(partitions)
        else:
            return [total]
    

    def _adjust_phrase_size(self, candidate: tuple, total_space: int):
        """
            Adjusts the candidate (notes, dots) so that the total effective duration does not exceed total_space
            If the total effective duration (rounded) is larger than total_space, then:
            1. It inspects the last syllable note (the one before the final rest).
                - If that note is a triplet variant, it prints a warning and leaves the candidate unchanged
            2. Otherwise, it tries to reduce the last syllable note to a smaller effective figure
                (For example, a Quarter (4) without a dot (16) might be replaced by an Eighth (8) with a dot (12),
                or, if already dotted, by the same figure without the dot)
                It chooses the candidate modification that reduces the duration by as little as possible while bringing
                the overall total under the limit
            3. If after this reduction there is still a gap, it adjusts the final rest (or even inserts additional silence notes)
                so that the overall duration exactly matches the desired total_space
        """
        notes, dots = candidate

        def effective(note, dot):
            if note == 0:
                return 0
            base = self.TIMES[note][1]
            return base + (0.5 * base if dot else 0)

        # Compute total effective duration (rounded to integer):
        total_eff = round(sum(effective(n, d) for n, d in zip(notes, dots)))

        # No adjustment needed; return an empty extra silences list:
        if total_eff <= total_space:
            return (notes, dots, [])

        # 1: Adjust the last syllable note
        # Candidate structure: index 0 = initial rest, indices 1 .. -2 = syllable notes, index -1 = final rest:
        last_syllable_index = len(notes) - 2
        last_note = notes[last_syllable_index]
        last_dot = dots[last_syllable_index]

        # If the last syllable note is a triplet variant, do not adjust it:
        if last_note in self.triplet_types:
            print(f"WARNING: Phrase exceeds space of {total_space} and has triplet at the end")
            return (notes, dots, [])
        
        # Build candidate modifications for the last syllable note using allowed non-triplet figures (non-zero):
        current_last_eff = effective(last_note, last_dot)
        allowed_non_triplet = [fig for fig in self.TIMES.keys() if fig not in self.triplet_types and fig != 0]
        candidate_mods = []

        # Try both undotted and dotted versions for each candidate:
        for fig in allowed_non_triplet:
            for dot_candidate in [False, True]:
                cand_eff = self.TIMES[fig][1] + (0.5 * self.TIMES[fig][1] if dot_candidate else 0)

                # Only consider candidates that reduce the effective duration:
                if cand_eff < current_last_eff:
                    candidate_mods.append((fig, dot_candidate, cand_eff))
        if not candidate_mods:
            print("WARNING: Cannot reduce last note further to adjust phrase size")
            return (notes, dots, [])
        
        # Sort candidate modifications by effective duration (largest first, but still less than current):
        candidate_mods.sort(key=lambda x: x[2], reverse=True)
        chosen_mod = None
        for mod_fig, mod_dot, mod_eff in candidate_mods:
            new_total_eff = total_eff - current_last_eff + mod_eff
            if new_total_eff <= total_space:
                chosen_mod = (mod_fig, mod_dot, mod_eff)
                total_eff = new_total_eff
                break
        
        # None of the mods bring the total under; choose the one that reduces the duration the least:
        if chosen_mod is None:
            chosen_mod = candidate_mods[0]
            total_eff = total_eff - current_last_eff + chosen_mod[2]

        # Apply the chosen modification:
        notes[last_syllable_index] = chosen_mod[0]
        dots[last_syllable_index] = chosen_mod[1]

        # 2: Fill the Remaining Gap Using a Greedy Coin-Change Algorithm:
        # Remove the existing final rest (last element):
        notes.pop()
        dots.pop()
        total_eff = round(sum(effective(n, d) for n, d in zip(notes, dots)))
        gap = total_space - total_eff

        # For silence filling we use allowed non-triplet figures (and we use them undotted) because
        # their effective durations equal their base values;
        # Coins available (sorted descending by effective duration):
        coins = []
        for fig in sorted([fig for fig in self.TIMES.keys() if fig not in self.triplet_types and fig != 0],
                           key=lambda f: self.TIMES[f][1], reverse=True):
            coins.append((fig, False, self.TIMES[fig][1]))

        # Greedy coin-change: choose as few coins as possible to exactly fill the gap:
        extra_silences = []
        remaining = gap
        for coin in coins:
            coin_value = coin[2]
            count = remaining // coin_value
            if count > 0:
                extra_silences.extend([ (coin[0], coin[1]) ] * count)
                remaining -= coin_value * count
            if remaining == 0:
                break
        
        # Because the smallest coin (Sixty-fourth, effective 1) is available, remaining should be 0:
        if remaining != 0:
            print(f"WARNING: Gap of {remaining} could not be exactly filled with available silence figures.")

        # Rebuild final candidate: the adjusted notes/dots plus the extra silence coins;
        # Here we return the adjusted candidate and the extra silences separately:
        return (notes, dots, extra_silences)
    

    def rate(self, candidate: tuple, syllables: list, total_space: int):
        """
        Objective function to rate the candidate solution
        
        Parameters:
            - candidate (tuple): (notes, dots)
                - notes: list[int] of length num_syllables+2
                - dots: list[bool] of the same length, indicating whether each note is dotted
            - syllables (list[str]): Syllable strings corresponding to candidate note positions 1..-2
            - "total_space" [int]: Total required space (based on bars and time signature)
        
        The function:
            1. Penalizes the absolute difference between the computed space (summing the durations of all
               notes with an extra half note duration added when dotted) and total_space. (The computed space is rounded)
            2. Rewards placement of stressed syllables ("*") on strong beats (accounting for the upbeat)
            3. Rewards the initial and final rests according to their effective duration relative to the maximum (96)
            4. Rewards (or penalizes) uniformity among the syllable notes
            5. Adds a punctuation bonus if the final note is large, proportional to its effective duration
        
        Returns:
            float: A score (higher is better)
        """
        notes, dots = candidate
        score = 0

        #? ---------------------------------------------------------------------------------
        #? 1. Total space calculation
        #?    For each note, add its base duration and add half the duration if dotted:
        computed_space = 0
        for idx, note in enumerate(notes):
            if note == 0:
                eff = 0
            else:
                eff = self.TIMES[note][1]
                if dots[idx]:
                    eff += 0.5 * self.TIMES[note][1]
            computed_space += eff
        computed_space = round(computed_space)
        score -= abs(computed_space - total_space) * (self.params["correct_fitting_importance"] / 100.0)

        #? ---------------------------------------------------------------------------------
        #? 2. Reward stressed syllables on strong beats
        #? Gets the type of meter and the respective strong times for each:
        numerator = self.signature[0]
        denom = self.signature[1]
        base_duration = self.TIMES[denom][1]
        bar_space = numerator * base_duration

        # Meter classification:
        if numerator == 1:
            meter = "unique"
        elif numerator % 3 == 0:
            meter = "triple"
        elif numerator % 4 == 0:
            meter = "quadruple"
        elif numerator % 2 == 0:
            meter = "duple"
        else:
            meter = "compound"

        # Determine beat boundaries and beat strengths:
        # Determine beat boundaries and beat strengths:
        if meter == "unique":
            beat_boundaries = [0, bar_space]
            beat_strengths = ["strong"]
        elif meter == "duple":
            beat_boundaries = [0, bar_space / 2, bar_space]
            beat_strengths = ["strong", "weak"]
        elif meter == "triple":
            beat_boundaries = [0, bar_space / 3, 2 * bar_space / 3, bar_space]
            beat_strengths = ["strong", "weak", "semi-strong"]
        elif meter == "quadruple":
            beat_boundaries = [0, bar_space / 4, bar_space / 2, 3 * bar_space / 4, bar_space]
            beat_strengths = ["strong", "weak", "semi-strong", "weak"]
        elif meter == "compound":
            subdivisions = self._generate_compound_subdivisions(numerator)
            random.shuffle(subdivisions)
            beat_boundaries = [0]
            for part in subdivisions:
                beat_boundaries.append(beat_boundaries[-1] + part * base_duration)
            if len(subdivisions) == 1:
                beat_strengths = ["strong"]
            elif len(subdivisions) == 2:
                beat_strengths = ["strong", "weak"]
            elif len(subdivisions) == 3:
                beat_strengths = ["strong", "weak", "semi-strong"]
            else:
                beat_strengths = ["strong", "weak", "semi-strong"] + ["weak"] * (len(subdivisions) - 3)
                # Ensure no more than two consecutive weak beats:
                for i in range(1, len(beat_strengths) - 1):
                    if beat_strengths[i - 1] == "weak" and beat_strengths[i] == "weak" and beat_strengths[i + 1] == "weak":
                        beat_strengths[i] = "semi-strong"

        # Process syllable notes:
        # upbeat_duration = self.upbeat * base_duration
        # bar_space = self.signature[0] * base_duration
        upbeat_duration = self.upbeat * base_duration
        cumulative_time = -upbeat_duration

        if notes[0] != 0:
            initial_rest_duration = self.TIMES[notes[0]][1]
            if dots[0]:
                initial_rest_duration += 0.5 * self.TIMES[notes[0]][1]
            cumulative_time += initial_rest_duration

        # For each syllable, compute its onset (effective) position and apply a continuous reward if stressed:
        for idx, syl in enumerate(syllables):

            # The effective onset of the syllable is given by cumulative_time modulo the bar length:
            effective_position = cumulative_time % bar_space

            # Identify which beat this effective_position falls into:
            beat_index = None
            for i in range(len(beat_boundaries) - 1):
                if beat_boundaries[i] <= effective_position < beat_boundaries[i + 1]:
                    beat_index = i
                    break
            if beat_index is None:
                beat_index = len(beat_boundaries) - 2

            beat_start = beat_boundaries[beat_index]
            beat_duration = beat_boundaries[beat_index + 1] - beat_boundaries[beat_index]
            offset = effective_position - beat_start

            # Tolerance of 15% of beat duration:
            tolerance = 0.02 * beat_duration

            # Compute a continuous reward factor that decreases linearly with offset:
            if "*" in syl:
                
                reward_factor = max(0, (tolerance - offset) / tolerance)
                if beat_strengths[beat_index] == "strong":
                    score += 10.0 * reward_factor * (self.params["beat_on_strong_beats_reward"] / 100.0)
                elif beat_strengths[beat_index] == "semi-strong":
                    score += 1.0 * reward_factor * (self.params["beat_on_strong_beats_reward"] / 100.0)

            # Compute effective duration of the current syllable note:
            note_val = notes[idx + 1]
            if note_val == 0:
                eff = 0
            else:
                eff = self.TIMES[note_val][1]
                if dots[idx + 1]:
                    eff += 0.5 * self.TIMES[note_val][1]

            # Update cumulative_time AFTER processing the onset of this syllable:
            cumulative_time += eff

        #? ---------------------------------------------------------------------------------
        #? 3. Initial Rest Anacrusis Penalty
        #?    If an upbeat is present (upbeat != 0), any effective duration in the initial,
        #?    rest is undesirable:
        if self.upbeat != 0:
            if notes[0] == 0:
                initial_eff = 0
            else:
                initial_eff = self.TIMES[notes[0]][1]
                if dots[0]:
                    initial_eff += 0.5 * self.TIMES[notes[0]][1]
            score += initial_eff * (self.params["initial_rest_anacrusis_penalty"] / 100.0)

        #? ---------------------------------------------------------------------------------
        #? 4. Rewards for initial and final rests
        #?    Compute the effective duration of each rest (including dot bonus),
        #?    compare with 96 (the maximum effective duration: dotted whole note),
        #?    and add a proportional reward:
        if notes[0] == 0:
            initial_eff = 0
        else:
            initial_eff = self.TIMES[notes[0]][1]
            if dots[0]:
                initial_eff += 0.5 * self.TIMES[notes[0]][1]
        
        if self.upbeat == 0:
            score += (initial_eff / 96.0) * self.params["initial_rest_duration_reward"]

        if notes[-1] == 0:
            final_eff = 0
        else:
            final_eff = self.TIMES[notes[-1]][1]
            if dots[-1]:
                final_eff += 0.5 * self.TIMES[notes[-1]][1]
        score += (final_eff / 96.0) * self.params["final_rest_duration_reward"]

        #? ---------------------------------------------------------------------------------
        #? 5. Uniformity bonus (or variety penalty):
        #?    Reward successive syllable notes that are the same, penalize differences:
        uniform_bonus = 0
        for i in range(1, len(notes) - 1):
            if i < len(notes) - 2 and notes[i] == notes[i + 1]:
                uniform_bonus += 1
            else:
                uniform_bonus -= 1
        score += uniform_bonus * ((100 - self.params["uniformity"]) / 100.0)

        #? ---------------------------------------------------------------------------------
        #? 6. Punctuation reward for a large last note:
        #?    Reward if the final note (the final rest) is large, based on its effective duration:
        last_note = notes[-2]
        if last_note == 0:
            last_eff = 0
        else:
            last_eff = self.TIMES[last_note][1]
            if dots[-2]:
                last_eff += 0.5 * self.TIMES[last_note][1]
        score += (last_eff / 96.0) * self.params["large_last_note_reward"]

        return score