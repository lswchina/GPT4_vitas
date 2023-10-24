import os
import time
import re
from util.NLP import NLP
import util.deal_with_UI as UI
import util.Constant as Constant
from model.Input import Input
from model.Question import Question
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
    if len(questions) == 0:
        question = '.'
    else:
        question = questions[-1]
    Answers = output.getResponses(Question(question), None, None)
    for key in Answers:
        return Input(-1, key)
    print("Without answer?")
    return Input(-1, "")
    
def ansSkill(index, output, fsm, rounds, request, lastQuestion, Inpt, time_before_testing):
    questions = []
    for req in request:
        if req[1] != 'Alexa':
            questions = NLP.splitSentence(req[0])
            break
    if rounds == 0 and index == 0:
        output.addHelpAns(questions)
        return output.getResponse(questions, lastQuestion, Inpt, 'help')
    if rounds == 1 and index == 0:
        return output.getHelpResponse(questions, lastQuestion, Inpt)
    elif time.time() - time_before_testing >= Constant.TIME_LIMIT:
        return output.getResponse(questions, lastQuestion, Inpt, 'stop')
    else:
        return output.getResponse(questions, lastQuestion, Inpt)
    
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

def generateTest(skill_log_path, res_dir, spider, skill, gpt, fsm):
    skillName_to_dirName = re.sub(r'(\W+)', '_', skill.skillName)
    output = getAns(skill.skillName, skill.getBascComds(), skill.getSysComds(), skill_log_path, gpt, fsm)
    endWithStop = False
    i = 0
    time_before_testing = time.time()
    while i <= 2 and time.time() - time_before_testing < Constant.TIME_LIMIT:
        time_start = time.time()
        fileTest = os.path.join(skill_log_path, skillName_to_dirName + str(i) + ".txt")
        log = ''
        Stop = False
        skillStart = False
        questions = []
        lastRequest = []
        lastQuestion = None
        Inpt = Input(-1, skill.invocation[0])
        rounds = 0

        request = UI.input_and_response(spider, Inpt, fileTest, False)
        if invalidRequest(request) or len(request) == 0:
            continue

        while Stop == False and getAlexa(request) is not None and skillStart == False and time.time() - time_before_testing < Constant.TIME_LIMIT and rounds < 4:
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
                result = pro_detc.privacyLeakage(request, gpt)            #problem 2: privacy violation
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
            if alexa_response is not None:
                questions = NLP.splitSentence(alexa_response)
            Inpt = ansAlexa(output, questions)
            if Inpt.get_input() == "":
                Stop = True
                break
            print(Inpt)
            rounds = rounds + 1
            request = UI.input_and_response(spider, Inpt, fileTest, False)
            if invalidRequest(request) == True or len(request) == 0:
                Stop = True
                break

        rounds = 0
        while Stop == False and time.time() - time_before_testing < Constant.TIME_LIMIT:
            skillStart = True
            Inpt, lastQuestion = ansSkill(i, output, fsm, rounds, request, lastQuestion, Inpt, time_before_testing)
            print(Inpt)
            if Inpt.get_input() in Constant.StopSign:
                Stop = True
                endWithStop = True
            
            #get new question 
            lastRequest = request
            request = UI.input_and_response(spider, Inpt, fileTest, True)
            if invalidRequest(request) == True:
                break
            print(request)

            #detect problems
            p1, type = pro_detc.isUnrespondingVUI(Inpt, lastRequest, request, spider, fileTest)     #problem 1: unexpected exit
            if p1:
                # Inpt = Input(0, 'what\'s the time')
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
                p2, privacy = pro_detc.privacyLeakage(request, gpt)            #problem 2: privacy violation
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
                Ques = fsm.has_ques("<END>")
                if Ques == None:
                    Ques = Question("<END>")
                    fsm.addQuesToQuesSet(Ques)
                fsm.updateFSM(lastQuestion, Inpt, Ques)
                lastQuestion = Ques
                break

        
        if invalidRequest(request) == True:
            i = 0
            continue
        if pro_detc.isUnstoppable(spider, Inpt, fileTest):   #problem 3: unstoppable skill
            log += "problem3----------unstoppable skill!\n"
            addProblem(os.path.join(res_dir, "problem3.txt"), skill.skillName)
        if lastQuestion == None or lastQuestion.get_ques() != "<END>":
            for sign in Constant.StopSign:
                if sign in Inpt.get_input():
                    Inpt = lastQuestion.has_input("what\'s the time")
                    lastQuestion.addTimes(Inpt)
                    Ques = fsm.has_ques("<END>")
                    if Ques == None:
                        Ques = Question("<END>")
                        fsm.addQuesToQuesSet(Ques)
                    fsm.updateFSM(lastQuestion, Inpt, Ques)
                    break
        if 'problem5' not in log and pro_detc.isUnavailable(skillStart, questions, skill.supportRegion):   #problem 5: unavailable skill
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
    
    if endWithStop == False and time.time() - time_before_testing < Constant.TIME_LIMIT:
        fileTest = os.path.join(skill_log_path, skillName_to_dirName + str(i) + ".txt")
        log = ''
        Inpt = Input(-1, skill.invocation[0])
        time_start = time.time()
        request = UI.input_and_response(spider, Inpt, fileTest, True)
        Inpt = Input(0, 'stop')
        request = UI.input_and_response(spider, Inpt, fileTest, True)
        if pro_detc.isUnstoppable(spider, Inpt, fileTest):   #problem 3: unstoppable skill
            log += "problem3----------unstoppable skill!\n"
            addProblem(os.path.join(res_dir, "problem3.txt"), skill.skillName)
        with open(fileTest, "a") as file:
            file.write("\n\nlog:\n")
            file.write(log)
            file.write("\n\ntime:\n")
            file.write(str(time.time() - time_start))
            file.close()
        return



#['[21:50:15:963] - Event: Text.TextMessage', '[21:50:17:684] - Directive: SkillDebugger.CaptureDebuggingInfo', '[21:50:17:752] - Directive: SpeechSynthesizer.Speak', '[21:50:17:755] - Directive: SpeechRecognizer.RequestProcessingCompleted', '[21:50:17:782] - Event: SpeechSynthesizer.SpeechStarted', '[21:50:20:955] - Event: SpeechSynthesizer.SpeechFinished']
