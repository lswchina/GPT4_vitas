import os
import random
from copy import deepcopy
import util.Azure as Azure

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

class askLlama:
    def __init__(self, skillName, useAPI, registry_ml_client):
        self.skillName = skillName
        self.__client = registry_ml_client
        self.__useAPI = useAPI

    def test(self, prompt):
        if self.__useAPI == True:
            ans = Azure.test(prompt, self.__client).split("\n")[0]
        else:
            print("VPA app:\n" + prompt + "\n")
            ans = input("Llama-2-13b:\n")
        return ans

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
