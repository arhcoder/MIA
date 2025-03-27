#/ PRODUCTION RULES FOR CONTEXT-FREE GRAMMARS OF SPANISH SENTENCES /#

#? [01]: Simple Declarative Sentences:
simple_declarative = ("Simple Declarative Sentence",
"""
S -> Sujeto Predicado

# Sujeto:
Sujeto -> Det Sus | PronPer | PronDem Sus

# Predicado (sólo verbo o verbo con objeto):
Predicado -> Verbo | Verbo Objeto

# Verbo (se mantienen las variantes):
Verbo -> VTran | VIntra | VConj | VCop

# Reglas para VTran:
VTran -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VTran -> 'V,plural,irregular,transitivo_intransitivo_pronominal,conjugado,pretérito_indicativo,yo'

# Reglas para VIntra:
VIntra -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,tú'
VIntra -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ustedes'

# Reglas para VConj:
VConj -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,vos'
VConj -> 'V,plural,irregular,transitivo_intransitivo,conjugado,presente_indicativo,nosotros'

# Reglas para VCop:
VCop -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VCop -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ellos'

# Objeto (sencillo: opcional, solo sustantivo con o sin determinante):
Objeto -> Det Sus | Sus

# Terminales (categorías gramaticales):
Det -> 'Det'
Sus -> 'Sus'
PronPer -> 'PronPer'
PronDem -> 'PronDem'
"""
)


#? [02] Simple Interrogative Sentences:
simple_interrogative = ("Simple Interrogative Sentence",
"""
# Estructura interrogativa sencilla: partícula interrogativa al inicio, seguida de sujeto y verbo, o solo verbo.
S -> PartInterr Sujeto Verbo | PartInterr Verbo

# Partículas interrogativas:
PartInterr -> PronIntExc | AdvInt

# Sujeto:
Sujeto -> PronPer | PronDem | Sus

# Verbo:
Verbo -> VTran | VIntra | VCop | VConj

# Reglas para VTran:
VTran -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VTran -> 'V,plural,irregular,transitivo_intransitivo_pronominal,conjugado,pretérito_indicativo,yo'

# Reglas para VIntra:
VIntra -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,tú'
VIntra -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ustedes'

# Reglas para VCop:
VCop -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VCop -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ellos'

# Reglas para VConj:
VConj -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,vos'
VConj -> 'V,plural,irregular,transitivo_intransitivo,conjugado,presente_indicativo,nosotros'

# Terminales:
PronIntExc -> 'PronIntExc'
AdvInt -> 'PronIntExc'
Det -> 'Det'
Sus -> 'Sus'
PronPer -> 'PronPer'
PronDem -> 'PronDem'
"""
)


#? [03] Exclamative Sentences:
exclamative_sentence = ("Exclamative Sentence",
"""
# Estructura exclamativa sencilla: interjección opcional seguida de sujeto y verbo, o sólo verbo.
S -> Int Sujeto Verbo | Int Verbo

# Interjecciones:
Int -> 'Int'

# Sujeto:
Sujeto -> Det Sus | PronPer | PronDem Sus

# Verbo:
Verbo -> VTran | VIntra | VCop | VConj

# Reglas para VTran:
VTran -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VTran -> 'V,plural,irregular,transitivo_intransitivo_pronominal,conjugado,pretérito_indicativo,yo'

# Reglas para VIntra:
VIntra -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,tú'
VIntra -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ustedes'

# Reglas para VCop:
VCop -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,él'
VCop -> 'V,plural,irregular,transitivo_intransitivo,conjugado,pretérito_indicativo,ellos'

# Reglas para VConj:
VConj -> 'V,singular,regular,transitivo_intransitivo,conjugado,presente_indicativo,vos'
VConj -> 'V,plural,irregular,transitivo_intransitivo,conjugado,presente_indicativo,nosotros'

# Terminales:
Det -> 'Det'
Sus -> 'Sus'
PronPer -> 'PronPer'
PronDem -> 'PronDem'
"""
)


#? [04] Imperative Sentences:
imperative_sentence = ("Imperative Sentence",
"""
# Estructura imperativa simple: se omite el sujeto (implícito) y se presenta el verbo en imperativo, con opción de objeto.
S -> VerboImp | VerboImp Objeto

# Verbo en Imperativo:
VerboImp -> VImp

# Reglas para VImp:
VImp -> 'V,singular,regular,neutro,conjugado,imperativo,tú'
VImp -> 'V,singular,irregular,neutro,conjugado,imperativo,tú'
VImp -> 'V,plural,irregular,neutro,conjugado,imperativo,ustedes'
VImp -> 'V,plural,regular,neutro,conjugado,imperativo,ustedes'

# Objeto (sencillo):
Objeto -> Det Sus | Sus

# Terminales:
Det -> 'Det'
Sus -> 'Sus'
"""
)

sentences_rules = [simple_declarative, simple_interrogative, exclamative_sentence, imperative_sentence]