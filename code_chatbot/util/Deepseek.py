from openai import OpenAI

class askDeepseek:
    def __init__(self, skillName, useAPI):
        self.skillName = skillName
        self.__useAPI = useAPI

    def test(self, prompt):
        messageBody = [
            {"role": "system", "content": "You are a chatbot."}
        ]
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": prompt})
            response = ''
            client = OpenAI(api_key = self.apk_key, base_url = "https://api.deepseek.com")
            for i in range(3):
                # self.update_duration_list()
                try:
                    responseBody = client.chat.completions.create(
                        model = "deepseek-chat",
                        messages = messageBody,
                        temperature = 0,
                        max_tokens = 450
                    )
                    response = str(responseBody.choices[0].message.content)
                    if response != "" and response != "\n":
                        break
                except Exception as e:
                    print(e)
        else:
            print("VPA app:\n" + prompt + "\n")
            response = input("Deepseek:\n")
        return response