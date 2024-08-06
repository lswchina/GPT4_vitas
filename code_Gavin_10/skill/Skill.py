import spacy
import re
import os
import sys
import openpyxl
from util.NLP import NLP

class Skill:
    def __init__(self, excelfilename, log_path, line):
        self.invocation = []
        self.skillName = ''
        self.supportRegion = True
        self.__basicComds = None#document-retrieved commands
        self.__sysComds = None#system-level commands
        self.__description_sents = []
        self.__parseExcel(excelfilename, line)
        self.__skillActions = []#skill functionality
        self.__userActions = []
        self.__otherActions = []
        skill_log_path = os.path.join(log_path, re.sub(r'(\W+)', '_', self.skillName))
        if self.skillName != '' and self.skillName != '<end_of_excel>': #and not os.path.exists(skill_log_path):
            spacyRets = []
            for sent in self.__description_sents:
                spacyRets.append(NLP.imergeNones(sent))
            self.__parse(spacyRets)
            self.__getInfoInQuotes()
    
    def __findSubjectType(self, subjects, subjectType):#0:skill 1:user 2:other
        skillSim = 0
        userSim = 0
        nlp = spacy.load("en_core_web_sm")
        if type(subjects) == spacy.tokens.span.Span:
            subject = nlp(subjects.root.text)
        else:
            subject = nlp(subjects.text)
        if subject[0].lemma_ == "which" or subject[0].lemma_ == "who" or subject[0].lemma_ == "it":
            return subjectType
        for i, skilln in enumerate(nlp(self.skillName)):
            if subject[0].similarity(skilln) > skillSim:
                skillSim = subject[0].similarity(skilln)
        skill = nlp("skill")
        if subject[0].similarity(skill[0]) > skillSim:
            skillSim = subject[0].similarity(skill[0])
        alexa = nlp("alexa")
        if subject[0].similarity(alexa[0]) > skillSim:
            skillSim = subject[0].similarity(alexa[0])
        we = nlp("we")
        if subject[0].similarity(we[0]) > skillSim:
            skillSim = subject[0].similarity(we[0])
        
        user = nlp("user")
        if subject[0].similarity(user[0]) > userSim:
            userSim = subject[0].similarity(user[0])
        you = nlp("you")
        if subject[0].similarity(you[0]) > userSim:
            userSim = subject[0].similarity(you[0])
        
        if userSim <= 0.8 and skillSim <= 0.8:
            return 2
        elif userSim > skillSim:
            return 1
        else:
            return 0

    def __parseExcel(self, excelfilename, line):
        excel = openpyxl.load_workbook(excelfilename)
        sheet = excel.worksheets[0]
        if line >= sheet.max_row:
            self.skillName = '<end_of_excel>'
            return
        skillAttri = list(sheet.rows)[line]
        if 'my Flash Briefing' in str(skillAttri[7].value):
            return
        if 'en-US' in dict(eval(skillAttri[10].value)).keys():
            self.supportRegion = True
        else:
            return
        self.skillName = skillAttri[1].value
        self.__description_sents = NLP.splitSentence(skillAttri[15].value)
        try:
            invocation_name = dict(eval(skillAttri[12].value)).get('en-US')
            self.invocation = ["Alexa, open " + invocation_name]
        except:
            self.invocation = dict(eval(skillAttri[7].value)).get('en-US')
            for i,invo in enumerate(self.invocation):
                self.invocation[i] = invo.strip("”")
        self.permission_list = []
        permissions_list = [] #eval(skillAttri[11].value)
        if isinstance(permissions_list, list):
            for per_dict in permissions_list:
                self.permission_list.append(per_dict.get('name'))

    def __parse(self, spacyRets):
        subjectType = 2
        for i, clause in enumerate(spacyRets):
            state = 0
            action = [] #record the actions
            for j, word in enumerate(clause):
                if NLP.getTokenDep(word) == 'nsubj' or NLP.getTokenDep(word) == 'nsubjpass':
                    if NLP.getTokenDep(word) == 'nsubjpass':
                        subjectType = 0
                        action.append(word)
                    else:
                        subjectType = self.__findSubjectType(word, subjectType)
                    j = j + 1
                    state = 1
                    break
                elif NLP.getTokenDep(word) == 'expl':
                    subjectType = 0 #subject: this skill
                    j = j + 1
                    state = 1
                    break
            if state == 0: #state: no subject
                subjectType = 1 #subject: you
                state = 1
                j = 0
            while j < len(clause):
                if state == 1:#state: find subject, to find verb/aux
                    if NLP.getTokenPos(clause[j]) == 'VERB':
                        if NLP.getTokenDep(clause[j]) != 'amod' and clause[j].lemma_ != 'can' and clause[j].lemma_ != 'need' and clause[j].lemma_ != 'will':
                            action.append(clause[j])
                            state = 2
                    elif NLP.getTokenPos(clause[j]) == 'AUX':
                        action.append(clause[j])
                        if NLP.getTokenDep(clause[j]) != 'auxpass':
                            state = 3
                    elif NLP.getTokenDep(clause[j]) == 'nsubj' or NLP.getTokenDep(clause[j]) == 'nsubjpass':#another subject
                        if len(action) != 0:
                            self.__addAction(action, subjectType)
                            action = []
                        if NLP.getTokenDep(clause[j]) == 'nsubjpass':
                            subjectType = 0
                            action.append(clause[j])
                        else:
                            subjectType = self.__findSubjectType(clause[j], subjectType)
                elif state == 2: #state: find verb, to find prep/noun
                    if (NLP.getTokenPos(clause[j]) == 'VERB' and NLP.getTokenDep(clause[j]) != 'amod') or NLP.getTokenPos(clause[j]) == 'AUX':
                        if j > 0 and NLP.getTokenPos(clause[j - 1]) == 'PART':
                            state = 1
                            continue
                        else:
                            if len(action) != 0:
                                self.__addAction(action, subjectType)
                                action = []
                            state = 1
                            continue
                    elif NLP.getTokenDep(clause[j]) == 'nsubj' or NLP.getTokenDep(clause[j]) == 'nsubjpass':#another subject
                        if len(action) != 0:
                            self.__addAction(action, subjectType)
                            action = []
                        if NLP.getTokenDep(clause[j]) == 'nsubjpass':
                            subjectType = 0
                            action.append(clause[j])
                        else:
                            subjectType = self.__findSubjectType(clause[j], subjectType)
                        state = 1
                    elif NLP.getTokenPos(clause[j]) == 'NOUN' or NLP.getTokenPos(clause[j]) == 'PROPN':
                        action.append(clause[j])
                    elif NLP.getTokenDep(clause[j]) == 'prep':
                        action.append(clause[j])
                    elif NLP.getTokenPos(clause[j]) == 'PART':
                        action.append(clause[j])
                elif state == 3:#find aux, to find prep/noun/adj
                    if (NLP.getTokenPos(clause[j]) == 'VERB' and NLP.getTokenDep(clause[j]) != 'amod') or NLP.getTokenPos(clause[j]) == 'AUX':
                        if j > 0 and (NLP.getTokenPos(clause[j - 1]) == 'PART' or NLP.getTokenPos(clause[j - 1]) == 'AUX'):
                            state = 1
                            continue
                        else:
                            if len(action) != 0:
                                self.__addAction(action, subjectType)
                                action = []
                            state = 1
                            continue
                    elif NLP.getTokenDep(clause[j]) == 'nsubj' or NLP.getTokenDep(clause[j]) == 'nsubjpass':#another subject
                        if len(action) != 0:
                            self.__addAction(action, subjectType)
                            action = []
                        if NLP.getTokenDep(clause[j]) == 'nsubjpass':
                            subjectType = 0
                            action.append(clause[j])
                        else:
                            subjectType = self.__findSubjectType(clause[j], subjectType)
                        state = 1
                    elif NLP.getTokenPos(clause[j]) == 'NOUN' or NLP.getTokenPos(clause[j]) == 'PROPN':
                        action.append(clause[j])
                    elif NLP.getTokenDep(clause[j]) == 'prep':
                        action.append(clause[j])
                    elif NLP.getTokenPos(clause[j]) == 'PART':
                        action.append(clause[j])
                    elif NLP.getTokenPos(clause[j]) == 'ADJ':
                        action.append(clause[j])
                j = j + 1
            if len(action) != 0:
                self.__addAction(action, subjectType)

    def __addAction(self, action, subjectType):
        if len(action) == 1 and (action[0].lemma_ == "can" or action[0].lemma_ == "will"):
            return
        if subjectType == 0:
            IsAdd = True
            for i, skillAction in enumerate(self.__skillActions):
                if len(skillAction) == len(action):
                    for j in range(len(action)):
                        if action[j].lemma_ != skillAction[j].lemma_:
                            break
                    if j == len(action) - 1 and action[j].lemma_ == skillAction[j].lemma_:
                        IsAdd = False
                        break
            if IsAdd == True:
                self.__skillActions.append(action)
        elif subjectType == 1:
            IsAdd = True
            for i, userAction in enumerate(self.__userActions):
                if len(userAction) == len(action):
                    for j in range(len(action)):
                        if action[j].lemma_ != userAction[j].lemma_:
                            break
                    if j == len(action) - 1 and action[j].lemma_ == userAction[j].lemma_:
                        IsAdd = False
                        break
            if IsAdd == True:
                self.__userActions.append(action)
        elif subjectType == 2:
            IsAdd = True
            for i, otherAction in enumerate(self.__otherActions):
                if len(otherAction) == len(action):
                    for j in range(len(action)):
                        if action[j].lemma_ != otherAction[j].lemma_:
                            break
                    if j == len(action) - 1 and action[j].lemma_ == otherAction[j].lemma_:
                        IsAdd = False
                        break
            if IsAdd == True:
                self.__otherActions.append(action)
        else:
            print("no subject?")
            sys.exit()

    def __getInfoInQuotes(self):
        self.__infoInQuotes = []
        inInfo = False
        impInfo = ''
        for sent in self.__description_sents:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(sent)
            for word in doc:
                if "\"" in word.text:
                    if inInfo == False:
                        inInfo = True
                    else:
                        inInfo = False
                        if 'Alexa' not in impInfo and 'alexa' not in impInfo:
                            self.__infoInQuotes.append(impInfo)
                        impInfo = ''
                else:
                    if inInfo == True:
                        if impInfo == '':
                            impInfo = re.sub(r"[^\sa-zA-Z0-9_\.,'?!]", '', word.text)
                        else:
                            impInfo = impInfo + ' ' + re.sub(r"[^\sa-zA-Z0-9_\.,'?!]", '', word.text)
        return self.__infoInQuotes

    def getBascComds(self):
        if self.__basicComds == None:
            self.__basicComds = []
            self.__basicComds.extend(self.__infoInQuotes)
            for i in range(len(self.__userActions)):
                if len(self.__userActions[i]) > 0 and self.__userActions[i][0].lemma_ == "be" or len(self.__userActions[i]) == 0:
                    continue
                bascComdContent = ""
                for j in range(len(self.__userActions[i])):
                    if bascComdContent == "":
                        bascComdContent = re.sub(r"[^\sa-zA-Z0-9_\.,'?!]", '', self.__userActions[i][j].text)
                    else:
                        bascComdContent = bascComdContent + " " + re.sub(r"[^\sa-zA-Z0-9_\.,'?!]", '', self.__userActions[i][j].text)
                if bascComdContent != "":
                    self.__basicComds.append(bascComdContent)
        print("basic command is ", self.__basicComds)
        return self.__basicComds
              
    def getSysComds(self):
        if self.__sysComds == None:
            self.__sysComds = []
            sysword = ['help', 'pause', 'resume', 'stop', 'what\'s the time']
            self.__sysComds.extend(sysword)
        return self.__sysComds
