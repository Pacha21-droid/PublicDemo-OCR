from __future__ import annotations
import os,re,json
from pathlib import Path

def match_case(original:str,replacement:str)->str:
    if original.isupper():
        return replacement.isupper()
    if original.islower():
        return replacement.islower()
    if original.istitle():
        return replacement.istitle()
    return replacement

#Checking grammar mistakes
try:
    from spellchecker import SpellChecker
    spell=SpellChecker()
except ImportError:
    spell = None

def check_spelling(text:str)->str:
    if not text:
        return text
    cleaned=re.sub(r"(?<=\w)\|(?=\w)","l",text)
    if spell is None:
        return cleaned
    def replace_token(match):
        token=match.group(0)
        parts=re.match(r"^([^\w]*)([\w'-]+)([^\w]*)$",token,flags=re.UNICODE)
        if not parts:
            return token
        prefix,core,suffix=parts.groups()
        if not core.isalpha() or len(core)<3:
            return token
        candidate = spell.correction(core.lower())
        if not candidate:
            return token
        if candidate.lower()==core.lower():
            return token
        corrected = match_case(core,candidate)
        return prefix+corrected+suffix
    return re.sub(r"\S+",replace_token,cleaned)

#Extract valuable fields
def extract_fields_regex(text:str)->dict:
    emails=re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',text)
    dates=re.findall( r"\b(?:"r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"r"|"r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"r")\b",text)
    prices=re.findall(r'[$€£]\s?\d+(?:\.\d{2})?',text)
    return{"emails":list(dict.fromkeys(emails)),
           "dates":list(dict.fromkeys(dates)),
           "prices":list(dict.fromkeys(prices))}

#Mini rules engine
def validate_and_apply_rules(extracted:dict,text:str):
    errors=[]
    lower_text=text.lower()
    if(re.search(r"\b(total|amount due|balance due)\b",lower_text) and not extracted.get("prices")):
        errors.append("A total or amount is mentioned,but no price was detected.")
    if(len(extracted.get("prices", []))>3 and not re.search(r"\b(total|grand total|amount due)\b",lower_text)):
        errors.append("Several prices were detected,but no total label was found.")
    if(re.search(r"\b(email|e-mail|contact)\b",lower_text) and not extracted.get("emails")):
        errors.append("Contact information is mentioned,but no email address was detected.")
    if(re.search(r"\b(due date|deadline|appointment|meeting)\b",lower_text) and not extracted.get("dates")):
        errors.append("A date-sensitive item is mentioned,but no numeric date was detected.")
    valid=len(errors)==0
    return valid,errors

#Classificatior
def classify(text:str)->str:
    text_lower=text.lower()
    result="document"
    if any(key in text_lower for key in["invoice", "bill to", "due date", "subtotal"]):
        result="invoice"
    elif any(key in text_lower for key in ["report", "summary", "analysis", "findings"]):
       result="report"
    elif any(key in text_lower for key in ["study", "abstract", "methodology", "conclusion"]):
        result="study"
    elif any(key in text_lower for key in ["receipt", "cashier", "change due", "thank you"]):
        result="receipt"
    return result

#Formatter
def format_text(text:str,doc_type:str,metadata,errors:None,valid:True,raw_text:False):
    if raw_text:
        return text
    return{"document_type":doc_type,"text":text,"metadata":metadata,
        "valid":bool(valid),"errors":list(errors or [])}

#Save to file
def save_output(type:str,payload,image_name:str,base_dir:str="output")->str:
    safe_type=re.sub(r"[^A-Za-z0-9_-]+","_",str(type).lower()).strip("_") or "document"
    source_stem=Path(image_name).stem
    safe_stem=re.sub(r"[^A-Za-z0-9_-]+","_",source_stem).strip("_") or "ocr_result"
    output_dir=Path(base_dir)/safe_type
    output_dir.mkdir(parents=True,exist_ok=True)
    if isinstance(payload,str):
        output_path=output_dir/f"{safe_stem}.txt"
        output_path.write_text(payload,encoding="utf-8")
    else:
        output_path=output_dir/f"{safe_stem}.json"
        output_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    return str(output_path.resolve())

#Post-Process orchestration(def)
def postprocess_pipeline(raw,image_name,base_dir="output"):
    spell_checked=check_spelling(raw)
    regex_extracted=extract_fields_regex(spell_checked)
    valid,errors=validate_and_apply_rules(regex_extracted,spell_checked)
    classified=classify(spell_checked)
    formatted=format_text(spell_checked,classified,regex_extracted,errors=errors,valid=valid,raw_text=False)
    saved_path=save_output(classified,formatted,image_name,base_dir)
    return saved_path,classified,formatted