import prompts
import openai
import string

verbose = True

class LLMInterface:

    def __init__(self, assets, town_map, llm='cmd'):
        self.llm = llm # By default, queries user input through CMD rather than an actual LLM
        self.requires_evalutation = True # if True, LLM needs to be queried at next time step
        self.new_goal = False
        self.assets = assets

        # State data
        self.current_goal = None
        self.dialogue_history = [] # List of all dialogue history
        self.phys_action_history = []
        self.town_map = town_map
        self.car_is_stopped = True
        self.car_speed = 25
        
    '''
        Prompts the LLM to adjust to an environmental change
    '''
    def evaluate(self):
        if self.requires_evalutation:
            result = self.prompt_high_level()
            letter = parse_mc_response(result)
            if letter == 'A' or letter == 'B':
                self.goal_setting_prompt()
                self.new_goal = True
            #elif letter == 'B':
                #self.dialogue_prompt()
            else:
                raise Exception(result)

            self.requires_evalutation = False

    '''
        Compiles the high-level prompt
    '''
    def prompt_high_level(self):
        prompt = prompts.get_high_level_prompt(self)

        return self.comm_w_llm(prompt)

    def goal_setting_prompt(self):
        prompt, goals = prompts.get_low_level_goal_setting(self)
        response = self.comm_w_llm(prompt)

        letter = parse_mc_response(response)

        self.current_goal = goals[letter]

        return response

    def physical_action_prompt(self, frame):
        prompt, actions = prompts.get_low_level_phys_action(self, frame)
        response = self.comm_w_llm(prompt)

        letter = parse_mc_response(response)

        action = actions[letter]

        return action, prompt, letter

    def speedchange_slot_val(self, orig_prompt, response):
        prompt = prompts.get_followup_speedchange(self)
        response = self.comm_w_llm(orig_prompt, response=response, second_prompt=prompt)

        letter = parse_mc_response(response)

        if letter == 'A':
            return 5
        elif letter == 'B':
            return -5
        else:
            return 0

    def jturn_slot_val(self, orig_prompt, response):
        prompt = prompts.get_followup_jturn(self)
        response = self.comm_w_llm(orig_prompt, response=response, second_prompt=prompt)

        return int(response)

    def dialogue_prompt(self):
        prompt = prompts.get_low_level_dialogue(self)
        response = self.comm_w_llm(prompt)
        formatted_response = 'CHAUFFEURGPT: {response}'.format(response=response)
        self.dialogue_history.append(formatted_response)

        return response

    def inject_llm_dialogue(self, dialogue):
        formatted_response = 'CHAUFFEURGPT: {dialogue}'.format(dialogue=dialogue)
        self.dialogue_history.append(formatted_response)

    def inject_physical_action(self, elem):
        act = elem['val']['act']
        slot_type = elem['val']['slot_type']
        slot_val = elem['val']['slot_val']

        action_str = act
        if slot_type != 'Null':
            action_str += ' ' + str(slot_type) + ' ' + str(slot_val)

        if act == 'Start':
            self.car_is_stopped = False
        elif act == 'Stop':
            self.car_is_stopped = True
        
        if act == 'SpeedChange':
            self.car_speed += slot_val

        self.phys_action_history.append(action_str)


    '''
        This function actually sends the already-created prompt
        to the LLM and receives the output
    '''
    def comm_w_llm(self, prompt, response=None, second_prompt=None):
        if self.llm == 'cmd':
            return receive_cmd_input(prompt, response=response, second_prompt=second_prompt)
        elif self.llm == 'gpt4':
            return receive_gpt4_input(prompt, response=response, second_prompt=second_prompt)
        elif self.llm == 'always_a':
            print(prompt)
            return 'D'
        else:
            raise Exception('Code not compatible with the LLM {llm} yet'.format(llm=self.llm))

    '''
        Adds string from the human representing a new communication
    '''
    def receive_dialogue(self, dialogue):
        formatted_dialogue = 'PASSENGER: {dialogue}'.format(dialogue=dialogue)
        self.dialogue_history.append(formatted_dialogue)
        self.requires_evalutation = True

def receive_cmd_input(prompt, response=None, second_prompt=None):
    print('------------------------------------------------------------------------')
    if response is None:
        print(prompt)
    else:
        print(second_prompt)
    print('------------------------------------------------------------------------')
    val = input("Input: ")
    return val


def receive_gpt4_input(prompt, response=None, second_prompt=None):
    if response is None:
        messages=[{"role": "user", "content": prompt}]
    else:
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
            {"role": "user", "content": second_prompt}
        ]

    gpt_response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=messages,
        temperature = 0
    )

    response_text = gpt_response['choices'][0]['message']['content']

    if verbose:
        print('------------------------------------------------------------------------')
        print(prompt)
        print('GPT4_RESPONSE:')
        print(response_text)
        print('------------------------------------------------------------------------')

    return response_text

def parse_mc_response(response):
    for letter in string.ascii_uppercase:
        if letter in response:
            return letter
    
    raise Exception('LLM did not return a valid character')