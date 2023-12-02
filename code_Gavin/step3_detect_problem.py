import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import util.deal_with_UI as UI
import util.Constant as Constant
from util.NLP import NLP
from model.Input import Input
from model.Question import Question
from skill.getAns import getAns

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

def isUnrespondingVUI(lastI, lastRequest, request, spider, FileName):
    if len(request) == 0:
        Inpt = Input(0, 'what\'s the time')
        requests = UI.input_and_response(spider, Inpt, FileName, True)
        if len(requests) != 0:
            print(requests)
        if len(requests) == 0 or requests[-1][1] != 'Alexa':
            if 'pause' in lastI.get_input():
                Inpt = Input(0, 'resume')
                print(Inpt.get_input())
                requests = UI.input_and_response(spider, Inpt, FileName, True)
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

def privacyLeakage(request, gpt):
    privacy = ['zipcode', 'yourname', 'phonenumber', 'creditcard', 'yourgender', 'yourbirthday', 'identitycard', 'youremail', 'address']
    # chrome_options = Options()
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--headless')
    # s = Service(executable_path=Constant.CHROME_PATH)
    # driver = webdriver.Chrome(options= chrome_options, service=s)
    output = getAns("", [], [], "", gpt, None)
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
                #print(word, protreatedQues)
                res = output.getResponses(Question(question), None, None)
                if len(res) > 0:
                    # driver.close()
                    # driver.quit()
                    return True, word
    # driver.close()
    # driver.quit()
    return False, ''

def isUnstoppable(spider, lastInpt, FileName):
    for sign in Constant.StopSign:
        if sign in lastInpt.get_input():
            Inpt = Input(0, 'what\'s the time')
            print(Inpt)
            requests = UI.input_and_response(spider, Inpt, FileName, True)
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
