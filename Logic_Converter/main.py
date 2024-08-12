import file_functions as ff
import logic_converter as lc
import lookup as lk

import traceback

# input_file = "Dryer_with_symbols.txt"
# input_file = "Sterilizer_Section1.txt"
input_file = "basic_rungs1.txt"

# Open input file & create output file
wb = ff.openFile(input_file)
wb = ff.prepareFile(wb) # Remove everything except the Mnemonic section
output_file = ff.createFile("output", "txt")

COUNT_INSTR = False
CONVERT = True


if COUNT_INSTR:
    lc.countInstructions(wb)

if CONVERT:
    # Convert the rungs to ladder logic
    try: 
        lc.loop_rungs(wb, output_file, view_rungs=True, num_rungs=-1)
        print("Conversion complete")
    except Exception as e:
        print("Conversion failed: ", e)
        traceback.print_exc()

# Testing - Functions
