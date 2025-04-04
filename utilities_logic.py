import lookup as lk
from structures import Block, Rung

from typing import List, Dict
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
    # print("Line 1: ", line1)
    # print("Line 2: ", line2)
    # print("Line 3: ", line3)
    # Determine which comparison is being used
    EQU = GRT = LES = False
    if line2 == None or line2 == "": # Added for strange coding where CMP and comp_type are on different rungs
        print("Incorrect usage of CMP instruction")
        catchErrors["count"] += 1
        catchErrors["list"].append(line1)
        rung.comment += f" - ERROR with ({line1})- NO FOLLOW-UP COMPARISON ARGS (GRT, LEQ, etc.)."
    else:
        if line2.find("EQUALS") != -1 or line2.find("P_EQ") != -1:
            EQU = True
        elif line2.find("GREATER_THAN") != -1 or line2.find("P_GT") != -1 or line2.find("GE") != -1:
            GRT = True
        elif line2.find("LESS_THAN") != -1 or line2.find("P_LT") != -1 or line2.find("LE") != -1:
            LES = True
        if line3.find("EQUALS") != -1 or line3.find("P_EQ") != -1:
            EQU = True
        elif line3.find("GREATER_THAN") != -1 or line3.find("P_GT") != -1 or line3.find("GE") != -1:
            GRT = True
        elif line3.find("LESS_THAN") != -1 or line3.find("P_LT") != -1 or line3.find("LE") != -1:
            LES = True

        # print(EQU, GRT, LES)
    
        if EQU and GRT:
            # print("GEQ")
            line1 = line1.replace("CMP(20)", "GEQ").replace("CMP(020)", "GEQ").replace("CMPL(060)", "GEQ")
            # Pop next 3 lines
            pop_count = 3
        elif EQU and LES:
            # print("LEQ")
            line1 = line1.replace("CMP(20)", "LEQ").replace("CMP(020)", "LEQ").replace("CMPL(060)", "LEQ")
            # Pop next 3 lines
            pop_count = 3
        elif EQU:
            # print("EQU")
            line1 = line1.replace("CMP(20)", "EQU").replace("CMP(020)", "EQU").replace("CMPL(060)", "EQU")
            # Pop next line1
            pop_count = 1
        elif GRT:
            # print("GRT")
            line1 = line1.replace("CMP(20)", "GRT").replace("CMP(020)", "GRT").replace("CMPL(060)", "GRT")
            # Pop next line1
            pop_count = 1
        elif LES:
            # print("LES")
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES").replace("CMPL(060)", "LES")
            # Pop next line1
            pop_count = 1
        else:
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES").replace("CMPL(060)", "LES")
            pop_count = 1
    
        # print(line1, pop_count)
    return line1, pop_count, catchErrors

def combine_simple_logic(block_array:List[Block])->List[Block]:
    index = 0
    multiple_out_added = 0
    working_logic = []
    OR_active = False

    multiple_count = 0
    for block in block_array:
        if block.block_type == "OUT":
            multiple_count += 1
    if multiple_count > 1:
        multiple_OUT = True
        # print("Multiple OUT blocks:", multiple_count)
    else:
        multiple_OUT = False

    for index, block in enumerate(reversed(block_array)):

        if block.details[0]["block_type"] == "TR":
            working_logic.append(block.details[0]["logic"])
            continue
        
        # Get working variables
        logic = block.converted_block
        block_type = block.block_type
        # print(index, block, block_type)

        # Determine previous block in array (next one in reversed array)
        try:
            prev_block = block_array[-index-2]
        except:
            prev_block = None

        if block_type == "OUT":
            # print("OUT type. Line: ", logic)
            if multiple_OUT: # If multiple outputs, we need brackets for branches
                if logic[0][0] == "[" and logic[0][-1] == "]":
                    logic[0] = logic[0][:-1]
                    # print("logic: ", logic)
                if multiple_out_added == 0:
                    working_logic.append("]")
                    working_logic.append(logic[0])
                    multiple_out_added += 1
                    # print("set OR active")
                    OR_active = True
                elif 0 < multiple_out_added < (multiple_count - 1):
                    working_logic.append(",")
                    working_logic.append(logic[0])
                    multiple_out_added += 1
                elif multiple_out_added == multiple_count - 1:
                    working_logic.append(",")
                    working_logic.append(logic[0])
                    working_logic.append("[")
                    OR_active = False
                else:
                    working_logic.append(logic[0])
            else: # If single output, no brackets needed
                working_logic.append(logic[0])

        elif block_type == "START" or block_type == "IN": # If start (LD) or IN block, then close bracket is it's open
            if multiple_OUT: # If multiple outputs, we need brackets for branches
                # if 0 < multiple_out_added <= multiple_count:
                #     working_logic.append(logic[0])
                # elif multiple_out_added == multiple_count:
                #     working_logic.append("[")
                #     working_logic.append(logic[0])
                # else:
                if OR_active and (multiple_out_added > 1): # If or active, and more than 1 output added already, wrap output in brackets
                    # print("OR active - wrap in brackets")
                    working_logic.insert(0, "]")
                    working_logic.append("[")
                    working_logic.append(logic[0])
                else:
                    working_logic.append(logic[0])
            else: # If single output, no brackets needed
                working_logic.append(logic[0])

    # print(working_logic)
    output_logic = "".join(reversed(working_logic))

    # print(output_logic)
    details = {
        "logic": output_logic,
        "block_type": "IN",
        "blocks_in": 1
    }
    block_type = "IN"
    blocks_in = 1

    output_block = [Block([details], block_type, blocks_in)]

    return output_block

def OR_block_list(block_array:List[Block], catchErrors)->List[Block]:
    # This function takes a list of blocks and combines them into a single OR block
    # This is done by adding brackets around each block and adding a comma between each block
    # The output is a single block with the logic of all blocks combined

    working_logic = []
    for index, block in enumerate(reversed(block_array)):
        logic = block.converted_block
        if len(logic) == 0:
            print("Logic is None")
            catchErrors["error"] = True
            continue
        # print("Block", index, logic)
        block_type = block.block_type
        if index == 0:
            working_logic.append("]")
        working_logic.append(logic[0])
        if index != len(block_array) - 1:
            working_logic.append(",")
    working_logic.append("[")
        
    output_logic = "".join(reversed(working_logic))
    details = {
        "logic": output_logic,
        "block_type": "IN",
        "blocks_in": 1
    }
    block_type = "IN"
    blocks_in = 1
    output_block = [Block([details], block_type, blocks_in)]
    
    return output_block, catchErrors

def createSubSet(block_list:List[Block], start_index:int, end_index:int) -> List[Block]:
        # print("Creating subset. Indexes: ", start_index, end_index)
        # for block in block_list:
        #     print(block)
        subset = block_list[start_index:end_index]
        # print("Subset. Indexes: ", start_index, end_index)
        # for block in subset:
        #     print(block)
        return subset

def concat_block_list(initial:List[Block], inter:List[Block], final:List[Block]) -> List[Block]:
    block_list = []

    if initial != None:
        for block in initial:
            block_list.append(block)
    block_list.append(inter[0])
    if final != None:
        for block in final:
            block_list.append(block)

    # print("Concatenated block list")
    # for block in block_list:
    #     print(block)
    return block_list

def determine_block_type(type_array:List[str]) -> str:
    if len(type_array) == 1:
        block_type = type_array[0]
    else:
        if "START" in type_array:
            block_type = "START"
        elif "OUT" in type_array:
            block_type = "OUT"
        else:
            block_type = "IN"
    return block_type