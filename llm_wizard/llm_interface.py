

#############################################################################################
#############################################################################################
#############################################################################################

# This section contains the prompts themselves
#header









#############################################################################################
#############################################################################################
#############################################################################################






class LLMInterface:

    def __init__(self, llm='cmd'):
        self.llm = llm # By default, queries user input through CMD rather than an actual LLM
        self.dialogue_history = [] # List of all dialogue history
        self.requires_evalutation = True # if True, LLM needs to be queried at next time step

    '''
        Prompts the LLM to adjust to an environmental change
    '''
    def evaluate(self):
        if self.requires_evalutation:
            pass

    '''
        Adds string from the human representing a new communication
    '''
    def receive_dialogue(self, dialogue):
        self.dialogue_history.append(dialogue)
        self.requires_evalutation = True 

def receive_cmd_input(prompt):
    print(prompt)
    val = input("")
    return val

