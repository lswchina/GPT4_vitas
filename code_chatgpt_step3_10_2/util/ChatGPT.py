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
            self.__Step3_Recorder_Path = os.path.join(log_dir, "step3_selectInput.txt")
        else:
            self.__Step1_Recorder_Path = ''
            self.__Step3_Recorder_Path = ''
        self.__answerDict1 = {}
        self.__answerDict3 = {}
        if log_dir_gpt != "":
            Step1_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step1_findState.txt")
            Step3_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step3_selectInput.txt")
            self.__answerDict1 = self.__getAnswerDict(1, Step1_Recorder_Path_gpt)
            self.__answerDict3 = self.__getAnswerDict(3, Step3_Recorder_Path_gpt)
            print(self.__answerDict1)
            print(self.__answerDict3)
        self.__useAPI = __useAPI
        self.__promptGlobal1 = ""
        self.__promptGlobal3 = ""

    def __getAnswerDict(self, type, log_path):
        answerDict = {}
        if type == 1:
            line = 16
        elif type == 3:
            line = 17
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
                    if type == 3:
                        if l.startswith("Output: "):
                            output_ = output_ + l.strip("\n")
                            answerDict[input_] = output_
                            input_ = ""
                            output_ = ""
                            gptResponse = False
                        else:
                            output_ = l
                    if type == 1:
                        output_ = l.strip("\n")
                        answerDict[input_] = output_
                        input_ = ""
                        gptResponse = False 
        return answerDict

    def step1_chat(self, skill_output, state_list):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        messageBody = [
            {"role": "system", "content": "Help the user find a semantically identical state in the FSM."}
        ]
        hasGlobal1 = True
        if self.__promptGlobal1 == "":
            hasGlobal1 = False
            self.getPromptGlobal1()
        input_ = 'sentence: "' + skill_output + '", state list: ' + str(state_list)
        promptBody = 'Input: ' + input_ + '\n'
        promptBody = promptBody + "Output:"
        if hasGlobal1 == False:
            self.__record_result(self.__Step1_Recorder_Path, "User:\n" + self.__promptGlobal1 + promptBody + "\n")
        else:
            self.__record_result(self.__Step1_Recorder_Path, "User:\n" + promptBody + "\n")
        state = self.__answerDict1.get(input_, None)
        if state == None:
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
            self.__record_result(self.__Step1_Recorder_Path, "GPT4:\n" + state + "\n")
        else:
            print("Input: ", input_, "; Output: ", state)
            self.__record_result(self.__Step1_Recorder_Path, "GPT4_before:\n" + state + "\n")
        messageBody.append({"role": "assistant", "content": state})
        state = state.strip('"')
        if state not in state_list and state != skill_output:
            state = self.step1_prompt2(state, skill_output, state_list, 'not_exist', messageBody)
        elif state == "<START>":
            state = self.step1_prompt2(state, skill_output, state_list, 'wrong', messageBody)
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

    def step3_chat(self, states, state, transitions, candidate_Inpt_list):
        candidate_input_list = [i.get_input() for i in candidate_Inpt_list]
        openai.api_key = os.getenv("OPENAI_API_KEY")
        messageBody = [
            {"role": "system", "content": "Choose one input from the input event list to cover more future states."}
        ]
        hasGlobal3 = True
        if self.__promptGlobal3 == "":
            hasGlobal3 = False
            self.__getPromptGlobal3()
        input_, candidate_input_set_to_weight = self.__gen_prompt_for_step3(states, state, transitions, candidate_Inpt_list, candidate_input_list)
        promptBody = "Input: " + input_ + "\n"
        promptBody = promptBody + "Thought:"
        if hasGlobal3 == False:
            self.__record_result(self.__Step3_Recorder_Path, "User:\n" + self.__promptGlobal3 + promptBody + "\n")
        else:
            self.__record_result(self.__Step3_Recorder_Path, "User:\n" + promptBody + "\n")
        response = self.__answerDict3.get(input_, None)
        if response == None:
            if self.__useAPI == True:
                messageBody.append({"role": "user", "content": self.__promptGlobal3 + promptBody})
                response = ''
                for i in range(3):
                    # self.update_duration_list()
                    try:
                        responseBody = openai.ChatCompletion.create(
                            model = "gpt-4",
                            messages = messageBody,
                            temperature = 0,
                            max_tokens = 400
                        )
                        response = str(responseBody['choices'][0]['message']['content'])
                        break
                    except Exception as e:
                        print(e)
            else:
                if hasGlobal3 == False:
                    print("Step3_User:\n" + self.__promptGlobal3 + promptBody + "\n")
                else:
                    print("Step3_User:\n" + promptBody + "\n")
                response = input("Step3_GPT4:\n")
            self.__record_result(self.__Step3_Recorder_Path, "GPT4:\n" + response + "\n")
        else:
            print("Input: ", input_, "; Output: ", response)
            self.__record_result(self.__Step3_Recorder_Path, "GPT4_before:\n" + response + "\n")
        messageBody.append({"role": "assistant", "content": response})
        select_input = ''
        inQuoteWords = []
        response = response.split("Output: ")[1]
        response_split = response.split("\"")
        if len(response_split) == 2:
            inQuoteWords.append(response)
        else:
            for i, word in enumerate(response_split):
                if i % 2 == 1:
                    inQuoteWords.append(word)
                else:
                    temp_split = word.split("'")
                    if len(temp_split) >= 3:
                        for j, word_ in enumerate(temp_split):
                            if j % 2 == 1:
                                inQuoteWords.append(word_)
                    elif len(response_split) == 1:
                        inQuoteWords.append(word)
        for input_ in candidate_input_list:
            for word in inQuoteWords:
                if input_ == word.lower():
                    select_input = input_
                    break
            if select_input != '':
                break
        if select_input == '':
            select_input = self.step3_prompt2(response, [], candidate_input_list, messageBody)
        else:
            better_inputs = self.__find_better_inputs(candidate_input_set_to_weight, candidate_Inpt_list, select_input)
            if len(better_inputs) != 0:
                select_input = self.step3_prompt2(response, better_inputs, [], messageBody)
        return select_input

    def __find_better_inputs(self, candidate_input_set_to_weight, candidate_Inpt_list, select_input):
        better_inputs = []
        weight_of_select_input = candidate_input_set_to_weight[select_input]
        time_of_select_input = 0
        type_id_of_select_input = -1
        for Inpt in candidate_Inpt_list:
            if Inpt.get_input() == select_input:
                time_of_select_input = Inpt.get_times()
                type_of_selec_input = Inpt.get_type()
                if type_of_selec_input == 0:
                    type_id_of_select_input = 0
                else:
                    type_id_of_select_input = 2
                break
        better_Inpt = []
        contain_low_times_crt = False
        for Inpt in candidate_Inpt_list:
            times = Inpt.get_times()
            type_ = Inpt.get_type()
            if type_ == 0:
                type_id = 0
            else:
                type_id = 2
            if type_id == 2 and times < 2:
                contain_low_times_crt = True
            input_weight = candidate_input_set_to_weight[Inpt.get_input()]
            if input_weight > weight_of_select_input:
                better_Inpt.append(Inpt)
            elif input_weight == weight_of_select_input:
                if type_id > type_id_of_select_input:
                    if times < 2:
                        better_Inpt.append(Inpt)
        if len(better_Inpt) == 0 and type_id_of_select_input == 2 and contain_low_times_crt == False:
            better_inputs = ['help', 'pause', 'resume', 'stop', 'what\'s the time']
        elif len(better_Inpt) != 0:
            better_inputs_temp = []
            for Inpt in better_Inpt:
                times = Inpt.get_times()
                type_ = Inpt.get_type()
                input_ = Inpt.get_input()
                if type_ != 0 and times < 2:
                    better_inputs.append(input_)
                elif type_ == 0:
                    better_inputs_temp.append(input_)
            if len(better_inputs) == 0 and len(better_inputs_temp) != 0:
                better_inputs = better_inputs_temp
        return better_inputs

    def __getPromptGlobal3(self):
        step3_Example = {'''<current state>="Say today's deals to get started.",FSM={Σ={"stop":0,"help":0,"today's deals":0},δ=()}''': ['''inputs after step1:["stop","help","today's deals"]. inputs after step 2:["today's deals"]. step 3:choose "today\'s deals"''', '"today\'s deals"'],
                        '''<current state>="You can choose a part type like ssd, hdd, cpu, or pick one from the list in the skill's description.",FSM={Σ={"stop":0,"help":0,"ssd":1,"hdd":1,"cpu":0,"today's deals":1},δ=([<current state>,"today's deals",<current state>])}.''': ['''inputs after step1:["stop","help","ssd","hdd","cpu"]. inputs after step2:["ssd","hdd","cpu"] left. step3:choose "cpu".''', '"cpu"']
                        }
        
        self.__promptGlobal3 = "We use a finite state machine to represent an Alexa Skill's behavior. "
        self.__promptGlobal3 = self.__promptGlobal3 + "Our FSM has Q representing the state set, Σ representing the input event dictionary(with key of input event and value of its invocation times) and δ represent the transition set. "
        self.__promptGlobal3 = self.__promptGlobal3 + "The transition from <current state> to <next state> by <input1> is represented as [<current state>, <input1>, <next state>]. "
        self.__promptGlobal3 = self.__promptGlobal3 + "If <next state> = <current state>, <input1> leads to a repeated state. "
        self.__promptGlobal3 = self.__promptGlobal3 + "If <next state> contains error information, <input1> leads to an error state.\n"
        
        # self.__promptGlobal3 = self.__promptGlobal3 + "We map the skill's outputs to states and users' inputs to input events. "
        # self.__promptGlobal3 = self.__promptGlobal3 + "The process of skills taking an input and giving new outputs are mapped to transitions in the FSM. "
        self.__promptGlobal3 = self.__promptGlobal3 + "Given the FSM and the current state, please choose an input event that is most likely to help us discover new states.\n"

        self.__promptGlobal3 = self.__promptGlobal3 + "The procedure contains 3 steps.\n"
        self.__promptGlobal3 = self.__promptGlobal3 + "Step1: discard input events that lead to repeated/error state\n"
        self.__promptGlobal3 = self.__promptGlobal3 + "Step2: from those input events that have never been invoked, retain one that is most likely to trigger new state and discard the others\n"
        self.__promptGlobal3 = self.__promptGlobal3 + "Step3: from the rest input events, pick one as the actual input considering invocation times and relevance to the current state\n"
        
        self.__promptGlobal3 = self.__promptGlobal3 + "For example:\n"
        for state_info, v in step3_Example.items():
            self.__promptGlobal3 = self.__promptGlobal3 + "Input: " + state_info + "\n"
            self.__promptGlobal3 = self.__promptGlobal3 + "Thought: " + v[0] + "\n"
            self.__promptGlobal3 = self.__promptGlobal3 + "Output: " + v[1] + "\n\n"
        return self.__promptGlobal3

    def step3_prompt2(self, inpt, better_inputs, candidate_input_list, messageBody):
        if len(better_inputs) != 0:
            promptBody2 = "Choosing an input event from " + str(better_inputs) + " might be better than the input event \"" + inpt + "\"."
            promptBody2 = promptBody2 + "Please choose another input event from the input event list " + str(better_inputs) + "."
        elif len(candidate_input_list) != 0:
            promptBody2 = '"' + inpt + "\" is not in the given input event list: " + str(candidate_input_list) + ". "
            promptBody2 = promptBody2 + "Please choose another input event from the input event list " + str(candidate_input_list) + "."
        self.__record_result(self.__Step3_Recorder_Path, "User:\n" + promptBody2 + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": promptBody2})
            response2 = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 450
                    )
                    response2 = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            print("Step3_User_2:\n" + promptBody2 + "\n")
            response2 = input("Step3_GPT4_2:\n")
        self.__record_result(self.__Step3_Recorder_Path, "GPT4:\n" + response2 + "\n")
        inQuoteWords = []
        response_split = response2.split("Output: ")
        if len(response_split) == 1:
            response_split = response2.split("\"")
        if len(response_split) == 1 or len(response_split) == 2:
            inQuoteWords.append(response2)
        else:
            for i, word in enumerate(response_split):
                if i % 2 == 1:
                    inQuoteWords.append(word)
                else:
                    temp_split = word.split("'")
                    if len(temp_split) >= 3:
                        for j, word_ in enumerate(temp_split):
                            if j % 2 == 1:
                                inQuoteWords.append(word_)
        if len(candidate_input_list) == 0:
            candidate_input_list = better_inputs
        for input_ in candidate_input_list:
            for word in inQuoteWords:
                if input_ == word.lower():
                    return input_
        for input_ in candidate_input_list:
            if input_ in response2:
                return input_
        ind = random.randint(0, len(candidate_input_list) - 1)
        return candidate_input_list[ind]

    def __gen_prompt_for_step3(self, states, state, transitions, candidate_Inpt_list, candidate_input_list):
        candidate_input_set_to_weight = {}
        for i in candidate_input_list:
            candidate_input_set_to_weight[i] = 4
        prompt = '<current state>="' + state + '",'
        prompt = prompt + "FSM={Σ={"
        for ind, Inpt in enumerate(candidate_Inpt_list):
            if ind != 0:
                prompt = prompt + ","
            prompt = prompt + '"' + Inpt.get_input() + '":' + str(Inpt.get_times())
        prompt = prompt + "},δ=("
        ind2 = 0
        for input in transitions.keys():
            if ind2 != 0:
                prompt = prompt + ','
            prompt = prompt + '[<current_state>,"' + input + '",'
            next_state = transitions[input]
            if next_state == state:
                prompt = prompt + "<current_state>]"
            else:
                prompt = prompt + '"' + next_state + '"]'
            ind2 = ind2 + 1
        prompt = prompt + ")}."
        state_info = states[state]
        for input in transitions.keys():
            if input not in candidate_input_list:
                print(input, "not in", candidate_input_list, "of state", state)
                continue
            next_state = transitions[input]
            if next_state == state:
                candidate_input_set_to_weight[input] -= 2
            next_state_info = states[next_state]
            if next_state_info[0] == True:
                candidate_input_set_to_weight[input] -= 2
            elif next_state_info[1] < state_info[1]:
                candidate_input_set_to_weight[input] -= 1
        return prompt, candidate_input_set_to_weight

    def __gen_prompt_for_step3_nl(self, states, state, transitions, candidate_input_set, candidate_input_list):
        candidate_input_set_to_weight = {}
        for i in candidate_input_list:
            candidate_input_set_to_weight[i] = 4
        prompt = "The skill's current state is \"" + state + "\". "
        if not transitions:
            prompt = prompt + "In the previous conversation, no input event is choosed at this state. "
        else:
            state_info = states[state]
            for input in transitions.keys():
                if input not in candidate_input_list:
                    print(input, "not in", candidate_input_list, "of state", state)
                    continue
                next_state = transitions[input]
                adj = "a"
                if next_state == state:
                    adj = adj + " repeated"
                    candidate_input_set_to_weight[input] -= 2
                next_state_info = states[next_state]
                if next_state_info[0] == True: 
                    if adj == "a":
                        adj = "an error"
                        candidate_input_set_to_weight[input] -= 3
                    else:
                        adj = adj + " error"
                        candidate_input_set_to_weight[input] -= 2
                elif next_state_info[1] > state_info[1]:
                    adj = adj + " future"
                elif next_state_info[1] < state_info[1]:
                    adj = adj + " previous"
                    candidate_input_set_to_weight[input] -= 1
                else:
                    adj = adj + " same-level"
                prompt = prompt + "If you choose the input event \"" + input + "\" at this state, the skill will transfer to " + adj + " state. "
            prompt = prompt + "In the previous conversation"
            for input_, info in candidate_input_set.items():
                time_ = info[1]
                if time_ != 0:
                    prompt = prompt + ', "' + input_ + '" is selected '
                    if time_ == 1:
                        prompt = prompt + "once"
                    elif time_ == 2:
                        prompt = prompt + "twice"
                    else:
                        prompt = prompt + "more than twice"
        system_level_list = []
        help_embedded_list = []
        context_related_list = []
        for input_, info in candidate_input_set.items():
            type_ = info[0]
            if type_ == "system-level":
                system_level_list.append(input_)
            elif type_ == "help-embedded":
                help_embedded_list.append(input_)
            else:
                context_related_list.append(input_)
        prompt = prompt + ". Please choose an input event from the system-level input event list " + str(system_level_list) + ", the help-embedded input event list " + str(help_embedded_list) + " or the context-related input event list " + context_related_list + " to cover more future states."
        return prompt, candidate_input_set_to_weight
            
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
