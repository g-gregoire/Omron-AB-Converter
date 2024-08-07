import file_functions as ff
import lookup as lk
from structures import Rung, Block

import pandas as pd


EOL = "^^^"
NL = "\n"
SP = " "
END = ";"

def loop_rungs(logic_file: pd.DataFrame, output_file, view_rungs = False, start_rung=0, num_rungs=-1):
    rung = ""
    rung_num = 0
    for rowindex, row in logic_file.iterrows():
        # print(rung_num)
        # Loop through each row and build the rung until the end of the rung
        rung, end_of_rung = getRung(row['logic'], rung)
        # print(rung)

        # Once the end of the rung is reached, decode the entire rung
        if end_of_rung:
            # print(rung)
            if rung_num <= start_rung-1:
                rung = ""
                continue

            # Call function to convert the rung
            # converted_rung = decodeRung(rung)
            rung_blocks = blockBreaker(rung)
            rung_blocks.convertBlocks()
            break
            ff.addRung(output_file, rung_num, converted_rung, "")
            rung_num += 1
            rung = ""

            # If the view_rungs flag is set, print the rung
            if view_rungs:
                print(converted_rung)

            # If the number of rungs is not specified, continue to the end of the file
            if num_rungs == -1:
                continue
            # If the number of rungs is specified, check if the number of rungs is reached
            elif rung_num >= (start_rung+num_rungs):
                    print("Reached end of requested rungs")
                    return
            
    return

def getRung(text: str, rung: str):
    # Check if the end of the rung is reached (^^^) and set the flag true
    if text == EOL:
        end_of_rung = True

    # Otherwise, add the text to the rung and new line
    else: 
        end_of_rung = False
        rung += text + NL

    return rung, end_of_rung

# Decode the rung and call the convert function
def decodeRung(rung: str):
    converted_rung = ""
    last_logic = ""
    last_instr = ""
    # Split instructions into an array; exclude the last empty string
    rung = rung.split(NL)[:-1]

    # Loop through each instruction in the rung
    for index, line in enumerate(rung):
        
        # Split out the instruction and the tag
        args = line.split(" ")

        # Convert the logic from Omron to AB, taking into consideration the last instruction
        logic, last_logic, conv_instr, last_instr = convertLogic(args, last_logic, last_instr)
        
        # If this is the first instruction, set the logic to last_logic, but don't add to the rung
        if index == 0:
            last_logic = logic
            continue
        
        # If this is the last line, add the previous logic and current logic
        if index == len(rung) - 1:
            converted_rung += last_logic + logic

        # Otherwise, add the previous logic to the rung, and current logic to the previous logic
        else:
            converted_rung += last_logic
            last_logic = logic

    # print(converted_rung)
    return converted_rung


def blockBreaker(rung: str):
    # This function splits rung into logic/load blocks

    # print(rung)
    # Create structures to use
    outputRung = Rung()
    startRung = False
    # Split instructions into an array; exclude the last empty string
    rung = rung.split(NL)[:-1]

    # Loop through each instruction in the rung
    for index, line in enumerate(rung):
        instr, param, instr_type, conv_instr = extractLine(line)

        if instr == "LD" or instr == "LDNOT":
            if not startRung:
                # print("Start Rung")
                startRung = True
                block = Block()
                block.addLine(line)
                # outputRung.viewRung()
            else:
                # print("New Block")
                outputRung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)

        elif instr == "ANDLD" or instr == "ORLD":
            outputRung.addConnector(instr)

        elif instr_type == "OUTPUT":
            # print("New Block")
            outputRung.addBlock(block) # Add the old block to the rung
            block = Block() # Create a new block
            block.addLine(line)

        else:
            block.addLine(line)

        if index == len(rung) - 1:
            # Append the last block to the rung
            outputRung.addBlock(block)
            # print("End of Rung")
    
    # outputRung.viewRung()
    return outputRung

# Convert Specific instructions from Omron to AB
def convertLogic(line, last_line, last_instr):
    # print(line)
    logic = ""
    instr = line[0]
    instr_type = lk.lookup[instr][0]
    try:
        last_instr_type = lk.lookup[last_instr][0]
    except: last_instr_type = None

    print(last_instr_type, instr_type)
    # Previous Line Modifications
    if last_instr_type == "OR" and instr_type == "AND":
        logic += "]"

    # Handle various instructions
    if instr == "ORLD":
        logic += "" # Hold off handling for now
    elif instr == "ANDLD":
        conv_instr = lk.lookup[instr][1]
        logic += conv_instr
    elif instr == "":
        logic += "" # Placeholder for other complicated instructions
    else:
        param = line[1]
        conv_instr = lk.lookup[instr][1]
        logic += conv_instr + "(" + param + ")"

    # Handle last line updates
    if instr == "OR" or instr == "ORNOT":
        if last_instr == "OR":
            last_logic = last_line
        else:
            last_logic = "[" + last_line
    else: 
        last_logic = last_line
    # print(logic)
    last_instr = instr
    return logic, instr, last_logic, conv_instr, last_instr


def extractLine(line: str):
    args = line.split(" ")
    instr = args[0]
    try: param = args[1]
    except: param = None

    instr_type = lk.lookup[instr][0]
    conv_instr = lk.lookup[instr][1]

    return instr, param, instr_type, conv_instr