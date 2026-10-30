import os,re,json
from spellchecker import SpellChecker
from pathlib import Path

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

#Mini rules engine
def validate_and_apply_rules(extracted:dict, text:str):
    is_valid=True
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
def format_text(text:str,type:str,metadata:str,errors:None,valid:True,raw_text:False)->dict:
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
def save_output(type:str,payload:dict,image_name:str,base_dir="output"):
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
