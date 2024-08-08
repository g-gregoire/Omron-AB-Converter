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
    "KEEP(11)": ["KEEP", "OTL"],

    # Timer Instructions
    "TIM": ["TIMER", ""],

    # Comparison Instructions
    "CMP(20)": ["COMPARE", ""],
    "GREATER_THAN": ["COMPARE", ""],
    "P_GT": ["COMPARE", ""],
    "LESS_THAN": ["COMPARE", ""],
    "P_LT": ["COMPARE", ""],
    "EQUALS": ["COMPARE", ""],
    "P_EQ": ["COMPARE", ""],
    
    # Count Instructions
    "CNT": ["COUNT", ""],

    # Math Instructions
    "ADD(30)": ["math", ""],
    "SUB(31)": ["math", ""],
    "MUL(32)": ["math", ""],
    "SCL(64)" : ["math", ""],

    # Logical Instructions
    "MOV(21)": ["logical", ""],
    "BIN(23)": ["logical", ""], # BCD to Binary
    "BCD(24)": ["logical", ""], # Binary to BCD
    "CLC(41)": ["logical", ""],
    "DIFU(13)": ["oneshot", "ONS"],
    "DIFD(14)": ["oneshot", "OSF"], # NEED TO CONFIRM INSTRUCTION

    # PID Instructions
    "PID(60)": ["pid", ""],

    # End of rung
    "^^^": ";\n",
    
    # Unknown Instructions
    "XFER": ["unknown", ""],
    "ADB": ["unknown", ""],
}