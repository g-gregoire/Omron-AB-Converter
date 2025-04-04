# parse entries from a .xlsx file, go through the table and add the text in column G to an array if the corresponding cell in column C is true
import os
import re
import pandas as pd

import pprint as pp
import utilities as util

dir = os.getcwd()

# Debugging and specific tag testing
DEBUG = False
TEST_TAG = "T0245"

def parseTagList(system_name, tag_info, VIEW_TAGS=False):

    global_symbols = tag_info["symbols"]
    cross_ref = tag_info["crossref"]
    scada_taglist = tag_info["scada_tags"]
    
    taglist = []
    types_array = []

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

    ### PLC TAGS - Cross-Reference ###
    for rowindex, row in cross_ref.iterrows():
    # Iterate through each row of the cross-ref list
        # print(rowindex)
        
        address = row["Address"]
        if address == "": continue
        detailed_address = util.expandTag(address)
        address = detailed_address["real_address"]
        if DEBUG and (address.find(TEST_TAG) != -1): print(address, detailed_address)


        query = global_symbols.query(f'Address == "{address}"')
        # if DEBUG and (address.find(TEST_TAG) != -1): 
            # print("First", query)
            # print("Type:", type(global_symbols["Address"].iloc[0]))
        if query.empty: 
            # print("Empty query", address)
            try: 
                query = global_symbols.query(f'Address == {address}')
                # if DEBUG and (address.find(TEST_TAG) != -1): 
                    # print("Second", query)
                    # print("Type:", type(global_symbols["Address"].iloc[0]))
            except:
                # print("Failed both query", address)
                query = pd.DataFrame()
        if DEBUG and (address.find(TEST_TAG) != -1): print(address, query)
        # print(address)

        if query.empty:
            # print("Tag does not have symbol or description")
            symbol = ""
            description = ""
            tag_type = ""
            scada_tagname = ""
            scada_desc = ""
        else:
            # print(query)
            # print("Symbol or Description found")
            # only take the first result
            symbol = query["Symbol"].iloc[0]
            description = query["Description"].iloc[0]
            tag_type = query["Type"].iloc[0]
            # print(symbol, description, tag_type)

        # Set default values to be used in NameCreator
        detailed_address["tagname"] =  str(symbol)
        detailed_address["description"] = description
        detailed_address["tag_type"] = tag_type
        detailed_address["source"] = "PLC"
        detailed_address["alias"] = ""
        detailed_address["parent"] = ""

        # break
        # Try to determine tag_type of tag
        detailed_address["tag_type"] = util.typeHandler(detailed_address)
        # print(detailed_address)

        # Convert to scada name then search for Scada tagname
        scada_tagname, scada_desc = util.checkForScadaTags(scada_taglist, detailed_address)
        if DEBUG and (address.find(TEST_TAG) != -1): print(address, scada_tagname, scada_desc)

        # Create tagname and description
        tagname, tag_description, parent = util.nameCreator(detailed_address, scada_tagname, scada_desc, system_name)
        if DEBUG and (address.find(TEST_TAG) != -1): print(address, tagname, tag_description, parent)

        # Assign tagname and description to detailed_address, as well as empty SCADA_tagname
        detailed_address["tagname"] = tagname
        detailed_address["description"] = tag_description
        if parent:
            detailed_address["parent"] = parent
        detailed_address["SCADA_tagname"] = []


        # Before appending, check if tag address already exists in taglist
        query = [tag for tag in taglist if tag["real_address"] == detailed_address["real_address"]]
        if query:
            # If tag already exists, take the longest tagname and description
            if len(tagname) > len(taglist[taglist.index(query[0])]["tagname"]):
                taglist[taglist.index(query[0])]["tagname"] = tagname
            if len(tag_description) > len(taglist[taglist.index(query[0])]["description"]):
                taglist[taglist.index(query[0])]["description"] = tag_description
        else:
            # Before appending, check if tagname already exists in taglist
            tagname_suffix = 1
            base_tagname = detailed_address["tagname"]
            query = [tag for tag in taglist if tag["tagname"] == detailed_address["tagname"]]
            if query:
                # If tag already exists, add a suffix to the tagname
                # print(query)
                while query:
                    # print("Tag already exists, adding suffix", detailed_address["tagname"])
                    tagname_suffix += 1
                    detailed_address["tagname"] = base_tagname + "_" + str(tagname_suffix)
                    query = [tag for tag in taglist if tag["tagname"] == detailed_address["tagname"]]

            # Otherwise, append the tag to the list
            taglist.append(detailed_address)
        
        # break # Break to only run first one
        # if rowindex > 250: break # Break to only run first ten

    
    ### SCADA TAGS ###
    for rowindex, row in scada_taglist.iterrows():
    # Now go through SCADA taglist to see if any tags are missing
        # break

        address = row["Clean_Address"]
        original_address = address
        tag_type = row["Type"]
        scada_tagname = row["TAG"]
        scada_description = row["DESCRIPTION"]
        # print(address)

        # Convert tag address to PLC address
        address = util.scadaToPlcAddress(address)
        detailed_address = util.expandTag(address)
        address = detailed_address["real_address"]
        tagname, tag_description, parent = util.nameCreator(detailed_address, scada_tagname, scada_description, system_name)

        # See if tag already exists in taglist, then add to SCADA_tagname column
        query = [tag for tag in taglist if tag["real_address"] == address]
        if query:
            # print("Tag already exists")
            # Tag has already been added, add it to the SCADA_Tag list
            query[0]["SCADA_tagname"].append(row["TAG"])
            query[0]["source"] = "BOTH"
            # print(query[0]["address"])
            
        else:
            # If tag does not exist, create tag
            # print("Tag does not exist in list. Adding tag:")
            detailed_address["real_address"] = address
            detailed_address["tagname"] = tagname
            detailed_address["description"] = tag_description
            # detailed_address["description"] = '"' + row["DESCRIPTION"] + '"'
            detailed_address["SCADA_tagname"] = [row["TAG"]]
            detailed_address["tag_type"] = ""
            detailed_address["source"] = "SCADA"
            detailed_address["alias"] = ""
            detailed_address["parent"] = ""
            # print(tagname, tag_description, tagtype)
            
            detailed_address["tag_type"] = util.typeHandler(detailed_address)

            # print("Appending: ", address, tagname, tag_description, tagtype)
            taglist.append(detailed_address)

        # break # Break to only run first one
        # if rowindex > 6: break # Break to only run first x rungs

        # Order list by address
        # taglist = dict(sorted(taglist.items()))

    # Lastly go through the taglist and check for aliases
    taglist, types_array = util.check_for_aliases(taglist, system_name, types_array)
    # taglist = util.check_for_aliases(taglist, system_name)
    
    if VIEW_TAGS:
        print("Taglist:")
        pp.pprint(taglist)

    return taglist, types_array
