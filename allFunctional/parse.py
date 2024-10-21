# parse entries from a .xlsx file, go through the table and add the text in column G to an array if the corresponding cell in column C is true
import os
import re
import pandas as pd
import pprint as pp

import file_functions as f

dir = os.getcwd()
  
def parseList(filename="", CONVERT_SCADA=False):

    if filename == "":
        filename = "IDH_PLC_Tags.xlsx" #use if nothing given by main file

    system_name = f.getSystemName(filename)
    
    # Set input dir
    _, input_dir, _, _ = f.getDirectories(dir)
    os.chdir(input_dir)
    file = os.path.join(input_dir, filename)
        
    # To open Workbook 
    # List of Symbols with either Tagnames or Descriptions
    global_symbols = pd.read_excel(file, sheet_name = 1)
    global_symbols = global_symbols.fillna('')
    # print(global_symbols.head())

    # Full list of all tags used in program (Cross-ref)
    full_taglist = pd.read_excel(file, sheet_name = 2)
    full_taglist = full_taglist.fillna('')
    # print(full_taglist.head())

    # List of all tags used in SCADA
    scada_taglist = pd.read_excel(file, sheet_name = 6)
    scada_taglist = scada_taglist.fillna('')
    # print(scada_taglist.head())
    
    taglist = []

    ## VARIOUS TYPES OF TAGS 
    # address = "a120.011" # Does not exist
    # address = "120.01" # With Symbol and description
    # address = "CNT06100" # With symbol, no description
    # address = "11.04" # With Description, no symbol
    # address = "0.01" # No symbol or description
    # address = "100" # Word tag, not bit
    # address = "TIM069(bit)" # Symbol with (bit)
    # address = "HR01.00" # Weird tag structure
    # address = "0.02" # Physical I/O (for digital truncation in SCADA, ie. 0.02 vs IR0.2)

    # Iterate through each row of the cross-ref list
    for rowindex, row in full_taglist.iterrows():
        # print(rowindex)
        
        address = row["Address"].replace("(bit)","")
        # print(address)
        if address.find("HR") >= 0 or address.find("AR") >= 0:
            # print(0)
            query = global_symbols.query(f'Address == "{address}"')
        elif address.find(".") >= 0:
            # print(1)
            query = global_symbols.query(f'Address == "{address}"')
        elif address.isnumeric():
            # print(1)
            query = global_symbols.query(f'Address == {address}')
        else:
            # print(2)
            query = global_symbols.query(f'Address == "{address}"')
        # print(query)
    
        if query.empty:
            # print("Tag does not have symbol or description")
            symbol = ""
            description = ""
        else:
            # print("Tag found")
            symbol =  query["Symbol"].to_string(index=False)
            description = query["Description"].to_string(index=False)


        # Try to determine type of tag
        tagType = typeFinder(row["Address"], query)

        # Convert to scada name then search for Scada tagname
        scada_tagname, scada_desc = checkForScadaTags(scada_taglist, row["Address"], tagType)

        tagname, tag_description = nameCreator(address, symbol, description, scada_tagname, scada_desc, system_name)
        
        # print("Appending: ", address, tagname, tag_description, tagType)
        taglist.append({
            "address" : address,
            "tagname" : tagname,
            "description" : tag_description,
            "type" : tagType
        })
        
        # print(taglist)
        # break # Break to only run first one
        # if rowindex > 250: break # Break to only run first ten
    
    # Now go through SCADA taglist to see if any tags are missing
    for rowindex, row in scada_taglist.iterrows():

        address = row["Clean_Address"]
        # print(address)

        # Convert tag address to PLC address
        address = scadaToPlcAddress(address)
        # print(address)

        # See if tag already exists in taglist
        query = [tag for tag in taglist if tag["address"] == address]
        if query:
            # print("Tag already exists")
            # Tag has already been added, so skip
            continue
            
        else:
            # If tag does not exist, create tag
            # print("Tag does not exist in list. Adding tag:")
            tagname = row["TAG"]
            tag_description = '"' + row["DESCRIPTION"] + '"'
            tagType = typeFinder(address)
            # print(tagname, tag_description, tagType)

             # Cannot have two underscores in a row
            tagname = re.sub('_+', '_', tagname)
            tagname = tagname.replace("-","_").replace("(","").replace(")","").replace(",","_").replace("/","")\
                .replace(" ","_").replace("|","").replace("*","").replace("#","").replace("<","")\
                .replace(">","").replace(":","").replace(";","").replace("=","").replace("+","")\
                .replace("%","").replace("$","").replace("@","").replace("!","").replace("^","")

            # print("Appending: ", address, tagname, tag_description, tagType)
            taglist.append({
                "address" : address,
                "tagname" : tagname,
                "description" : tag_description,
                "type" : tagType
            })

        # break # Break to only run first one
        # if rowindex > 6: break # Break to only run first x rungs

        # Order list by address
        # taglist = dict(sorted(taglist.items()))
    
    return taglist


def typeFinder(address:str, tagQuery:pd.DataFrame = pd.DataFrame()):
    # Handle timer (TIM) tags
    if re.match(r'TIM\d{3}', address):
        return "TIMER"
    # Handle counter (CNT) tags
    if re.match(r'CNT\d{3}', address):
        return "COUNTER"
    if address.find("(bit)") >= 0: # Deal with explicit Bit definitions first
        return "BOOL"
    # Timers match TIMxxx format with regex
    if address.find("_TMR") >= 0:
        return "TIMER"
    # Counters match CNTxxx format with regex
    if address.find("_CTR") >= 0:
        return "COUNTER"
    if not tagQuery.empty: # Use Type if already specified
        if tagQuery["Type"].to_string(index=False) == "CHANNEL":
            return "REAL"
        return tagQuery["Type"].to_string(index=False) # If it's a CHANNEL tag, then it's an REAL
    if address.find(".") >= 0: # If there's a '.' then it's a Bool
        return "BOOL"
    if address.isnumeric(): # If it's a full number (ie. 120), then it's an INT (or word)
        return "DINT"
    if address.find("DM") >= 0: # If it's a DMxxx tag, then it's an INT/word
        return "DINT"
    
    # If nothing catches, return "UNKNOWN"
    return "BOOL"

def scadaToPlcAddress(scada_address:str):
    # Convert SCADA address to PLC address
    # print(scada_address)
    if scada_address.find(".") >= 0: # For BOOL IR tags (digital in/out)
        address = scada_address.replace("IR", "")
        split = address.split(".")
        if int(split[1]) < 10:
            return split[0] + ".0" + str(int(split[1]))
        else:
            return split[0] + "." + str(int(split[1]))
    elif scada_address.find("IR") >= 0: # For INT/REAL IR Tags (analog in/out)
        return scada_address.replace("IR", "")
    else:
        return scada_address
    
def checkForScadaTags(scada_taglist:pd.DataFrame, tagname:str, tagtype:str):
    # Convert PLC address to SCADA address
    tag = []
    # print(tagname, tagtype)
    if tagtype == "BOOL":
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


def nameCreator(address:str, symbol="", description="", scada_tagname="", scada_description="", system_name=""):
    # print(address, symbol, description, scada_tagname, scada_description)
    # Determine tag name to use

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
    elif re.match(r'TIM\d{3}', address):
        tagname = address.replace("TIM", "T").replace("(bit)", "") + "_TMR"
    # Handle counter (CNT) tags
    elif re.match(r'CNT\d{3}', address):
        tagname = address.replace("CNT", "C").replace("(bit)", "") + "_CTR"
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

#%% Execute code
