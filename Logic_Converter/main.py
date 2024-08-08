import file_functions as ff
import logic_converter as lc
import lookup as lk

import traceback

# input_file = "test_rungs_ster.txt"
input_file = "basic_rungs1.txt"

# Open input file & create output file
wb = ff.openFile(input_file)
output_file = ff.createFile("output", "txt")

try: 
    lc.loop_rungs(wb, output_file, view_rungs=True, num_rungs=-1)
    print("Conversion complete")
except Exception as e:
    print("Conversion failed: ", e)
    traceback.print_exc()

# Testing - Functions
