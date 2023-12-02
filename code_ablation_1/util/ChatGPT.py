import os
import configparser
import openai
import random

class askChatGPT:
    def __init__(self, skillName, log_dir, log_dir_gpt, useAPI, config_path):
        self.skillName = skillName
        if log_dir != "":
            self.__Step2_Recorder_Path = os.path.join(log_dir, "step2_genInputs.txt")
            self.__Step3_Recorder_Path = os.path.join(log_dir, "step3_selectInput.txt")
        else:
            self.__Step2_Recorder_Path = ''
            self.__Step3_Recorder_Path = ''
        self.__answerDict2 = {}
        self.__answerDict3 = {}
        if log_dir_gpt != "":
            Step2_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step2_genInputs.txt")
            Step3_Recorder_Path_gpt = os.path.join(log_dir_gpt, "step3_selectInput.txt")
            self.__answerDict2 = self.__getAnswerDict(2, Step2_Recorder_Path_gpt)
            self.__answerDict3 = self.__getAnswerDict(3, Step3_Recorder_Path_gpt)
            print(self.__answerDict2)
            print(self.__answerDict3)
        self.__useAPI = useAPI
        self.__promptGlobal2 = ""
        self.__promptGlobal3 = ""
        self.__messageBody2 = [
            {"role": "system", "content": "Find all the responses to the skill's sentence."}
        ]
        self.__messageBody3 = [
            {"role": "system", "content": "Choose one input from the input event list to cover more future states."}
        ]
        cf = configparser.ConfigParser()
        cf.read(config_path)
        openai.api_type = "azure"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_base = cf.get('Azure', 'apibase')
        openai.api_version = cf.get('Azure', 'apiversion')

    def __getAnswerDict(self, type, log_path):
        answerDict = {}
        if type == 2:
            line = 28
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
                    if type == 2:
                        output_ = l.strip("\n")
                        answerDict[input_] = output_
                        input_ = ""
                        gptResponse = False 
        return answerDict

    def step2_chat(self, Ques):
        hasGlobal2 = True
        if self.__promptGlobal2 == "":
            hasGlobal2 = False
            self.__getPromptGlobal2()
        skill_output = Ques.get_ques()
        input_ = 'skill: "' + skill_output + '"'
        promptBody = 'Input: ' + input_ + '\n'
        promptBody = promptBody + "Output:"
        if hasGlobal2 == False:
            self.__record_result(self.__Step2_Recorder_Path, "User:\n" + self.__promptGlobal2 + promptBody + "\n")
            self.__messageBody2.append({"role": "user", "content": self.__promptGlobal2 + promptBody})
        else:
            self.__record_result(self.__Step2_Recorder_Path, "User:\n" + promptBody + "\n")
            self.__messageBody2.append({"role": "user", "content": promptBody})
        gpt_response = self.__answerDict2.get(input_, None)
        if gpt_response == None:
            if self.__useAPI == True:
                gpt_response = ''
                for i in range(3):
                    # self.update_duration_list()
                    try:
                        responseBody = openai.ChatCompletion.create(
                            engine="Gavin_deployment",
                            messages = self.__messageBody2,
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
        else:
            print("Input: ", input_, "; Output: ", gpt_response)
            self.__record_result(self.__Step2_Recorder_Path, "GPT4_before:\n" + gpt_response + "\n")
        self.__messageBody2.append({"role": "assistant", "content": gpt_response})
        self.step2_lastPrompt = self.__messageBody2
        if len(self.__messageBody2) > 3:
            self.__messageBody2 = self.__messageBody2[:3]
        index1 = gpt_response.find("[")
        index2 = gpt_response.find("]", index1)
        if index1 != -1 and index2 != -1:
            gpt_response = gpt_response[index1: index2 + 1]
            try:
                response_list = list(eval(gpt_response))
            except:
                index2 = gpt_response.find("]", index2)
                if index2 != -1:
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
                        engine="Gavin_deployment",
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
        index2 = responses2.find("]", index1)
        if index1 != -1 and index2 != -1 and index2 > index1 + 1:
            responses2 = responses2[index1: index2 + 1]
            try:
                responses2_list = list(eval(responses2))
            except:
                index2 = responses2.find("]", index2)
                if index2 != -1:
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
        self.__promptGlobal2 = "Given a sentence and its context, find all the responses to the sentence in a python list."
        self.__promptGlobal2 = self.__promptGlobal2 + "The responses should be precious and simple.\n"
        self.__promptGlobal2 = self.__promptGlobal2 + "For example:\n"
        for skill_output in step2_Example.keys():
            self.__promptGlobal2 = self.__promptGlobal2 + 'Input: skill: "' + skill_output + '"\n'
            self.__promptGlobal2 = self.__promptGlobal2 + "Output: " + step2_Example[skill_output] + "\n\n"
        return self.__promptGlobal2

    def __remove_low_certain(self, response_list):
        response_list = response_list[0:3]
        return response_list

    def step3_chat(self, states, state, transitions, candidate_Inpt_list):
        candidate_input_list = [i.get_input() for i in candidate_Inpt_list]
        hasGlobal3 = True
        if self.__promptGlobal3 == "":
            hasGlobal3 = False
            self.__getPromptGlobal3()
        input_, candidate_input_set_to_weight = self.__gen_prompt_for_step3(states, state, transitions, candidate_Inpt_list, candidate_input_list)
        promptBody = "Input: " + input_ + "\n"
        promptBody = promptBody + "Thought:"
        if hasGlobal3 == False:
            self.__record_result(self.__Step3_Recorder_Path, "User:\n" + self.__promptGlobal3 + promptBody + "\n")
            self.__messageBody3.append({"role": "user", "content": self.__promptGlobal3 + promptBody})
        else:
            self.__record_result(self.__Step3_Recorder_Path, "User:\n" + promptBody + "\n")
            self.__messageBody3.append({"role": "user", "content": promptBody})
        response = self.__answerDict3.get(input_, None)
        if response == None:
            if self.__useAPI == True:
                response = ''
                for i in range(3):
                    # self.update_duration_list()
                    try:
                        responseBody = openai.ChatCompletion.create(
                            engine="Gavin_deployment",
                            messages = self.__messageBody3,
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
        self.__messageBody3.append({"role": "assistant", "content": response})
        select_input = ''
        inQuoteWords = []
        if "Output: " in response:
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
        else:
            response = ""
        if select_input == '':
            select_input = self.step3_prompt2(response, [], candidate_input_list, self.__messageBody3)
        else:
            better_inputs = self.__find_better_inputs(candidate_input_set_to_weight, candidate_Inpt_list, select_input)
            if len(better_inputs) != 0:
                select_input = self.step3_prompt2(response, better_inputs, [], self.__messageBody3)
        if len(self.__messageBody3) > 3:
            self.__messageBody3 = self.__messageBody3[:3]
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
                    type_id_of_select_input = 1
                else:
                    type_id_of_select_input = 2
                break
        better_inputs = []
        type_1_list = []
        type_2_list = []
        for Inpt in candidate_Inpt_list:
            type_ = Inpt.get_type()
            input_ = Inpt.get_input()
            if type_ == 0:
                type_1_list.append(Inpt)
            else:
                type_2_list.append(Inpt)
            if weight_of_select_input == 0 and candidate_input_set_to_weight[input_] == 4:
                better_inputs.append(input_)
        if len(better_inputs) > 0:
            return better_inputs
        if type_id_of_select_input == 2:
            for type_2_Inpt in type_2_list:
                type_2_input = type_2_Inpt.get_input()
                if type_2_Inpt.get_times() < time_of_select_input and candidate_input_set_to_weight[type_2_input] == 4:
                    better_inputs.append(type_2_input)
            if len(better_inputs) > 0:
                return better_inputs
            if time_of_select_input >= 3:
                for type_1_Inpt in type_1_list:
                    type_1_input = type_1_Inpt.get_input()
                    better_inputs.append(type_1_input)
        else:
            for type_2_Inpt in type_2_list:
                type_2_input = type_2_Inpt.get_input()
                if type_2_Inpt.get_times() < 3 and candidate_input_set_to_weight[type_2_input] == 4:
                    better_inputs.append(type_2_input)
            if len(better_inputs) > 0:
                return better_inputs
            for type_1_Inpt in type_1_list:
                type_1_input = type_1_Inpt.get_input()
                if type_1_Inpt.get_times() < time_of_select_input and candidate_input_set_to_weight[type_1_input] == 4:
                    better_inputs.append(type_1_input)
        return better_inputs

    def __getPromptGlobal3(self):
        step3_Example = {'''<current state>="Say today's deals to get started.",FSM={Σ={"stop":0,"help":0,"today's deals":0},δ=()}''': ['''inputs after step1:["stop","help","today's deals"]. inputs after step 2:["today's deals"]. step 3:choose "today\'s deals"''', '"today\'s deals"'],
                        '''<current state>="You can choose a part type like ssd, hdd, cpu, or pick one from the list in the skill's description.",FSM={Σ={"stop":0,"help":0,"ssd":1,"hdd":1,"cpu":0,"today's deals":1},δ=([<current state>,"today's deals",<current state>])}.''': ['''inputs after step1:["stop","help","ssd","hdd","cpu"]. inputs after step2:["ssd","hdd","cpu"] left. step3:choose "cpu".''', '"cpu"']
                        }
        
        self.__promptGlobal3 = "We use a finite state machine to represent an Alexa Skill's behavior. "
        self.__promptGlobal3 = self.__promptGlobal3 + "Our FSM has Q(state set), Σ(input event dictionary(key: input event, value: invocation times)) and δ(transition set). "
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
            if inpt != "":
                promptBody2 = '"' + inpt + "\" is not in the given input event list: " + str(candidate_input_list) + ". "
            else:
                promptBody2 = "No input is given. "
            promptBody2 = promptBody2 + "Please choose another input event from the input event list " + str(candidate_input_list) + "."
        self.__record_result(self.__Step3_Recorder_Path, "User:\n" + promptBody2 + "\n")
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": promptBody2})
            response2 = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        engine="Gavin_deployment",
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
                candidate_input_set_to_weight[input] = 0
            next_state_info = states[next_state]
            if next_state_info[0] == True:
                candidate_input_set_to_weight[input] = 0
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
