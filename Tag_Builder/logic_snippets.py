import routine_components as rt
import file_functions as f

from datetime import date
import re

# New line
n = '\n'

def NOP(file, rnum, comment=None):
    file, rnum = f.addRung(file, rnum, "NOP()", str(comment)) 

    return file, rnum

def section(secNum, comment):

    string = """**********************************************************
    
""" + str(secNum) + ". " + comment + """
    
**********************************************************"""

    secNum += 1

    return secNum, string

def firstComment(file, rnum, phase, tagfile):
    cmt = rt.first_cmt_start.replace(rt.tag, phase.tag).replace(rt.phase, phase.description)
    cmt += "0. PRE-START\n"
    for step in range(phase.steps):
        cmt += str(step+1) + ". " + str(phase.step_detail[step+1][0]) + "\n"

    cmt += rt.first_cmt_end.replace(rt.date, date.today().strftime('%d%b%Y'))
    file, rnum = f.addRung(file, rnum, "NOP()", str(cmt)) 

    tagfile = f.addTag(phase.tag, "Phase " + phase.tag + " - " + phase.description , "UDDT_Phase", tagfile, phasenum=phase.number)

    return file, rnum, tagfile

def setPhaseNum(file, rnum, snum, phase, tagfile):
    base_comment = rt.set_phase_cmt
    comment = base_comment.replace(rt.cmt_num, str(snum))

    base_logic = rt.set_phase_lgc
    logic = base_logic.replace(rt.phase, phase.tag).replace(rt.phase_num, str(phase.number))

    file, rnum = f.addRung(file, rnum, logic, comment)
    snum += 1

    for param in phase.phase_parameters:
        desc = param.replace("_", " ") + " Phase Parameter"
        param = phase.tag + "_" + param.replace(" ", "_") + "_SP"
        # tagfile = f.addTag(param, desc, "UDDT_Setpoint", tagfile)

    return file, rnum, snum, tagfile

def addAOIControls(file, rnum, snum, phase, tagfile):

    # Standard series of commands - can be updated
    commands = ["Start", "Hold", "Restart", "Stop", "Abort", "Reset"]
    states = [("Restarting","Running"), ("Stopping","Stopped"), ("Holding", "Held"), ("Aborting", "Aborted")]

    snum, comment = section(snum, "Handle Commands from Batch Engine")
    file, rnum = NOP(file, rnum, comment)

    for cmd in commands:
        comment = cmd + " Command"

        base_logic = rt.batch_cmd
        logic = base_logic.replace(rt.phase, phase.tag).replace(rt.cmd, cmd)

        file, rnum = f.addRung(file, rnum, logic, comment)

    # Add Manual Mode Control
    logic = rt.phase_mode_ctrl.replace(rt.phase, phase.tag)
    comment = "Set Phase Mode"
    file, rnum = f.addRung(file, rnum, logic, comment)


    comment = """**********************************************************
    
    Handle Phase State Transitions

    **********************************************************"""
    file, rnum = NOP(file, rnum, comment)

    for sts, cmd in states:

        comment = sts
        if sts == "Stopping" or sts == "Holding" or sts == "Aborting":
            base_logic = rt.state_trans_tmr
            logic = base_logic.replace(rt.phase, phase.tag).replace(rt.state, sts).replace(rt.cmd, cmd)
        else: 
            base_logic = rt.state_trans
            logic = base_logic.replace(rt.phase, phase.tag).replace(rt.state, sts).replace(rt.cmd, cmd)

        file, rnum = f.addRung(file, rnum, logic, comment)
    
    logic = rt.set_AOI_lgc.replace(rt.phase, phase.tag)
    comment = "Run Phase AOI"
    file, rnum = f.addRung(file, rnum, logic, comment)

    return file, rnum, snum, tagfile

def addPermissives(file, rnum, snum, phase, tagfile):

    # Set permissive number
    perm_num = 0

    snum, comment = section(snum, "Prestart Conditions")
    file, rnum = NOP(file, rnum, comment)
    
    if len(phase.EM)>0:
        # Prestart 0
        comment = "Prestart Condition " + str(perm_num)
        logic = rt.prestart0_start
        for em in phase.EM:
            logic += rt.prestart0_lgc.replace(rt.em, em)
        
        logic += rt.prestart0_end.replace(rt.phase, phase.tag).replace(rt.prestart_num, str(perm_num))
        file, rnum = f.addRung(file, rnum, logic, comment)
        perm_num += 1

        # Prestart 1
        comment = "Prestart Condition " + str(perm_num)
        logic = rt.prestart1_start
        for em in phase.EM:
            logic += rt.prestart1_lgc.replace(rt.phase, phase.tag).replace(rt.em, em)
        
        logic += rt.prestart1_end.replace(rt.phase, phase.tag).replace(rt.prestart_num, str(perm_num))
        file, rnum = f.addRung(file, rnum, logic, comment)
        perm_num += 1
    
    if len(phase.permissives) > 0:
        # Prestart 2
        comment = "Prestart Condition " + str(perm_num)
        logic = rt.prestart2_start
        for perm in phase.permissives:
            if bool(re.search(r'\d', perm[1])): tag = phase.unit + "_" + perm[1]
            else: tag = perm[1]
            if perm[0] == "TAG":
                logic += rt.prestart2_lgc_tag.replace(rt.phase, phase.tag).replace(rt.tag, tag)
            elif perm[0] == "GRT":
                logic += rt.prestart2_lgc_grt.replace(rt.phase, phase.tag).replace(rt.tag, tag).replace(rt.value, perm[2])
            elif perm[0] == "LES":
                logic += rt.prestart2_lgc_les.replace(rt.phase, phase.tag).replace(rt.tag, tag).replace(rt.value, perm[2])
            
        logic += rt.prestart2_end.replace(rt.phase, phase.tag).replace(rt.prestart_num, str(perm_num))
        file, rnum = f.addRung(file, rnum, logic, comment)
        perm_num += 1
    
    # Centralization
    if len(phase.EM)>0:
        comment = "Prestart Centralization"
        logic = ""
        for i in range(2):
            logic += rt.prestart_centr_lgc.replace(rt.phase, phase.tag).replace(rt.prestart_num, str(i))
        logic += rt.prestart_centr_end.replace(rt.phase, phase.tag)
        file, rnum = f.addRung(file, rnum, logic, comment)

    # Centralization for HMI only
    comment = """
Prestart Centralization FOR HMI
This bit is used to manage alarms that are enabled as prestart conditions. They are actually evaluated in Step 0, but the HMI should not allow to start

"""
    logic = ""
    for i in range(perm_num):
        logic += rt.prestart_centr_lgc.replace(rt.phase, phase.tag).replace(rt.prestart_num, str(i))
    logic += rt.prestart_centr_HMI_end.replace(rt.phase, phase.tag)
    file, rnum = f.addRung(file, rnum, logic, comment)


    return file, rnum, snum, tagfile

def addInterlocks(file, rnum, snum, phase, tagfile):

    # Set interlock number
    intlk = 0

    snum, comment = section(snum, "Interlock Conditions")
    file, rnum = NOP(file, rnum, comment)
    
    if len(phase.EM)>0:
        # interlock 0
        comment = "Interlock Condition " + str(intlk)
        logic = rt.interlock0_start
        for em in phase.EM:
            logic += rt.interlock0_lgc.replace(rt.em, em)
        
        logic += rt.interlock0_end.replace(rt.phase, phase.tag).replace(rt.intlk_num, str(intlk))
        file, rnum = f.addRung(file, rnum, logic, comment)
        intlk += 1

    # interlock 1
    comment = "Interlock Condition " + str(intlk)
    logic = rt.interlock1_start
    if phase.alarms != []:
        for alarm in phase.alarms:
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic += rt.interlock1_lgc.replace(rt.phase, phase.tag).replace(rt.alarm, alarm)
    
    logic += rt.interlock1_end.replace(rt.phase, phase.tag).replace(rt.intlk_num, str(intlk))
    file, rnum = f.addRung(file, rnum, logic, comment)
    intlk += 1

    # COMMENT OUT IF SYSTEM DOESNT HAVE STOP/ABORT ALARMS. 

    # interlock 2
    comment = "Interlock Condition " + str(intlk)
    logic = rt.interlock2_lgc.replace(rt.phase, phase.tag).replace(rt.intlk_num, str(intlk))
    file, rnum = f.addRung(file, rnum, logic, comment)
    intlk += 1

    # interlock 3
    comment = "Interlock Condition " + str(intlk)
    logic = rt.interlock3_lgc.replace(rt.phase, phase.tag).replace(rt.intlk_num, str(intlk))
    file, rnum = f.addRung(file, rnum, logic, comment)
    intlk += 1
    
    
    # Centralization
    comment = "Interlock Centralization"
    logic = ""
    for i in range(intlk):
        logic += rt.interlock_centr_lgc.replace(rt.phase, phase.tag).replace(rt.intlk_num, str(i))
    logic += rt.interlock_centr_end.replace(rt.phase, phase.tag)
    file, rnum = f.addRung(file, rnum, logic, comment)


    return file, rnum, snum, tagfile

def emAcqRelease(file, rnum, snum, phase, tagfile):

    snum, comment = section(snum, "Equipment Modules Acquisition & Release Section")
    file, rnum = NOP(file, rnum, comment)

    # EM Acquisition
    if len(phase.EM)>0:
        comment = "Acquire EM"
        logic = rt.EM_acq_start.replace(rt.phase, phase.tag)

        if len(phase.EM)>1:
                logic += rt.EM_acq_lgc1_start

        for i, em in enumerate(phase.EM):
            logic += rt.EM_acq_lgc1.replace(rt.phase, phase.tag).replace(rt.em, em)
            if i != len(phase.EM)-1:
                logic += "," # Add commas for all but the last one
        if len(phase.EM)>1:
            logic += rt.EM_acq_lgc1_end1
        else:
            logic += rt.EM_acq_lgc1_end2

        for em in phase.EM:
            logic += rt.EM_acq_lgc2.replace(rt.phase, phase.tag).replace(rt.em, em)
        logic += rt.EM_acq_end.replace(rt.phase, phase.tag)
    else: 
        logic = rt.EM_acq_noEM.replace(rt.phase, phase.tag)
    

    file, rnum = f.addRung(file, rnum, logic, comment)

    # EM Release and reset tags
    if len(phase.EM)>0:
        comment = "Release EM and Reset Tags"
        logic = rt.EM_rel_start.replace(rt.phase, phase.tag)

        if len(phase.EM)>1:
            logic += rt.EM_rel_lgc_start
        for i, em in enumerate(phase.EM):
                logic += rt.EM_rel_lgc.replace(rt.phase, phase.tag).replace(rt.em, em)
                if i != len(phase.EM)-1:
                    logic += "," # Add commas for all but the last one

        # Here we're checking if any of the phase steps have a "PROMPT" type in them. If so, reset prompts
        types = (steps for steps in phase.step_detail if "PROMPT" in phase.step_detail[steps][1][0].upper()) 
        try: 
            next(types)
            hasprompts = True
        except: hasprompts = False
        if hasprompts: 
            if len(phase.EM)>0: logic += "," # Add commas 
            logic += rt.prompt_reset.replace(rt.phase, phase.tag)

        if len(phase.EM)>1:
            logic += rt.EM_rel_end
        
    file, rnum = f.addRung(file, rnum, logic, comment)

    return file, rnum, snum, tagfile

def addPhaseSteps(file, rnum, snum, phase, tagfile):
    
    comment = """6. Phase Step Control Section

- Logical flow through phase steps when phase is running, using a "Step Complete" boolean to indicate when a step has completed
- Upon step completion, the next step number identifier is moved into the "CurrentStep" variable
- When a phase is not running, or all steps are complete, CurrentStep = 999"""

    snum, comment = section(snum, comment)
    file, rnum = NOP(file, rnum, comment)

    for step in range(phase.steps + 1):
        if step > 0: comment = "Step " + str(step) + " - " + phase.step_detail[step][0]
        else: comment = "Step 0 - PRE-START"
        next_step = step + 1
        if step != phase.steps:
            logic = rt.step_ctrl.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.next_step, str(next_step))
        else: 
            logic = rt.step_ctrl_last.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.next_step, str(next_step))
        file, rnum = f.addRung(file, rnum, logic, comment)
    
    return file, rnum, snum, tagfile

def addPhaseLogic(file, rnum, snum, phase, tagfile):
    
    snum, comment = section(snum, "Phase Step Execution Section")
    file, rnum = NOP(file, rnum, comment)

    # Step 0 - basic
    comment = "Step 0 - PRE-START"
    step = 0
    logic = rt.step_lgc_step0_start.replace(rt.phase, phase.tag).replace(rt.current_step, str(step))
    for param in phase.rpt_parameters:
        param = phase.tag + "_" + param.replace(" ", "_")
        logic += rt.step_lgc_step0_lgc.replace(rt.report, param)
        # tagfile = f.addTag(param, param + " Report Parameter", "REAL", tagfile)
    logic += rt.step_lgc_step0_end.replace(rt.phase, phase.tag).replace(rt.current_step, str(step))

    file, rnum = f.addRung(file, rnum, logic, comment)

    promptnum = 1
    # Remaining Steps
    for step in phase.step_detail:
        type = phase.step_detail[step][1][0].upper()
        # print(type)
        comment = "Step " + str(step) + " - " + phase.step_detail[step][0]
        # TIMER TYPE
        if type == "TIMER":
            parameter = phase.tag + "_" + phase.step_detail[step][1][1].replace(" ", "_") + "_SP"
            report = phase.tag + "_" + phase.step_detail[step][1][1].replace(" ", "_") + "_RPT"
            timer = phase.tag + "_" + phase.step_detail[step][1][1].replace(" ", "_").replace("TIME", "TMR")
            logic = rt.step_lgc_tmr.replace(rt.phase, phase.tag).replace(rt.parameter, parameter).replace(rt.report, report).replace(rt.timer, timer).replace(rt.current_step, str(step))
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(report, report + " Report Parameter", "REAL", tagfile)
            tagfile = f.addTag(timer, timer + " Timer", "Timer", tagfile)
        # PROMPT TYPE
        elif type == "PROMPT":
            if promptnum == 1:
                logic = rt.step_lgc_prompt.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.promptnum, str(promptnum))
            # If previous phase step is also prompt, add a delay timer to this step
            elif phase.step_detail[step-1][1][0].upper() == "PROMPT":
                logic = rt.step_lgc_prompt_delay.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.promptnum, str(promptnum))
            else:
                logic = rt.step_lgc_prompt.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.promptnum, str(promptnum))                
            promptnum += 1
        # COMPARISON TYPE 
        elif type == "GRT" or type == "LES" or type == "GEQ" or type == "LEQ":
            tag = phase.unit + "_" + phase.step_detail[step][1][1].replace("-","_")
            parameter = phase.tag + "_" + phase.step_detail[step][1][2].replace(" ", "_").replace("-","_") + "_SP"
            report = phase.tag + "_" + phase.step_detail[step][1][2].replace(" ", "_").replace("-","_") + "_RPT"
            logic = rt.step_lgc_comp.replace(rt.phase, phase.tag).replace(rt.parameter, parameter).replace(rt.report, report).replace(rt.tag, tag).replace(rt.comparator, type).replace(rt.current_step, str(step))
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(report, report + " Report Parameter", "REAL", tagfile)
        # TIMER-TAG TYPE
        elif type == "TMR-TAG":
            tag = phase.unit + "_" + phase.step_detail[step][1][1].replace("-","_")
            parameter = phase.tag + "_" + phase.step_detail[step][1][2].replace(" ", "_").replace("-","_") + "_SP"
            report = phase.tag + "_" + phase.step_detail[step][1][2].replace(" ", "_").replace("-","_") + "_RPT"
            logic = rt.step_lgc_tmr_tag.replace(rt.phase, phase.tag).replace(rt.parameter, parameter).replace(rt.report, report).replace(rt.timer, timer).replace(rt.tag, tag).replace(rt.current_step, str(step))
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(report, report + " Report Parameter", "REAL", tagfile)
        # SIGNAL TYPE
        elif type == "SIGNAL":
            try: tag = "CIP_to_Comp_" + phase.step_detail[step][1][1].replace(" ","").replace("-","_")
            except: tag = "temp"
            logic = rt.step_lgc_tag.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.tag, tag)
        # TAG TYPE
        elif type == "TAG": 
            try: tag = phase.step_detail[step][1][1].replace("-","_")
            except: tag = "temp_tag"
            logic = rt.step_lgc_tag.replace(rt.phase, phase.tag).replace(rt.current_step, str(step)).replace(rt.tag, tag)
        
        else: logic = rt.step_lgc_basic.replace(rt.phase, phase.tag).replace(rt.current_step, str(step))
        file, rnum = f.addRung(file, rnum, logic, comment)
    
    return file, rnum, snum, tagfile

def addALarmLogic(file, rnum, snum, phase, tagfile):
    
    snum, comment = section(snum, "Phase Alarm Section")
    file, rnum = NOP(file, rnum, comment)

    dint = int(phase.number/32)
    bit = phase.number - dint*32

    # Enable Logic
    for alarm in phase.alarms:
        comment = alarm +  " Alarm Enable"
        
        logic = rt.alarm_enable_start.replace(rt.phase, phase.tag)
        if len(phase.alarms[alarm][1]) > 1 : 
            logic += "["
            for i, step in enumerate(phase.alarms[alarm][1]):
                logic += rt.alarm_enable_lgc.replace(rt.phase, phase.tag).replace(rt.step, str(step))
                if i != len(phase.alarms[alarm][1])-1:
                    logic += "," # Add commas for all but the last one
            logic += "]"
        else: 
            logic += rt.alarm_enable_lgc.replace(rt.phase, phase.tag).replace(rt.step, str(phase.alarms[alarm][1][0]))

        alarm = alarm.replace(" ", "_") + "_ALM"
        logic += rt.alarm_enable_end.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))
        file, rnum = f.addRung(file, rnum, logic, comment)

    # Activate Alarm Logic
    for alarm in phase.alarms:
        comment = alarm +  " Alarm"
        type = phase.alarms[alarm][0]
        try: alarm_word = alarm.split()[0]
        except: alarm_word = alarm
        
        if type == "TAG":
            tag = alarm.replace(" ", "_").replace("-", "_")
            cmd = "XIO"
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_tag.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.tag, tag).replace(rt.cmd, cmd).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))
            tagfile = f.addTag(alarm, alarm + " Alarm", "UDDT_Alarm", tagfile)
        elif type == "LIMIT":
            if "HI" in alarm.upper(): cmd = "GRT"
            elif "LO" in alarm.upper(): cmd = "LES"
            else: cmd = "GEQ"
            timer = phase.tag + "_" + alarm.replace(" ", "_") + "_TMR"
            parameter = phase.tag + "_" + phase.alarms[alarm][2][0]
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_limit.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.timer, timer).replace(rt.parameter, parameter).replace(rt.cmd, cmd).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))
            tagfile = f.addTag(alarm, alarm + " Alarm", "UDDT_Alarm", tagfile)
        elif type == "TIMEOUT":
            value = "temp" #phase.tag + "_" + phase.alarms[alarm][4].replace(" ", "_") + "_SP"
            tag = "temp" #phase.tag + "_" + "MAX_" + alarm[0] + "TIME_SP"
            parameter = phase.tag + "_" + phase.alarms[alarm][2][0]
            timer = phase.tag + "_" + alarm.replace(" ", "_") + "_TMR"
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_timeout.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.timer, timer).replace(rt.tag, tag).replace(rt.value, value).replace(rt.parameter, parameter).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))    
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(alarm, alarm + " Alarm", "UDDT_Alarm", tagfile)
            tagfile = f.addTag(timer, timer + " Timer", "Timer", tagfile)
        elif type == "RANGE":
            tag = "temp" #phase.alarms[alarm][3]
            timer = phase.tag + "_" + alarm.replace(" ", "_") + "_TMR"
            parameter = phase.tag + "_" + phase.alarms[alarm][2][0]
            param_low = phase.tag + "_" + phase.alarms[alarm][2][1]
            param_high = phase.tag + "_" + phase.alarms[alarm][2][2]
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_outofrange.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.timer, timer).replace(rt.tag, tag).replace(rt.parameter, parameter).replace(rt.param_low, param_low).replace(rt.param_high, param_high).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))    
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(param_low, param_low + " Low Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(param_high, param_high + " High Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(alarm, alarm + " Alarm", "UDDT_Alarm", tagfile)
            tagfile = f.addTag(timer, timer + " Timer", "Timer", tagfile)
        elif type == "NOFEEDBACK":
            tag = "temp" #phase.alarms[alarm][3]
            parameter = phase.tag + "_" + alarm.replace(" ", "_") + "_SP"
            timer = phase.tag + "_" + alarm.replace(" ", "_") + "_TMR"
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_tag.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.tag, tag).replace(rt.cmd, cmd).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))    
            tagfile = f.addTag(parameter, parameter + " Setpoint", "UDDT_Setpoint", tagfile)
            tagfile = f.addTag(alarm, alarm + " Alarm", "UDDT_Alarm", tagfile)
            tagfile = f.addTag(timer, timer + " Timer", "Timer", tagfile)
        else: 
            alarm = alarm.replace(" ", "_") + "_ALM"
            logic = rt.alarm_active_lgc.replace(rt.phase, phase.tag).replace(rt.alarm, alarm).replace(rt.tag, "temp").replace(rt.dint, str(dint)).replace(rt.bit, str(bit))
        
        file, rnum = f.addRung(file, rnum, logic, comment)

    # Add hold, stop & abort logic
    comment = "Hold Phase"
    logic = rt.alarm_hold_lgc.replace(rt.phase, phase.tag)
    file, rnum = f.addRung(file, rnum, logic, comment)
    
    # COMMENTED OUT SINCE COMPOUNDING DOESNT NEED STOP/ABORT. BRING BACK IF NEEDED
    comment = "Stop Phase"
    logic = rt.alarm_stop_lgc.replace(rt.phase, phase.tag)
    file, rnum = f.addRung(file, rnum, logic, comment)
    comment = "Abort Phase"
    logic = rt.alarm_abort_lgc.replace(rt.phase, phase.tag)
    file, rnum = f.addRung(file, rnum, logic, comment)
    
    return file, rnum, snum, tagfile

def addEMLogic(file, rnum, snum, phase, tagfile):
    
    snum, comment = section(snum, "Equipment Module Control Section")
    file, rnum = NOP(file, rnum, comment)

    dint = int(phase.number/32)
    bit = phase.number - dint*32

    if len(phase.EM)>0:
        for em in phase.EM:
            comment = "Enable " + em

            # Need to add enabled steps from phase object
            logic = rt.em_enable_start.replace(rt.phase, phase.tag)
            if len(phase.EM[em]) > 1 : 
                logic += "["
                for step, signal in phase.EM[em]:
                    logic += rt.em_enable_lgc.replace(rt.phase, phase.tag).replace(rt.step, str(step))
                    if step != phase.EM[em][-1][0]:
                        logic += "," # Add commas for all but the last one
                logic += "]"
            else: logic += rt.em_enable_lgc.replace(rt.phase, phase.tag).replace(rt.step, str(phase.EM[em][0][0]))

            logic += rt.em_enable_end.replace(rt.phase, phase.tag).replace(rt.em, em).replace(rt.dint, str(dint)).replace(rt.bit, str(bit))
            file, rnum = f.addRung(file, rnum, logic, comment)

        # repeated to place enables beside each other and then activations
        for em in phase.EM:
            comment = "Set " + em + " Signal"

            # Need to add active steps and phase signals from phase object
            for step, signal in phase.EM[em]:
                signal = em.replace("-","") + "_" + signal.replace("-","_")
                logic = rt.em_signal_lgc.replace(rt.phase, phase.tag).replace(rt.step, str(step)).replace(rt.em, em).replace(rt.em_signal, signal)
                file, rnum = f.addRung(file, rnum, logic, comment)

    return file, rnum, snum, tagfile

def addPhaseReset(file, phases):
    logic = rt.reset_lgc_start
    rnum = 0
    for phase in phases:
        logic += rt.reset_lgc.replace(rt.phase, phase.tag)
        if phase != phases[-1]: logic += "," 

    logic += rt.reset_lgc_end

    file, rnum = f.addRung(file, rnum, logic)

    return file

def addPhaseModeEnable(file, phases):
    logic = rt.mode_en_lgc_start
    rnum = 0
    for phase in phases:
        logic += rt.mode_en_lgc.replace(rt.phase, phase.tag)
        if phase != phases[-1]: logic += "," 

    logic += rt.mode_en_lgc_end

    file, rnum = f.addRung(file, rnum, logic)

    return file

def addPhaseJSR(file, phases):
    logic = ""
    rnum = 0
    for phase in phases:
        if phase.number >= 100: rung_number = "R" + str(phase.number)
        elif phase.number >= 10: rung_number = "R0" + str(phase.number)
        else: rung_number = "R00" + str(phase.number)
        routine_name = rung_number + "_" + phase.tag + "_" + phase.description.replace("(","").replace(")","").replace(" ","_").replace("-","_")
        if len(routine_name) > 40: routine_name = routine_name[0:40]
        if routine_name[-1] == "_": routine_name = routine_name[:-1]

        logic += rt.JSR_lgc.replace(rt.routine, routine_name)
        if phase != phases[-1]: logic += "\n" 

    file.write(logic)

    return logic