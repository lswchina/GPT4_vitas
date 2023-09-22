import os
import openai
import random

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

class askChatGPT:
    def __init__(self, skillName, log_dir, log_dir_gpt, __useAPI):
        self.skillName = skillName
        if log_dir != "":
            self.__Step1_Recorder_Path = os.path.join(log_dir, "step1_findState.txt")
            self.__Step2_Recorder_Path = os.path.join(log_dir, "step2_genInputs.txt")
        else:
            self.__Step1_Recorder_Path = ''
            self.__Step2_Recorder_Path = ''
        self.__answerDict1 = {}
        self.__answerDict2 = {}
        if log_dir_gpt != "":
            Step1_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step1_findState.txt")
            Step2_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step2_genInputs.txt")
            self.__answerDict1 = self.__getAnswerDict(1, Step1_Recorder_Path_gpt)
            self.__answerDict2 = self.__getAnswerDict(2, Step2_Recorder_Path_gpt)
        self.__useAPI = __useAPI
        self.__promptGlobal1 = ""
        self.__promptGlobal2 = ""

    def __getAnswerDict(self, type, log_path):
        answerDict = {}
        if type == 1:
            line = 16
        elif type == 2:
            line = 28
        if not os.path.exists(log_path):
            return answerDict
        gptResponse = False
        input_ = ""
        output_ = ""
        with open(log_path, "r", encoding="utf-8") as f:
            for num, l in enumerate(f):
                if num < line - 1:
                    continue
                if l.startswith("Input: "):
                    input_ = l.strip("\n")[7:]
                elif l.startswith("GPT4:") and input_ != "":
                    gptResponse = True
                elif gptResponse == True:
                    output_ = l.strip("\n")
                    answerDict[input_] = [output_]
                    input_ = ""
                    gptResponse = False
        return answerDict

    def step1_chat(self, skill_output, state_list):
        input_ = 'sentence: "' + skill_output + '", state list: ' + str(state_list)
        state = self.__answerDict1.get(input_, None)
        if state != None:
            state = state.strip('"')
            if state not in state_list and state != skill_output:
                return skill_output
            return state

        openai.api_key = os.getenv("OPENAI_API_KEY")
        messageBody = [
            {"role": "system", "content": "Help the user find a semantically identical state in the FSM."}
        ]
        hasGlobal1 = True
        if self.__promptGlobal1 == "":
            hasGlobal1 = False
            self.getPromptGlobal1()
        promptBody = 'Input: ' + input_ + '\n'
        promptBody = promptBody + "Output:"
        if hasGlobal1 == False:
            self.__record_result(self.__Step1_Recorder_Path, "User:\n" + self.__promptGlobal1 + promptBody + "\n")
        else:
            self.__record_result(self.__Step1_Recorder_Path, "User:\n" + promptBody + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": self.__promptGlobal1 + promptBody})
            state = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 200
                    )
                    state = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            if hasGlobal1 == False:
                print("Step1_User:\n" + self.__promptGlobal1 + promptBody + "\n")
            else:
                print("Step1_User:\n" + promptBody + "\n")
            state = input("Step1_GPT4:\n")
        state = state.strip('"')
        self.__record_result(self.__Step1_Recorder_Path, "GPT4:\n" + state + "\n")
        messageBody.append({"role": "assistant", "content": state})
        if state not in state_list and state != skill_output:
            state = self.step1_prompt2(state, skill_output, state_list, 'not_exist', messageBody)
        return state

    def getPromptGlobal1(self):
        if self.__promptGlobal1 != "":
            return self.__promptGlobal1
        step1_Example = {'sentence: "What are you interested in.", state list: []': '"What are you interested in."',
                 'sentence: "Ok, which other animal sound do you want to listen to.", state list: ["What are you interested in."]': '"Ok, which other animal sound do you want to listen to."',
                 'sentence: "Alright, now ask me for another animal.", state list: ["What are you interested in.", "Come on, ask for another animal."]': '"Come on, ask for another animal."',
                 'sentence: "What animal sound do you like to hear.", state list: ["What are you interested in.", "Ok, which other animal sound do you want to listen to."]': '"Ok, which other animal sound do you want to listen to."',
                 }
        self.__promptGlobal1 = "We use a finite state machine to respresent an Alexa Skill's behavior. " 
        self.__promptGlobal1 = self.__promptGlobal1 + "The skill's output sentences are mapped to states in the FSM. "
        self.__promptGlobal1 = self.__promptGlobal1 + "Semantically identical sentences are mapped to the same state. "
        self.__promptGlobal1 = self.__promptGlobal1 + "Given a sentence and the FSM's state list, please try to find a semantically identical state in the state list. "
        self.__promptGlobal1 = self.__promptGlobal1 + "If the semantically identical state is found, output the state. "
        self.__promptGlobal1 = self.__promptGlobal1 + "Otherwise, output the sentence itself.\n"
        self.__promptGlobal1 = self.__promptGlobal1 + "For example:\n"
        for skill_output in step1_Example.keys():
            self.__promptGlobal1 = self.__promptGlobal1 + "Input: " + skill_output + "\n"
            self.__promptGlobal1 = self.__promptGlobal1 + "Output: " + step1_Example[skill_output] + "\n\n"
        return self.__promptGlobal1

    def step1_prompt2(self, state, skill_output, state_list, errorMessage, messageBody):
        if errorMessage == 'not_exist':
            promptBody2 = "The \"" + state + "\" is not in the state list " + str(state_list) + ". "
            promptBody2 = promptBody2 + "Find a semantically identical state from the state list " + str(state_list) + " for the response \"" + skill_output + "\"."
        elif errorMessage == 'wrong':
            promptBody2 = "The state \"" + state + "\" and sentence " + skill_output + " are not semantically identical."
        else:
            promptBody2 = "The state \"" + errorMessage + "\" and sentence " + skill_output + " are semantically idential."
        self.__record_result(self.__Step1_Recorder_Path, "User:\n" + promptBody2 + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": promptBody2})
            state2 = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 250
                    )
                    state2 = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            print("Step1_User_2:\n" + promptBody2)
            state2 = input("Step1_GPT4_2:\n")
        self.__record_result(self.__Step1_Recorder_Path, "GPT4:\n" + state2 + "\n")
        if state2 not in state_list:
            if errorMessage == 'not_exist' or errorMessage == 'wrong':
                return skill_output
            else:
                return errorMessage
        return state2

    def step2_chat(self, Ques):
        skill_output = Ques.get_ques()
        input_ = 'skill: "' + skill_output + '"'
        gpt_response = self.__answerDict2.get(input_, None)
        if gpt_response != None:
            index1 = gpt_response.find("[")
            index2 = gpt_response.rfind("]")
            if index1 != -1 and index2 != -1:
                gpt_response = gpt_response[index1: index2 + 1]
                response_list = list(eval(gpt_response))
                if len(response_list) == 1 and response_list[0] == "":
                    response_list = []
            else:
                response_list = []
            if len(response_list) > 3 and (Ques.get_quesType() == 3 or Ques.get_quesType() == -1):
                response_list = self.__remove_low_certain(response_list)
            return response_list

        openai.api_key = os.getenv("OPENAI_API_KEY")
        messageBody = [
            {"role": "system", "content": "Find all the responses to the skill's sentence."}
        ]
        hasGlobal2 = True
        if self.__promptGlobal2 == "":
            hasGlobal2 = False
            self.__getPromptGlobal2()
        promptBody = 'Input: ' + input_ + '\n'
        promptBody = promptBody + "Output:"
        if hasGlobal2 == False:
            self.__record_result(self.__Step2_Recorder_Path, "User:\n" + self.__promptGlobal2 + promptBody + "\n")
        else:
            self.__record_result(self.__Step2_Recorder_Path, "User:\n" + promptBody + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": self.__promptGlobal2 + promptBody})
            gpt_response = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 300
                    )
                    gpt_response = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            if hasGlobal2 == False:
                print("Step2_User:\n" + self.__promptGlobal2 + promptBody + "\n")
            else:
                print("Step2_User:\n" + promptBody + "\n")
            gpt_response = input("Step2_GPT4:\n")
        self.__record_result(self.__Step2_Recorder_Path, "GPT4:\n" + gpt_response + "\n")
        messageBody.append({"role": "assistant", "content": gpt_response})
        self.step2_lastPrompt = messageBody
        index1 = gpt_response.find("[")
        index2 = gpt_response.rfind("]")
        if index1 != -1 and index2 != -1:
            gpt_response = gpt_response[index1: index2 + 1]
            response_list = list(eval(gpt_response))
            if len(response_list) == 1 and response_list[0] == "":
                response_list = []
        else:
            response_list = []
        if len(response_list) == 0:
            response_list = self.step2_prompt2('', Ques, [], -1, "", [])
        if len(response_list) > 3 and (Ques.get_quesType() == 3 or Ques.get_quesType() == -1):
            response_list = self.__remove_low_certain(response_list)
        return response_list
            
    def step2_prompt2(self, inpt, Ques, context_related_inputs, type, state, nouns):
        skill_output = Ques.get_ques()
        if inpt == '':
            messageBody = self.step2_lastPrompt
            promptBody2 = "The output should be a non-empty python list of the possible non-empty responses to the sentence \"" + skill_output + "\"."
        else:
            messageBody = [
                {"role": "system", "content": "Find all the responses to the skill's sentence."}
            ]
            if self.__promptGlobal2 == "":
                self.__getPromptGlobal2()
            # Help the user give a valid response to the voice assistant.
            skill_output = Ques.get_ques()
            promptBody = 'Input: skill: "' + skill_output + '"\n'
            promptBody = promptBody + "Output:"
            messageBody.append({"role": "user", "content": self.__promptGlobal2 + promptBody})
            messageBody.append({"role": "assistant", "content": str(context_related_inputs)})
            promptBody2 = '"' + inpt + '" is not a valid response for the sentence "' + skill_output + '". '
            promptBody2 = promptBody2 + "The output should be a python list of "
            if type == 1:
                if len(nouns) == 0:
                    promptBody2 = promptBody2 + "the phrases after 'say' / 'ask'."
                else:
                    promptBody2 = promptBody2 + "nouns related to " + nouns[0] + "."
            elif type == 2:
                promptBody2 = promptBody2 + "the conjunctions linked by 'and', 'or', ','."
            elif type == 3:
                promptBody2 = promptBody2 + "nouns related to " + ', '.join(nouns) + "."
            elif type == 0:
                promptBody2 = promptBody2 + "'yes', 'no'."
            elif type == -1:
                promptBody2 = promptBody2 + "responses to " + state + "."
        self.__record_result(self.__Step2_Recorder_Path, "User:\n" + promptBody2 + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": promptBody2})
            responses2 = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 350
                    )
                    responses2 = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            print("Step2_User_2:\n" + promptBody2 + "\n")
            responses2 = input("Step2_GPT4_2:\n")
        self.__record_result(self.__Step2_Recorder_Path, "GPT4:\n" + responses2 + "\n")
        index1 = responses2.find("[")
        index2 = responses2.find("]")
        if index1 != -1 and index2 != -1 and index2 > index1 + 1:
            responses2 = responses2[index1: index2 + 1]
            responses2_list = list(eval(responses2))
            if len(responses2_list) > 3 and (Ques.get_quesType() == 3 or Ques.get_quesType() == -1):
                responses2_list = self.__remove_low_certain(responses2_list)
            return responses2_list
        else:
            return []

    def __getPromptGlobal2(self):
        step2_Example = {"Say today's deals to get started": '["today\'s deals"]',
                        "You can choose a part type like ssd, hdd, cpu, or pick one from the list in the skill's description.": '["ssd", "hdd", "cpu"]',
                        "Do you want to see hdd deals?": '["yes", "no"]',
                        "Say next to proceed to the next step, or specify a step by saying step followed by a step number between 1 and 9.": '["next", "step 1", "step 2", "step 3", "step 4", "step 5", "step 6", "step 7", "step 8", "step 9"]',
                        "Which do you prefer, coffee or tea?": '["coffee", "tea"]',
                        "Would you like to start and register your account?": '["yes", "no"]',
                        "Please tell me the date you are traveling.": '["today", "tomorrow", "2023.12.31", "National Day"]',
                        "What animal sound do you like to hear?": '["rabbit", "rat", "cat", "dog", "monkey", "tiger", "lion"]'
                        }
        self.__promptGlobal2 = "Given an Alexa skill called " + self.skillName + "."
        self.__promptGlobal2 = self.__promptGlobal2 + "For a sentence of this skill and its context, find all the responses to the sentence in a python list."
        self.__promptGlobal2 = self.__promptGlobal2 + "The responses should be precious and simple.\n"
        self.__promptGlobal2 = self.__promptGlobal2 + "For example:\n"
        for skill_output in step2_Example.keys():
            self.__promptGlobal2 = self.__promptGlobal2 + 'Input: skill: "' + skill_output + '"\n'
            self.__promptGlobal2 = self.__promptGlobal2 + "Output: " + step2_Example[skill_output] + "\n\n"
        return self.__promptGlobal2

    def __remove_low_certain(self, response_list):
        response_list = response_list[0:3]
        return response_list
            
    def __record_result(self, path, content):
        if path == '':
            return
        with open(path, "a", encoding="utf-8") as file:
            file.write(content)
            file.write("\n")

    # def update_duration_list(self):
    #     if self.last_invoke_time == 0:
    #         self.last_invoke_time = time.time()
    #     else:
    #         invoke_time = time.time()
    #         duration = invoke_time - self.last_invoke_time
    #         self.duration[self.index_in_duration] = duration
    #         total = self.duration[0] + self.duration[1] + self.duration[2]
    #         if total <= 60:
    #             time.sleep(61 - total)
    #             invoke_time = time.time()
    #             duration = invoke_time - self.last_invoke_time
    #             self.duration[self.index_in_duration] = duration
    #         self.last_invoke_time = invoke_time
    #         self.index_in_duration = (self.index_in_duration + 1) % 3
