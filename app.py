from obs_controller import OBSController
import json

class App:
    # TODO Add TeamsController
    def __init__(self):
        with open('config.json', 'r') as json_file:
                config = json.load(json_file)
        self._min_time = config["settings"]["min_time"]
        self._min_participants = config["settings"]["min_participants"]
        self._min_participants_ratio = config["settings"]["min_participants_ratio"]
        self.warning_sound_path = config["sound"]["warning_sound_path"]

        self._obs_controller = OBSController()

    # TODO Implement this function
    def _check_disconnect(self) -> bool:
        return True

    # TODO implement this function
    def update(self):
        if (self._check_disconnect()):
            # TODO cleanup operations
            return False
        
        return True

if __name__ == "__main__":
    app = App()
    while (app.update()):
         pass