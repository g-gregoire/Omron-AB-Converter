import file_functions as ff
import lookup as lk
import logic_converter as lc
import tag_functions as tf
import parse

import pandas as pd
import traceback
import os

dir = os.getcwd()

def getTagContents(tag_info_filename):
    # This file is used to extract the following files for use throughout the conversion processes
    # 1. PLC Tag List
    # 2. SCADA Tag List
    # 3. PLC Logic File

    # Get all directories
    _, input_dir, _, _ = ff.getDirectories(dir)

    # Get System Name
    system_name = ff.getSystemName(tag_info_filename)

    # Set input dir
    os.chdir(input_dir)

    # 1. Extract PLC Tag List
    file = os.path.join(input_dir, tag_info_filename)

    # List of Symbols with either Tagnames or Descriptions
    global_symbols = pd.read_excel(file, sheet_name = 0)
    global_symbols = global_symbols.fillna('')
    # print(global_symbols.head())

    # Full list of all addresses used in program (Cross-ref)
    cross_ref = pd.read_excel(file, sheet_name = 1)
    cross_ref = cross_ref.fillna('')
    # print(cross_ref.head())

    # List of all tags used in SCADA
    scada_taglist = pd.read_excel(file, sheet_name = 2)
    scada_taglist = scada_taglist.fillna('') # This list has been manually updated to remove duplicates
    # print(scada_taglist.head())

    plc_taglist = {
        "symbols": global_symbols, 
        "crossref": cross_ref, 
        "scada_tags": scada_taglist
    }

    # print(plc_taglist)

    print("Tag Files extracted successfully")
    return plc_taglist

def getLogicContents(logic_input_filename):
    # This file is used to extract the following files for use throughout the conversion processes
    # 1. PLC Logic File

    # Get all directories
    _, input_dir, _, _ = ff.getDirectories(dir)

    # Set input dir
    os.chdir(input_dir)

    # 3. Extract PLC Logic File
    # Open input file & create output file
    plc_logic_file = ff.openFile(logic_input_filename)
    plc_logic_file = ff.prepareFile(plc_logic_file) # Remove everything except the Mnemonic section

    # print(plc_logic_file)

    print("Logic File extracted successfully")
    return plc_logic_file

def readTagLookup(tag_lookup_filename):
    # Read in tag lookup file

    # Get all directories
    _, input_dir, _, _ = ff.getDirectories(dir)

    # Get System Name
    system_name = ff.getSystemName(tag_lookup_filename)

    # Set input dir
    os.chdir(input_dir)

    # 1. Extract PLC Tag List
    file = os.path.join(input_dir, tag_lookup_filename)

    tag_lookup = pd.read_csv(file)
    tag_lookup = tag_lookup.fillna('')
    # print(tag_lookup.head())

    return tag_lookup

def tagConversion(system_name, tag_info, scada_tag_export_filename, tag_output_filename, CREATE_TAGS = True, VIEW_TAGS=False, CREATE_LOOKUP = True, CONVERT_SCADA_TAGS = True):

    sys_name = system_name[0]
    sys_name_short = system_name[1]

    global_symbols = tag_info["symbols"]
    cross_ref = tag_info["crossref"]
    scada_taglist = tag_info["scada_tags"]

    # Create file to be used for tag import
    if CREATE_TAGS:
        print("Creating tags")
        # Create tag output file
        tag_import_file = ff.create_plc_tag_import_file(sys_name_short)
        # Parse input file for tag information
        tagList, types_array = parse.parseTagList(sys_name_short, tag_info, VIEW_TAGS)
        # print(types_array)

        # Create underlying arrays from List
        for alias_type in types_array:
            tag_import_file = ff.addTag(alias_type, tag_import_file, sys_name_short, BASE_ALIAS=True)
        
        # Create tags from List
        # tag_import_file = rung.createTags(tagList, tag_import_file, output_filename)
        for tag in tagList:
            # Check if tag has a parent
            if tag['parent'] != "":
                # Then check if parent already exists in tag list
                # Create parent address tag
                parent_address = tag["real_address"].split(".")[0]
                parent_alias = tag["alias"].split(".")[0]
                # Check if parent address already exists
                query = [parent for parent in tagList if parent['real_address'] == parent_address]
                if (len(query) == 0):
                    # If parent does not exist, log the existing tag and then create a parent tag too
                    tag_import_file = ff.addTag(tag, tag_import_file)
                    new_tag = {
                        "address": parent_address,
                        "real_address": parent_address,
                        "prefix": tag["prefix"],
                        "tagname": tag["parent"],
                        "description": "",
                        "tag_type": "DINT",
                        "source": "PLC"
                    }
                    tag_import_file = ff.addTag(new_tag, tag_import_file)
                else: pass
            else:
                tag_import_file = ff.addTag(tag, tag_import_file)
            # print(tag['symbol'], tag['description'], tag['tag_type'])
        # tag_import_file.close()

        if CREATE_LOOKUP:
            # Create General Lookup file for PLC and SCADA tags
            tag_lookup = ff.createLookupTable(tagList, tag_output_filename, sys_name_short)
            # tag_lookup = pd.DataFrame(tagList)

            if CONVERT_SCADA_TAGS:
                # Create Scada tag lookup file
                scada_lookup = tf.createSCADAoutput(sys_name_short, scada_taglist, tag_lookup)

                # Separate SCADA export into multiple tables
                scada_subtables = tf.extractScadaTags(scada_tag_export_filename)
                # Update subtables with new tag names and plc addresses
                updated_subtables = tf.updateScadaTags(scada_subtables, scada_lookup)
                # Recombine subtables and save to file
                tf.regroupScadaTables(sys_name_short, updated_subtables)

        else:
            tag_lookup = None


    print("Tag conversion complete")
    
    return tag_lookup, tag_import_file

def logicConversion(system_name, logic_input_file, tag_lookup, instr_count_total, output_filename="logic.txt", CONVERT=False, VIEW_RUNGS=False, COUNT_INSTR=False, PRINT_ERRORS=False):

    sys_name = system_name[0]
    sys_name_short = system_name[1]
    # system_name = "Sterilizer"

    # Initialize variables
    catchErrors = None
    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number
    
    # Open input file & create output file
    print("Creating conversion files")
    logic_wb = ff.openFile(logic_input_file)
    logic_wb = ff.prepareFile(logic_wb) # Remove everything except the Mnemonic section
    output_file, simple_output = ff.createFile(output_filename, logic_input_file, simple_output=True)
    output_file = ff.addContext(output_file, logic_input_file, sys_name) # Add required headers, etc.

    # Add specific logic chunks
    if COUNT_INSTR:
        print("Begin instruction count")
        _, instr_count_total = lc.countInstructions(logic_wb, instr_count_total)

    if CONVERT:
        # Convert the rungs to ladder logic
        print("Begin logic conversion")
        try:
            routine = lc.extract_rungs(logic_wb) # Extracts comments and rungs into routine object
            routine, catchErrors = lc.loop_rungs_v2(output_file, simple_output, routine, tag_lookup, sys_name_short, view_rungs=VIEW_RUNGS, num_rungs=-1) # Converts rungs to ladder logic
        except Exception as e:
            routine.rungs = [rung for rung in routine.rungs if rung.num != 0] # Filter out rungs with num == 0
            print("\nConversion failed on rung", routine.rungs[-1].num)
            print("Rung Logic:")
            print( routine.rungs[-1].original)
            print("Failed with error: ", e,  lk.NL)
            traceback.print_exc()

    if PRINT_ERRORS:
        if catchErrors != None:
            if catchErrors["count"] == 0:
                print("No errors in conversion")
            else:
                print("Errors: ", catchErrors)
    
    # Add footer at the end
    output_file = ff.addFooter(output_file)

    output_file.close()

    return instr_count_total
