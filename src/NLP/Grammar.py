from nltk import CFG # type: ignore
import random
from NLP.rules import sentences_rules
from NLP.words import complete_sentence

class Grammar:

    def __init__(self, sentence_type: int):
        """
            Creates a Free-Context Grammar capable of generate sentences based on the type of sentence
            FOR NOW BASED PURELY ON SPANISH SENTENCES

            Parameters:
                - sentence_type [int]: Which kind of sentenceIt could be:
                    - 1: Simple Declarative Sentences
                    - 2: Simple Interrogative Sentences
                    - 3: Exclamative Sentences
                    - 4: Imperative Sentences
            
            Methods:
                - generate(): Returns a random sentence in two formats:
                    - [str]: Sentence as capitalized text
                    - [list[str]]: Sentence as list of syllables:
                        - If syllable contains "*" it is a tonic
                        - If syllable is a "", it is a space between words
                    Example of output:
                        - "Juanito alimaña come manzanas"
                        - ["Jua", "ni*", "to", "", "a", "li", "ma*", "ña", "", "co*", "me", "", "man", "za*", "nas"]
        """

        #? Validations:
        if not (1 <= sentence_type <= len(sentences_rules)):
            raise ValueError(f"\"sentence_type\" must be an integer between 1 and {len(sentences_rules)}")

        #? Starts the grammar:
        self.title, grammar_rules = sentences_rules[sentence_type - 1]
        self.grammar = CFG.fromstring(grammar_rules)
        self._sentence_type = sentence_type
    

    def generate(self):
        """
            Generates a random sentence [str] based on PoS categories.

            Returns:
            - [list[dict]]: List of dictionaries of the selected words, and its characteristics
              Each element contains:
                - "word" [str]: Selected word
                - "syllables" [list[str]]: List of words syllables as string 
                - "tonic" [int]: Number of the tonic syllable (NOTATION STARTING FROM 0)
        """
        productions = self.grammar.productions()
        nonterminals = [prod.lhs() for prod in productions]
        def generate_random(symbol):
            choices = [prod for prod in productions if prod.lhs() == symbol]
            chosen = random.choice(choices)
            result = []
            for sym in chosen.rhs():
                if sym in nonterminals:
                    result.extend(generate_random(sym))
                else:
                    result.append(str(sym))
            return result
        
        #/ Example of return: "Det Sus Adj VConj Adv"
        sentence = generate_random(self.grammar.start())

        #? Gets a sentence with words and syllables:
        sentence_words = complete_sentence(" ".join(sentence))

        #* Sentece as text:
        sentence_text = " ".join([word["word"] for word in sentence_words]).capitalize()

        #* Sentence as syllables:
        sentence_syllables = []
        for word in sentence_words:
            syllables = word["syllables"]
            tonic_index = word["tonic"]
            syllables[tonic_index] = syllables[tonic_index] + "*"
            sentence_syllables.extend(syllables)
            sentence_syllables.append(" ")
        # Removes the last space:
        sentence_syllables.pop()
        sentence_syllables[0] = sentence_syllables[0].capitalize()

        return sentence_text, sentence_syllables
    
    #? TUNING:
    @property
    def sentence_type(self):
        return self._tuning

    @sentence_type.setter
    def sentence_type(self, value: int):
        if not (1 <= value <= len(sentences_rules)):
            raise ValueError(f"\"sentence_type\" must be an integer between 1 and {len(sentences_rules)}")
        self.title, grammar_rules = sentences_rules[value - 1]
        self.grammar = CFG.fromstring(grammar_rules)
        self._sentence_type = value