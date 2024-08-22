import file_functions as ff
import logic_converter as lc
import lookup as lk

import traceback

# input_file = "Dryer_with_symbols.txt"
input_file = "Dryer_no_symbols.txt"
# input_file = "Sterilizer_Section1.txt"
# input_file = "basic_rungs1.txt"

tag_filename = "tag_lookup.csv"

# Open input file & create output file
wb = ff.openFile(input_file)
wb = ff.prepareFile(wb) # Remove everything except the Mnemonic section
output_file = ff.createFile("output", "txt")
tag_file = ff.openFile(tag_filename)

COUNT_INSTR = False
CONVERT = True
VIEW_RUNGS = False
PRINT_ERRORS = True

catchErrors = None

if COUNT_INSTR:
    lc.countInstructions(wb)

if CONVERT:
    # Convert the rungs to ladder logic
    try: 
        catchErrors = lc.loop_rungs(wb, output_file, tag_file, view_rungs=VIEW_RUNGS, num_rungs=-1)
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
# Testing - Functions
