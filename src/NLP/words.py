import pandas as pd
import random
import re
import os

base_path = "Data/pos/"

def complete_sentence(categories_string):
    """
        Generates a sentence with its attributes based on PartOfSpeech string sentence
        Example input: "Det Sus Adj V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,yo Adv"

        Parameters:
            - categories_string [str]: String with the sentence in which PoS are separated by spaces
              Each PoS is a string with this possible values:
                - "Adj": Adjectives
                - "Adv": Adverbs
                - "Conj": Conjuctions
                - "Det": Determinants
                - "Int": Interjections
                - "Sus": Nouns
                - "Prep": Prepositions
                - Pronouns:
                    - "PronPer": Personal Pronouns
                    - "PronRef": Reflexibe Pronouns
                    - "PronPrep": Prepositional Pronouns
                    - "PronDem": Demostrative Pronouns
                    - "PronIntExc": Interrogative Exclamative Pronouns
                    - "PronRel": Relative Pronouns
                - Verbs: Each verb has the following format:
                    - "V,<number>,<regularity>,<transitivity>,<conjugation>,<time>,<person>"
        
        Returns:
            - [list[dict]]: List of dictionaries of the selected words, and its characteristics
              Each element contains:
                - "word" [str]: Selected word
                - "syllables" [list[str]]: List of words syllables as string 
                - "tonic" [int]: Number of the tonic syllable (NOTATION STARTING FROM 0)
    """

    # Generates random genre and number:
    gender = random.choice(["femenino", "masculino"])
    number = random.choice(["singular", "plural"])

    # Generates the sentence replacing each PoS with a word:
    sentence = []
    categories = categories_string.upper().split()
    for category in categories:

        # If it is a verb:
        if category.startswith("V,"):
            category = category.lower()
            file_path = os.path.join(base_path, "verbs.csv")
            parts = category.split(",")
            category = "V"
            if len(parts) != 7:
                raise ValueError(f"Verb incorrect format: {category}")
            file_map = {
                "V": "verbs.csv"
            }
            
            # parts[0] es "V", luego number, regularity, transitivity, conjugation, time, person:
            filters = {
                "number": parts[1],
                "regularity": parts[2],
                "transitivity": parts[3],
                "conjugation": parts[4],
                "time": parts[5],
                "person": parts[6]
            }
        else:
            file_map = {
                "ADJ": "adjectives.csv",
                "ADV": "adverbs.csv",
                "CON": "conjunctions.csv",
                "DET": "determinants.csv",
                "INT": "interjections.csv",
                "SUS": "nouns.csv",
                "PREP": "prepositions.csv",
                "PRONPER": "pronouns.csv",
                "PRONREF": "pronouns.csv",
                "PRONPREP": "pronouns.csv",
                "PRONDEM": "pronouns.csv",
                "PRONINTEXC": "pronouns.csv",
                "PRONREL": "pronouns.csv",
                "V": "verbs.csv"
            }

            # If it is valid category:
            if category not in file_map:
                raise ValueError(f"Uknowkn PoS Category: {category}")
        
        # PoS dictionaries path:
        file_path = os.path.join(base_path, file_map[category])

        # Special filters for genres and numbers:
        filters = {}
        if category in ["ADJ", "DET", "SUS"]:
            filters["genre"] = gender
            filters["number"] = number
        elif category.startswith("PRON"):
            filters["type"] = {
                "PRONPER": "personal",
                "PRONREF": "reflexivo",
                "PRONPREP": "preposicional",
                "PRONDEM": "demostrativo",
                "PRONINTEXC": "interrogativo_exclamativo",
                "PRONREL": "relativo",
            }[category]
            filters["genre"] = gender
            filters["number"] = number

        # Gets the correct dictionary:
        df = pd.read_csv(file_path)
        if filters:
            for column, value in filters.items():
                if column in df.columns:
                    if value.lower() == "neutro":
                        df = df[df[column].str.lower().isin(["femenino", "masculino", "neutro"])]
                    else:
                        df = df[df[column].str.lower().isin([value.lower(), "neutro"])]
        if df.empty:
            raise ValueError(f"No words for {category} in {file_path} with filters {filters}")
        
        # Gets a random row for the selected words:
        row = df.sample().iloc[0]
        word_data = {
            "word": row["word"],
            "tonic": int(row["tonic"] - 1),
            "syllables": re.sub(r"[^\w\s]", "", row["syllables"]).split()
        }
        sentence.append(word_data)

    return sentence