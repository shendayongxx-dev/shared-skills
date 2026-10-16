def check(value, schema, path="$"):
    errors=[]
    types={"object":dict,"array":list,"string":str,"integer":int,"number":(int,float),"boolean":bool,"null":type(None)}
    names=schema.get("type",[])
    if isinstance(names,str): names=[names]
    if names and not any(isinstance(value,types[n]) and (n not in ("integer","number") or not isinstance(value,bool)) for n in names):
        return [path+": wrong type"]
    if "const" in schema and value!=schema["const"]: errors.append(path+": wrong version/value")
    if "enum" in schema and value not in schema["enum"]: errors.append(path+": unknown value")
    if isinstance(value,dict):
        props=schema.get("properties",{})
        errors += [path+"."+k+": required" for k in schema.get("required",[]) if k not in value]
        if schema.get("additionalProperties") is False: errors += [path+"."+k+": unexpected" for k in value if k not in props]
        for k in value:
            if k in props: errors += check(value[k],props[k],path+"."+k)
    if isinstance(value,list):
        if len(value)<schema.get("minItems",0) or len(value)>schema.get("maxItems",float("inf")): errors.append(path+": invalid length")
        if schema.get("uniqueItems") and len(set(map(str,value)))!=len(value): errors.append(path+": duplicates")
        for i,x in enumerate(value): errors += check(x,schema.get("items",{}),path+"["+str(i)+"]")
    if isinstance(value,str) and len(value)<schema.get("minLength",0): errors.append(path+": empty")
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if value<schema.get("minimum",-float("inf")) or value>schema.get("maximum",float("inf")): errors.append(path+": out of range")
    return errors
