from model.Input import Input
class Question():
    def __init__(self, ques):
        self.__ques = ques
        self.__quesType = -1
        self.__reward = 0
        self.__Inpt_list = []
        self.__gpt_times = 0

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__ques == other.__ques
        else:
            return False

    def __hash__(self):
        return hash(self.__ques)

    def __str__(self):
        return self.__ques
    
    def __repr__(self):
        return self.__ques

    def get_ques(self):
        return self.__ques

    def get_quesType(self):
        return self.__quesType
    
    def get_reward(self):
        return self.__reward

    def getInputs(self):
        return self.__Inpt_list

    def addSysInputs(self, sysAns):
        for ans in sysAns:
            new_input = Input(0, ans)
            self.__Inpt_list.append(new_input)

    def addHelpInputs(self, helpAns):
        for ans in helpAns:
            new_input = Input(1, ans)
            if new_input not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)

    def addContextInputs(self, contextAns):
        self.__Inpt_list = [I for I in self.__Inpt_list if not I.isContextRelatedInput()]
        for ans in contextAns:
            if not isinstance(ans, str):
                continue
            ans0 = ans.lower()
            new_input = Input(2, ans0)
            if new_input not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)

    def setType(self, type):
        self.__quesType = type

    def addReward(self, u):
        self.__reward = self.__reward + u

    def addTimes(self, Inpt):
        for i, Input_ in enumerate(self.__Inpt_list):
            if Input_ == Inpt:
                self.__Inpt_list[i].addTimes()
                break
    
    def addGPTTimes(self):
        self.__gpt_times += 1

    def isOutOfGPTTimes(self):
        return self.__gpt_times >= 3

    def has_input(self, inpt):
        for Inpt in self.__Inpt_list:
            if Inpt.get_input() == inpt:
                return Inpt
        return None