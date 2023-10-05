from llm_interface import LLMInterface
import warnings
import map_tool
import json
import openai

with open('API_KEY.txt', 'r') as fp:
    api_key = fp.read()
openai.api_key = api_key

class SDN_Tester:

    def __init__(self, log_folder_path, model, llm):
        self.log_folder_path = log_folder_path
        self.model = model

        self.cur_timestep = 0

        self.eval_goal_updates = False
        self.eval_physical_actions = True

        if self.eval_physical_actions:
            self.total_physical_actions = 0
            self.physical_action_slot_types_correct = 0
            self.physical_action_slot_vals_correct = 0

        annotated_log_path = self.log_folder_path + 'annotated_log.json'
        with open(annotated_log_path, 'r') as f:
            self.annotated_log = json.load(f)

        self.llm = llm

    # Loads the following from the log folder:
    # - Knowledge, including street names and known landmarks
    # - Map topology
    def load_initial(self):
        config_path = self.log_folder_path + 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        map_name = config['environment']['map']
        
        trajectory_csv = self.log_folder_path + 'trajectory.csv'
        town_map = map_tool.TownMap(map_name, config, trajectory_csv=trajectory_csv)

        assets = []
        for elem in config['environment']['landmarks']:
            asset = {}
            asset['type'] = elem['asset']
            assets.append(asset)

        self.interface = LLMInterface(assets, town_map, llm=self.llm)


    # Loads the following for a particular timestep:
    # - RGB image associated with the timestep
    # - Annotated log data that occurred during the timestep
    def process_next_timestep(self):
        elem = self.annotated_log[self.cur_timestep]

        print(f'FRAME: {elem["frame"]}')

        if elem['type'] == 'DialogueMove':
            if elem['from'] == 'dorothy':
                self.interface.receive_dialogue(elem['utterance_gt'])
            elif elem['from'] == 'wizard':
                self.interface.inject_llm_dialogue(elem['utterance_gt'])

        if self.eval_goal_updates:
            self.eval_goal_update(elem)
        if self.eval_physical_actions:
            self.eval_physical_action(elem)

        if elem['type'] == 'PhysicalAction':
            self.interface.inject_physical_action(elem)

        self.cur_timestep += 1

    def eval_goal_update(self, elem):
        if elem['type'] == 'BeliefUpdate' and elem['val']['act'] == 'GoalUpdate':
            try:
                destination = elem['val']['slot_val'][-1]['landmark']['asset']

                self.interface.evaluate()

                if destination.lower() in self.interface.current_goal:
                    num_correct_goal_updates += 1
            except Exception as e:
                warnings.warn('some sort of issue')
                print(e)

    def eval_physical_action(self, elem):
        if elem['type'] == 'PhysicalAction':
            self.total_physical_actions += 1
            # TODO: add slot val evaluation
            #self.physical_action_slot_vals_correct
            frame = elem['frame']
            try:
                act = elem['val']['act']
                slot_type = elem['val']['slot_type']
                slot_val = elem['val']['slot_val']

                pred_act, orig_prompt, letter = self.interface.physical_action_prompt(frame)

                if pred_act == act:
                    print('Correct slot type!')
                    self.physical_action_slot_types_correct += 1

                    slot_val_correct = False
                    if act == 'SpeedChange':
                        ans = self.interface.speedchange_slot_val(orig_prompt, letter)
                        slot_val_correct = (ans == slot_val)
                    elif act == 'JTurn':
                        ans = self.interface.jturn_slot_val(orig_prompt, letter)
                        slot_val_correct = (abs(ans - slot_val) <= 15)
                    else:
                        slot_val_correct = True
                    
                    if slot_val_correct:
                        print('Slot val correct!')
                        self.physical_action_slot_vals_correct += 1
                    else:
                        print('Slot val incorrect')
                else:
                    print(f'Incorrect; correct action was {act}')

                

            except Exception as e:
                warnings.warn('some sort of issue')
                print(e)

    # Provides the information from a timestep to the model and
    # removes information that the model should not access
    def give_timestep_to_model(self):
        pass

    # Gets the total number of timesteps
    def get_total_timesteps(self):
        return len(self.annotated_log)

    # Finalizes analysis of model over entire log data
    def complete_analysis(self):
        if self.eval_physical_actions:
            slot_type_accuracy = self.physical_action_slot_types_correct / self.total_physical_actions
            slot_val_accuracy = self.physical_action_slot_vals_correct / self.total_physical_actions
            print(f'Total physical actions = {self.total_physical_actions}')
            print(f'Slot type accuracy = {slot_type_accuracy}')
            print(f'Slot val accuracy = {slot_val_accuracy}')


    # Tests the model on one particular log folder
    def test_on_log(self):
        # Get the initial data and provide it to the model
        self.load_initial()

        # Loop through timesteps
        total_timesteps = self.get_total_timesteps()
        while self.cur_timestep < total_timesteps:
            self.process_next_timestep()

        self.complete_analysis()


if __name__ == '__main__':
    log_folder_path = '/data/owenh/arc_data/log_1651158519/'
    model = 6

    sdn_tester = SDN_Tester(log_folder_path, model, 'gpt4')
    sdn_tester.test_on_log()