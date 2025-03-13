# Component files
header = "header.xml"
datatypes = "datatypes.xml"
aoi = "AOIs.xml"
tags = "tags.xml"
routine_header = "routine-header.xml"
footer = "footer.xml"
tagcsv = "tag.csv"

# Lookup conversion for Omron to AB
lookup = {
    # Comments
    "'": {"instr": "", "type": "comment", "args": 0},

    # Load Instructions
    "ANDLD": {"instr": "XIC", "type": "load", "args": 1},
    "LD": {"instr": "XIC", "type": "load", "args": 1},
    "LDNOT": {"instr": "XIO", "type": "load", "args": 1},
    "ORLD": {"instr": "XIC", "type": "load", "args": 1},

    # Logic Instructions
    "AND": {"instr": "XIC", "type": "logic", "args": 1},
    "ANDNOT": {"instr": "XIO", "type": "logic", "args": 1},
    "ANDW(34)": {"instr": "AND", "type": "logic", "args": 1},
    "OR": {"instr": "XIC", "type": "logic", "args": 1},
    "ORNOT": {"instr": "XIO", "type": "logic", "args": 1},

    # Output Instructions
    "OUT": {"instr": "OTE", "type": "output", "args": 1},
    "SET": {"instr": "OTL", "type": "output", "args": 1},
    "RSET": {"instr": "OTU", "type": "output", "args": 1},
    "KEEP(11)": {"instr": "OTL", "type": "output", "args": 1},
    "OTU": {"instr": "OTU", "type": "output", "args": 1},

    # Oneshot Instructions
    "DIFD(14)": {"instr": "OSF", "type": "oneshot", "args": 1},
    "DIFU(13)": {"instr": "OSR", "type": "oneshot", "args": 1},

    # Timer Instructions
    "TIM": {"instr": "TON", "type": "timer", "args": 1},
    "TTIM(87)": {"instr": "RTO", "type": "timer", "args": 1},

    # Counter Instructions
    "CNT": {"instr": "CTU", "type": "counter", "args": 1},
    "CNR(545)": {"instr": "RES", "type": "counter", "args": 1},

    # Reset Instructions (Counter/Timer)
    "RESET": {"instr": "RES", "type": "reset", "args": 1},

    # Comparison Instructions
    "CMP(20)": {"instr": "", "type": "compare", "args": 2},
    "CMPL(60)": {"instr": "", "type": "compare", "args": 2},
    "AND<(310)": {"instr": "LT", "type": "compare", "args": 2},
    "AND<=(315)": {"instr": "LE", "type": "compare", "args": 2},
    "AND=(300)": {"instr": "EQ", "type": "compare", "args": 2},
    "AND=L(300)": {"instr": "EQU", "type": "compare", "args": 2},
    "AND>(320)": {"instr": "GT", "type": "compare", "args": 2},
    "AND>=(325)": {"instr": "GE", "type": "compare", "args": 2},
    "LD<(310)": {"instr": "LT", "type": "compare", "args": 2},
    "LD<=(315)": {"instr": "LE", "type": "compare", "args": 2},
    "LD=(300)": {"instr": "EQ", "type": "compare", "args": 2},
    "LD>(320)": {"instr": "GT", "type": "compare", "args": 2},
    "LD>=(325)": {"instr": "GE", "type": "compare", "args": 2},
    "OR<=(315)": {"instr": "LEQ", "type": "or_compare", "args": 2},
    "OR=(300)": {"instr": "EQU", "type": "or_compare", "args": 2},
    "OR>(320)": {"instr": "GRT", "type": "or_compare", "args": 2},
    "OR>=(325)": {"instr": "GEQ", "type": "or_compare", "args": 2},
    "GREATER_THAN": {"instr": "GRT", "type": "compare", "args": 2},
    "LESS_THAN": {"instr": "LES", "type": "compare", "args": 2},
    "EQUALS": {"instr": "EQU", "type": "compare", "args": 2},
    "P_GT": {"instr": "GRT", "type": "compare", "args": 2},
    "P_LT": {"instr": "LES", "type": "compare", "args": 2},
    "P_EQ": {"instr": "EQU", "type": "compare", "args": 2},
    "EQU": {"instr": "EQU", "type": "compare", "args": 2},
    "GRT": {"instr": "GRT", "type": "compare", "args": 2},
    "GEQ": {"instr": "GEQ", "type": "compare", "args": 2},
    "LES": {"instr": "LES", "type": "compare", "args": 2},
    "LEQ": {"instr": "LEQ", "type": "compare", "args": 2},

    # Math Instructions
    "-B(414)": {"instr": "SUB", "type": "math", "args": 3},
    "*(420)": {"instr": "MUL", "type": "math", "args": 3},
    "*B(424)": {"instr": "MUL", "type": "math", "args": 3},
    "/(430)": {"instr": "DIV", "type": "math", "args": 3},
    "/BL(435)": {"instr": "DIV", "type": "math", "args": 3},
    "/UL(433)": {"instr": "DIV", "type": "math", "args": 3},
    "+(400)": {"instr": "ADD", "type": "math", "args": 3},
    "+B(404)": {"instr": "ADD", "type": "math", "args": 3},
    "+BCL(407)": {"instr": "ADD", "type": "math", "args": 3},
    "+C(402)": {"instr": "ADD", "type": "math", "args": 3},
    "+CL(403)": {"instr": "ADD", "type": "math", "args": 3},
    "+L(401)": {"instr": "ADD", "type": "math", "args": 3},
    "ADD(30)": {"instr": "ADD", "type": "math", "args": 3},
    "SUB(31)": {"instr": "SUB", "type": "math", "args": 3},
    "MUL(32)": {"instr": "MUL", "type": "math", "args": 3},
    "DIV(33)": {"instr": "DIV", "type": "math", "args": 3},
    "ADB(50)": {"instr": "ADD", "type": "math", "args": 3},
    "SBB(51)": {"instr": "SUB", "type": "math", "args": 3},
    "MLB(52)": {"instr": "MUL", "type": "math", "args": 3},
    "DVB(53)": {"instr": "DIV", "type": "math", "args": 3},

    # Copy Instructions
    "MOV(21)": {"instr": "MOV", "type": "copy", "args": 2},
    "MOVD(83)": {"instr": "MOV", "type": "copy", "args": 2},
    "MOVL(498)": {"instr": "MOV", "type": "copy", "args": 2},
    "BCD(24)": {"instr": "MOV", "type": "copy", "args": 2},
    "BCDL(59)": {"instr": "MOV", "type": "copy", "args": 2},
    "BIN(23)": {"instr": "MOV", "type": "copy", "args": 2},
    "XFER(70)": {"instr": "COP", "type": "copy", "args": 3},
    "XFRB(62)": {"instr": "COP", "type": "copy", "args": 3},
    "BSET(71)": {"instr": "FLL", "type": "copy", "args": 3}, # For fill length, Omron specifies start & end bits; AB specifies start bit & length
    "MOVB(82)": {"instr": "BTD", "type": "copy", "args": 5}, # Omron has 3 args (Source, Control Word, Dest), AB has 5 (Source, Source bit, Dest, Dest Bit, Length).

    # Scaling Instructions
    "SCL(64)": {"instr": "CPT", "type": "scaling", "args": 2},
    "SCL(194)": {"instr": "CPT", "type": "scaling", "args": 2},
    "APR(69)": {"instr": "CPT", "type": "scaling", "args": 2},

    # PID Instructions
    "PID(60)": {"instr": "PID", "type": "pid", "args": 3}, # PID Includes more than 3 args, but we're only interested in PID, PV and CV
    "PID(190)": {"instr": "PID", "type": "pid", "args": 3}, # PID Includes more than 3 args, but we're only interested in PID, PV and CV

    # Stack Instructions
    "PUSH(632)": {"instr": "FFL", "type": "stack", "args": 3}, # Args: Source, FIFO, Control Word. CW should be the same across the same FFL and FFU.
    "FIFO(633)": {"instr": "FFU", "type": "stack", "args": 3}, # Args: FIFO, Dest, Control Word. CW should be the same across the same FFL and FFU.

    # End of Rung
    "^^^": ";\n",

     # Other Instructions - No 1:1 conversion
    # "CLC(41)": ["other", "CLC"],
    # "DATE(735)": ["?", "System"],
    # "CADD(730)": ["?", "Math"],
    # "PMCR(260)": {"instr": "", "type": "macro", "args": "?"},
    # "SSET(630)": {"instr": "?", "type": "stack", "args": "?"}, # Not needed with ABR

    # Ignored Instructions
    "CLC(41)": {"instr": "ignore", "type": "macro", "args": "?"},
    "DATE(735)": {"instr": "ignore", "type": "macro", "args": "?"},
    "CADD(730)": {"instr": "ignore", "type": "macro", "args": "?"},
    "PMCR(260)": {"instr": "ignore", "type": "macro", "args": "?"},
    "SSET(630)": {"instr": "ignore", "type": "stack", "args": "?"}, # Not needed with ABR

}
