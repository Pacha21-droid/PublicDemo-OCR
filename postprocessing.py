import os,re,json
from spellchecker import SpellChecker
from pathlib import Path
from __future__ import annotations

def match_case(original:str,replacement:str)->str:
    if original.isupper():
        return replacement.isupper()
    if original.islower():
        return replacement.islower()
    if original.istitle():
        return replacement.istitle()
    return replacement


#Checking grammar mistakes
spell=SpellChecker()
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
    text_lower=text.lower()
    
    if len(extracted["prices"])==0 and "total" in text_lower:
        errors.append("Uncertainty: 'Total' mentioned in text, but no prices were extracted.")
        is_valid = False
        
    if len(extracted["prices"])>3 and "total" not in text_lower:
        errors.append("Uncertainty: Multiple prices found (>3) without a clear 'total' keyword to disambiguate.")
        is_valid=False

    if ("contact us" in text_lower or "reach out at" in text_lower or "email us" in text_lower) and len(extracted["emails"])==0:
        errors.append("Uncertainty: Contact prompt detected ('email us'/'contact'), but no email address was extracted.")
        is_valid=False

    time_sensitive_keywords=["due date", "invoice date", "expires", "deadline", "valid until"]
    if any(keyword in text_lower for keyword in time_sensitive_keywords) and len(extracted["dates"])==0:
        errors.append("Uncertainty: Time-sensitive keywords found, but no dates were extracted.")
        is_valid=False

    cleaned_emails=[]
    for email in extracted["emails"]:
        if email.endswith('.'):
            errors.append(f"Uncertainty: Email '{email}' contains a trailing period, suggesting it caught sentence punctuation.")
            cleaned_emails.append(email.rstrip('.'))
        else:
            cleaned_emails.append(email)
    extracted["emails"]=cleaned_emails
    return is_valid, errors

#Classificatior
def classify(text):
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
def format_text(text,type,metadata,errors:None,valid:True,raw_text:False):
    clean_text=text.strip() if isinstance(text, str) else str(text)
    if raw_text:
        return clean_text
    if errors is None:
        errors=[]
    payload={"document_info": {
            "document_type":type,
            "status":"valid" if valid else "flagged",},
            "extracted_data":metadata,
            "validation_errors":errors,
            "content":{"full_text":clean_text
            }}
    return payload

#Save to file
def save_output(type,payload,image_name,base_dir="output"):
    class_dir=Path(base_dir) / type
    class_dir.mkdir(parents=True,exist_ok=True)
    base_name=os.path.splitext(os.path.basename(image_name))[0]
    if isinstance(payload,str):
        filepath=class_dir / f"{base_name}.txt"
        filepath.write_text(payload,encoding="utf-8")
        print(f"Saved raw text to {filepath}")
    elif isinstance(payload,dict):
        filepath=class_dir / f"{base_name}.json"
        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(payload,f,indent=4,ensure_ascii=False)
        print(f"Saved structured JSON to {filepath}")    
    return str(filepath)

#Post-Process orchestration(def)
def postprocess_pipeline(raw,image_name,base_dir="output"):
    spell_checked=check_spelling(raw)
    regex_extracted=extract_fields_regex(spell_checked)
    valid, errors = validate_and_apply_rules(regex_extracted,spell_checked)
    classified=classify(spell_checked)
    formatted=format_text(spell_checked,classified,regex_extracted,valid,errors,raw)
    saved=(formatted,image_name,base_dir)
    return saved,formatted