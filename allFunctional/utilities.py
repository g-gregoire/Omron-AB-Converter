import re
import pandas as pd

def expandTag(tag):
    """
    Extract tag into its components, including delimiting letters, suffix numbers, and type if clear
    """
    # Remove any spaces
    tag = str(tag).replace(" ", "")
    # print(tag)

    # Extract the letters from the start, if any
    tag_name_match = re.search(r'^[a-zA-Z]+', tag)
    prefix = tag_name_match.group(0) if tag_name_match else None
    # Extract the tag number, with possible decimal. To deal with tags like T472 and T0472 (same tag)
    tag_num_match = re.search(r'\d+(\.\d+)?', tag)
    tag_num = tag_num_match.group(0) if tag_num_match else None
    if tag_num.find(".") >= 0:
        tag_num = float(tag_num)
        tag_num = "{:.2f}".format(tag_num)
    else:
        tag_num = int(tag_num)
        tag_num = "{:d}".format(tag_num)

    # Create Compact address to handle things like T472 and T0472 (same tag)
    if prefix:
        compact_name = prefix + str(tag_num)
    else:
        compact_name = str(tag_num)

    # Try to determine tag type
    # tag_type = typeHandler(tag, prefix, tag_num)

    tag_detailed = {
        "address": tag,
        "real_address": compact_name,
        "prefix": prefix,
        "number": tag_num,
    }
    # print(tag_detailed)

    return tag_detailed
    
def typeHandler(tag_detailed):
    address = tag_detailed["address"]
    prefix = tag_detailed["prefix"]
    number = tag_detailed["number"]
    tag_type = tag_detailed["tag_type"]

    # Handle timer (TIM) tags before all else
    if prefix == "T":
        return "TIMER"
    # Handle counter (CNT) tags before all else
    if prefix == "C":
        return "COUNTER"

    # Handle known types
    if tag_type != "":
        # Channel type is a REAL
        if tag_type == "CHANNEL":
            return "REAL"
        if tag_type == "BOOL":
            return tag_type
        if tag_type == "INT" or tag_type == "DINT" or tag_type == "WORD" or tag_type == "DWORD" or\
            tag_type == "NUMBER" or tag_type == "UDINT" or tag_type == "UINT":
            return "DINT"
        else:
            return "DINT"
        
    # Handle unknown types based on address formation.
    else:
        # If it's a full number (ie. 120), then it's a DINT, if it has a '.' then it's a BOOL
        if isinstance(number, int):
            # print("Address is numeric")
            return "DINT"
        if isinstance(number, float):
            # print("Address is decimal")
            return "BOOL"
    
    # If nothing caught, return "BOOL"
    return "BOOL"

def checkForScadaTags(scada_taglist:pd.DataFrame, tag_detailed:dict):
    
    # 1. Convert PLC address to SCADA address
    tagname = tag_detailed["tagname"]
    tag_type = tag_detailed["tag_type"]
    tag = []
    # print(tagname, tagtype)
    if tag_type == "BOOL":
        # Handle timer (TIM) tags
        if tagname.find("TIM") >= 0:
            tagname = tagname.replace("TIM", "").replace("(bit)", "") + "_TMR"
            tag.append(tagname)
        # Handle counter (CNT) tags
        elif tagname.find("CNT") >= 0:
            tagname = tagname.replace("CNT", "").replace("(bit)", "") + "_CTR"
            tag.append(tagname)
        else:
            try:
                tag.append("IR" + tagname.split('.')[0] + "." + str(int(tagname.split('.')[1])))
                tag.append("IR" + tagname)
            except:
                tag.append(tagname)
    else:
        tag.append(tagname)
    # print(tag)

    query = scada_taglist.query(f'Clean_Address == "{tag[0]}"')
    if query.empty and len(tag) > 1 and tag[1] != None:
        query = scada_taglist.query(f'Clean_Address == "{tag[1]}"')
    if query.empty:
        # print("Tag not found in SCADA")
        return "", ""
    # else:
        # print("Tag found in SCADA")

    scada_tagname = query["TAG"].to_string(index=False)
    scada_description = query["DESCRIPTION"].to_string(index=False) 
    
    # print(scada_tagname, scada_description)
    return scada_tagname, scada_description

def scadaToPlcAddress(scada_address:str):
    # Convert SCADA address to PLC address
    # print(scada_address)
    if scada_address.find(".") >= 0: # For BOOL IR tags (digital in/out)
        address = scada_address.replace("IR", "").replace("CIO","")
        split = address.split(".")
        if int(split[1]) < 10:
            return split[0] + ".0" + str(int(split[1]))
        else:
            return split[0] + "." + str(int(split[1]))
    elif scada_address.find("IR") >= 0: # For INT/REAL IR Tags (analog in/out)
        return scada_address.replace("IR", "")
    elif scada_address.find("CIO") >= 0: # For INT/REAL IR Tags (analog in/out)
        return scada_address.replace("CIO", "")
    else:
        return scada_address
 

def nameCreator(tag_detailed:dict, scada_tagname="", scada_description="", system_name=""):
    # print(address, symbol, description, scada_tagname, scada_description)
    # Determine tag name to use

    symbol = tag_detailed["tagname"]
    description = tag_detailed["description"]
    address = tag_detailed["address"]
    tag_type = tag_detailed["tag_type"]

    if scada_tagname != "": # Use symbol if it exists already
        # print(1)
        tagname = scada_tagname.upper()
    elif scada_tagname == "" and symbol != "": # If no SCADA tag, use symbol
        # print(2)
        tagname = symbol.upper()
    elif scada_tagname == "" and symbol == "" and scada_description != "": # If only scada description, create tagname from description
        # print(3)
        tagname = scada_description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
    elif scada_tagname == "" and symbol == "" and scada_description == "" and description != "": # If only description, create tagname from description
        # print(4)
        # print(len(description))
        tagname = description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
    # Handle timer (TIM) tags
    elif tag_type == "TIMER":
        tagname = address.replace("TIM", "T").replace("(bit)", "")
    # Handle counter (CNT) tags
    elif tag_type == "COUNTER":
        tagname = address.replace("CNT", "C").replace("(bit)", "")
    else: # If none exist, create tagname from address
        # print(5)
        split = address.split(".")
        tagname = system_name + "_ADDR_"
        for word in split:
            if word == split[-1]: tagname += word
            else: tagname = tagname + word + "_"
        # print(tagname)

    # Determine tag description to use
    if scada_description != "": # Use SCADA description if it exists
        tag_description = scada_description
    elif scada_description == "" and description != "": # If no SCADA description, use PLC description
        tag_description = description
    else: # If no description, use symbol
        tag_description = symbol

    # Add timer suffix to tagname
    if tag_type == "TIMER":
        tagname = tagname + "_TMR"
    # Add counter suffix to tagname
    if tag_type == "COUNTER":
        tagname = tagname + "_CTR"

    ## Check for invalid characters
    # Remove (, ), , and / from tagname
    tagname = tagname.replace("-","_").replace("(","").replace(")","").replace(",","_").replace("/","")\
                .replace(" ","_").replace("|","").replace("*","").replace("#","").replace("<","")\
                .replace(">","").replace(":","").replace(";","").replace("=","").replace("+","")\
                .replace("%","").replace("$","").replace("@","").replace("!","").replace("^","")

    # Cannot use hyphen in tagname
    if tagname.find("-") >= 0:
        tagname = tagname.replace("-","_")
    # First character cannot be an underscore
    if tagname[0] == "_":
        tagname = tagname[1:]
    # Last character cannot be an underscore
    if tagname[-1] == "_":
        tagname = tagname[:-1]
    # Cannot have two underscores in a row
    tagname = re.sub('_+', '_', tagname)
    # Tagname cannot start with a number
    if tagname[0].isnumeric():
        tagname = "Tag_" + tagname
    
    # Add quotes to description
    if tag_description != "":
        tag_description = '"' + tag_description + '"'

    # print(tagname, tag_description)
    return tagname, tag_description