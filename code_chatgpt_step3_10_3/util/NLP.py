import re
import html
import spacy

class NLP():
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
            if NLP.getTokenDep(word) == "conj":
                return True
        return False

    @staticmethod
    def isIQAns(spacyRet):
        instruction_list = ['say', 'ask', 'tell']
        for word in spacyRet:
            if word.lemma_ in instruction_list:
                return True
        return False

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
    def isWhQ(question):
        OQAns = []
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
            OQAns = Answers.get(beginWord, [])
            if len(OQAns) > 0:
                return True
        return False

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