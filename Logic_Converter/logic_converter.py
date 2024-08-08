import file_functions as ff
import lookup as lk
from structures import Rung, Block

import pandas as pd
from pprint import pprint


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
            # Call function to break the rung into blocks
            rung_blocks = blockBreaker(rung)
            # Call function to convert the blocks
            converted_rung = convertBlocks(rung_blocks)
            # Call function to assemble the blocks
            converted_rung = assembleBlocks2(converted_rung)
            # break

            ff.addRung(output_file, rung_num, converted_rung.converted_logic, converted_rung.comment)
            rung_num += 1
            rung = ""

            # If the view_rungs flag is set, print the rung
            if view_rungs:
                converted_rung.viewRung()

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
    OUTPUT_BLOCK = False
    # Split instructions into an array; exclude the last empty string
    rung = rung.split(NL)[:-1]

    # Check for comments
    if rung[0][0] == "'":
        outputRung.addComment(rung[0])
        # print(rung[0])
        rung = rung[1:]

    # Loop through each instruction in the rung
    for index, line in enumerate(rung):
        # print(line)
        # Extract current line
        instr, param, instr_type, conv_instr = extractLine(line)
        # Extract previous line
        try: 
            last_line = rung[index-1]
            last_instr, last_param, last_instr_type, last_conv_instr = extractLine(last_line)
        except: 
            last_line = last_instr = last_param = last_instr_type = last_conv_instr = None

        if instr == "LD" or instr == "LDNOT":
            if not startRung:
                # print("Start Rung")
                startRung = True
                block = Block()
                block.addLine(line)
                # outputRung.addConnector("START")
                # outputRung.viewRung()
            else:
                # print("New Block")
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)

        elif instr == "OR" or instr == "ORNOT":
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(line) # This is used to add the current block
            outputRung.addBlock(block)
            block = Block() 
            block.addLine("ORLD") # This is used to artifically add an ORLD block
            outputRung.addBlock(block)
            block = Block()

        elif instr == "ANDLD" or instr == "ORLD":
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(instr)
            outputRung.addBlock(block)
            block = Block()

        elif instr_type == "OUTPUT":
            # print("New Block")
            if len(block.logic) > 0 and checkMultipleOutputs(rung) and not OUTPUT_BLOCK:
                outputRung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                OUTPUT_BLOCK = True
            elif len(block.logic) > 0 and OUTPUT_BLOCK and (last_instr != "AND" and last_instr != "ANDNOT"):
                outputRung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
            elif OUTPUT_BLOCK:
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                outputRung.addBlock(block)
                block = Block()
            else:
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block

        else:
            block.addLine(line) # Add any non-specific lines to the block

        if index == len(rung) - 1:
            # Append the last block to the rung
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            # print("End of Rung")
    
    # outputRung.viewRung()
    return outputRung

def checkMultipleOutputs(rung):
    # This function checks for multiple outputs in a rung
    output_count = 0
    for line in rung:
        instr, param, instr_type, conv_instr = extractLine(line)
        if instr == "OUT" or instr == "SET" or instr == "RSET":
            output_count += 1
    # print(output_count)
    return (output_count>0)

def convertBlocks(rung: Rung):
    # This function converts the blocks in a rung
    for index, block in enumerate(rung.blocks):
        # print(block)
        converted_logic = ""
        OR_BLOCK = False

        # Loop through each instruction in the block
        for index, line in enumerate(block.logic):
            # print(line)
            instr, param, instr_type, conv_instr = extractLine(line) # Extract current line
            if instr == "ORLD" or instr == "ANDLD":
                converted_logic = instr
                rung.addConvertedBlock(converted_logic)
                continue
            try: # Extract next line
                next_line = block.logic[index+1]
                next_instr, next_param, next_instr_type, next_conv_instr = extractLine(next_line)
            except: 
                next_line = next_instr = next_param = next_instr_type = next_conv_instr = None
            # Extract next line
            try: 
                after_next_line = block.logic[index+2]
                after_next_instr, after_next_param, after_next_instr_type, after_next_conv_instr = extractLine(after_next_line)
            except:
                after_next_line = after_next_instr = after_next_param = after_next_instr_type = after_next_conv_instr = None

            # Begin Conversion
            # Create OR block
            if not OR_BLOCK and (next_instr == "OR" or next_instr == "ORNOT"):
                OR_BLOCK = True
                # print("Start OR block")
                converted_logic += "[" 
                # print(converted_logic)
            elif not OR_BLOCK and (next_instr == "AND" or next_instr == "ANDNOT") and (after_next_instr == "OR" or after_next_instr == "ORNOT"):
                OR_BLOCK = True
                # print("Start OR block")
                converted_logic += "[" 
                # print(converted_logic)
            
            # print("Add Logic")
            converted_logic += conv_instr + "(" + param + ")"
            # print(converted_logic)

            # Allow for LD-AD-OR block (LD & AND are part of the first branch)
            if OR_BLOCK and next_instr != "OR" and after_next_instr != "OR": 
                # print("End OR Block")
                converted_logic += "]"
                # print(converted_logic)
                OR_BLOCK = False
            # Don't add anything if the next instruction is an AND within an OR block
            elif OR_BLOCK and (next_instr == "AND" or next_instr == "ANDNOT"): 
                continue
            # If it's an OR block and it's not the end of the block, add a comma
            elif OR_BLOCK and next_line != None:
                # print("New line - add comma")
                converted_logic += ","
                # print(converted_logic)
            # If the OR block is open and it's the last line, close the OR block
            elif OR_BLOCK and next_line == None: 
                # print("End OR Block")
                converted_logic += "]"
                # print(converted_logic)
                OR_BLOCK = False
            
            if next_line == None: # Last line in the block, add to the rung
                # print("End of block")
                rung.addConvertedBlock(converted_logic)
        # print(converted_logic)
        # break
    # rung.viewRung()

    return rung

# NOT USED
def assembleBlocks(rung: Rung):
    # This function assembles the blocks in a rung
    converted_rung = ""
    OR_BLOCK = False
    OUTPUT_BLOCK = False
    for index, block in enumerate(rung.converted_blocks):
        # print(block)
        # Check next block
        try: next_block = rung.converted_blocks[index+1]
        except: next_block = None
        # Check which connector is used
        try: connector = rung.connectors[index]
        except: connector = None
        # Check the next connector
        try: next_connector = rung.connectors[index+1]
        except: next_connector = None
        
        # Check for all possible connectors
        # AND/OR BLOCK HANDLING
        if not OR_BLOCK and next_connector == "ORLD": # This is ahead of the "Start" block to catch the first ORLD
            # print("ORLD Block")
            converted_rung += "[" + block
            OR_BLOCK = True
        elif connector == "START":
            # print("Start Block")
            converted_rung += block
        elif connector == "ANDLD":
            # print("ANDLD Block")
            converted_rung += block
        elif OR_BLOCK and next_connector != "ORLD":
            converted_rung += "," + block + "]"
            OR_BLOCK = False
        elif OR_BLOCK and next_connector == "ORLD":
            converted_rung += "," + block     
        # OUTPUT HANDLING
        elif connector == "OUTPUT" and next_connector != "OUTPUT":
            # print("Output Block")
            converted_rung += block
        elif connector == "OUTPUT" and next_connector == "OUTPUT":
            # print("Output Block")
            converted_rung += "[" + block
            OUTPUT_BLOCK = True
        elif OUTPUT_BLOCK and next_connector == "OUTPUT":
            # print("Output Block")
            converted_rung += "," + block
        elif OUTPUT_BLOCK and next_connector == None:
            # print("Output Block")
            converted_rung += "," + block + "]"
            OUTPUT_BLOCK = False
        elif connector == None:
            pass
        else:
            pass

    
    # print(converted_rung)

def assembleBlocks2(rung: Rung):
    new_rung = rung.converted_blocks.copy()
    new_block = ""
    index = 0
    while len(new_rung) > 1:
        block = new_rung[index]
        # print(index, block)
        
        if index > 100: # Watchdog break out of infinite loop
            break
        if block == "ORLD":
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])

            new_block = "[" + new_rung[index-2] + "," + new_rung[index-1] + "]"
            new_rung[index-2] = new_block # Replace the first block with the new block
            new_rung.pop(index-1) # Remove the third block
            new_rung.pop(index-1) # Remove the second block
            # print(new_rung)
            # Reset index
            index = 0
            continue
        elif block == "ANDLD":
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])
            new_block = new_rung[index-2] + new_rung[index-1]
            new_rung[index-2] = new_block # Replace the first block with the new block
            new_rung.pop(index-1) # Remove the second block
            new_rung.pop(index-1) # Remove the third block
            # print(new_rung)
            # Reset index and continue
            index = 0
            continue


        # If end of rung, without any ORLD or ANDLD, combine the remaining blocks
        if index == len(new_rung) - 1:
            new_block = ""
            index = 0
            while len(new_rung) > 1:
                new_rung[index] = new_rung[index] + new_rung[index+1]
                new_rung.pop(index+1)
            # print(new_block)
        
        # Increment index
        index += 1
    rung.addConvertedLogic(new_rung[0])
    return rung


# Convert Specific instructions from Omron to AB
def convertLogic(line, last_line, last_instr):
    # print(line)
    logic = ""
    instr = line[0]
    instr_type = lk.lookup[instr][0]
    try:
        last_instr_type = lk.lookup[last_instr][0]
    except: last_instr_type = None

    # print(last_instr_type, instr_type)
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

def countInstructions(logic_file: pd.DataFrame):
    # This function counts the number of different instructions in the program,
    # and how many times each instruction is used
    rung = ""
    instr_count = {}
    for rowindex, row in logic_file.iterrows():
        # print(rung_num)
        # Loop through each row and build the rung until the end of the rung
        rung, end_of_rung = getRung(row['logic'], "")
        instr = rung.split(' ')[0]
        # print(instr)
        if instr in instr_count:
            instr_count[instr] += 1
        else:
            instr_count[instr] = 1
    pprint(instr_count)