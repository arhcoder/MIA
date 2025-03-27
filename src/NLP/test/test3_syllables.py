import random
from NLP.Grammar import Grammar

#? Generate 10 random sentences:
for i in range(10):
    grammar = Grammar(sentence_type=random.randint(1, 4))
    sentence_text, sentence_syllables = grammar.generate()
    print(f"\nORACIÓN {i+1}:")
    print(" *", sentence_text)
    print(" *", sentence_syllables)