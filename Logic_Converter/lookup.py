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

    # Output Instructions
    "OUT": ["OUTPUT", "OTE"],
    "SET": ["OUTPUT", "OTL"],
    "RSET": ["OUTPUT", "OTU"],
    "DIFU(13)": ["oneshot", "OSR"],
    "DIFD(14)": ["oneshot", "OSF"], 
    "KEEP(11)": ["KEEP", "OTL"],

    # Timer Instructions
    "TIM": ["TIMER", "TON"],
    # Count Instructions
    "CNT": ["COUNTER", "CTU"],
    "RESET": ["RESET", "RES"],

    # Comparison Instructions
    "CMP(20)": ["COMPARE", ""],
    "GREATER_THAN": ["COMPARE", ""],
    "P_GT": ["COMPARE", ""],
    "LESS_THAN": ["COMPARE", ""],
    "P_LT": ["COMPARE", ""],
    "EQUALS": ["COMPARE", ""],
    "P_EQ": ["COMPARE", ""],
    

    # Math Instructions
    "ADD(30)": ["math", "ADD"],
    "SUB(31)": ["math", "SUB"],
    "MUL(32)": ["math", "MUL"],
    "DIV(33)": ["math", "DIV"],
    "SCL(64)" : ["math", ""],

    # Logical Instructions
    "MOV(21)": ["logical", "MOV"],
    "BIN(23)": ["logical", ""], # BCD to Binary
    "BCD(24)": ["logical", ""], # Binary to BCD
    "CLC(41)": ["logical", ""],

    # PID Instructions
    "PID(60)": ["pid", ""],

    # End of rung
    "^^^": ";\n",
    
    # Unknown Instructions
    "XFER": ["unknown", ""],
    "ADB": ["unknown", ""],
}