import file_functions as f
import lookup as lk
import logic_converter as lc
import rung_logic as rung
import parse

import traceback

def tagConversion(tag_input_filename, tag_filename, scada_input_filename, output_filename, CREATE_TAGS = False, CREATE_EXCEL = False, CONVERT_SCADA_TAGS = False):

    # Create file to be used for tag import
    if CREATE_TAGS:
        # Create tag output file
        tagfile = f.createTagFile(output_filename, system_ref = tag_input_filename)
        # Parse input file for tag information
        tagList = parse.parseList(filename=tag_input_filename)
        # Create tags from List
        # tagfile = rung.createTags(tagList, tagfile, output_filename)
        for tag in tagList:
            tagfile = f.addTag(tag['tagname'], tag['description'] , tag['type'], tagfile)
            # print(tag['symbol'], tag['description'], tag['type'])
        tagfile.close()

        if CREATE_EXCEL:
            # Create Excel file for tag import
            tagfile = f.createExcel(tagList, tagfile, tag_filename, system_ref = tag_input_filename)

        if CONVERT_SCADA_TAGS:
            # Create Excel file for tag import
            scada_file = rung.createSCADAoutput(tag_input_filename, scada_input_filename)

    return

def runConversion(input_filename, tag_filename, output_filename="logic.txt", CONVERT=False, VIEW_RUNGS=False, COUNT_INSTR=False, PRINT_ERRORS=False):

    system_name = f.getSystemName(input_filename)
    # system_name = "Sterilizer"
    tag_filename = system_name + "_" + tag_filename

    # Open input file & create output file
    logic_wb = f.openFile(input_filename)
    logic_wb = f.prepareFile(logic_wb) # Remove everything except the Mnemonic section
    output_file = f.createFile(output_filename, input_filename)
    tag_file = f.openFile(tag_filename)
    output_file = f.addContext(output_file, system_name)

    # Initialize variables
    catchErrors = None
    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number
    
    # Add specific logic chunks
    if COUNT_INSTR:
        lc.countInstructions(logic_wb)

    if CONVERT:
        # Convert the rungs to ladder logic
        try:
            catchErrors = lc.loop_rungs(logic_wb, output_file, tag_file, view_rungs=VIEW_RUNGS, num_rungs=-1, system_name= system_name)
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
