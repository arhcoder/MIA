
#! PARAMETERS TO MODIFY IN WAY TO SET THE ALGORITHMS RESULTS !#


#? [01] RYTHM PATTERNS:
simulated_annealing_phrases_params = {

    "initial_temperature": 100,
    "cooling_rate": 0.98,
    "iterations": 10000,
    "selection_bias": 5,
    "dot_probability": 0.2,

    #? Set this parameters between -100 and 100 as IMPORTANCE:
    #*
    #*    1. A value of 0 will imply that the parameter in question will not positively or negatively
    #*       affect the evaluation, it will be an inactive parameter
    #*
    #*    2. A value of -100 means that it will punish that parameter to the maximum extent, to avoid
    #*       the characteristic of the parameter
    #*
    #*    3. A value of 100 means that the presence of that characteristic will be rewarded the most
    #*
    #? USE THE PARAMETERS IN A BALANCED WAY, NOT GOING TO extremes so as not to lose variety:
    "correct_fitting_importance": 100,
    "beat_on_strong_beats_reward": 100,
    "initial_rest_duration_reward": 10,
    "initial_rest_anacrusis_penalty": -100,
    "final_rest_duration_reward": 20,
    "large_last_note_reward": 30,

    #? This probabilities just set between 0 and 100:
    "probability_find_initial_rest": 20,
    "probability_find_final_rest": 20,

    #? Uniformity is the grade on which there are
    #? repetitive use of notes figures:
    "uniformity": 50
}


#? [02] CHORD PROGRESSIONS:
genetic_progression_params = {

    "population_size": 50,
    "generations_per_chord": 12,
    "mutation_rate": 0.1,
    "tournament_size": 5,
    "elitism_size": 3,

    #? FOR INITIALIZATION:
    #* In the step to initializate, the complexity is how complex the chords will be:
    #* If complexity = 0, it just will take basics major - minor (sometimes dim)
    #* If complexity = 100, it will take with some frequency complex chords as maj11, m7b5, 7#5, etc
    #/ SO, if complexity is up to 50, the chords must be more jazzy,
    #! But if the mutation rate is near to 1 (100%), then will be more possible to see rare chords,
    #! but unestable chord progressions;
    #? It has to be between 0 and 100:
    "chords_complexity": 20,

    "scoring_prefs": {

        # Basic preferences:
        "first_chord_is_tonic": 2,
        "first_chord_not_tonic_penalty": 0,
        "last_chord_is_dominant": 2,
        "last_chord_not_dominant_penalty": 0,
        "first_last_combined_bonus": 5,
        "tonic_on_last_bonus": 2,
        "secondary_dominants": 10,
        "cadence": 30,
        "scale_membership_multiplier": 50,
        "diversity_multiplier": 40,
        "voice_leading_multiplier": 10,
        "sus_before_major": 10,
        "sus_nonresolution_penalty": 8,
        "complexity_penalty_factor": 17,
        "dominant_seventh_bonus": 17,
        "tension_resolution": 20,
        "leading_tone_resolution_bonus": 5,

        # Extra cadences structures:
        "cadence_deceptive": 17,
        "cadence_64": 10,
        "cadence_semicadence": 4,
        "picardy_third_bonus": 6
    }
}