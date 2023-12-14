import re
import util.deal_with_UI as UI
import util.Constant as Constant
from util.NLP import NLP

def isCrash(lastRequest, request):
    withAlexa = False
    for ques, speaker in request:
        if speaker == 'Alexa':
            withAlexa = True
            break
    if withAlexa == False:
        return False
    lastQuestions = ''
    for ques, speaker in lastRequest:
        if speaker != 'Alexa':
            lastQuestions = lastQuestions + ques
    goodbye = False
    lastQuestions = lastQuestions.lower()
    goodbye_list = ["see you", "bye", "thank", "account", "app", "App", "tomorrow", "come back"]
    for item in goodbye_list:
        if item in lastQuestions:
            goodbye = True
            break
    if goodbye == False:
        return True
    return False

def isUnrespondingVUI(last_input, lastRequest, request, spider, FileName):
    if len(request) == 0:
        inpt = 'what\'s the time'
        try:
            requests = UI.input_and_response(spider, inpt, FileName, True)
        except:
            return True, 1
        if len(requests) != 0:
            print(requests)
        if len(requests) == 0 or requests[-1][1] != 'Alexa':
            if 'pause' in last_input:
                inpt = 'resume'
                print(inpt)
                requests = UI.input_and_response(spider, inpt, FileName, True)
                if len(requests) != 0 and requests[-1][1] != 'Alexa':
                    return True, 0
                elif len(requests) == 0:
                    return True, 2
                else:
                    return True, 1
            else:
                return True, 2
        else:
            isCra = isCrash(lastRequest, requests)
            if isCra == True:
                return True, 1
            return True, 0
    return False, 0

def privacyLeakage(request):
    privacy = ['zipcode', 'yourname', 'phonenumber', 'creditcard', 'yourgender', 'yourbirthday', 'identitycard', 'youremail', 'address']
    for question, speaker in request:
        if speaker == 'Alexa':
            continue
        protreatedQues = '' #remove character except letters, and convert to lower case
        for letter in question:
            if letter >= 'a' and letter <= 'z':
                protreatedQues = protreatedQues + letter
            elif letter >= 'A' and letter <= 'Z':
                letter = letter.lower()
                protreatedQues = protreatedQues + letter
        for word in privacy:
            if word in protreatedQues:
                spacyRet = NLP.imergeNones(question)
                if NLP.isIQAns(spacyRet) or NLP.isWhQ(question):
                    return True, word
    return False, ''

def isUnstoppable(spider, last_inpt, FileName):
    for sign in Constant.StopSign:
        if sign in last_inpt:
            inpt = 'what\'s the time'
            print(inpt)
            requests = UI.input_and_response(spider, inpt, FileName, True)
            if len(requests) != 0:
                print(requests)
            if len(requests) > 0 and requests[-1][1] != 'Alexa':
                return True
            return False
    return False

def unexpectedSkills(request, skillname, support_region):
    questions = []
    openSkillSentence = ''
    for req in request:
        if req[1] == 'Alexa':
            questions = NLP.splitSentence(req[0])
            for ques in questions:
                if 'Here\'s' in ques or 'Did you mean' in ques or 'Do you mean' in ques:
                    openSkillSentence = ques
                    break
    isSkillStart = True
    skillNa = re.findall(r'Here\'s the skill (.*?)$', openSkillSentence)
    if len(skillNa) == 0:
        skillNa = re.findall(r'Here\'s (.*?)$', openSkillSentence)
    if len(skillNa) == 0:
        skillNa = re.findall(r'Did you mean (.*?)$', openSkillSentence)
        isSkillStart = False
    if len(skillNa) == 0:
        skillNa = re.findall(r'Do you mean (.*?)$', openSkillSentence)
        isSkillStart = False
    print(skillNa)
    if len(skillNa) == 0:
        return False, ""
    skillname_expect = re.sub(r"[^a-zA-Z0-9]", '', skillname)
    skillname_real = re.sub(r"[^a-zA-Z0-9]", '', skillNa[0])
    if skillname_expect not in skillname_real:
        if support_region == False:
            return True, 'region'
        elif isSkillStart == True:
            unexpected_error = "expect " + skillname + ", but start " + skillNa[0]
            return True, unexpected_error    
        else:
            return True, ""
    return False, ""

def isUnavailable(skillStart, questions, support_region):
    goodbye_list = ["account", "app", "App"]
    if skillStart == False:
        for question in questions:
            for goodbye in goodbye_list:
                if goodbye in question:
                    return False
        if support_region == False:
            return False
        else:
            return True
    return False
