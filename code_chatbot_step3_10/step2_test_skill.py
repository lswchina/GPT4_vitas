import os
import time
import re
from util.NLP import NLP
import util.deal_with_UI as UI
import util.Constant as Constant
from skill.getAns import getAns
import step3_detect_problem as pro_detc

def addProblem(fileName, inputs):
    if not os.path.exists(fileName):
        file = open(fileName, 'w')
        file.close()
    with open(fileName, "r+", encoding='utf-8') as file:
        lines = file.readlines()
        if len(lines) == 0 or inputs not in lines[-1]:
            file.write(inputs)
            file.write("\n")

def invalidRequest(request):
    if len(request) == 1 and request[0][0] == 'cookie wrong':
        return True
    return False

def ansAlexa(output, questions):
    ans = output.getResponse(questions)
    return ans
    
def ansSkill(output, request, time_before_testing):
    questions = ""
    for req in request:
        if req[1] != 'Alexa':
            questions = req[0]
            break
    if time.time() - time_before_testing >= Constant.TIME_LIMIT:
        return "stop"
    else:
        return output.getResponse(questions)
    
def isSkillStart(request):
    for req in request:
        if req[1] != "Alexa":
            return True
    return False

def getAlexa(request):
    for req in request:
        if req[1] == 'Alexa':
            return req[0]
    return None

def generateTest(skill_log_path, res_dir, spider, skill, gpt):
    skillName_to_dirName = re.sub(r'(\W+)', '_', skill.skillName)
    output = getAns(gpt)
    endWithStop = False
    i = 0
    time_before_testing = time.time()
    while time.time() - time_before_testing < Constant.TIME_LIMIT:
        time_start = time.time()
        fileTest = os.path.join(skill_log_path, skillName_to_dirName + str(i) + ".txt")
        log = ''
        Stop = False
        skillStart = False
        questions = ""
        lastRequest = []
        inpt = skill.invocation[0]
        rounds = 0

        request = UI.input_and_response(spider, inpt, fileTest, False)
        if invalidRequest(request) or len(request) == 0:
            continue

        while Stop == False and getAlexa(request) is not None and skillStart == False and rounds < 4:
            print(request)
            result = pro_detc.unexpectedSkills(request, skill.skillName, skill.supportRegion) #problem 4: unexpected skills started
            if result[0] == True:
                if result[1] != 'region':
                    if rounds == 0 and result[1] != "":
                        log += "problem4----------unexpected skills started!\n"
                        addProblem(os.path.join(res_dir, "problem4.txt"), skill.skillName + ": " + result[1])
                        skillStart = True
                    else:
                        log += "problem5----------unavailable skill!\n"
                        addProblem(os.path.join(res_dir, "problem5.txt"), skill.skillName)
                Stop = True
                break
            
            skillStart = isSkillStart(request)
            if skillStart == True:
                result = pro_detc.privacyLeakage(request)            #problem 2: privacy violation
                if result[0]:
                    log += "problem2----------privacy violation!\n"
                    if len(skill.permission_list) == 0:
                        addProblem(os.path.join(res_dir, "problem2.txt"), skill.skillName + ": " + result[1])
                    else:
                        permission_str = ','.join(skill.permission_list)
                        addProblem(os.path.join(res_dir, "problem2.txt"), skill.skillName + ": " + result[1] + "(" + permission_str + ")")
                break
            #answer alexa
            alexa_response = getAlexa(request)
            if alexa_response is None:
                Stop = True
                break
            questions = alexa_response
            inpt = ansAlexa(output, questions)
            if inpt == "":
                Stop = True
                break
            print(inpt)
            rounds = rounds + 1
            request = UI.input_and_response(spider, inpt, fileTest, False)
            if invalidRequest(request) == True or len(request) == 0:
                Stop = True
                break
        if rounds >= 4:
            Stop = True

        rounds = 0
        while Stop == False:
            skillStart = True
            inpt = ansSkill(output, request, time_before_testing)
            print(inpt)
            if inpt in Constant.StopSign:
                Stop = True
                endWithStop = True
            
            #get new question 
            lastRequest = request
            request = UI.input_and_response(spider, inpt, fileTest, True)
            if invalidRequest(request) == True:
                break
            print(request)

            #detect problems
            p1, type = pro_detc.isUnrespondingVUI(inpt, lastRequest, request, spider, fileTest)     #problem 1: unexpected exit
            if p1:
                if type == 1:
                    if Stop == False:
                        log += "problem1----------unexpected exit!\n"
                        addProblem(os.path.join(res_dir, "problem1.txt"), skill.skillName)
                elif type == 2:
                    if Stop == False:
                        log += "problem1----------unexpected exit!\n"
                        addProblem(os.path.join(res_dir, "problem1.txt"), skill.skillName)
                    else:
                        log += "problem3----------unstoppable skill!\n"
                        addProblem(os.path.join(res_dir, "problem3.txt"), skill.skillName)
            elif pro_detc.isCrash(lastRequest, request):      #problem 1: unexpected exit
                log += "problem1----------unexpected exit!\n"
                addProblem(os.path.join(res_dir, "problem1.txt"), skill.skillName)
                p1 = True
            else:
                p2, privacy = pro_detc.privacyLeakage(request)            #problem 2: privacy violation
                if p2:
                    log += "problem2----------privacy violation!\n"
                    if len(skill.permission_list) == 0:
                        addProblem(os.path.join(res_dir, "problem2.txt"), skill.skillName + ": " + privacy)
                    else:
                        permission_str = ','.join(skill.permission_list)
                        addProblem(os.path.join(res_dir, "problem2.txt"), skill.skillName + ": " + privacy + "(" + permission_str + ")")
                rounds = rounds + 1
            
            #check is stopped
            alexa_response = getAlexa(request)
            if p1 or alexa_response is not None or Stop:
                break

        
        if invalidRequest(request) == True:
            i = 0
            continue
        if pro_detc.isUnstoppable(spider, inpt, fileTest):   #problem 3: unstoppable skill
            log += "problem3----------unstoppable skill!\n"
            addProblem(os.path.join(res_dir, "problem3.txt"), skill.skillName)
        if 'problem5' not in log and pro_detc.isUnavailable(skillStart, NLP.splitSentence(questions), skill.supportRegion):   #problem 5: unavailable skill
            log += "problem5----------unavailable skill!\n"
            addProblem(os.path.join(res_dir, "problem5.txt"), skill.skillName)
        with open(fileTest, "a") as file:
            file.write("\n\nlog:\n")
            file.write(log)
            file.write("\n\ntime:\n")
            file.write(str(time.time() - time_start))
            file.close()
        if 'problem' in log:
            addProblem(os.path.join(res_dir, "problem.txt"), skill.skillName)
        if 'problem1' in log or 'problem3' in log:
            UI.re_open_with_no_exit(spider)
        if 'problem4' in log or 'problem5' in log:
            return
        i = i + 1



#['[21:50:15:963] - Event: Text.TextMessage', '[21:50:17:684] - Directive: SkillDebugger.CaptureDebuggingInfo', '[21:50:17:752] - Directive: SpeechSynthesizer.Speak', '[21:50:17:755] - Directive: SpeechRecognizer.RequestProcessingCompleted', '[21:50:17:782] - Event: SpeechSynthesizer.SpeechStarted', '[21:50:20:955] - Event: SpeechSynthesizer.SpeechFinished']
