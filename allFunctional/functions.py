import file_functions as f
import lookup as lk
import logic_converter as lc
import tag_functions as tf
import parse

import pandas as pd
import traceback
import os

dir = os.getcwd()

def getFileContents(tag_input_filename, scada_input_filename, logic_input_filename):
    # This file is used to extract the following files for use throughout the conversion processes
    # 1. PLC Tag List
    # 2. SCADA Tag List
    # 3. PLC Logic File

    # Get all directories
    _, input_dir, output_dir, _ = f.getDirectories(dir)

    # Get System Name
    system_name = f.getSystemName(tag_input_filename)

    # Set input dir
    os.chdir(input_dir)

    # 1. Extract PLC Tag List
    file = os.path.join(input_dir, tag_input_filename)

    # List of Symbols with either Tagnames or Descriptions
    global_symbols = pd.read_excel(file, sheet_name = 1)
    global_symbols = global_symbols.fillna('')
    # print(global_symbols.head())

    # Full list of all tags used in program (Cross-ref)
    cross_ref = pd.read_excel(file, sheet_name = 2)
    cross_ref = cross_ref.fillna('')
    # print(cross_ref.head())

    # List of all tags used in SCADA
    scada_taglist = pd.read_excel(file, sheet_name = 6)
    scada_taglist = scada_taglist.fillna('') # This list has been manually updated to remove duplicates
    # print(scada_taglist.head())

    plc_taglist = [global_symbols, cross_ref, scada_taglist]

    # 2. Extract PLC Tag List
    file = os.path.join(input_dir, scada_input_filename)

    # Read SCADA input file
    if system_name == "IDH":
        scada_taglist = pd.read_excel(file, sheet_name = 1)
    elif system_name == "Sterilizer":
        scada_taglist = pd.read_excel(file, sheet_name = 3)
    else:
        scada_taglist = pd.read_excel(file, sheet_name = 0)
    scada_taglist = scada_taglist.fillna('')
    # print(scada_taglist.head())


    # 3. Extract PLC Logic File
    # Open input file & create output file
    plc_logic_file = f.openFile(logic_input_filename)
    plc_logic_file = f.prepareFile(plc_logic_file) # Remove everything except the Mnemonic section

    return plc_taglist, scada_taglist, plc_logic_file


def tagConversion(tag_input_filename, tag_filename, scada_taglist, output_filename, CREATE_TAGS = True, CREATE_LOOKUP = True, CONVERT_SCADA_TAGS = True):

    # Create file to be used for tag import
    if CREATE_TAGS:
        # Create tag output file
        tag_import_file = f.createTagFile(output_filename, system_ref = tag_input_filename)
        # Parse input file for tag information
        tagList = parse.parseList(tag_input_filename, scada_taglist)
        # Create tags from List
        # tag_import_file = rung.createTags(tagList, tag_import_file, output_filename)
        for tag in tagList:
            tag_import_file = f.addTag(tag['tagname'], tag['description'] , tag['type'], tag_import_file)
            # print(tag['symbol'], tag['description'], tag['type'])
        # tag_import_file.close()

        if CREATE_LOOKUP:
            # Create General Lookup file for PLC and SCADA tags
            tag_lookup = f.createExcel(tagList, tag_filename, tag_input_filename)
            # tag_lookup = pd.DataFrame(tagList)


        if CONVERT_SCADA_TAGS:
            # Create Excel file for tag import
            scada_file = tf.createSCADAoutput(tag_input_filename, scada_taglist, tag_lookup)

    return tag_lookup, tag_import_file

def logicConversion(logic_input_file, tag_lookup, tag_import_file, output_filename="logic.txt", CONVERT=False, VIEW_RUNGS=False, COUNT_INSTR=False, PRINT_ERRORS=False):

    system_name = f.getSystemName(logic_input_file)
    # system_name = "Sterilizer"

    # Initialize variables
    catchErrors = None
    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number
    
    # Open input file & create output file
    logic_wb = f.openFile(logic_input_file)
    logic_wb = f.prepareFile(logic_wb) # Remove everything except the Mnemonic section
    output_file = f.createFile(output_filename, logic_input_file)
    output_file = f.addContext(output_file, system_name)

    # Add specific logic chunks
    if COUNT_INSTR:
        lc.countInstructions(logic_wb)

    if CONVERT:
        # Convert the rungs to ladder logic
        try:
            catchErrors = lc.loop_rungs(logic_wb, output_file, tag_lookup, view_rungs=VIEW_RUNGS, num_rungs=-1, system_name= system_name)
            print("Conversion complete")
        except Exception as e:
            print("Conversion failed: ", e)
            traceback.print_exc()

    if PRINT_ERRORS:
        if catchErrors != None:
            if catchErrors["count"] == 0:
                print("No errors in conversion")
            else:
                print("Errors: ", catchErrors)

    # Add footer at the end
    output_file = f.addFooter(output_file)

    output_file.close()

    # return tagfile
    return
