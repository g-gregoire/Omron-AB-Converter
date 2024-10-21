import file_functions as f
import lookup as lk
import logic_converter as lc
import tag_functions as tf
import parse

import pandas as pd
import traceback

def tagConversion(tag_input_filename, tag_filename, scada_input_filename, output_filename, CREATE_TAGS = False, CREATE_EXCEL = False, CONVERT_SCADA_TAGS = False):

    # Create file to be used for tag import
    if CREATE_TAGS:
        # Create tag output file
        tag_import_file = f.createTagFile(output_filename, system_ref = tag_input_filename)
        # Parse input file for tag information
        tagList = parse.parseList(filename=tag_input_filename)
        # Create tags from List
        # tag_import_file = rung.createTags(tagList, tag_import_file, output_filename)
        for tag in tagList:
            tag_import_file = f.addTag(tag['tagname'], tag['description'] , tag['type'], tag_import_file)
            # print(tag['symbol'], tag['description'], tag['type'])
        # tag_import_file.close()

        if CREATE_EXCEL:
            # Create Excel file for tag import
            tag_lookup = f.createExcel(tagList, tag_filename, tag_input_filename)
            # tag_lookup = pd.DataFrame(tagList)


        if CONVERT_SCADA_TAGS:
            # Create Excel file for tag import
            scada_file = tf.createSCADAoutput(tag_input_filename, scada_input_filename, tag_lookup)

    return tag_lookup, tag_import_file

def runConversion(logic_input_file, tag_lookup, tag_import_file, output_filename="logic.txt", CONVERT=False, VIEW_RUNGS=False, COUNT_INSTR=False, PRINT_ERRORS=False):

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
