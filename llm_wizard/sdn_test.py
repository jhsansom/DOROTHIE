import map_tool
import json

class SDN_Tester:

    def __init__(self, log_folder_path, model):
        self.log_folder_path = log_folder_path
        self.model = model

        self.cur_timestep = 0

    # Loads the following from the log folder:
    # - Knowledge, including street names and known landmarks
    # - Map topology
    def load_initial(self):
        config_path = self.log_folder_path + 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        street_names = config['environment']['street_names']
        
        map_name = config['environment']['map']
        
        self.town_map = map_tool.TownMap(map_name)

        # Add vehicle
        road_id = config['environment']['departure']['OpenDriveID']['road_id']
        vehicle_pos = self.town_map.get_road_position(road_id)
        self.town_map.insert_char('X', vehicle_pos)

        # Add landmarks
        landmarks = config['environment']['landmarks']
        self.town_map.add_landmark(landmarks)

        print(self.town_map.text_map)


    # Loads the following for a particular timestep:
    # - RGB image associated with the timestep
    # - Annotated log data that occurred during the timestep
    def process_next_timestep(self):
        self.cur_timestep += 1


    # Provides the information from a timestep to the model and
    # removes information that the model should not access
    def give_timestep_to_model(self):
        pass

    # Gets the total number of timesteps
    def get_total_timesteps(self):
        return 0 # TODO: fix this

    # Finalizes analysis of model over entire log data
    def complete_analysis(self):
        pass


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

    sdn_tester = SDN_Tester(log_folder_path, model)
    sdn_tester.test_on_log()