import emoji
import util.Huggingface as hug

class askLlama:
    def __init__(self, skillName, useAPI, model, tokenizer):
        self.skillName = skillName
        self.__model = model
        self.__tokenizer = tokenizer
        self.__useAPI = useAPI

    def test(self, prompt):
        if self.__useAPI == True:
            # ans = hug.input_and_output(prompt, self.__model, self.__tokenizer).split("\n")[0]
            results = hug.send_and_receive(prompt, self.__model).split("\n")[0]
            ans = ""
            for i in range(len(results)):
                ans = results[i]
                if ans != "":
                    break
            if len(ans) > 10:
                pre = ans[:10]
                beginInd = ans.find(pre, 1)
                ans = ans[:beginInd]
            ans = emoji.demojize(ans)
        else:
            print("VPA app:\n" + prompt + "\n")
            ans = input("Llama-2-70b-hf:\n")
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
