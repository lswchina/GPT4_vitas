import spacy
import re
import openpyxl
from util.NLP import NLP

class Skill:
    def __init__(self, excelfilename, line):
        self.invocation = []
        self.skillName = ''
        self.supportRegion = True
        self.__basicComds = None#document-retrieved commands
        self.__sysComds = None#system-level commands
        self.__description_sents = []
        self.__parseExcel(excelfilename, line)
        if self.skillName != '' and self.skillName != '<end_of_excel>':
            self.__getInfoInQuotes()
    
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
        permissions_list = eval(skillAttri[11].value)
        if isinstance(permissions_list, list):
            for per_dict in permissions_list:
                self.permission_list.append(per_dict.get('name'))

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
        return self.__basicComds
              
    def getSysComds(self):
        if self.__sysComds == None:
            self.__sysComds = []
            sysword = ['help', 'stop']
            self.__sysComds.extend(sysword)
        return self.__sysComds
