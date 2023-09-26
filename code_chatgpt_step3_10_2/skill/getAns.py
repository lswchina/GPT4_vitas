import np
import time
from random import sample
from util.NLP import NLP
from model.Input import Input
from model.Question import Question

class getAns:
    def __init__(self, skillName, basicComds, sysComds, log_dir, gpt, fsm):
        self.timeStart = time.time()
        self.skillName = skillName
        self.sysAns = sysComds
        if len(basicComds) > 3:
            for ans in sample(basicComds, 3):
                ans0 = ans.lower()
                if ans0 not in self.sysAns:
                    self.sysAns.append(ans0)
        self.helpAns = []
        self.gpt = gpt
        self.FSM = fsm

    def getResponses(self, Ques, lastQ, lastI):
        spacyRet = NLP.imergeNones(Ques.get_ques())
        ques_type = Ques.get_quesType()
        response_list = []
        if ques_type != -1:
            response_list.extend(NLP.getYNAns(spacyRet))
            response_list.extend(NLP.getIQAns(spacyRet))
            response_list.extend(NLP.getSQAns(spacyRet))
            if ques_type == 3:
                whAns, response_list = NLP.getWhQAns(Ques, response_list)
                response_list.extend(whAns)
        return response_list

    def getResponse(self, questions, lastQ, lastI, next_input = ''):
        #find the question to answer and store in ques
        Ques = self.selectQuestion(questions)
        print("The question is ", Ques)
        #step 1
        current_state = self.FSM.updateFSM(lastQ, lastI, Ques, questions)
        Ques_of_current_state = Ques
        if current_state != Ques_of_current_state.get_ques():
            Ques_of_current_state = self.FSM.has_ques(current_state)
        candidate_Inpt_list = self.FSM.getInputsOfQues(Ques_of_current_state)
        if len(candidate_Inpt_list) == 0:
            if current_state != ".":
                context_ans = self.getResponses(Ques_of_current_state, lastQ, lastI)
            else:
                context_ans = []
            self.FSM.addInputs(Ques_of_current_state, self.sysAns, self.helpAns, context_ans)
            candidate_Inpt_list = self.FSM.getInputsOfQues(Ques_of_current_state)
        if next_input == '':
            state_info = self.FSM.getStateInfoOfState(current_state)
            #Done: maybe transitions does not need Ques?
            #Done: candidate_Inpt_list belongs to current_state, not Ques.get_ques()
            ans = self.gpt.step3_chat(state_info, current_state, self.FSM.getTransitionOfState(current_state), candidate_Inpt_list)
        else:
            ans = next_input
        Inpt = Ques_of_current_state.has_input(ans)
        self.FSM.addTimes(Ques_of_current_state, Inpt)
        print(candidate_Inpt_list)
        return [Inpt, Ques]

    def selectQuestion(self, questions):
        ques = ''
        Ques_list = []
        Ques_from_Ques_list = None
        reward1 = 0
        for question in reversed(questions):
            Ques = self.FSM.has_ques(question)
            if Ques != None:
                question_type = Ques.get_quesType()
            else:
                Ques = Question(question)
                question_type = -1
                whAns = NLP.isWhQ(question)
                if whAns == None:
                    spacyRet = NLP.imergeNones(question)
                    if NLP.isYNAns(spacyRet):
                        question_type = 0
                    elif NLP.isIQAns(spacyRet):
                        question_type = 1
                    elif NLP.isSQAns(spacyRet):
                        question_type = 2
                else:
                    question_type = 3
                    Ques.setWhAns(whAns)
                if question_type != -1:
                    Ques.setType(question_type)
                self.FSM.addQuesToQuesSet(Ques)
            if question_type != -1:
                if question_type >= 0 and question_type <= 3:
                    Ques_list.append(Ques)
                    r = Ques.get_reward()
                    if r > reward1 or (r == reward1 and Ques_from_Ques_list == None):
                        reward1 = r
                        Ques_from_Ques_list = Ques
        if len(Ques_list) != 0:
            print("The question list is ", str(Ques_list))
            Ques = self.__pull(Ques_list, Ques_from_Ques_list)
            return Ques
        else:
            if len(questions) > 0:
                ques = questions[-1]
            else:
                ques = '.'
            Ques = self.FSM.has_ques(ques)
            if Ques == None:
                Ques = Question(ques)
                self.FSM.addQuesToQuesSet(Ques)
        return Ques

    def __pull(self, Ques_list, maxQues):
        epsilon = 0.1
        exploration_flag = True
        if maxQues != None and np.random.uniform() > epsilon:
            exploration_flag = False
        if exploration_flag:
            print("Choose randomly")
            i = int(np.random.randint(len(Ques_list)))
            return Ques_list[i]
        else:
            print("Choose the max")
            return maxQues

    def addHelpAns(self, questions):
        for question in questions:
            spacyRet = NLP.imergeNones(question)
            Ques = self.FSM.has_ques(question)
            if Ques == None:
                if NLP.isIQAns(spacyRet):
                    Ques = Question(question)
                    Ques.setType(1)
                if NLP.isSQAns(spacyRet):
                    Ques = Question(question)
                    Ques.setType(2)
                if Ques != None:
                    self.FSM.addQuesToQuesSet(Ques)
                    response_list = []
                    response_list.extend(NLP.getIQAns(spacyRet))
                    response_list.extend(NLP.getSQAns(spacyRet))
                    self.FSM.addInputs(Ques, self.sysAns, [], response_list)
                    for ans in response_list:
                        if not isinstance(ans, str):
                            continue
                        ans0 = ans.lower()
                        if ans0 not in self.helpAns:
                            self.helpAns.append(ans0)
        if len(self.helpAns) == 0:
            ques = questions[-1]
            Ques = self.FSM.has_ques(ques)
            if Ques == None:
                Ques = Question(ques)
                response_list = []
                whAns = NLP.isWhQ(ques)
                if whAns != None:
                    Ques.setWhAns(whAns)
                    Ques.setType(3)
                    response_list.extend(NLP.getWhQAns(Ques, response_list))
                else:
                    spacyRet = NLP.imergeNones(ques)
                    if NLP.isYNAns(spacyRet):
                        Ques.setType(0)
                        response_list.extend(NLP.getYNAns(spacyRet))
                self.FSM.addQuesToQuesSet(Ques)
                self.FSM.addInputs(Ques, self.sysAns, [], response_list)
        return

    def getHelpResponse(self, questions, lastQ, Inpt):
        self.addHelpAns(questions)
        return self.getResponse(questions, lastQ, Inpt)
    
if __name__ == '__main__':
    NLP.getNoneOfIQ("Please say a valid stock ticker symbol or name .")
