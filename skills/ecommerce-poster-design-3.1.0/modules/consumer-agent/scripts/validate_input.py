"""Schema and semantic checks for A-D-2.0. Null tags are supported."""
import argparse, re, hashlib, json
from common import load_json, root_dir
from schema_check import check

def context_hash(data):
    # Poster/version/loop excluded. Brief, C selection and immutable facts stay fixed.
    stable={k:data[k] for k in ("source_input","style_guide","protected_content","evaluation_context")}
    return hashlib.sha256(json.dumps(stable,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def validate(data):
    errors=check(data,load_json(root_dir()/"assets/schemas/input.schema.json"))
    if errors: return errors
    s=data["source_input"]; e=data["evaluation_context"]; pc=data["protected_content"]
    if data["request_id"]!=s["request_id"]: errors.append("request_id must match source_input")
    if not (s["product"]["name"].strip() or s["product"]["category"].strip()): errors.append("product name or category required")
    if e["product_img"]!=s["product"]["image_refs"][0]: errors.append("product_img must match first image_ref")
    from math import gcd
    w,h=s["canvas"]["width"],s["canvas"]["height"]; g=gcd(w,h)
    if e["aspect_ratio"]!=str(w//g)+":"+str(h//g): errors.append("aspect_ratio conflicts with canvas")
    if e["orientation"]!=("vertical" if h>w else "horizontal" if w>h else "square"): errors.append("orientation conflicts with canvas")
    taxonomy=load_json(root_dir()/"assets/taxonomy.json")
    for i,(group,key) in enumerate(zip(("populations","motivations","usage_scenes"),("audience_id","motivation_id","scenario_id"))):
        tag=" ".join(re.sub(r"[｜|:：]+"," ",e["scene_tags"][i]).split())
        upstream=data["style_guide"]["tags"][key]
        if upstream is None:
            if tag!="null": errors.append("null upstream tag must remain null")
            continue
        items=taxonomy[group]
        selected=next((x for x in items if tag in (x["id"],x["name"],x["id"]+" "+x["name"])),None)
        if selected is None or selected["id"]!=upstream: errors.append("scene_tags conflicts with upstream "+key)
    # Protect original confirmed values; do not flatten the returned object.
    checks={"product_identity":[s["product"]["name"] or s["product"]["category"]],
            "selling_points":s["product"]["selling_points"],"brand_and_logo":[s["brand"]["name"]],
            "price_and_unit":[s["commerce"]["price_text"]],
            "promotion_and_period":[s["commerce"]["promotion_text"],s["commerce"]["promotion_period"]],
            "cta":[s["marketing"]["cta"]],"legal_text":[s["commerce"]["legal_text"]]}
    for group,values in checks.items():
        for value in values:
            if value and value not in pc[group]: errors.append("protected_content."+group+" missing original value")
    if pc["product_quantity"]!=s["product"]["quantity"]: errors.append("protected quantity differs")
    previous=data["loop_state"]["previous_result"]
    if previous:
        if previous.get("request_id")!=data["request_id"]: errors.append("previous result belongs to another request")
        if previous.get("protected_content")!=pc: errors.append("protected_content changed across iterations")
        if not set(previous.get("locked_dimensions",[])).issubset(data["loop_state"]["locked_dimensions"]):
            errors.append("previous locks must be inherited")
        if previous.get("meta",{}).get("context_hash")!=context_hash(data):
            errors.append("locked brief/C context changed; start a new evaluation track")
    return errors

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("input");a=p.parse_args()
    errors=validate(load_json(a.input));print("\\n".join(errors) if errors else "VALID")
    raise SystemExit(bool(errors))
