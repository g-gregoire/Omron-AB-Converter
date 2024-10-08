# Component files
header = "header.xml"
datatypes = "datatypes.xml"
aoi = "AOIs.xml"
tags = "tags.xml"
routine_header = "routine-header.xml"
footer = "footer.xml"
tagcsv = "tag.csv"

# Lookup conversion fOR Omron to AB
lookup = {
    # Comments
    "'": "Comment",
    # LOAD Instructions
    "LD": ["LOAD", "XIC"],
    "LDNOT": ["LOAD", "XIO"],
    # END LOAD Instructions
    "ORLD": ["LOAD", ""],
    "ANDLD": ["LOAD", "]"],
    # Input AND Instructions
    "AND": ["AND", "XIC"],
    "ANDNOT": ["AND", "XIO"],
    # Input OR Instructions
    "OR": ["OR", "XIC"],
    "ORNOT": ["OR", "XIO"],
    # Branching Instructions
    # "STBR": ["BRANCH", "STBR"],
    # "NWBR": ["BRANCH", "NWBR"],

    # Output Instructions
    "OUT": ["OUTPUT", "OTE"],
    "SET": ["OUTPUT", "OTL"],
    "RSET": ["OUTPUT", "OTU"],
    "DIFU(13)": ["oneshot", "OSR"],
    "DIFD(14)": ["oneshot", "OSF"], 
    "KEEP(11)": ["KEEP", "OTL"],
    "OTU": ["KEEP", "OTU"],

    # Timer Instructions
    "TIM": ["TIMER", "TON"],
    # Count Instructions
    "CNT": ["COUNTER", "CTU"],
    "RESET": ["RESET", "RES"],

    # Comparison Instructions
    "CMP(20)": ["COMPARE", ""],
    "GREATER_THAN": ["COMPARE", "GRT"],
    "P_GT": ["COMPARE", "GRT"],
    "LESS_THAN": ["COMPARE", "LES"],
    "P_LT": ["COMPARE", "LES"],
    "EQUALS": ["COMPARE", "EQU"],
    "P_EQ": ["COMPARE", "EQU"],
    # Converted Comparison Instructions
    "EQU": ["COMPARE", "EQU"],
    "GRT": ["COMPARE", "GRT"],
    "GEQ": ["COMPARE", "GEQ"],
    "LES": ["COMPARE", "LES"],
    "LEQ": ["COMPARE", "LEQ"],

    # Math Instructions
    "ADD(30)": ["math", "ADD"],
    "SUB(31)": ["math", "SUB"],
    "MUL(32)": ["math", "MUL"],
    "DIV(33)": ["math", "DIV"],
    # Binary Math
    "ADB(50)": ["math", "ADD"],
    "SBB(51)": ["math", "SUB"],
    "MLB(52)": ["math", "MUL"],
    "DVB(53)": ["math", "DIV"],
    
    "SCL(64)": ["scaling", "CPT"],

    # PID Instructions
    "PID(60)": ["pid", "PID"],

    # Logical Instructions
    "MOV(21)": ["logical", "MOV"],
    "XFER(70)": ["copy", "COP"],
    "MOVB(82)": ["btd", "BTD"],

    # Other Instructions - No 1:1 conversion
    # "CLC(41)": ["other", "CLC"],
    # "BIN(23)": ["other", "BIN"], # Binary to BCD
    # "BCD(24)": ["other", "BCD"], # BCD to Binary
    # "ADB(50)": ["other", "ADB"],
    # "SCL(64)": ["other", "SCL"],

    # PID Instructions
    # "PID(60)": ["pid", "PID"],

    # End of rung
    "^^^": ";\n",
}
