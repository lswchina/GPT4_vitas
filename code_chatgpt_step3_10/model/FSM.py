from copy import deepcopy
from util.NLP import NLP
import util.Constant as Constant
class FSM():
    def __init__(self, gpt):
        self.__states = {}
        self.__states_temp = {}
        self.__find_last_state = {}
        self.__find_last_Inpt = {}
        self.__find_lastQ = {}
        self.__Ques_to_state = {}
        self.__QuesSet = set()
        self.__transitions = {}
        self.__gpt = gpt

    def addInputs(self, Ques, sysAns, helpAns, contextAns):
        Ques.addSysInputs(sysAns)
        Ques.addContextInputs(contextAns)
        Ques.addHelpInputs(helpAns)
        if Ques not in self.__QuesSet:
            self.__QuesSet.add(Ques)

    def addTimes(self, Ques, Inpt):
        Ques.addTimes(Inpt)

    def addQuesToQuesSet(self, Ques):
        self.__QuesSet.add(Ques)

    def getInputsOfQues(self, Ques):
        return Ques.getInputs()

    def getStateInfoOfQues(self, Ques, state):
        if self.__states_temp.get(Ques, None) != None:
            states_ = deepcopy(self.__states)
            states_[state] = self.__states_temp[Ques]
            return states_
        else:
            return self.__states

    def getContextRelatedInputsOfQues(self, Ques):
        context_related_Inpts = []
        for Inpt in self.getInputsOfQues(Ques):
            if Inpt.isContextRelatedInput():
                context_related_Inpts.append(Inpt)
        return context_related_Inpts
    
    def getTransitionOfQues(self, current_state, Ques):
        return self.__transitions.get(current_state, {}).get(Ques, {})
        
    def has_ques(self, ques):
        for Ques in self.__QuesSet:
            if Ques.get_ques() == ques:
                return Ques
        return None

    def __isErrorState(self, questions):
        error_list = ["sorry", "error", "try again", "say again"]
        for ques in questions:
            ques_lower = ques.lower()
            for word in error_list:
                if word in ques_lower:
                    return True
        return False

    def updateFSM(self, lastQ, lastI, Ques, questions=[]):
        #step 1
        if lastQ == None:
            last_state = "<START>"
            self.__states[last_state] = [False, 0]
            self.__Ques_to_state[lastQ] = "<START>"
        else:
            last_state = self.__Ques_to_state[lastQ]

        if self.__Ques_to_state.get(Ques, None) == None:
            #ques is not met before
            if Ques.get_ques() == "<END>":
                state = "<END>"
                lastQ.addReward(-1)
            else:
                if len(self.__states) != 0:
                    state_list = [*self.__states]
                else:
                    state_list = []
                if last_state not in state_list:
                    state_list.append(last_state)
                state = self.__gpt.step1_chat(Ques.get_ques(), state_list) # = ques
                if lastQ != None:
                    lastQ.addReward(1)
        else:
            #ques is processed before
            state = self.__Ques_to_state[Ques]
            if lastQ != None:
                lastQ.addReward(-1)
        
        if self.__states_temp.get(lastQ, None) != None:
            last_state_previous = last_state
            # check 1: the transition (last_state, q, lasta, state2) is in the FSM, q != lastq, state2 != self.state, which means last_state is wrong
            for Q, value in self.__transitions.get(last_state, {}).items():
                if Q != lastQ and value.get(lastI, None) != None and value[lastI] != state:
                    last_state = self.__updateStateByCallGPT(last_state, lastQ, [*self.__states])
                    break
            # check 2: ques2 and lastq shares the last_state, but ques2 and lastq has different candidate input set
            if last_state == last_state_previous:
                candidate_answer0 = set(lastQ.getInputs())
                Ques2 = None
                for Q in self.__transitions.get(last_state, {}).keys():
                    if Q != lastQ:
                        candidate_answer1 = set(Q.getInputs())
                        if len(candidate_answer0) != len(candidate_answer1) or candidate_answer0 & candidate_answer1 != candidate_answer0:
                            Ques2 = Q
                            break
                if Ques2 != None:
                    last_state = self.__updateStateByCallGPT(last_state, lastQ, [*self.__states])
            
            # the information of last_state is not added to the FSM, add it now
            if lastQ != None:
                self.__states[last_state] = self.__states_temp[lastQ] #add to self.states now
                self.__states_temp.pop(lastQ)
                self.__Ques_to_state[lastQ] = last_state
            
            last_last_state = self.__find_last_state[lastQ]
            last_last_Inpt = self.__find_last_Inpt[lastQ]
            last_last_Ques = self.__find_lastQ[lastQ]
            if self.__transitions.get(last_last_state, None) == None:
                self.__transitions[last_last_state] = {}
            if self.__transitions[last_last_state].get(last_last_Ques, None) == None:
                self.__transitions[last_last_state][last_last_Ques] = {}
            self.__transitions[last_last_state][last_last_Ques][last_last_Inpt] = last_state #add to self.transitions now
            self.__find_last_state.pop(lastQ)
            self.__find_last_Inpt.pop(lastQ)
            self.__find_lastQ.pop(lastQ)

        if self.__Ques_to_state.get(Ques, None) == None:
            if Ques.get_ques() == "<END>":
                if lastI.get_input() in Constant.StopSign:
                    isErrorState = False
                else:
                    isErrorState = True
                depth = self.__states[last_state][1] + 1
                self.__states[state] = [isErrorState, depth]
                self.__Ques_to_state[Ques] = state
                if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and (isErrorState or Ques == lastQ):
                    self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
                if self.__transitions.get(last_state, None) == None:
                    self.__transitions[last_state] = {}
                if lastQ != None:
                    if self.__transitions[last_state].get(lastQ, None) == None:
                        self.__transitions[last_state][lastQ] = {}
                    self.__transitions[last_state][lastQ][lastI] = state
            else:
                isErrorState = self.__isErrorState(questions)
                depth = self.__states[last_state][1] + 1
                self.__states_temp[Ques] = [isErrorState, depth]
                self.__Ques_to_state[Ques] = state
                if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and (isErrorState or Ques == lastQ):
                    self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
                self.__find_last_state[Ques] = last_state
                self.__find_last_Inpt[Ques] = lastI
                self.__find_lastQ[Ques] = lastQ #not add to self.transitions here, later...
        else:
            depth = self.__states[state][1]
            if self.__states[last_state][1] + 1 < depth:
                self.__states[state][1] = self.__states[last_state][1] + 1
            if lastQ != None and lastI in self.getContextRelatedInputsOfQues(lastQ) and Ques == lastQ:
                self.__updateContextRelatedInputByCallGPT(lastQ, lastI, last_state)
            if self.__transitions.get(last_state, None) == None:
                self.__transitions[last_state] = {}
            if lastQ != None:
                if self.__transitions[last_state].get(lastQ, None) == None:
                    self.__transitions[last_state][lastQ] = {}
                self.__transitions[last_state][lastQ][lastI] = state
        return state

    def __updateStateByCallGPT(self, state, lastQ, state_list):
        skill_output = lastQ.get_ques()
        messageBody = [
            {"role": "system", "content": "Help the user find the correct state in the FSM."}
        ]
        promptBody = 'Input: response: "' + skill_output + '\", state_list: ' + str(state_list) + "\n"
        promptBody = promptBody + "Output:\n"
        messageBody.append({"role": "user", "content": self.__gpt.getPromptGlobal1() + promptBody})
        messageBody.append({"role": "assistant", "content": state})
        state = self.__gpt.step1_prompt2(state, skill_output, state_list, 'wrong', messageBody)
        return state

    def __updateContextRelatedInputByCallGPT(self, lastQ, lastI, last_state):
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
            context_related_inputs = []
            for Inpt in lastQ.getInputs():
                if Inpt.isContextRelatedInput():
                    context_related_inputs.append(Inpt.get_input())
            context_related_inputs_after = self.__gpt.step2_prompt2(lastI.get_input(), lastQ, context_related_inputs, type_, last_state, nouns)
        lastQ.addContextInputs(context_related_inputs_after)
        lastQ.addGPTTimes()