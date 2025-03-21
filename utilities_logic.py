import lookup as lk
from structures import Block, Rung

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

def combine_compare(rung:Rung, line1, line2, line3, catchErrors):
    # print("Compare")
    pop_count = 0
    if line1 != None: instr1, params1, details1 = expand_instruction(line1)
    if line2 != None: instr2, params2, details2 = expand_instruction(line2)
    if line3 != None: instr3, params3, details3 = expand_instruction(line3)
    print("Line 1: ", line1)
    print("Line 2: ", line2)
    print("Line 3: ", line3)
    # Determine which comparison is being used
    EQU = GRT = LES = False
    if line2 == None: # Added for strange coding where CMP and comp_type are on different rungs
        # print("End of rung")
        catchErrors["error"] = True
        catchErrors["list"].append(line1)
        rung.comment += f" - ERROR CONVERTING THIS RUNG ({instr1})."
    else:
        if line2.find("EQUALS") != -1 or line2.find("P_EQ") != -1:
            EQU = True
        elif line2.find("GREATER_THAN") != -1 or line2.find("P_GT") != -1:
            GRT = True
        elif line2.find("LESS_THAN") != -1 or line2.find("P_LT") != -1:
            LES = True
        if line3.find("EQUALS") != -1 or line3.find("P_EQ") != -1:
            EQU = True
        elif line3.find("GREATER_THAN") != -1 or line3.find("P_GT") != -1:
            GRT = True
        elif line3.find("LESS_THAN") != -1 or line3.find("P_LT") != -1:
            LES = True
    
        if EQU and GRT:
            # print("GEQ")
            line1 = line1.replace("CMP(20)", "GEQ").replace("CMP(020)", "GEQ")
            # Pop next 3 lines
            pop_count = 2
        elif EQU and LES:
            # print("LEQ")
            line1 = line1.replace("CMP(20)", "LEQ").replace("CMP(020)", "LEQ")
            # Pop next 3 lines
            pop_count = 2
        elif EQU:
            # print("EQU")
            line1 = line1.replace("CMP(20)", "EQU").replace("CMP(020)", "EQU")
            # Pop next line1
            pop_count = 1
        elif GRT:
            # print("GRT")
            line1 = line1.replace("CMP(20)", "GRT").replace("CMP(020)", "GRT")
            # Pop next line1
            pop_count = 1
        elif LES:
            # print("LES")
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES")
            # Pop next line1
            pop_count = 1
        else:
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES")
            pop_count = 1
    
    return line1, pop_count, catchErrors