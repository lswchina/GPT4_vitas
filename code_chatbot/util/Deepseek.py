from openai import OpenAI
import os
from tenacity import retry, stop_after_attempt, wait_exponential

class askDeepseek:
    def __init__(self, skillName, useAPI):
        self.skillName = skillName
        self.__useAPI = useAPI
        self.apk_key = os.getenv("DEEPSEEK_API_KEY")

    def test(self, prompt):
        messageBody = [
            {"role": "system", "content": "You are a chatbot."}
        ]
        if self.__useAPI == True:
            messageBody.append({"role": "user", "content": prompt})
            response = self.__query(messageBody, 0, 450)
        else:
            print("VPA app:\n" + prompt + "\n")
            response = input("Deepseek:\n")
        return response
    
    def retry_if_result_empty(result):
        return result == "" or result == None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry = retry_if_result_empty
    )
    def __query(self, messageBody, tempr, maxt):
        client = OpenAI(api_key = self.apk_key, base_url = "https://api.deepseek.com")
        try:
            response = client.chat.completions.create(
                model = "deepseek-chat",
                messages = messageBody,
                temperature = tempr,
                max_tokens = maxt,
                timeout = 60
            )
            result = response.choices[0].message.content.strip()
            return result
        except Exception as e:
            print(f"Deepseek query error: {str(e)}")
        return ''