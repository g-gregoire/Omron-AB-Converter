import file_functions as ff
import logic_converter as lc
import lookup as lk
import main_functions as mf

import traceback

input_file = "basic_rungs1.txt"
# input_file = "Dryer_no_symbols.txt"
# input_file = "Sterilizer_Section1.txt"

tag_filename = "tag_lookup.csv"

output_filename = "output.L5X"

CONVERT = True # Perform conversion
VIEW_RUNGS = True # View the rungs as they are converted
COUNT_INSTR = False # Count the number & type of instructions in the file
PRINT_ERRORS = True # Print errors of failed conversions

catchErrors = None

mf.runConversion(input_file, tag_filename, output_filename=output_filename, CONVERT=CONVERT, VIEW_RUNGS=VIEW_RUNGS, COUNT_INSTR=COUNT_INSTR, PRINT_ERRORS=[PRINT_ERRORS])

# Testing - Functions
