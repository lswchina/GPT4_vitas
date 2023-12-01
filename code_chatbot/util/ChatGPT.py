import os
import configparser
import openai

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

class askChatGPT:
    def __init__(self, skillName, useAPI, config_path):
        self.skillName = skillName
        self.__useAPI = useAPI
        cf = configparser.ConfigParser()
        cf.read(config_path)
        openai.api_type = "azure"
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_base = cf.get('Azure', 'apibase')
        openai.api_version = cf.get('Azure', 'apiversion')

    def test(self, prompt):
        messageBody = [
            {"role": "system", "content": "You are a chatbot."}
        ]
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": prompt})
            response = ''
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = openai.ChatCompletion.create(
                        model = "gpt-4",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 450
                    )
                    response = str(responseBody['choices'][0]['message']['content'])
                    break
                except Exception as e:
                    print(e)
        else:
            print("VPA app:\n" + prompt + "\n")
            response = input("GPT4:\n")
        return response


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
