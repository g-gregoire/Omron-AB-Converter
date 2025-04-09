import re
import pandas as pd
import math

DEBUG = False
TEST_TAG = "W20.01"

def expandTag(tag):
    """
    Extract tag into its components, including delimiting letters, suffix numbers, and type if clear
    """
    # Remove any spaces
    tag = str(tag).upper().replace(" ", "")
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
    elif prefix == "T" or prefix == "C":
        tag_num = f"{int(tag_num):04d}"
    else:
        tag_num = int(tag_num)
        tag_num = "{:d}".format(tag_num)

    # Create Compact address to handle things like T472 and T0472 (same tag)
    if prefix:
        compact_name = prefix + str(tag_num)
    else:
        compact_name = str(tag_num)

    if isinstance(tag, float):
        tag = float("{:.2f}".format(tag))

    # if compact_name == "5.11":
    #     print(tag, tag_num, compact_name)
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
    address = tag_detailed["real_address"]
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

    address = tag_detailed["real_address"]
    prefix = tag_detailed["prefix"]
    number = tag_detailed["number"]
    try: plc_symbol = tag_detailed["tagname"]
    except: plc_symbol = ""
    try: plc_description = tag_detailed["description"]
    except: plc_description = ""
    try: tag_type = tag_detailed["tag_type"]
    except: tag_type = ""
    try: parent = tag_detailed["parent"]
    except: parent = ""

    if DEBUG and (address.find(TEST_TAG) != -1): 
        print("Addr: ", address, "Type: ", tag_type)
    
    # if address == TEST_TAG: # Testing for specific tags
    #     print("Addr: ", address, "Tag: ", scada_tagname, "Desc: ", plc_description, "Type: ", tag_type)

    # if address == TEST_TAG: # Testing for specific tags
    #     print(address, prefix, number, plc_symbol, plc_description, scada_tagname, scada_description)

    # TAGNAME
    # Handle timer (TIM) tags - set to 4-digit format
    if tag_type == "TIMER" and scada_tagname == "" and plc_symbol == "" :
        prefix = prefix.replace("TIM", "T").replace("(bit)", "")
        number = f"{int(number):04d}"
        tagname = prefix + number
        # if address == TEST_TAG: # Testing for specific tags
        #     print(number, tagname)

    # Handle counter (CNT) tags
    elif tag_type == "COUNTER" and scada_tagname == "" and plc_symbol == "" :
        prefix = prefix.replace("CNT", "C").replace("(bit)", "")
        number = f"{int(number):04d}"
        tagname = prefix + number
    elif plc_symbol != "" and scada_tagname != "": # If we have both, use plc_symbol
        # print(2)
        tagname = plc_symbol.upper()
    elif scada_tagname == "" and plc_symbol != "": # If no SCADA tag, use plc_symbol (redundant)
        # print(2)
        tagname = plc_symbol.upper()
    elif plc_symbol == "" and scada_tagname != "": # If only scada tag, use scada_tagname
        # print(1)
        tagname = scada_tagname.upper()
        # suffix = tagname[-3:]
        # # Remove suffix if it is a scada _DO, _DI, _AO, _AI tag
        # if suffix == "_DI" or suffix == "_DO" or suffix == "_AI" or suffix == "_AO":
        #     tagname = tagname[:-3]
    elif scada_tagname == "" and plc_symbol == "" and scada_description != "": # If only scada description, create tagname from description
        # print(3)
        tagname = scada_description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
    elif scada_tagname == "" and plc_symbol == "" and scada_description == "" and plc_description != "": # If only PLC description, create tagname from description
        # print(4)
        # print(len(description))
        tagname = plc_description.upper().replace(".", "_").replace("/", "").replace("()", "").replace(")", "").split()[:4]
        tagname = "_".join(tagname)
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
    # if address == TEST_TAG: # Testing for specific tags
    #     print(number, tagname)

    # DESCRIPTION
    # Determine tag description to use
    if scada_description != "": # Use SCADA description if it exists
        tag_description = scada_description
    elif scada_description == "" and plc_description != "": # If no SCADA description, use PLC description
        tag_description = plc_description
    else: # If no description, use plc_symbol
        tag_description = plc_symbol
    # Add original address to description
    tag_description = tag_description + " (OMR " + address + ")"

    # Add timer suffix to tagname
    if tag_type == "TIMER":
        tagname = tagname + "_TMR"
    # Add counter suffix to tagname
    if tag_type == "COUNTER":
        tagname = tagname + "_CTR"

    # Check to replace 'MINUS' with '_'
    if tagname.find("MINUS") != -1:
        tagname = tagname.replace("MINUS", "_")

    ## Check for invalid characters
    # Remove (, ), , and / from tagname
    tagname = tagname.replace("-","_").replace("(","").replace(")","").replace(",","_").replace("/","")\
                .replace(" ","_").replace("|","").replace("*","").replace("#","").replace("<","")\
                .replace(">","").replace(":","").replace(";","").replace("=","").replace("+","")\
                .replace("%","").replace("$","").replace("@","").replace("!","").replace("^","")\
                .replace("&","").replace("'","")
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
    # if address == TEST_TAG: # Testing for specific tags
    #     print("end", number, tagname)

    return tagname, tag_description, parent

def checkForScadaTags(scada_taglist:pd.DataFrame, tag_detailed:dict):
    
    # 1. Convert PLC address to SCADA address
    tagname = tag_detailed["tagname"]
    address = tag_detailed["real_address"]
    tag_type = tag_detailed["tag_type"]
    number_only = tag_detailed["number"]
    prefix = tag_detailed["prefix"]
    tag = []

    if tagname == "": tagname = address

    if DEBUG and (address.find(TEST_TAG) != -1): print("OG:", address, tag, tagname, tag_type)

    # print(tagname, tag_detailed)
    if tag_type == "BOOL":
        # Handle timer (TIM) tags
        if tagname.find("TIM") >= 0:
            tagname = tagname.replace("TIM", "").replace("(bit)", "") + "_TMR"
            # tag.append(tagname)
        # Handle counter (CNT) tags
        elif tagname.find("CNT") >= 0:
            tagname = tagname.replace("CNT", "").replace("(bit)", "") + "_CTR"
            # tag.append(tagname)
        else:
            try:
                # This ensures the formatting of the bit part of the DINT is correct, ie.
                # 1.01 should search for 1.1
                # 1.1 should search for 1.10 (DANGER: This would cause issues)
                decimal = address.split(".")[1]
                if decimal[0] == "0": decimal = str(int(decimal))
                elif decimal == "1": decimal = "10"

                if prefix == "" or prefix == None: 
                    prefix = "CIO"
                    tagname = prefix + str(address.split('.')[0]) + "." + str(decimal)
                else:
                    tagname = str(address.split('.')[0]) + "." + str(decimal)
                    

                # tag.append(prefix + str(address.split('.')[0]) + "." + str(decimal))
                # tag.append("CIO" + str(address))
            except:
                # tag.append(tagname)
                pass
    
    # else:
        # tag.append(tagname)
    # print(tag)
    if DEBUG and (address.find(TEST_TAG) != -1): 
        print("Search Tags:", address, tag, tagname, tag_type)


    clean_tagname = str(tagname).strip()
    # query = scada_taglist.query(f'Clean_Address == {tagname}')
    query = scada_taglist.query(f'Clean_Address == @clean_tagname')

    if DEBUG and (address.find(TEST_TAG) != -1): 
        print("First", query)
    if query.empty:
        query = scada_taglist.query(f'Clean_Address == "{tagname}"')
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

def check_for_aliases(taglist, system_name, types_array):
    for tag in taglist:
        prefix = tag["prefix"]
        address = tag["real_address"]
        number = tag["number"]
        # print(address)
        if DEBUG and address == TEST_TAG: print(tag)

        whole_number = get_whole_number(number)

        # if another tag exists with the same prefix & number, but different address, add an alias
        for tag2 in taglist:
            whole_number2 = get_whole_number(tag2["number"])
            prefix2 = tag2["prefix"]
            if prefix == prefix2 and whole_number == whole_number2 and tag2["real_address"] != address:
                tag["alias"] = get_alias(tag, system_name)

                # Create array of all types found in prefix
                if prefix == None: prefix = "IR"
                if prefix not in types_array:
                    types_array.append(prefix)
                break
    
        if DEBUG and address == TEST_TAG: print(tag)
    
    return taglist, types_array

def get_whole_number(number:str):
    # Get integer value of tag number. ie. 1.01, 1.0 and 1 should all return 1
    try: whole_number = int(number)
    except: whole_number = int(number.split(".")[0])

    return str(whole_number)

def get_alias(tag, system_name):
    prefix = tag["prefix"]
    address = tag["real_address"]
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