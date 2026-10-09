"""Assemble A 1.0 normalized artifacts into the A-D-2.0 consumer interface."""
import argparse
from copy import deepcopy
from math import gcd
from common import load_json, write_json
from validate_input import validate


SUPPORTED_SUPPLEMENT_KEYS = {
    "theme",
    "required_information",
    "brand_requirements",
    "brand_tone",
    "test_requirement",
}


def _as_text_list(value, field):
    """Accept a single brief string or a list of strings and normalize to a list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value):
        return list(value)
    raise ValueError(f"brief supplement {field} must be a string or a list of non-empty strings")


def normalize_supplement(supplement):
    """Normalize common natural-brief aliases into the A-D-2.0 context fields."""
    if supplement is None:
        return {}
    if not isinstance(supplement, dict):
        raise ValueError("brief supplement must be a JSON object")
    unknown = sorted(set(supplement) - SUPPORTED_SUPPLEMENT_KEYS)
    if unknown:
        raise ValueError(
            "unsupported brief supplement fields: "
            + ", ".join(unknown)
            + "; supported fields: "
            + ", ".join(sorted(SUPPORTED_SUPPLEMENT_KEYS))
        )

    normalized = {}
    theme = supplement.get("theme", "")
    if theme is None:
        theme = ""
    if not isinstance(theme, str):
        raise ValueError("brief supplement theme must be a string")
    normalized["theme"] = theme

    required = _as_text_list(supplement.get("required_information"), "required_information")
    # test_requirement was used by early visual-E2E fixtures. Treat it as an
    # explicit must-show/check requirement instead of crashing on an unknown kwarg.
    required += _as_text_list(supplement.get("test_requirement"), "test_requirement")
    if required:
        normalized["required_information"] = list(dict.fromkeys(required))

    brand = _as_text_list(supplement.get("brand_requirements"), "brand_requirements")
    brand += _as_text_list(supplement.get("brand_tone"), "brand_tone")
    if brand:
        normalized["brand_requirements"] = list(dict.fromkeys(brand))
    return normalized

def assemble(source, style, protected, poster_image, version_id="v01", iteration=1, previous=None, theme="", required_information=None, brand_requirements=None):
    width, height = source["canvas"]["width"], source["canvas"]["height"]
    if type(width) is not int or type(height) is not int or min(width,height)<=0:
        raise ValueError("canvas dimensions must be positive integers")
    refs=source["product"]["image_refs"]
    if not refs: raise ValueError("product.image_refs needs a main image")
    divisor=gcd(width,height)
    # Defaults only use known normalized facts. Original explicit requirements override them.
    required = required_information
    if required is None:
        required=[source["product"]["name"] or source["product"]["category"]]
        required += list(source["product"]["selling_points"])
        required += [source["commerce"][k] for k in ("price_text","promotion_text","promotion_period","legal_text") if source["commerce"][k]]
        required += [source["marketing"]["cta"]] if source["marketing"]["cta"] else []
    brand_rules = brand_requirements
    if brand_rules is None:
        brand_rules=list(source["brand"]["required_elements"])+list(source["brand"]["forbidden_elements"])
    tags=style["tags"]
    data={"schema_version":"A-D-2.0","request_id":source["request_id"],"poster_image":poster_image,
          "source_input":deepcopy(source),"style_guide":deepcopy(style),"protected_content":deepcopy(protected),
          "evaluation_context":{"product_img":refs[0],"scene_tags":[str(tags[k]) if tags[k] is not None else "null" for k in ("audience_id","motivation_id","scenario_id")],
          "theme":theme,"required_information":list(required),"brand_requirements":list(brand_rules),
          "aspect_ratio":str(width//divisor)+":"+str(height//divisor),"orientation":"vertical" if height>width else "horizontal" if width>height else "square"},
          "loop_state":{"iteration":iteration,"version_id":version_id,"locked_dimensions":list(previous.get("locked_dimensions",[])) if previous else [],"previous_result":deepcopy(previous)}}
    errors=validate(data)
    if errors: raise ValueError("; ".join(errors))
    return data

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--style",required=True);p.add_argument("--protected",required=True)
    p.add_argument("--poster",required=True);p.add_argument("--output",required=True)
    p.add_argument("--version",default="v01");p.add_argument("--iteration",type=int,default=1)
    p.add_argument("--previous");p.add_argument("--brief-supplement")
    a=p.parse_args()
    supplement=normalize_supplement(load_json(a.brief_supplement) if a.brief_supplement else {})
    result=assemble(load_json(a.source),load_json(a.style),load_json(a.protected),a.poster,a.version,a.iteration,
                    load_json(a.previous) if a.previous else None,**supplement)
    write_json(a.output,result)
