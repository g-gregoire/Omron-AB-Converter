import lookup as lk

import re
import pandas as pd

TEST_TAG = "D32253"

def expand_instruction(line: str):
    # This function expands the instruction into its instruction, parameters and details
    # Returned values look like: "MOV(21)", ["A", "B"], {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1}
    line = line.replace("@" , "").replace("!","").replace("%","")
    args = line.split(" ")
    instr = args[0].replace("(0","(") # Remove leading 0 from instruction code if it exists (ie. MOV(021) -> MOV(21))
    params = args[1:]

    # Get instruction into from lookup table
    try:
        details = lk.lookup[instr]
        details["logic"] = line
    except:
        details = None

    return instr, params, details