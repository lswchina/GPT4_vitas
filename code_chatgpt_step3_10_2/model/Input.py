import util.Constant as Constant
class Input():
    def __init__(self, type_, input):
        self.__input = input
        self.__times = 0
        self.__type = type_ #0: sys, 1: help, 2: context

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
        else:
            type_name = "not-a-skill-answer"            
        return "{0}:[{1}, {2}]".format(self.__input, type_name, self.__times)
    
    def __repr__(self):
        type_name = ""
        if self.__type == 0:
            type_name = Constant.SYSTEM_LEVEL_LABEL
        elif self.__type == 1:
            type_name = Constant.HELP_EMBEDDED_LABEL
        elif self.__type == 2:
            type_name = Constant.CONTEXT_RELATED_LABEL
        else:
            type_name = "not-a-skill-answer"
        return '"{0}":["{1}", {2}]'.format(self.__input, type_name, self.__times)
    
    def get_input(self):
        return self.__input

    def get_times(self):
        return self.__times
    
    def get_type(self):
        return self.__type
    
    def isContextRelatedInput(self):
        return self.__type == 2

    def addTimes(self):
        self.__times += 1