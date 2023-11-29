from copy import deepcopy
from util.NLP import NLP
import util.Constant as Constant
class FSM():
    def __init__(self, gpt):
        self.__stateToInfo = {}
        self.__stateToInfoTemp = {}
        self.__find_last_state = {}
        self.__find_last_Inpt = {}
        self.__QuesSet = set()
        self.__transitions = {}
        self.__gpt = gpt

    def addInputs(self, Ques, sysAns, helpAns, contextAns):
        Ques.addContextInputs(contextAns)
        Ques.addHelpInputs(helpAns)
        Ques.addSysInputs(sysAns)
        if Ques not in self.__QuesSet:
            self.__QuesSet.add(Ques)

    def addTimes(self, Ques, Inpt):
        Ques.addTimes(Inpt)

    def addQuesToQuesSet(self, Ques):
        self.__QuesSet.add(Ques)

    def getInputsOfQues(self, Ques):
        return Ques.getInputs()

    def getStateInfoOfState(self, state):
        if self.__stateToInfoTemp.get(state, None) != None:
            states_ = deepcopy(self.__stateToInfo)
            states_[state] = self.__stateToInfoTemp[state]
            return states_
        else:
            return self.__stateToInfo

    def getContextRelatedInputsOfQues(self, Ques):
        context_related_Inpts = []
        for Inpt in self.getInputsOfQues(Ques):
            if Inpt.isContextRelatedInput():
                context_related_Inpts.append(Inpt)
        return context_related_Inpts

    def getContextRelatedinputsOfQues(self, Ques):
        context_related_inputs = []
        for Inpt in self.getInputsOfQues(Ques):
            if Inpt.isContextRelatedInput():
                context_related_inputs.append(Inpt.get_input())
        return context_related_inputs
    
    def getTransitionOfState(self, current_state):
        return self.__transitions.get(current_state, {})
        
    def has_ques(self, ques):
        for Ques in self.__QuesSet:
            if Ques.get_ques() == ques:
                return Ques
        return None

    def __isErrorState(self, questions):
        if len(questions) == 0 or (len(questions) == 1 and questions[0] == ""):
            return True
        error_list = ["sorry", "error", "try again", "say again"]
        for ques in questions:
            ques_lower = ques.lower()
            for word in error_list:
                if word in ques_lower:
                    return True
        return False

    def updateFSM(self, lastQ, lastI, Ques, questions=[]):
        #get last_state
        if lastQ == None:
            last_state = "<START>"
            self.__stateToInfo[last_state] = [False, 0]
        else:
            last_state = lastQ.getState()

        #get state, update reward
        state = Ques.getState()
        if state == None:
            #ques is not met before
            if Ques.get_ques() == "<END>":
                state = "<END>"
                lastQ.addReward(-1)
            else:
                if len(self.__stateToInfo) != 0:
                    state_list = [*self.__stateToInfo]
                else:
                    state_list = []
                if last_state not in state_list:
                    state_list.append(last_state)
                state = Ques.get_ques()
                if lastQ != None:
                    lastQ.addReward(1)
        else:
            #ques is processed before
            if lastQ != None:
                lastQ.addReward(-1)
        
        #check rule1, add info of last_state to FSM
        if self.__stateToInfoTemp.get(last_state, None) != None:
            # the information of last_state is not added to the FSM, add it now
            self.__stateToInfo[last_state] = self.__stateToInfoTemp[last_state] #add to self.__stateToInfo now
            self.__stateToInfoTemp.pop(last_state)
            if lastQ != None:
                lastQ.setState(last_state)  #add state to lastQ now
            
            last_last_state = self.__find_last_state[lastQ]
            last_last_Inpt = self.__find_last_Inpt[lastQ]
            if self.__transitions.get(last_last_state, None) == None:
                self.__transitions[last_last_state] = {}
            self.__transitions[last_last_state][last_last_Inpt.get_input()] = last_state #add to self.transitions now
            self.__find_last_state.pop(lastQ)
            self.__find_last_Inpt.pop(lastQ)
        
        #check rule2
        self.__checkTheErrorStateToUpdateContextRelatedInput(lastQ, lastI, Ques, last_state, state, questions)

        return state

    def __checkTheErrorStateToUpdateContextRelatedInput(self, lastQ, lastI, Ques, last_state, state, questions):
        if Ques.getState() == None:
            if Ques.get_ques() == "<END>":
                if lastI.get_input() in Constant.StopSign:
                    isErrorState = False
                else:
                    isErrorState = True
                depth = self.__stateToInfo[last_state][1] + 1
                self.__stateToInfo[state] = [isErrorState, depth]
                Ques.setState(state)
                if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and (isErrorState or Ques == lastQ):
                    self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
                if self.__transitions.get(last_state, None) == None:
                    self.__transitions[last_state] = {}
                # if lastQ != None:
                #     if self.__transitions[last_state].get(lastQ, None) == None:
                #         self.__transitions[last_state][lastQ] = {}
                #     self.__transitions[last_state][lastQ][lastI.get_input()] = state
                self.__transitions[last_state][lastI.get_input()] = state
            else:
                isErrorState = self.__isErrorState(questions)
                depth = self.__stateToInfo[last_state][1] + 1
                self.__stateToInfoTemp[state] = [isErrorState, depth]
                Ques.setState(state)
                if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and (isErrorState or Ques == lastQ):
                    self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
                self.__find_last_state[Ques] = last_state
                self.__find_last_Inpt[Ques] = lastI
                # self.__find_lastQ[Ques] = lastQ #not add to self.transitions here, later...
        else:
            depth = self.__stateToInfo[state][1]
            if self.__stateToInfo[last_state][1] + 1 < depth:
                self.__stateToInfo[state][1] = self.__stateToInfo[last_state][1] + 1
            if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and Ques == lastQ:
                self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
            if self.__transitions.get(last_state, None) == None:
                self.__transitions[last_state] = {}
            # if lastQ != None:
            #     if self.__transitions[last_state].get(lastQ, None) == None:
            #         self.__transitions[last_state][lastQ] = {}
            #     self.__transitions[last_state][lastQ][lastI.get_input()] = state
            self.__transitions[last_state][lastI.get_input()] = state

    def __updateContextRelatedInputByCallGPT(self, lastQ, lastI, last_state):
        context_related_inputs = self.getContextRelatedinputsOfQues(lastQ)
        if lastQ.isOutOfGPTTimes() == True:
            context_related_inputs_after = []
        else:
            type_ = lastQ.get_quesType()
            last_ques = lastQ.get_ques()
            nouns = []
            if type_ == 3:
                type_ == -1
                beginWord = ''
                clauses = last_ques.split(",")
                for clause in clauses:
                    beginWord = clause.split(" ")[0]
                    if beginWord == "what" or beginWord == "What":
                        type_ = 3
                        nouns = NLP.getNoneOfWhatQ(last_ques)
                        break
            if type_ == 1:
                nouns = NLP.getNoneOfIQ(last_ques)
            context_related_inputs_after = self.__gpt.step2_prompt2(lastI.get_input(), lastQ, context_related_inputs, type_, last_state, nouns)
        context_related_inputs_delete = set(context_related_inputs).difference(set(context_related_inputs_after))
        transition_of_last_state = self.__transitions.get(last_state, None)
        if transition_of_last_state != None:
            for inpt_del in context_related_inputs_delete:
                transition_of_last_state.pop(inpt_del, None)
            self.__transitions[last_state] = transition_of_last_state
        lastQ.addContextInputs(context_related_inputs_after)
        lastQ.addGPTTimes()