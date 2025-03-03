# parse entries from a .xlsx file, go through the table and add the text in column G to an array if the corresponding cell in column C is true
import os
import re
import pandas as pd

import pprint as pp
import utilities as util

dir = os.getcwd()
  
def parseTagList(system_name, tag_info, VIEW_TAGS=False):

    global_symbols = tag_info["symbols"]
    cross_ref = tag_info["crossref"]
    scada_taglist = tag_info["scada_tags"]
    
    taglist = []

    ## VARIOUS tag_TYPES OF TAGS - for testing
    # address = "a120.011" # Does not exist
    # address = "120.01" # With Symbol and description
    # address = "CNT06100" # With symbol, no description
    # address = "11.04" # With Description, no symbol
    # address = "0.01" # No symbol or description
    # address = "100" # Word tag, not bit
    # address = "TIM069(bit)" # Symbol with (bit)
    # address = "HR01.00" # Weird tag structure
    # address = "0.02" # Physical I/O (for digital truncation in SCADA, ie. 0.02 vs IR0.2)

    ### PLC TAGS ###
    # Iterate through each row of the cross-ref list
    for rowindex, row in cross_ref.iterrows():
        # print(rowindex)
        
        address = row["Address"]
        detailed_address = util.expandTag(address)

        try: query = global_symbols.query(f'Address == "{address}"')
        except: query = global_symbols.query(f'Address == {address}')
        # print(address)

        if query.empty:
            # print("Tag does not have symbol or description")
            symbol = ""
            description = ""
            tag_type = ""
        else:
            # print(query)
            # print("Symbol or Description found")
            # only take the first result
            symbol = query["Symbol"].iloc[0]
            description = query["Description"].iloc[0]
            tag_type = query["Type"].iloc[0]
            # print(symbol, description, tag_type)

        detailed_address["tagname"] =  str(symbol)
        detailed_address["description"] = description
        detailed_address["tag_type"] = tag_type
        detailed_address["source"] = "PLC"
        detailed_address["alias"] = ""

        # break
        # Try to determine tag_type of tag
        detailed_address["tag_type"] = util.typeHandler(detailed_address)
        # print(detailed_address)

        # Convert to scada name then search for Scada tagname
        scada_tagname, scada_desc = util.checkForScadaTags(scada_taglist, detailed_address)

        # Create tagname and description
        tagname, tag_description = util.nameCreator(detailed_address, scada_tagname, scada_desc, system_name)

        # Assign tagname and description to detailed_address, as well as empty SCADA_tagname
        detailed_address["tagname"] = tagname
        detailed_address["description"] = tag_description
        detailed_address["SCADA_tagname"] = []
        
        # Before appending, check if tag already exists in taglist
        query = [tag for tag in taglist if tag["real_address"] == detailed_address["real_address"]]
        if query:
            # If tag already exists, take the longest tagname and description
            if len(tagname) > len(taglist[taglist.index(query[0])]["tagname"]):
                taglist[taglist.index(query[0])]["tagname"] = tagname
            if len(tag_description) > len(taglist[taglist.index(query[0])]["description"]):
                taglist[taglist.index(query[0])]["description"] = tag_description
        else:
            # Otherwise, append the tag to the list
            taglist.append(detailed_address)
        
        # break # Break to only run first one
        # if rowindex > 250: break # Break to only run first ten

    ### SCADA TAGS ###
    # Now go through SCADA taglist to see if any tags are missing
    for rowindex, row in scada_taglist.iterrows():
        # break

        address = row["Clean_Address"]
        original_address = address
        type = row["Type"]
        # print(address)

        # Convert tag address to PLC address
        address = util.scadaToPlcAddress(address)
        detailed_address = util.expandTag(address)

        # See if tag already exists in taglist, then add to SCADA_tagname column
        query = [tag for tag in taglist if tag["address"] == address]
        if query:
            # print("Tag already exists")
            # Tag has already been added, add it to the SCADA_Tag list
            query[0]["SCADA_tagname"].append(row["TAG"])
            query[0]["source"] = "BOTH"
            # print(query[0]["address"])
            
        else:
            # If tag does not exist, create tag
            # print("Tag does not exist in list. Adding tag:")
            detailed_address["address"] = address
            detailed_address["tagname"] = row["TAG"]
            detailed_address["description"] = row["DESCRIPTION"]
            # detailed_address["description"] = '"' + row["DESCRIPTION"] + '"'
            detailed_address["SCADA_tagname"] = [row["TAG"]]
            detailed_address["tag_type"] = ""
            detailed_address["source"] = "SCADA"
            detailed_address["alias"] = ""
            # print(tagname, tag_description, tagtype)
            
            detailed_address["tag_type"] = util.typeHandler(detailed_address)

             # Cannot have two underscores in a row
            tagname = re.sub('_+', '_', tagname)
            tagname = tagname.replace("-","_").replace("(","").replace(")","").replace(",","_").replace("/","")\
                .replace(" ","_").replace("|","").replace("*","").replace("#","").replace("<","")\
                .replace(">","").replace(":","").replace(";","").replace("=","").replace("+","")\
                .replace("%","").replace("$","").replace("@","").replace("!","").replace("^","")

            # print("Appending: ", address, tagname, tag_description, tagtype)
            taglist.append(detailed_address)

        # break # Break to only run first one
        # if rowindex > 6: break # Break to only run first x rungs

        # Order list by address
        # taglist = dict(sorted(taglist.items()))

    # Lastly go through the taglist and check for aliases
    util.check_for_aliases(taglist, system_name)
    
    if VIEW_TAGS:
        pp.pprint(taglist)

    return taglist
