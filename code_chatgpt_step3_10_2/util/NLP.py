import re
import html
import spacy

class NLP():
    KEY_LIST = ['number', 'year', 'month', 'day', 'date', 'score', 'animal', 'capital', 'language', 'food', 'stock', 'fruit', 'country', 'name', 'gender', 'job', 'color']
    KNOWLEDGE_LIST = [
        ['0', '1', '2', '3', '20', '50'],
        ['1990', '2000', '2010', '2020'],
        ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'September'],
        ['today', 'yesterday', 'twenty-nineth of March', 'May the first'],
        ['today', 'yesterday', 'twenty-nineth of March', 'May the first'],
        ['1.0', '5.0', '3.0', '10.0', '100.0'],
        ['rat', 'cow', 'tiger', 'rabbit', 'dragon', 'snake', 'horse', 'sheep', 'monkey', 'chicken', 'dog', 'pig', 'elephant', 'cat', 'lion'],
        ['Beijing', 'Tokyo', 'Washington DC', 'Seoul', 'Canberra', 'Berlin', 'Paris'],
        ['English', 'Chinese', 'Spanish', 'Japanese', 'German', 'Korean', 'French'],
        ['salad', 'roast chicken', 'fried potato', 'pizza', 'spaghetti'],
        ['Microsoft', 'Facebook', 'Wal-Mart', 'Ford', 'Mitsubishi', 'Sony', 'Tencent'],
        ['apple', 'pear', 'orange', 'banana', 'peach', 'pineapple', 'watermelon', 'cherry', 'durian'],
        ['China', 'Japan', 'America', 'Keorea', 'Australia', 'Germany', 'England', 'France'],
        ['Lisa', 'Lily', 'Bob', 'Harry'],
        ['female', 'male'],
        ['teacher', 'doctor'],
        ['red', 'orange', 'yellow', 'green', 'blue', 'violet', 'white', 'black']
    ]

    NUMBER_LIST = ['much', 'many']
    KNOW_LIST = ['1', '2', '3', '4', '5']

    def __init__(self):
        pass

    @staticmethod
    def splitSentence(Line):
        Line = NLP.toValidStr(Line)
        Lines = Line.split("<Short audio>.")
        sentences = []
        for line in Lines:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(line)
            tempsents = []
            for sent in doc.sents:
                tempsents.append(sent.text)
            tempsents.append("<Short audio>")
            sentences.extend(tempsents)
        if len(sentences) == 0:
            sentences.append(" ")
        else:
            sentences.pop()
        return sentences

    @staticmethod
    def getTokenPos(token):
        if type(token) == spacy.tokens.span.Span:
            return token.root.pos_
        return token.pos_
        
    @staticmethod
    def getTokenDep(token):
        if type(token) == spacy.tokens.span.Span:
            return token.root.dep_
        return token.dep_

    @staticmethod
    def getTokenHead(token):
        if type(token) == spacy.tokens.span.Span:
            return token.root.head
        return token.head

    @staticmethod
    def toValidStr(string):
        string = html.unescape(string)
        string = string.encode(encoding='utf-8', errors = 'ignore').decode(encoding='utf-8')
        string = string.replace("‘", '\'')
        string = string.replace("’", '\'')
        string = string.replace("”", '\"')
        string = string.replace("“", '\"')
        text = re.compile(u"[\s\w\.'!?,<>:]").findall(string)
        string = "".join(text)
        return string

    @staticmethod
    def imergeNones(question):
        spacyRet = []
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(question)
        for word in doc:
            spacyRet.append(word)
        for chunk in doc.noun_chunks:
            words = chunk.text.replace(" ", "")
            begin = 0
            isEqual = False
            words_left = -1
            words_right = -1
            for j in range(len(spacyRet)):
                length = len(spacyRet[j].text)
                if begin + length > len(words):
                    words_right = j
                    break
                elif spacyRet[j].text == words[begin: begin + length]:
                    if isEqual == False:
                        words_left = j
                        isEqual = True
                    begin = begin + length
                else:
                    isEqual = False
                    begin = 0
                    words_left = -1
                    words_right = -1
            if words_left >= 0:
                if words_right == -1:
                    words_right = len(spacyRet)
                del spacyRet[words_left: words_right]
                spacyRet.insert(words_left, chunk)
        return spacyRet
    
    @staticmethod
    def isSQAns(spacyRet):
        for word in reversed(spacyRet):
            if NLP.getTokenDep(word) == "conj" and NLP.getTokenPos(word) != 'VERB':
                return True
        return False

    @staticmethod
    def getSQAns(spacyRet):
        sQAns = []
        split_list = ['.', '?', '!', ',', 'and', 'or']
        Ans = set()
        for word in reversed(spacyRet):
            if NLP.getTokenDep(word) == "conj" and NLP.getTokenPos(word) != 'VERB':
                if NLP.getTokenPos(NLP.getTokenHead(word)) == NLP.getTokenPos(word):
                    current = word
                    while NLP.getTokenPos(NLP.getTokenHead(current)) == NLP.getTokenPos(current) and NLP.getTokenDep(NLP.getTokenHead(current)) == 'conj':
                        next_phrase = ''
                        for phrase in spacyRet:
                            if NLP.getTokenHead(current).text in phrase.text:
                                next_phrase = phrase.text
                            elif next_phrase != '':
                                if phrase.text in split_list:
                                    break
                                else:
                                    next_phrase = next_phrase + " " + phrase.text
                        if next_phrase in Ans:
                            break
                        Ans.add(next_phrase)
                        current = NLP.getTokenHead(current)
        for ans in Ans:
            answer = re.sub(r"[^\sa-zA-Z0-9_\.,?!]", '', ans)
            temp = re.sub(r"[^a-zA-Z]", '', answer)
            if temp != 'Alexa' and temp != 'alexa':
                sQAns.append(answer)
        return sQAns

    @staticmethod
    def isIQAns(spacyRet):
        instruction_list = ['say', 'ask', 'tell']
        for word in spacyRet:
            if word.lemma_ in instruction_list:
                return True
        return False

    @staticmethod
    def getIQAns(spacyRet):
        iQAns = []
        instruction_list = ['say', 'ask', 'tell']
        first_parse_result = []
        isInsQ = False
        intruction_words = []
        instr_w = ""
        for word in spacyRet:
            if isInsQ == False:
                if word.lemma_ in instruction_list:
                    isInsQ = True
                    intruction_words = [word]
                    instr_w = word.lemma_
            else:
                if word.lemma_ in instruction_list and (word.lemma_ != 'tell' or intruction_words[0].lemma_ == 'tell'):
                    if instr_w != "" and instr_w not in instruction_list:
                        instr_w = re.sub(r"[^\sa-zA-Z0-9_\.,?!]", '', instr_w)
                        temp = re.sub(r"[^a-zA-Z]", '', instr_w)
                        if temp.lower() != 'sayalexa' and temp.lower() != 'askalexa' and temp.lower() != 'tellalexa':
                            first_parse_result.append(intruction_words)
                    intruction_words = [word]
                    instr_w = word.lemma_
                else:
                    if NLP.getTokenPos(word) == "PUNCT" or word.lemma_ == "or" or word.lemma_ == "and":
                        if word.text != "." and word.text != "?" and word.text != "!":
                            if word.text != "'" and word.text != '"' and word.text != ":" and instr_w != "" and instr_w not in instruction_list:
                                instr_w = re.sub(r"[^\sa-zA-Z0-9_\.,?!]", '', instr_w)
                                temp = re.sub(r"[^a-zA-Z]", '', instr_w)
                                if temp.lower() != 'sayalexa' and temp.lower() != 'askalexa' and temp.lower() != 'tellalexa':
                                    first_parse_result.append(intruction_words)
                                intruction_words = [intruction_words[0]]
                                instr_w = intruction_words[0].lemma_
                        else:
                            isInsQ = False
                    else:
                        intruction_words.append(word)
                        instr_w = instr_w + " " + word.text
        if instr_w != "" and instr_w not in instruction_list:
            instr_w = re.sub(r"[^\sa-zA-Z0-9_\.,?!]", '', instr_w)
            temp = re.sub(r"[^a-zA-Z]", '', instr_w)
            if temp.lower() != 'sayalexa' and temp.lower() != 'askalexa' and temp.lower() != 'tellalexa':
                first_parse_result.append(intruction_words)
        for sentence in first_parse_result:
            if sentence[0].lemma_ == "ask":
                ans = NLP.getAskAns(sentence)
                if ans != "":
                    iQAns.append(ans)
            elif sentence[0].lemma_ == "say":
                ans = NLP.getSayAns(sentence)
                if ans != "":
                    iQAns.append(ans)
            else:
                iQAns.extend(NLP.getTellAns(sentence))
        return iQAns

    @staticmethod
    def getAskAns(ask_sentence):
        wh_list = ["what", "when", "where", "who", "whom", "whose", "why", "how"]
        prep_list = ["to", "for", "about", "like"]
        Ans = ""
        if ask_sentence[1].text.lower() == "that":
            if len(ask_sentence) <= 3:
                return Ans
            Ans = ask_sentence[2].text
            for i in range(3, len(ask_sentence)):
                Ans = Ans + " " + ask_sentence[i].text
        else:
            isInstr = False
            for i in range(1, len(ask_sentence)):
                if isInstr == False:
                    if ask_sentence[i].lemma_ in prep_list:
                        isInstr = True
                    if ask_sentence[i].text.lower() in wh_list:
                        isInstr = True
                        Ans = ask_sentence[i].text
                else:
                    if Ans == "":
                        Ans = ask_sentence[i].text
                    else:
                        Ans = Ans + " " + ask_sentence[i].text
        if Ans == "":
            Ans = ask_sentence[1].text
            for i in range(2, len(ask_sentence)):
                Ans = Ans + " " + ask_sentence[i].text
        return Ans

    @staticmethod
    def getSayAns(ask_sentence):
        wh_list = ["what", "when", "where", "who", "whom", "whose", "why", "how"]
        prep_list = ["to", "for"]
        Ans = ""
        if ask_sentence[1].text.lower() in wh_list:
            Ans = ask_sentence[1].text
            for i in range(2, len(ask_sentence)):
                Ans = Ans + " " + ask_sentence[i].text
        elif ask_sentence[1].text.lower() == "that":
            if len(ask_sentence) <= 3:
                return Ans
            Ans = ask_sentence[2].text
            for i in range(3, len(ask_sentence)):
                Ans = Ans + " " + ask_sentence[i].text
        else:
            isLike = False
            for i in range(1, len(ask_sentence)):
                if isLike == False:
                    if ask_sentence[i].lemma_ == "like":
                        isLike = True
                else:
                    if Ans == "":
                        Ans = ask_sentence[i].text
                    else:
                        Ans = Ans + " " + ask_sentence[i].text
            if isLike == True and Ans != "":
                return Ans
            Ans = ask_sentence[1].text
            for i in range(2, len(ask_sentence)):
                if ask_sentence[i].lemma_ in prep_list:
                    return Ans
                Ans = Ans + " " + ask_sentence[i].text
        return Ans

    @staticmethod
    def getTellAns(tell_sentence):
        Ans = []
        if tell_sentence[1].text.lower() != 'me' or len(tell_sentence) <= 2:
            return Ans
        for word in tell_sentence[2:]:
            for i, KEY in enumerate(NLP.KEY_LIST):
                if KEY in word.text.lower():
                    Ans = NLP.KNOWLEDGE_LIST[i]
                    break
            if len(Ans) > 0:
                break
        print(tell_sentence)
        if len(Ans) == 0 and len(tell_sentence) >= 3:
            if 'how many' in tell_sentence[2].text.lower() or 'how much' in tell_sentence[2].text.lower():
                Ans = NLP.KNOW_LIST
        return Ans

    @staticmethod
    def isYNAns(spacyRet):
        index = 0
        for word in spacyRet:
            if index == 0:
                if NLP.getTokenDep(word) == "aux" or NLP.getTokenPos(word) == "AUX":
                    return True
            if NLP.getTokenPos(word) == 'PUNCT' and word.text == ',':
                index = 0
            index = index + 1
        return False

    @staticmethod
    def getYNAns(spacyRet):
        yNQAns = []
        index = 0
        is_Aux = False
        for i, word in enumerate(spacyRet):
            if index == 0:
                if NLP.getTokenDep(word) == "aux" or NLP.getTokenPos(word) == "AUX":
                    is_Aux = True
                index = 1
                continue
            if index == 1 and is_Aux == True:
                if NLP.getTokenDep(word) == "nsubj" or NLP.getTokenDep(word) == "attr" or word.text == 'you':
                    yNQAns.append("Yes")
                    yNQAns.append("No")
                    yNQAns.append('I do not know')
                    break
            if NLP.getTokenPos(word) == 'PUNCT' and word.text == ',':
                index = 0
                is_Aux = False
                continue
            index = index + 1
        return yNQAns

    @staticmethod
    def isWhQ(question):
        instr_list = ["say", "ask", "tell", "give"]
        for word in instr_list:
            if word in question:
                return False
        Answers = {
            "What": [''],
            "what": [''],
            "When": ['Today', 'At 2pm'],
            "when": ['Today', 'At 2pm'],
            "Where": ['China', 'In the supermarket'],
            "where": ['China', 'In the supermarket'],
            "Who": ['Taylor Swift', 'Tagore'],
            "who": ['Taylor Swift', 'Tagore'],
            "Whom": ['Taylor Swift', 'Tagore'],
            "whom": ['Taylor Swift', 'Tagore'],
            "Whose": ['Mine', 'Adele\'s'],
            "whose": ['Mine', 'Adele\'s'],
            "Why": [''],
            "why": [''],
            "How": [''],
            "how": ['']
        }
        clauses = question.split(",")
        beginWord = ''
        for clause in clauses:
            words = clause.split(" ")
            for word in words:
                if word != '':
                    beginWord = word
                    break
            if beginWord in Answers.keys():
                return Answers[beginWord]
        return None

    def getWhQAns(Ques, response):
        ques = Ques.get_ques()
        whAns = Ques.getWhAns()
        if whAns != None and len(whAns) == 1:
            clauses = ques.split(",")
            for clause in clauses:
                words = clause.split(" ")
                for word in words:
                    if word == 'What' or word == 'what':
                        whAns, response = NLP.getWhatAns(clause, response)
                    elif word == 'How' or word == 'how':
                        whAns = NLP.getHowAns(clause)
                    else:
                        pass
                    break
                if len(whAns) > 1:
                    break
            if len(whAns) == 1:
                whAns = ["I do not know"]
        return whAns, response

    def getWhatAns(question, response):
        Key = []
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(question)
        for chunk in doc.noun_chunks:
            if chunk.text == 'What' or chunk.text == 'what' or chunk.text == 'you':
                continue
            if 'what' in chunk.text or 'What' in chunk.text:
                Key.append(chunk.text[5:].lower())
            else:
                Key.append(chunk.text.lower())
        for word in doc:
            if word.pos_ == "NOUN" or word.pos_ == 'PROPN':
                exist = False
                for key in Key:
                    if word.text.lower() in key:
                        exist = True
                        break
                if exist == False:
                    Key.append(word.text.lower())
        index = -1
        for key in Key:
            for i, KEY in enumerate(NLP.KEY_LIST):
                if KEY in key:
                    index = i
                    break
            if index != -1:
                break
        response_remove = []
        for ans in response:
            for KEY in NLP.KEY_LIST:
                if KEY in ans.lower():
                    response_remove.append(ans)
                    break
        for ans in response_remove:
            response.remove(ans)
        if index == -1:
            return [''], response
        return NLP.KNOWLEDGE_LIST[index], response

    def getHowAns(question):
        words = question.split(" ")
        if len(words) > 1 and words[1] in NLP.NUMBER_LIST:
            return NLP.KNOW_LIST
        return ['']

    @staticmethod
    def getNoneOfWhatQ(question):
        Key = []
        nlp_ = spacy.load("en_core_web_sm")
        doc = nlp_(question)
        for chunk in doc.noun_chunks:
            if chunk.text == 'What' or chunk.text == 'what' or chunk.text == 'you':
                continue
            if 'what' in chunk.text or 'What' in chunk.text:
                Key.append(chunk.text[5:].lower())
        if len(Key) != 0:
            return Key
        for word in doc:
            if word.pos_ == "NOUN" or word.pos_ == 'PROPN':
                Key.append(word.text.lower())
        return Key

    @staticmethod
    def getNoneOfIQ(question):
        instruction_list = ['say', 'ask', 'tell']
        nlp_ = spacy.load("en_core_web_sm")
        doc = nlp_(question)
        findInstruc = False
        for word in doc:
            if word.lemma_ in instruction_list:
                findInstruc = True
                continue
            if findInstruc == True:
                if word.pos_ == "DET" or word.pos_ == "PRON" or word.pos_ == "ADJ":
                    continue
                if word.pos_ == "NOUN":
                    return [word.text.lower()]
                else:
                    return []
        return []