elif instr_type.upper() == "SPECIAL_RESET":
        # print("Special Reset instruction", og_param, og_param2)
        try:
            start_addr = int(og_param.replace("CNT", "").replace("C", ""))
            end_addr = int(og_param2.replace("CNT", "").replace("C", ""))
            ctrl_length = end_addr - start_addr + 1
            print(ctrl_length)
        except:
            ctrl_length = 1
        # Now build out multiple branched Resets
        if ctrl_length > 1:
            converted_instruction = "["
            for i in range(ctrl_length):
                in_param = "C" + str(int(start_addr) + i)
                out_param = convert_tagname(in_param, tagfile, system_name)
                converted_instruction += conv_instr + "(" + out_param + "),"
            converted_instruction = converted_instruction[:-1] + "]"
        else:
            converted_instruction = conv_instr + "(" + param + ")"
        # print(converted_instruction)