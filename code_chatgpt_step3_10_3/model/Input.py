import util.Constant as Constant
class Input():
    def __init__(self, type_, input, init_weight):
        self.__input = input
        self.__times = Constant.M
        self.__type = type_ #0: sys, 1: help, 2: context, 3: document
        self.__new_state = 0
        self.__weight = init_weight
        
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__input == other.__input
        else:
            return False

    def __hash__(self):
        return hash(self.__input)
    
    def __str__(self):
        type_name = ""
        if self.__type == 0:
            type_name = Constant.SYSTEM_LEVEL_LABEL
        elif self.__type == 1:
            type_name = Constant.HELP_EMBEDDED_LABEL
        elif self.__type == 2:
            type_name = Constant.CONTEXT_RELATED_LABEL
        elif self.__type == 3:
            type_name = Constant.DOCUMENT_RECHIEVED_LABEL
        return "{0}:[{1}, {2}]".format(self.__input, type_name, self.__times)
    
    def __repr__(self):
        type_name = ""
        if self.__type == 0:
            type_name = Constant.SYSTEM_LEVEL_LABEL
        elif self.__type == 1:
            type_name = Constant.HELP_EMBEDDED_LABEL
        elif self.__type == 2:
            type_name = Constant.CONTEXT_RELATED_LABEL
        elif self.__type == 3:
            type_name = Constant.DOCUMENT_RECHIEVED_LABEL
        return '"{0}":["{1}", {2}]'.format(self.__input, type_name, self.__times)
    
    def get_input(self):
        return self.__input

    def get_times(self):
        return self.__times
    
    def get_type(self):
        return self.__type

    def get_weight(self):
        return self.__weight
    
    def isContextRelatedInput(self):
        return self.__type == 2

    def addTimes(self):
        self.__times += 1
        self.__updateWeight()

    def addNewState(self, u):
        self.__new_state += u
        self.__updateWeight()

    def __updateWeight(self):
        self.__weight = (Constant.ALPHA *  + Constant.BETA * self.__new_state) / (Constant.GAMMA * self.__times)
