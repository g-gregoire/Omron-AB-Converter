# Component files
header = "header.xml"
datatypes = "datatypes.xml"
aoi = "AOIs.xml"
tags = "tags.xml"
routine_header = "routine-header.xml"
footer = "footer.xml"
tagcsv = "tag.csv"

# Lookup conversion for Omron to AB
# Args are the number of arguments the instruction takes in Rockwell
# blocks_in is the number of blocks the instruction takes in Omron
# block_type is the type of block the instruction is in Omron
lookup = {
    # Comments
    "'": {"instr": "", "type": "comment", "args": 0, "block_type": "IN", "blocks_in": 1},

    # Load Instructions
    "LD": {"instr": "XIC", "type": "load", "args": 1, "block_type": "START", "blocks_in": 1},
    "LDNOT": {"instr": "XIO", "type": "load", "args": 1, "block_type": "START", "blocks_in": 1},

    # Logic Block Instructions (Interlocking)
    "ANDLD": {"instr": "ANDLD", "type": "load", "args": 1, "block_type": "INTER", "blocks_in": 1},
    "ORLD": {"instr": "ORLD", "type": "load", "args": 1, "block_type": "INTER", "blocks_in": 1},

    # Logic Instructions
    "AND": {"instr": "XIC", "type": "logic", "args": 1, "block_type": "IN", "blocks_in": 1},
    "ANDNOT": {"instr": "XIO", "type": "logic", "args": 1, "block_type": "IN", "blocks_in": 1},
    "OR": {"instr": "XIC", "type": "logic", "args": 1, "block_type": "OR", "blocks_in": 1},
    "ORNOT": {"instr": "XIO", "type": "logic", "args": 1, "block_type": "OR", "blocks_in": 1},

    # Output Instructions
    "OUT": {"instr": "OTE", "type": "output", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "SET": {"instr": "OTL", "type": "output", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "RSET": {"instr": "OTU", "type": "output", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "KEEP(11)": {"instr": "OTL", "type": "keep", "args": 1, "block_type": "OUT", "blocks_in": 2},
    "OTU": {"instr": "OTU", "type": "output", "args": 1, "block_type": "OUT", "blocks_in": 1},

    # Oneshot Instructions
    "DIFD(14)": {"instr": "OSF", "type": "oneshot", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "DIFU(13)": {"instr": "OSR", "type": "oneshot", "args": 1, "block_type": "OUT", "blocks_in": 1},

    # Timer Instructions
    "TIM": {"instr": "TON", "type": "timer", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "TTIM(87)": {"instr": "RTO", "type": "ret_timer", "args": 1, "block_type": "OUT", "blocks_in": 2}, # Retentive timer with resset input

    # Counter Instructions
    "CNT": {"instr": "CTU", "type": "counter", "args": 1, "block_type": "OUT", "blocks_in": 2},

    # Reset Instructions (Counter/Timer)
    "RESET": {"instr": "RES", "type": "reset", "args": 1, "block_type": "OUT", "blocks_in": 1},
    "CNR(545)": {"instr": "RES", "type": "counter", "args": 1, "block_type": "OUT", "blocks_in": 1}, # Reset counters & timers in input range: N1(start range) & N2(end range)

    # Comparison Instructions
    "CMP(20)": {"instr": "", "type": "compare", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "CMPL(60)": {"instr": "", "type": "compare", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "AND<(310)": {"instr": "LES", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "AND<=(315)": {"instr": "LEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "AND=(300)": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "AND=L(300)": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "AND>(320)": {"instr": "GRT", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "AND>=(325)": {"instr": "GEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LD<(310)": {"instr": "LES", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LD<=(315)": {"instr": "LEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LD=(300)": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LD>(320)": {"instr": "GRT", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LD>=(325)": {"instr": "GEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "OR<=(315)": {"instr": "LEQ", "type": "or_compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "OR=(300)": {"instr": "EQU", "type": "or_compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "OR>(320)": {"instr": "GRT", "type": "or_compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "OR>=(325)": {"instr": "GEQ", "type": "or_compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "GREATER_THAN": {"instr": "GRT", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LESS_THAN": {"instr": "LES", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "EQUALS": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "P_GT": {"instr": "GRT", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "P_LT": {"instr": "LES", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "P_EQ": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "EQU": {"instr": "EQU", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "GRT": {"instr": "GRT", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "GEQ": {"instr": "GEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LES": {"instr": "LES", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},
    "LEQ": {"instr": "LEQ", "type": "compare", "args": 2, "block_type": "IN", "blocks_in": 1},

    # Math Instructions
    "-B(414)": {"instr": "SUB", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "*(420)": {"instr": "MUL", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "*B(424)": {"instr": "MUL", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "/(430)": {"instr": "DIV", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "/BL(435)": {"instr": "DIV", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "/UL(433)": {"instr": "DIV", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+(400)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+B(404)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+BCL(407)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+C(402)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+CL(403)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "+L(401)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "ADD(30)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "SUB(31)": {"instr": "SUB", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "MUL(32)": {"instr": "MUL", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "DIV(33)": {"instr": "DIV", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "ADB(50)": {"instr": "ADD", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "SBB(51)": {"instr": "SUB", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "MLB(52)": {"instr": "MUL", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "DVB(53)": {"instr": "DIV", "type": "math", "args": 3, "block_type": "OUT", "blocks_in": 1},

    # Copy Instructions
    "MOV(21)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "MOVD(83)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "MOVL(498)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "BCD(24)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "BCDL(59)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "BIN(23)": {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "XFER(70)": {"instr": "COP", "type": "copy", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "XFRB(62)": {"instr": "COP", "type": "copy", "args": 3, "block_type": "OUT", "blocks_in": 1},
    "BSET(71)": {"instr": "FLL", "type": "copy", "args": 3, "block_type": "OUT", "blocks_in": 1}, # For fill length, Omron specifies start & end bits; AB specifies start bit & length
    "MOVB(82)": {"instr": "BTD", "type": "copy", "args": 5, "block_type": "OUT", "blocks_in": 1}, # Omron has 3 args (Source, Control Word, Dest), AB has 5 (Source, Source bit, Dest, Dest Bit, Length).
    "ANDW(34)": {"instr": "AND", "type": "logic", "args": 1, "block_type": "IN", "blocks_in": 1},

    # Scaling Instructions
    "SCL(64)": {"instr": "CPT", "type": "scaling", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "SCL(194)": {"instr": "CPT", "type": "scaling", "args": 2, "block_type": "OUT", "blocks_in": 1},
    "APR(69)": {"instr": "CPT", "type": "scaling", "args": 2, "block_type": "OUT", "blocks_in": 1},

    # PID Instructions
    "PID(60)": {"instr": "PID", "type": "pid", "args": 3, "block_type": "OUT", "blocks_in": 1}, # PID Includes more than 3 args, but we're only interested in PID, PV and CV
    "PID(190)": {"instr": "PID", "type": "pid", "args": 3, "block_type": "OUT", "blocks_in": 1}, # PID Includes more than 3 args, but we're only interested in PID, PV and CV

    # Stack Instructions
    "PUSH(632)": {"instr": "FFL", "type": "stack", "args": 3, "block_type": "OUT", "blocks_in": 1}, # Args: Source, FIFO, Control Word. CW should be the same across the same FFL and FFU.
    "FIFO(633)": {"instr": "FFU", "type": "stack", "args": 3, "block_type": "OUT", "blocks_in": 1}, # Args: FIFO, Dest, Control Word. CW should be the same across the same FFL and FFU.

    # End of Rung
    "^^^": ";\n",

     # Other Instructions - No 1:1 conversion
    # "CLC(41)": ["other", "CLC"],
    # "DATE(735)": ["?", "System"],
    # "CADD(730)": ["?", "Math"],
    # "PMCR(260)": {"instr": "", "type": "macro", "args": "?"},
    # "SSET(630)": {"in str": "?", "type": "stack", "args": "?"}, # Not needed with Rockwell

    # Ignored Instructions
    "CLC(41)": {"instr": "ignore", "type": "macro", "args": 0, "block_type": "OUT", "blocks_in": 1},
    "DATE(735)": {"instr": "ignore", "type": "macro", "args": 0, "block_type": "OUT", "blocks_in": 1},
    "CADD(730)": {"instr": "ignore", "type": "macro", "args": 0, "block_type": "OUT", "blocks_in": 1},
    "PMCR(260)": {"instr": "ignore", "type": "macro", "args": 0, "block_type": "OUT", "blocks_in": 1},
    "SSET(630)": {"instr": "ignore", "type": "stack", "args": 0, "block_type": "OUT", "blocks_in": 1}, # Not needed with Rockwell
}
