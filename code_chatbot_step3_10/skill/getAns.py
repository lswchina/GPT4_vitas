import time
from random import sample
from util.NLP import NLP

class getAns:
    def __init__(self, gpt):
        self.gpt = gpt

    def getResponse(self, questions):
        #find the question to answer and store in ques
        print("The question is ", questions)
        ans = self.gpt.test(questions)
        ans = ans.replace("\n", "")
        return ans
    
if __name__ == '__main__':
    NLP.getNoneOfIQ("Please say a valid stock ticker symbol or name .")
