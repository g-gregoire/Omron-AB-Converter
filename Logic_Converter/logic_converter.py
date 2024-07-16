import file_functions as ff
import logic_converter as lc
import lookup as lk

EOL = "^^^"
NL = "\n"
SP = " "
END = ";"

def getRung(text: str, rung: str):
    if text == EOL:
        flag = True
    else: 
        flag = False
        rung += text + NL

    return rung, flag

# Decode the rung and call the convert function
def decodeRung(rung: str):
    conv_rung = ""
    last_logic = ""
    last_instr = ""
    # Split into rungs; exclude the last empty string
    rung = rung.split(NL)[:-1]
    # Split out arguments for each instruction
    for index, line in enumerate(rung):
        args = line.split(" ")
        logic, last_logic, last_instr = convertLogic(args, last_logic, last_instr)
        if index == 0:
            continue
        if index == len(rung) - 1:
            conv_rung += last_logic + logic + END
        else:
            conv_rung += last_logic
            last_logic = logic
    print(conv_rung)
    return conv_rung

# Convert Specific instructions from Omron to AB
def convertLogic(line, last_line, last_instr):
    # print(line)
    instr = line[0]
    instr_type = lk.lookup[instr][1]
    # Handle various instructions
    if instr == "ORLD":
        logic = "" # Hold off handling for now
    elif instr == "ANDLD":
        conv_instr = lk.lookup[instr][0]
        logic = conv_instr
    elif instr == "":
        logic = "" # Placeholder for other complicated instructions
    else:
        param = line[1]
        conv_instr = lk.lookup[instr][0]
        logic = conv_instr + "(" + param + ")"

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
    return logic, last_logic, last_instr