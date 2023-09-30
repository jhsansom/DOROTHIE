from llm_interface import LLMInterface
import openai
import json
import os

openai.api_key = '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'

def examine_log(log_path):

    annotated_log_path = log_path + 'annotated_log.json'
    with open(annotated_log_path, 'r') as f:
        annotated_log = json.load(f)

    config_path = log_path + 'config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    assets = []
    for elem in config['environment']['landmarks']:
        asset = {}
        asset['type'] = elem['asset']
        assets.append(asset)

    interface = LLMInterface(assets, llm='gpt4')

    # Test for goal updates
    num_goal_updates = 0
    num_correct_goal_updates = 0
    for elem in annotated_log:
        if elem['type'] == 'DialogueMove':
            if elem['from'] == 'dorothy':
                interface.receive_dialogue(elem['utterance_gt'])
            elif elem['from'] == 'wizard':
                interface.inject_llm_dialogue(elem['utterance_gt'])

        if elem['type'] == 'BeliefUpdate' and elem['val']['act'] == 'GoalUpdate':
            try:
                destination = elem['val']['slot_val'][num_goal_updates]['landmark']['asset']
                num_goal_updates += 1

                interface.evaluate()

                if destination.lower() in interface.current_goal:
                    num_correct_goal_updates += 1
            except Exception as e:
                print(e)

    if num_goal_updates != 0:
        frac_correct = num_correct_goal_updates/num_goal_updates
    else:
        frac_correct = 1
    print('Fraction of correct goal updates: {:.2f}'.format(frac_correct))

    return frac_correct


parent_dir = '/data/owenh/arc_data/'
direcs = os.listdir(parent_dir)
num_direcs = len(direcs)

frac_correct = 0
for directory in direcs:
    if 'log_' in directory:
        full_path = parent_dir + directory + '/'
        print('Testing directory = ' + full_path)
        frac_correct += examine_log(full_path)


frac_correct = frac_correct / num_direcs
print('Overall fraction of correct goal updates: {:.2f}'.format(frac_correct))