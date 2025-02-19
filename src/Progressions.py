import random, re
from Key import chords_of_scale, degree_of_chord, notes_of_scale, notes_of_chord
from Rythm import Rythm
from Selectors import lwrs, cwrs
from Blocks.Harmony import Harmony
from Blocks.Chord import Chord
from Data.harmony.chords import patterns, classifications
from Data.key.scales import diatonics


class GeneticProgression:

    def __init__(self, params: dict):
        """
            Class to construct Chord Progressions with Genetic Algorithm
            [CHECK THE FILE "conf.py" TO SEE THE DEFAULT CONFIGURATIONS OF params DICT]

            Parameters:
                - params [dict]: Dictionary containing the configuration parameters for the Genetic
                  Algorithm and chord progression rules. The varaible names are the keys of dictionary

                    Genetic Algorithm Configuration:
                    ---------------------------------
                    - "population_size" [int]:
                        Number of chord progressions in each generation 
                    
                    - "generations_per_chord" [int]:
                        Number of generations to evolve for each chord in the progression
                    
                    - "mutation_rate" [float]:
                        Probability of mutation in the genetic algorithm 
                        A value near 1 (100%) increases the likelihood of rare chords but may result in unstable progressions
                    
                    - "tournament_size" [int]:
                        Number of candidates participating in the selection tournament 
                        Higher values increase selective pressure
                    
                    - "elitism_size" [int]:
                        Number of top-performing chord progressions carried over to the next generation
                    
                    Chord Complexity:
                    -----------------
                    - "chords_complexity" [int]:
                        Determines how complex the chords will be in the progression:
                            - 0: Uses only basic major and minor chords (and occasionally diminished)
                            - 100: Uses complex chords frequently (e.g., maj11, m7b5, 7#5)
                            - Values above 50 lean towards jazzier chords
                        Should be between 0 and 100

                    Scoring Preferences:
                    --------------------
                    This section controls how the fitness of a chord progression is calculated. Each value represents a weight or penalty for the corresponding rule:

                    - "first_chord_is_tonic" [int (AMOUNT OF POINTS)]:
                        Bonus if the first chord is the tonic (I) chord

                    - "first_chord_not_tonic_penalty" [int (AMOUNT OF POINTS)]:
                        Penalty if the first chord is not the tonic
                    
                    - "last_chord_is_dominant" [int (AMOUNT OF POINTS)]:
                        Bonus if the last chord is a dominant (V) chord
                    
                    - "last_chord_not_dominant_penalty" [int (AMOUNT OF POINTS)]:
                        Penalty if the last chord is not dominant
                    
                    - "first_last_combined_bonus" [int (AMOUNT OF POINTS)]:
                        Bonus for having a tonic as the first chord and a dominant as the last chord
                    
                    - "tonic_on_last_bonus" [int (AMOUNT OF POINTS)]:
                        Bonus if the last chord is the tonic, ensuring resolution
                    
                    - "secondary_dominants" [int (AMOUNT OF POINTS)]:
                        Bonus for using secondary dominants to add harmonic interest
                    
                    - "cadence" [int (AMOUNT OF POINTS)]:
                        Bonus for creating standard cadences (e.g., V-I, IV-I)
                    
                    - "scale_membership_multiplier" [int (AMOUNT OF POINTS)]:
                        Multiplier for chords that belong to the key's scale
                    
                    - "diversity_multiplier" [int (AMOUNT OF POINTS)]:
                        Multiplier for harmonic diversity within the progression
                    
                    - "voice_leading_multiplier" [int (AMOUNT OF POINTS)]:
                        Multiplier for smooth voice leading between chords
                    
                    - "sus_before_major" [int (AMOUNT OF POINTS)]:
                        Bonus for using suspended chords before resolving to major chords
                    
                    - "sus_nonresolution_penalty" [int (AMOUNT OF POINTS)]:
                        Penalty for using suspended chords without resolving them
                    
                    - "complexity_penalty_factor" [int (AMOUNT OF POINTS)]:
                        Penalty for overly complex chords if chords_complexity is low
                    
                    - "dominant_seventh_bonus" [int (AMOUNT OF POINTS)]:
                        Bonus for using dominant seventh chords, enhancing harmonic tension
                    
                    - "tension_resolution" [int (AMOUNT OF POINTS)]:
                        Bonus for resolving harmonic tension effectively
                    
                    - "leading_tone_resolution_bonus" [int (AMOUNT OF POINTS)]:
                        Bonus for resolving leading tones to the tonic
                    
                    Extra Cadences:
                    ---------------
                    - "cadence_deceptive" [int (AMOUNT OF POINTS)]:
                        Bonus for using deceptive cadences (e.g., V-vi)
                    
                    - "cadence_64" [int (AMOUNT OF POINTS)]:
                        Bonus for using cadential 6/4 chords before resolving
                    
                    - "cadence_semicadence" [int (AMOUNT OF POINTS)]:
                        Bonus for using semicadences (e.g., ending on V)
                    
                    - "picardy_third_bonus" [int (AMOUNT OF POINTS)]:
                        Bonus for using a Picardy third (ending on a major tonic in a minor key)
        """

        # Load GA parameters from config file:
        self.params = params
        self.notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.population = []
        self.key = None
        self.scale = None
    
    
    #? MAIN FUNCTION TO CREATE A PROGRESSION:
    def create(self, chords: int, key: str, scale: str):
        """
            Main method to get a progression acoording to a key, with Genetic Algorithm

            Parameters:
                - chords [int]: Amount of chords on the progression
                - key [str]: Name of the key
                    It could be some of this values:
                    ["C", "D", "E", "F", "G", "A", "B"]
                    Or some of this values:
                    ["C#", "D#", "F#", "G#", "A#"] or ["Db", "Eb", "Gb", "Ab", "Bb"]
                - scale [str]: Name of the type of scale
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

            Returns: Best solution of chord progression in format:
                list[tuple] in which each tuple has:
                    - [str] Name of root note on the chord
                    - [str] Type of the chord
                    - [str] Degree of the chord on the key
                    - [int] Inversion (if 0, it is fundamental state)
                    Example of progression:
                    [
                        ("C", "", "I", 0): C major as I degree on fundamental state: C-E-G
                        ("A", "m", iv, 0): A minor as iv degree on fundamental state: A-C-E
                        ("F", "", VI, 1): F major as VI degree on first inversion: A-C-F
                        ("G", "7", V, 2): G major with minor 7th on second inversion: D-F-G-B
                    ]
        """
        #? Some validations:
        if not isinstance(chords, int) or chords < 2:
            raise ValueError("\"chords\" must be integer higher than 1")
        
        flats_to_sharps = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        key = key.capitalize()
        if not key in flats_to_sharps.keys() and not key in self.notes:
            raise ValueError(f"\"key\" must be any from {self.notes + list(flats_to_sharps.keys())}")
        
        scale = scale.lower()
        if not scale in diatonics.keys():
            raise ValueError(f"\"scale\" must be any from {list(diatonics.keys())}")
        self.scale = scale

        #? Flats to sharp:
        if key in flats_to_sharps:
            key = flats_to_sharps[key]
        self.key = key


        #/ GENETIC ALGORITHM /#
        #? Initializate population:
        self.population = self.initialize(self.params["population_size"], chords, key, scale)

        #? Generaton steps:
        for _ in range(int(self.params["generations_per_chord"] * chords)):

            #? Evaluation of progressions:
            evaluated = [(self.rate(ind), ind) for ind in self.population]
            evaluated.sort(reverse=True, key=lambda x: x[0])
            
            #? Elitism: keep top solutions:
            elite = [ind for (_, ind) in evaluated[:self.params["elitism_size"]]]
            
            #? New self.population:
            children = []
            while len(children) < self.params["population_size"] - self.params["elitism_size"]:
                parent1 = self.selection()
                parent2 = self.selection()
                child1, child2 = self.crossover(parent1, parent2)
                children.append(self.mutate(child1, key, scale))
                children.append(self.mutate(child2, key, scale))
            self.population = elite + children[:self.params["population_size"] - self.params["elitism_size"]]
        
        
        #/ Returns just the best individual:
        #? Returns as list[tuple] in which each tuple has:
        #*  - [str] Name of root note on the chord
        #*  - [str] Type of the chord
        #*  - [str] Degree of the chord on the key
        #*  - [int] Inversion (if 0, it is fundamental state)
        return max(self.population, key=lambda x: self.rate(x))
    

    #? Initialization with LWRS:
    def initialize(self, size: int, chords: int, key: str, scale: str):

        #* Step 1: Get chords_in the key/scale (ignore degree):
        scale_chords = chords_of_scale(key, scale)
        chords_in = [(root, ctype) for root, ctype, _ in scale_chords]

        #* Step 2: Generate chords_out (maj/min not in chords_in):
        chords_out = []
        for note in self.notes:

            # Check if major chord is in scale:
            if (note, "") not in chords_in:
                chords_out.append((note, ""))

            # Check if minor chord is in scale:
            if (note, "m") not in chords_in:
                chords_out.append((note, "m"))

        #* Step 3: Prepare in/out selection list for lwrs algorithm:
        in_out_list = ["in"] * 7 + ["out"] * 5

        #* Step 4: Generation of population:
        population = []
        for _ in range(size):

            progression = []
            for _ in range(chords):

                #* Step 5: Selection of the chord in basic mode (just major or minor or dim or aug)
                #? It uses Logarithmic Random Weighted Selector (lwrs) to select if the chord is on the key or not:
                selection = lwrs(in_out_list)
                if selection == "in":
                    root, ctype = random.choice(chords_in)
                else:
                    root, ctype = random.choice(chords_out)

                #* Step 6: Selects the chord complexity based on the parameter "chords_complexity";
                #* It Apply chord complexity modifications to major/minor or augmented/diminished chords:
                #? It takes the complexity, with the algorithm Complexity Weighted Random Selector (cwrs);
                #? This method gives probability of chord complexity according to:
                #?  1. If complexity is 0, the the 100% times it will keep just major/minor (or aumented/diminished)
                #?      chords (first element on the list has 100%)
                #?  2. If complexity is up to 50, then the first element (just major/minor) (or aumented/diminished)
                #?      has the 50% to appear, the rest of chords has more probability
                #?  3. If complexity is 100, then all the chord types has the same probabiility to be selected
                #/ If complexity is near to 100, the chords will be more jazzy, if near to 0, more simle chords

                # First get the category (major/minor) (aumented/diminished):
                category = classifications[ctype]
                same_category = [t for t in classifications if classifications[t] == category]

                # Select new chord type based on complexitty:
                ctype = cwrs(same_category, self.params["chords_complexity"])

                #* Step 7: Determine degree:
                degree = degree_of_chord(root, ctype, key, scale)

                #* Step 9: Select inversion:
                inversion = lwrs([*range(0, len(patterns[ctype]))])

                #* Step 10: Build chord tuple and add to progression:
                chord_tuple = (root, ctype, degree, inversion)
                progression.append(chord_tuple)

            population.append(progression)

        return population
    

    #? Tournament selection:
    def selection(self):
        contestants = random.sample(self.population, self.params["tournament_size"])
        return max(contestants, key=lambda x: self.rate(x))
    
    
    #? Single point crossover:
    def crossover(self, parent1, parent2):
        crossover_point = random.randint(1, len(parent1)-1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        return child1, child2
    

    #? Replace completly some random chord on the progression:
    def mutate(self, solution, key, scale):
        if random.random() < self.params["mutation_rate"]:
            idx = random.randint(0, len(solution)-1)
            new_root = random.choice(self.notes)
            new_type = random.choice(list(patterns.keys()))
            new_degree = degree_of_chord(new_root, new_type, key, scale)
            new_inversion = random.choice([*range(0, len(patterns[new_type]))])
            solution = solution[:idx] + [(new_root, new_type, new_degree, new_inversion)] + solution[idx+1:]
        return solution
    

    #? To see the whole population in order:
    def all(self):
        evaluated = [(self.rate(ind), ind) for ind in self.population]
        evaluated.sort(reverse=True, key=lambda x: x[0])
        return evaluated
    

    #! CHORDS QUALITY EVALUATION !#


    #/ OBJECTIVE FUNCTION /#
    #* THE LOGIC TO GET BETTER CHORDS *#
    def rate(self, progression):
        """
            Rates a chord progression (a list of chord tuples) and returns a total score

            NOTE:
            - Each chord is a tuple with: (root: str, chord type: str, scale degree: str, inversion: int)
            - The scale degree string may contain a "*" (meaning the chord is out-of-key)
            - The extra symbols (accidentals, °, +, or parenthetical content as (maj7))
        """

        #! MODIFY THE FIILE conf.py TO THE SCORING PREFERENCES:
        scoring_prefs = self.params["scoring_prefs"]

        #? Another functions:
        def clean_degree(degree_str):
            """
                Remove asterisks, accidentals, symbols, and any parenthetical text from the degree string
                For example, "*bI (maj7)" becomes "I"
            """
            without_asterisk = degree_str.replace("*", "")
            without_parentheses = re.sub(r"\(.*?\)", "", without_asterisk)
            cleaned = re.sub(r"[#b°+]", "", without_parentheses)
            return cleaned.strip()

        def note_distance(note1, note2, note_list):
            """
                Computes the minimal semitone distance between note1 and note2, using the ordering in note_list
            """
            i1 = note_list.index(note1)
            i2 = note_list.index(note2)
            diff = abs(i1 - i2)
            return min(diff, 12 - diff)

        #? EVALUATION:
        quality_scores = {}

        #? 1. First chord is tonic:
        first_chord = progression[0]
        first_degree = first_chord[2]
        cleaned_first = clean_degree(first_degree)
        if "*" in first_degree:
            quality_scores["first_chord_is_tonic"] = scoring_prefs["first_chord_not_tonic_penalty"]
        else:
            quality_scores["first_chord_is_tonic"] = (
                scoring_prefs["first_chord_is_tonic"] 
                if cleaned_first.upper() == "I" 
                else scoring_prefs["first_chord_not_tonic_penalty"]
            )

        #? 2. Last chord is dominant (V):
        last_chord = progression[-1]
        last_degree = last_chord[2]
        cleaned_last = clean_degree(last_degree)
        if "*" in last_degree:
            quality_scores["last_chord_is_dominant"] = scoring_prefs["last_chord_not_dominant_penalty"]
        else:
            quality_scores["last_chord_is_dominant"] = (
                scoring_prefs["last_chord_is_dominant"]
                if " ".join(re.findall("[a-zA-Z]+", cleaned_last)).upper() == "V"
                else scoring_prefs["last_chord_not_dominant_penalty"]
            )

        #? 2a. Extra bonus: if first chord is tonic and last chord is dominant:
        bonus_first_last = 0
        if (cleaned_first.upper() == "I") and (" ".join(re.findall("[a-zA-Z]+", cleaned_last)).upper() == "V"):
            bonus_first_last += scoring_prefs["first_last_combined_bonus"]
        
        #? Also bonus if the last chord is itself tonic:
        if cleaned_last.upper() == "I":
            bonus_first_last += scoring_prefs["tonic_on_last_bonus"]
        quality_scores["first_last_bonus"] = bonus_first_last

        #? 3. Reward if a chord is preceded by its respective fifth (Secondary Dominants):
        dominant_precedes_score = 0.0
        for i in range(1, len(progression)):
            prev_root = progression[i - 1][0]
            curr_root = progression[i][0]
            prev_index = self.notes.index(prev_root)
            curr_index = self.notes.index(curr_root)
            interval = (curr_index - prev_index) % 12
            if interval == 7:
                dominant_precedes_score += scoring_prefs["secondary_dominants"]
        quality_scores["secondary_dominants"] = dominant_precedes_score

        #? 4. Cadence structures (e.g., authentic cadence V -> I or plagal cadence IV -> I):
        cadence_score = 0.0
        if len(progression) >= 2:
            penult_degree = progression[-2][2]
            last_degree = progression[-1][2]
            cleaned_penult = clean_degree(penult_degree)
            cleaned_last = clean_degree(last_degree)
            if ((" ".join(re.findall("[a-zA-Z]+", cleaned_penult)).upper() == "V" and cleaned_last.upper() == "I") or
                (" ".join(re.findall("[a-zA-Z]+", cleaned_penult)).upper() == "IV" and cleaned_last.upper() == "I")):
                cadence_score += scoring_prefs["cadence"]
        quality_scores["cadence"] = cadence_score

        #? 5. Scale membership: average fraction of chord notes that belong to the scale:
        scale_notes = notes_of_scale(self.key, self.scale)
        total_fraction = 0.0
        for chord in progression:
            chord_notes = notes_of_chord(chord[0], chord[1], chord[3])
            count_in_scale = sum(1 for note in chord_notes if note in scale_notes)
            fraction = count_in_scale / len(chord_notes)
            total_fraction += fraction
        avg_fraction = total_fraction / len(progression)
        quality_scores["scale_membership"] = avg_fraction * scoring_prefs["scale_membership_multiplier"]

        #? 6. Diversity: ratio of unique chords (by identity) to total chords:
        chord_ids = []
        for chord in progression:
            chord_id = (chord[0], chord[1], clean_degree(chord[2]), chord[3])
            chord_ids.append(chord_id)
        unique_count = len(set(chord_ids))
        diversity_ratio = unique_count / len(progression)  # 1 means all chords are unique
        quality_scores["diversity"] = diversity_ratio * scoring_prefs["diversity_multiplier"]

        #? 7. Voice leading: evaluate smoothness (lower average movement in semitones is better):
        total_voice_movement = 0.0
        count_voice_movements = 0
        for i in range(1, len(progression)):
            prev_notes = notes_of_chord(progression[i - 1][0],
                                        progression[i - 1][1],
                                        progression[i - 1][3])
            curr_notes = notes_of_chord(progression[i][0],
                                        progression[i][1],
                                        progression[i][3])
            min_length = min(len(prev_notes), len(curr_notes))
            for j in range(min_length):
                movement = note_distance(prev_notes[j], curr_notes[j], self.notes)
                total_voice_movement += movement
                count_voice_movements += 1
        if count_voice_movements > 0:
            avg_voice_movement = total_voice_movement / count_voice_movements
            voice_leading_score = max(0, 1 - (avg_voice_movement / 6))
        else:
            voice_leading_score = 0.0
        quality_scores["voice_leading"] = voice_leading_score * scoring_prefs["voice_leading_multiplier"]

        #? 8. Chord complexity: penalize chords with more than 3 notes if chords_complexity is low:
        #? Reward them if chords_complexity is high:
        #? Logic of complexity: 0 (simple triads) to 100 (complex chords allowed):
        complexity_level = self.params["chords_complexity"]
        complexity_score = 0.0
        for chord in progression:
            chord_notes = notes_of_chord(chord[0], chord[1], chord[3])
            note_count = len(chord_notes)
            if note_count > 3:
                if complexity_level < 50:
                    penalty = (note_count - 3) * ((50 - complexity_level) / 50)
                    complexity_score -= penalty * scoring_prefs["complexity_penalty_factor"]
                elif complexity_level > 50:
                    reward = (note_count - 3) * ((complexity_level - 50) / 50)
                    complexity_score += reward * scoring_prefs["complexity_penalty_factor"]
        quality_scores["complexity"] = complexity_score

        #? 9. Extra evaluation: sus chord transition
        #? Reward if a sus2 or sus4 chord is immediately followed by a major chord (type "") with the same root:
        sus_transition_score = 0.0
        sus_nonres_score = 0.0
        for i in range(len(progression) - 1):
            curr_chord = progression[i]
            next_chord = progression[i+1]
            curr_type = curr_chord[1]
            #* Resolution: If current chord is sus2 or sus4 and the next chord has the same root:
            if curr_type in {"sus2", "sus4"} and (curr_chord[0] == next_chord[0]):
                # If the next chord is a major chord (type is ""):
                if next_chord[1] == "":
                    sus_transition_score += scoring_prefs["sus_before_major"]
            #* Non-Resolution:
            if progression[i][1] in {"sus2", "sus4"}:
                if not (progression[i+1][0] == progression[i][0] and progression[i+1][1] == ""):
                    sus_nonres_score -= scoring_prefs.get("sus_nonresolution_penalty", 0)
        quality_scores["sus_transitions"] = sus_transition_score
        quality_scores["sus_nonresolution"] = sus_nonres_score


        #? 10. Extra evaluation: dominant seventh bonus:
        #? Reward if a chord that has a dominant function (its cleaned degree contains "V") is also a 7 chord:
        dominant_seventh_score = 0.0
        for chord in progression:
            chord_degree = chord[2]
            cleaned = clean_degree(chord_degree)
            if " ".join(re.findall("[a-zA-Z]+", cleaned)).upper() == "V" and chord[1] == "7":
                dominant_seventh_score += scoring_prefs["dominant_seventh_bonus"]
        quality_scores["dominant_seventh"] = dominant_seventh_score

        #? 11. Extra evaluation: tension-resolution:
        #? Reward if a tension chord (dominant-type) is immediately followed by a tonic resolution:
        tension_score = 0.0
        tension_chord_types = {"7", "7b9", "7#9", "7b5", "7#5", "aug7", "dim7", "m7b5"}
        for i in range(len(progression) - 1):
            curr_chord = progression[i]
            next_chord = progression[i+1]
            if curr_chord[1] in tension_chord_types:
                next_cleaned = clean_degree(next_chord[2])
                if next_cleaned.upper() == "I":
                    tension_score += scoring_prefs["tension_resolution"]
        quality_scores["tension_resolution"] = tension_score

        #? 12. Extra evaluation: Leading Tone Resolution: (vii° -> I):
        leading_tone_score = 0.0
        for i in range(len(progression)-1):
            if clean_degree(progression[i][2]).upper() == "VII" and progression[i][1] == "dim":
                if clean_degree(progression[i+1][2]).upper() == "I":
                    leading_tone_score += scoring_prefs.get("leading_tone_resolution_bonus", 0)
        quality_scores["leading_tone"] = leading_tone_score


        #? Another Cadence Patterns:
        #* A1. Deceptive Cadence (V → vi):
        deceptive_score = 0.0
        if len(progression) >= 2:
            penult_deg = clean_degree(progression[-2][2])
            last_deg = clean_degree(progression[-1][2])
            # Check if penultimate chord is dominant and last chord is vi (minor quality):
            if penult_deg.upper() == "V" and last_deg.upper() == "VI" and progression[-1][1] == "m":
                deceptive_score += scoring_prefs.get("cadence_deceptive", 0)
        quality_scores["cadence_deceptive"] = deceptive_score

        #* A2. 6/4 Cadential Chord: typically a I chord in second inversion resolving to V:
        cadence_64_score = 0.0
        if len(progression) >= 2:
            penult_deg = clean_degree(progression[-2][2])
            if penult_deg.upper() == "I" and progression[-2][3] == 2:
                last_deg = clean_degree(progression[-1][2])
                if last_deg.upper() == "V":
                    cadence_64_score += scoring_prefs.get("cadence_64", 0)
        quality_scores["cadence_64"] = cadence_64_score

        #* A3. Semicadence: bonus for ending on a dominant when not preceded by a tonic:
        semicadence_score = 0.0
        if len(progression) >= 2:
            penult_deg = clean_degree(progression[-2][2])
            last_deg = clean_degree(progression[-1][2])
            if last_deg.upper() == "V" and penult_deg.upper() != "I":
                semicadence_score += scoring_prefs.get("cadence_semicadence", 0)
        quality_scores["cadence_semicadence"] = semicadence_score

        #* A4. Picardy Third: in minor keys, if the final chord is tonic (I) but in major (not minor), award bonus:
        picardy_score = 0.0
        if self.scale in {"minor", "minor harmonic", "minor melodic", "aeolian"}:
            last_deg = clean_degree(progression[-1][2])
            if last_deg.upper() == "I" and progression[-1][1] != "m":
                picardy_score += scoring_prefs.get("picardy_third_bonus", 0)
        quality_scores["picardy_third"] = picardy_score

        
        #? Gets the total score:
        total_score = sum(quality_scores.values())
        # print("Quality breakdown:", quality_scores)

        return total_score



def build_harmony(chords_per_sentence: list, chords_durations: list, chords_progression: list, params: dict, signature: tuple, upbeat: int, key: str, scale: str, chords_octave: int):
    """
        Builds a Harmony object for a chord progression given

        Parameters:
        
            - chords_per_sentence [list[int]]: Each integer indicates the number of chords in that phrase
            For example, [1, 1, 2, 2] means phrase 1 has 1 chord, phrase 2 has 1 chord, phrase 3 has 2 chords, etc
            
            - chords_durations [list[int]]: Each integer indicates how many bars the corresponding phrase occupies
            For example, [2, 2, 1, 1] means phrase 1 is 2 bars, phrase 2 is 2 bars, etc
            
            - chords_progression [list[tuple]]: Each tuple contains chord information (RESULT OF GeneticProgressions):
            ([str] root, [str] type, [str] degree, [int] inversion)
            
            - params [dict] parameters (for instance, the simulated annealing parameters) to be passed to the Rythm class
            See "conf.py" file
            
            - signature [tuple]: Time signature (e.g., (4, 4))
            
            - upbeat [int]: Number of upbeat beats
            
            - key [str], scale [str]: Key name and scale type (for Harmony)
            
            - chords_octave [int]: Octave in which chords should be rendered
            
            The function uses the Rythm.fit method (with for_chords=True) to generate, for each phrase,
            a chord rhythm that is padded with extra silences (if needed) so that the total effective duration
            exactly meets the expected size. Then, it builds a Harmony object by assigning each chord (from chords_progression)
            its corresponding time value and dot flag :3
        
        Returns:
            A Harmony object with the assembled chord progression
    """
    rythm_harmony = Rythm(signature=signature, upbeat=upbeat, params=params, for_chords=True)
    
    # Process each phrase: for each phrase, generate a chord sentence;
    # The number of phrases is the length of chords_per_sentence (which should match the length of chords_durations):

    #? Construct the Harmony object:
    harmony = Harmony(signature=signature, key_name=key, key_type=scale, upbeat=upbeat)

    processes_chords = 0
    for i in range(len(chords_per_sentence)):
        n_chords = chords_per_sentence[i]
        bars = chords_durations[i]

        # Generate a chord sentence consisting of n_chords tokens ("X*"):
        chord_sentence = ["X*"] * n_chords

        # Fit the chord sentence into the required number of bars;
        # In chord mode, our modified Rythm.fit now returns a tuple:
        # (initial_rest, chord_figures, final_rest, extra_silences, dots)
        result = rythm_harmony.fit(sentence=chord_sentence, bars=bars)

        # In candidate structure:
        # - times_chords[0] is the initial rest (unused for chord sound),
        # - times_chords[1] is the list of syllable note figures (i.e. the chord sounds),
        # - times_chords[2] is the final rest,
        # - times_chords[3] is the extra silences (if any),
        # - times_chords[4] is the list of dot flags
        # initial_rest = result[0]
        syllable_figures = result[1]
        # final_rest = result[2]
        extra_silences_phrase = result[3]
        dots_full = result[4]

        chord_phrase = syllable_figures[:]
        chord_phrase_dots = dots_full[1:-1]

        #* Add the chords:
        # print("Amount of chords:", len(chord_phrase))
        for i in range(len(chord_phrase)):
            fig = chord_phrase[i]
            dot_flag = chord_phrase_dots[i]
            # print("Num of chord:", i+1)
            # print(chords_progression)
            # print("\t* SELECTED:", chords_progression[processes_chords])
            chord_info = chords_progression[processes_chords]
            chord_obj = Chord(
                name=chord_info[0],
                ctype=chord_info[1],
                degree=chord_info[2],
                inversion=chord_info[3],
                octave=chords_octave,
                time=fig,
                dot=dot_flag
            )
            harmony.add_element(chord_obj)
            processes_chords += 1

        #* Add extra silences if required:
        if extra_silences_phrase:
            for coin in extra_silences_phrase:
                # print(f"\nExtra silence added for sentence {i+1}: Fig: {coin[0]} - Dot: {coin[1]}")
                chord_obj = Chord(
                    name="X",
                    ctype="",
                    inversion=0,
                    octave=0,
                    time=coin[0],
                    dot=coin[1]
                )
                harmony.add_element(chord_obj)
    
    return harmony