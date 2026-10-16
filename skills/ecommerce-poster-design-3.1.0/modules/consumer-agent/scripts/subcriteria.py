"""Internal item scoring; A-D schemas remain unchanged."""
from decimal import Decimal, ROUND_HALF_UP
from common import load_json, root_dir

def calculate(draft, context):
    rubric=load_json(root_dir()/"assets/rubric.json")
    groups=rubric["subcriteria"]; items=draft.get("subcriteria")
    expected={row[0] for rows in groups.values() for row in rows}
    if not isinstance(items,dict) or set(items)!=expected:
        raise ValueError("exactly 25 subcriteria required")
    if "dimension_scores" in draft or "dimension_evidence" in draft:
        raise ValueError("model must not supply derived dimension scores/evidence")
    scores={}; evidence={}; details={}
    commerce=context["source_input"]["commerce"]
    for key in ("D3_1","D5_1"):
        if isinstance(items[key],dict) and items[key].get("level")==0 and not draft.get("critical_issues"):
            raise ValueError(key+": confirmed factual failure needs critical_issues or input-error routing")
    absent={"D3_1":not commerce["price_text"],"D3_2":not commerce["price_text"],
            "D3_3":not commerce["promotion_text"] and not commerce["promotion_period"],
            "D3_4":not context["source_input"]["marketing"]["cta"]}
    for dimension,rows in groups.items():
        total=Decimal(0); active=0; lines=[]; entries=[]
        for key,label,weight in rows:
            item=items[key]
            if not isinstance(item,dict): raise ValueError(key+": object required")
            text=item.get("evidence"); level=item.get("level")
            if "level" not in item or not isinstance(text,str) or not text.strip():
                raise ValueError(key+": level and nonempty evidence required")
            if level is None:
                reason=item.get("not_applicable_reason")
                if not absent.get(key,False) or not isinstance(reason,str) or not reason.strip():
                    raise ValueError(key+": N/A needs absent transaction element and reason")
                contribution=None
            else:
                if type(level) is not int or not 0<=level<=4: raise ValueError(key+": integer level 0–4 required")
                contribution=Decimal(weight)*level/4; total+=contribution; active+=weight
            entries.append({"id":key,"label":label,"weight":weight,"level":level,"evidence":text,
                            "contribution":float(contribution) if contribution is not None else None,
                            "not_applicable_reason":item.get("not_applicable_reason")})
            lines.append(key+" "+label+"="+str(level)+"："+text)
        raw=total*20/active
        scores[dimension]=int(raw.quantize(Decimal("1"),rounding=ROUND_HALF_UP))
        evidence[dimension]="；".join(lines)
        details[dimension]={"items":entries,"applicable_weight":active,"raw_score":float(raw),"score":scores[dimension]}
    return scores,evidence,{"rubric_version":rubric["version"],"dimensions":details,"score":sum(scores.values())}
