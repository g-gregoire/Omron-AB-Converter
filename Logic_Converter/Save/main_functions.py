import file_functions as ff
import lookup as lk
import logic_converter as lc

import traceback

def runConversion(input_filename, tag_filename, output_filename="logic.txt", CONVERT=False, VIEW_RUNGS=False, COUNT_INSTR=False, PRINT_ERRORS=False):

    # Open input file & create output file
    logic_wb = ff.openFile(input_filename)
    logic_wb = ff.prepareFile(logic_wb) # Remove everything except the Mnemonic section
    output_file = ff.createFile(output_filename, input_filename)
    tag_file = ff.openFile(tag_filename)
    output_file = ff.addContext(output_file)

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
            catchErrors = lc.loop_rungs(logic_wb, output_file, tag_file, view_rungs=VIEW_RUNGS, num_rungs=-1)
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
    output_file = ff.addFooter(output_file)

    output_file.close()

    # return tagfile