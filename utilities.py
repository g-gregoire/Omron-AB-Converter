import re
import pandas as pd

TEST_TAG = "D32253"

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

    # print(address)

    # Handle timer (TIM) tags before all else
    if prefix == "T":
        return "TIMER"
    # Handle counter (CNT) tags before all else
    if prefix == "C":
        return "COUNTER"

    # Handle known types
    if tag_type != "":
        # print("Known type: ", tag_type)
        # print(tag_detailed)
        # Channel type is a REAL
        if tag_type == "CHANNEL" or tag_type == "NUMBER" or tag_type == "DWORD" or tag_type == "UINT"\
            or tag_type == "UDINT" or tag_type == "DINT":
            return "REAL"
        if tag_type == "BOOL":
            return tag_type
        if tag_type == "INT" or tag_type == "WORD":
            return "DINT"
        else:
            return "DINT"
        
    # Handle unknown types based on address formation.
    else:
        # print("No defined type")
        # Set all remaining D type tags to REAL
        if prefix == "D":
            return "REAL"
        # If it's a full number (ie. 120), then it's a DINT, if it has a '.' then it's a BOOL
        if number.find(".") >= 0:
            # print("Address is decimal")
            return "BOOL"
        elif number.isnumeric():
            # print("Address is numeric")
            return "DINT"
    
    # If nothing caught, return "BOOL"
    return "BOOL"

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
    # Determine tag name to use

    address = tag_detailed["address"]
    try: plc_symbol = tag_detailed["tagname"]
    except: plc_symbol = ""
    try: plc_description = tag_detailed["description"]
    except: plc_description = ""
    try: tag_type = tag_detailed["tag_type"]
    except: tag_type = ""
    try: parent = tag_detailed["parent"]
    except: parent = ""
    
    # if address == TEST_TAG: # Testing for specific tags
    #     print("Add: ", address, "Tag: ", scada_tagname, "Desc: ", plc_description)

    # if address == TEST_TAG: # Testing for specific tags
    #     print(address, plc_symbol, plc_description, scada_tagname, scada_description)

    # TAGNAME
    if plc_symbol != "" and scada_tagname != "": # If we have both, use plc_symbol
        # print(2)
        tagname = plc_symbol.upper()
    elif scada_tagname == "" and plc_symbol != "": # If no SCADA tag, use plc_symbol (redundant)
        # print(2)
        tagname = plc_symbol.upper()
    elif plc_symbol == "" and scada_tagname != "": # If only scada tag, use scada_tagname
        # print(1)
        tagname = scada_tagname.upper()
        suffix = tagname[-3:]
        # Remove suffix if it is a scada _DO, _DI, _AO, _AI tag
        if suffix == "_DI" or suffix == "_DO" or suffix == "_AI" or suffix == "_AO":
            tagname = tagname[:-3]
    elif scada_tagname == "" and plc_symbol == "" and scada_description != "": # If only scada description, create tagname from description
        # print(3)
        tagname = scada_description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
    elif scada_tagname == "" and plc_symbol == "" and scada_description == "" and plc_description != "": # If only PLC description, create tagname from description
        # print(4)
        # print(len(description))
        tagname = plc_description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
    # Handle timer (TIM) tags
    elif tag_type == "TIMER":
        tagname = address.replace("TIM", "T").replace("(bit)", "")
    # Handle counter (CNT) tags
    elif tag_type == "COUNTER":
        tagname = address.replace("CNT", "C").replace("(bit)", "")
    else: # If none exist, create tagname from address
        # print(5)
        tagname = "ADDR_" + address
        split = address.split(".") # Split address by period
        if len(split) > 1:
            parent_tag = split[0]
            parent = system_name + "_ADDR_" + parent_tag
        # Previously created new tag for each bit in a dint, now just add the dint to reduce tag count
        # for word in split:
        #     if word == split[-1]: tagname += word
        #     else: tagname = tagname + word + "_"
        # tagname += split[0] 
    prefix = tagname[:4]
    if prefix != "EXT_": # Only add system name if it is not already there
        tagname = system_name + "_" + tagname
        # print(tagname)

    # DESCRIPTION
    # Determine tag description to use
    if scada_description != "": # Use SCADA description if it exists
        tag_description = scada_description
    elif scada_description == "" and plc_description != "": # If no SCADA description, use PLC description
        tag_description = plc_description
    else: # If no description, use plc_symbol
        tag_description = plc_symbol

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

    # if address == TEST_TAG: # Testing for specific tags
    #     print("Add: ", address, "Tag: ", tagname, "Desc: ", tag_description)

    return tagname, tag_description, parent

def checkForScadaTags(scada_taglist:pd.DataFrame, tag_detailed:dict):
    
    # 1. Convert PLC address to SCADA address
    tagname = tag_detailed["tagname"]
    address = tag_detailed["address"]
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
                # This ensures the formatting of the bit part of the DINT is correct (ie. 1.01 instead of 1.1)
                tag.append("CIO" + str(address.split('.')[0]) + "." + str(int(address.split('.')[1])))
                tag.append("CIO" + str(address))
            except:
                tag.append(tagname)
    else:
        tag.append(tagname)
    # print(tag)
    # if address == TEST_TAG: # Testing for specific tags
    #     print(address, tagname, tag_type)
    #     print(tag)

    query = scada_taglist.query(f'Clean_Address == "{tag[0]}"')
    if query.empty and len(tag) > 1 and tag[1] != None:
        query = scada_taglist.query(f'Clean_Address == "{tag[1]}"')
    if query.empty:
        # print("Tag not found in SCADA")
        return "", ""
    # else:
        # print("Tag found in SCADA")

    if not query.empty and len(query) > 1: # If multiple tags found, choose the first one
        query = query.iloc[0]
        scada_tagname = query["TAG"]
        scada_description = query["DESCRIPTION"]
    else:
        scada_tagname = query["TAG"].to_string(index=False)
        scada_description = query["DESCRIPTION"].to_string(index=False) 
    
    # print(scada_tagname, scada_description)
    return scada_tagname, scada_description

def check_for_aliases(taglist, system_name):
    for tag in taglist:
        prefix = tag["prefix"]
        address = tag["address"]
        number = tag["number"]
        # print(address)

        whole_number = get_whole_number(number)

        # if another tag exists with the same prefix & number, but different address, add an alias
        for tag2 in taglist:
            whole_number2 = get_whole_number(tag2["number"])
            prefix2 = tag2["prefix"]
            if prefix == prefix2 and whole_number == whole_number2 and tag2["address"] != address:
                tag["alias"] = get_alias(tag, system_name)
                break
    
    return taglist
        

def get_whole_number(number:str):
    # Get integer value of tag number. ie. 1.01, 1.0 and 1 should all return 1
    try: whole_number = int(number)
    except: whole_number = int(number.split(".")[0])

    return str(whole_number)

def get_alias(tag, system_name):
    prefix = tag["prefix"]
    address = tag["address"]
    number = tag["number"]

    # Check if decimal value or not
    if number.find(".") >= 0:
        int_number = number.split(".")[0]
        bit_number = number.split(".")[1]
    else:
        int_number = number
        bit_number = None
    
    # Check for None bit
    if prefix == None: prefix = "IR"

    # Add alias to tag
    if bit_number:
        alias = f"{system_name}_{prefix}_array[{int_number}].{bit_number}"
    else:
        alias = f"{system_name}_{prefix}_array[{int_number}]"

    # print(alias)
    return alias