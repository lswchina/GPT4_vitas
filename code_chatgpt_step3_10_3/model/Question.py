from model.Input import Input
class Question():
    def __init__(self, ques):
        self.__ques = ques
        self.__quesType = -1
        self.__reward = 0
        self.__Inpt_list = []
        self.__gpt_times = 0
        self.__state = None

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
    
    def get_inputSet(self):
        inputSet = set()
        for Inpt in self.__Inpt_list:
            inputSet.add(Inpt.get_input())
        return inputSet

    def getState(self):
        return self.__state

    def addSysInputs(self, sysAns):
        for ans in sysAns:
            new_input = Input(0, ans, 0.1)
            if new_input not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)
        
    def addBascInputs(self, bascAnsToIW):
        for ans in bascAnsToIW.keys():
            new_input = Input(3, ans, bascAnsToIW[ans])
            if ans not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)

    def addHelpInputs(self, helpAns):
        for ans in helpAns:
            new_input = Input(1, ans, 0.9)
            if new_input not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)

    def addContextInputs(self, contextAns):
        self.__Inpt_list = [I for I in self.__Inpt_list if not I.isContextRelatedInput()]
        for ans in contextAns:
            if not isinstance(ans, str):
                continue
            ans0 = ans.lower()
            new_input = Input(2, ans0, 1.0)
            if new_input not in self.__Inpt_list:
                self.__Inpt_list.append(new_input)

    def addNewState(self, Inpt, u):
        for Inpt_ in self.__Inpt_list:
            if Inpt_ == Inpt:
                Inpt_.addNewState(u)

    def setType(self, type):
        self.__quesType = type

    def setState(self, state):
        self.__state = state

    def addReward(self, u):
        self.__reward = self.__reward + u

    def addTimes(self, Inpt):
        for i, Input_ in enumerate(self.__Inpt_list):
            if Input_.get_input() == Inpt.get_input():
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

    def select_Inpt(self):
        highest_weight = 0
        selectInpt = None
        for Inpt in self.__Inpt_list:
            weight = Inpt.get_weight()
            if weight > highest_weight:
                highest_weight = weight
                selectInpt = Inpt
        return selectInpt