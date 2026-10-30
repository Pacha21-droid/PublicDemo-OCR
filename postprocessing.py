import os,re,json
from spellchecker import SpellChecker

#Checking grammar mistakes
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

#Extract valuable fields
def extract_fields_regex(text:str)->dict:
    emails=re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    dates=re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
    prices=re.findall(r'[$€£]\s?\d+(?:\.\d{2})?', text)
    results={"emails":emails,
             "dates":dates,
             "prices":prices}
    return results


#Post-Process orchestration(def)
