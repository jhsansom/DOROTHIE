import string

header = '''
You are ChauffeurGPT. You are responsible for safely piloting a car according to the instructions of a passenger.
You must communicate with the passenger and make high-level decisions regarding the current navigational goals.

'''

only_mc = '''
Please ONLY output the letter corresponding to your choice.
Do not output any text except for the letter corresponding to your choice
'''

#############################################################################################
#################################### High-level prompts #####################################
#############################################################################################

high_level_current_goal = '''
The current goal is {goal}
'''

high_level_decisions = '''
You can output one of the following choices:
(A) SET NEW GOAL: change the existing goal
(B) SPEAK: ouput dialogue for the passenger
'''

def print_dialogue(llm_interface):
    prompt = "DIALOGUE HISTORY:\n"
    for utterance in llm_interface.dialogue_history:
        prompt += utterance
        prompt += "\n"

    return prompt

def get_high_level_prompt(llm_interface):
    prompt = header
    prompt += print_dialogue(llm_interface)
    prompt += high_level_current_goal.format(goal=llm_interface.current_goal)
    prompt += high_level_decisions
    prompt += only_mc

    return prompt

def print_map(llm_interface, frame):
    prompt = "CURRENT MAP:\n"
    prompt += llm_interface.town_map.load_map_at_frame(frame)
    prompt += '\n'
    prompt += llm_interface.town_map.get_vehicle_string()
    prompt += '\nLandmark labels:\n'
    prompt += llm_interface.town_map.get_landmark_string()
    prompt += '\nStreet names:\n'
    prompt += llm_interface.town_map.get_streetname_string()

    return prompt


#############################################################################################
############################## Low-level goal-setting prompts ###############################
#############################################################################################

low_level_goal_setting = '''
You have been tasked with choosing the new navigational goal.
The vehicle will take the fastest route to this navigational goal.

The current goal is {goal}

You can choose a new goal from among these options:
'''

goal_choice = "({letter}) {potential_goal}\n"

def get_low_level_goal_setting(llm_interface):
    prompt = header
    prompt += print_dialogue(llm_interface)
    prompt += low_level_goal_setting.format(goal=llm_interface.current_goal)
    goals = {}
    for i, asset in enumerate(llm_interface.assets):
        asset_name = asset['type']
        letter = string.ascii_uppercase[i]
        prompt += goal_choice.format(letter=letter, potential_goal=asset_name)
        goals[letter] = asset_name

    prompt += only_mc

    return prompt, goals

#############################################################################################
################################ Low-level dialogue prompts #################################
#############################################################################################

low_level_dialogue = '''
You have been tasked with communicating with the human passenger.
Please take this opportunity to provide the passenger with information
or to ask them a question.
'''

def get_low_level_dialogue(llm_interface):
    prompt = header
    prompt += low_level_dialogue

    return prompt

#############################################################################################
################################## Physical action prompts ##################################
#############################################################################################

low_level_phys_action = '''
You have been tasked with choosing the next physical action.
You can choose a new action from among these options:
'''

action_choice = "({letter}) {potential_action}\n"

all_actions = ['LaneFollow', 'LaneSwitch', 'UTurn', 'JTurn', 'Stop', 'Start', 'SpeedChange']

def get_low_level_phys_action(llm_interface, frame):
    prompt = header
    prompt += print_dialogue(llm_interface)
    prompt += '\n'
    prompt += print_map(llm_interface, frame)
    prompt += '\n'
    prompt += low_level_phys_action
    actions = {}
    for i, action in enumerate(all_actions):
        letter = string.ascii_uppercase[i]
        prompt += action_choice.format(letter=letter, potential_action=action)
        actions[letter] = action

    prompt += only_mc

    return prompt, actions

#############################################################################################
###################################### Other prompts ########################################
#############################################################################################

# Lower-level prompts
navigation_block = '''For navigational purposes, you have access to a planner function that you may call in the following manner:
```Python
loc1 = Landmark('Home') # this is the location of 'home'
loc2 = Intersection('Broadway', 'Baits') # this is the intersection between two roads named 'Broadway' and 'Baits'
loc3 = StreetSegment('Broadway', loc1, loc2) # this is the location of a street segment between loc1 and loc2
Planner(loc1, [loc2, loc3]) # this planning function maps a route from the current position to loc1 while avoiding loc2 and loc3
```
Here is a sample output of the planner function. It lists all intersections and landmarks that will be passed along the way:
```Python
Planner(loc1, [])
>>> [['uturn'], ['straight', Intersection('Baits', 'Hubbard')], ['right'], ['straight', Landmark('Home')]]
```
'''

dialogue_history_header = '''The following is the history, which contains dialogue between yourself (ChaufferGPT) and the passenger. 
It also contains records you have made regarding road conditions:'''

sample_dialogue_history = '''
PASSENGER: can you take me to Arbys?
CHAUFFEURGPT: yes
PASSENGER: actually nevermind. can you take me to Wendys?
CHAUFFEURGPT: no worries. yes, I can
NOTE: there is construction blocking the intersection of Hayward and Baits
PASSENGER: actually, I changed my mind again. can you take me to Arbys?
'''

other_stuff = '''
This is the plan that is currently saved into your navigational history:
```Python
goal = Landmark('Arbys')
Planner(goal, [])
>>> [['straight', Intersection('Fuller', 'Hubbard')], ['left'], ['straight', Landmark('Arbys')]]
```

Here is your current location:
```Python
loc1 = Intersection('Fuller', 'Draper')
loc2 = Intersection('Fuller', 'Hubbard')
current_location = StreetSegment('Fuller', loc1, loc2)
facing_towards = loc2
```

Here is a description of your current visual input:
There is a road in front of you with an ambulance that is blocking both lanes.

You must now produce an ouput of the following form. You do not need to output all output types. You do not need to output them in any specific order either.
OUTPUTTYPE1
Your outputs for output type 1
OUTPUTTYPE2
Your outputs for output type 2
'''
