import os,re,json
from spellchecker import SpellChecker

spell=SpellChecker()
def check_spelling(text):
    cleaned=re.sub(r'(?<=\w)[|](?=\w)','l',text)
    cleaned=re.sub(r'\s+','',cleaned).strip()
    words=cleaned.split()
    corrected=[]
    for word in words:
        if any(char.isdigit() for char in word) or '@' in word or re.match(r'^[$€£#]',word):
            corrected.append(word)
            continue
        match=re.match(r'^([^\w]*)([\w]+)([^\w]*)$',word)
        if match:
           prefix,core,suffix=match.groups()
           if core.lower() in spell.unknown([core.lower()]):
               correction=spell.correction(core)
               core=correction if correction else core
               corrected.append(f"{prefix}{core}{suffix}")
        else:
            corrected.append(word) 
        return " ".join(corrected)
#Post-Process orchestration(def)
