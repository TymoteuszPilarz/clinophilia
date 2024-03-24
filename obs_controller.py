import os
import obsws_python as obs
import json


class OBSController:
    def __init__(self):
        with open("config.json", "r") as json_file:
            config = json.load(json_file)
        self._obs_path = config["obs"]["path"]
        self._host = config["obs"]["host"]
        self._port = config["obs"]["port"]
        self._password = config["obs"]["password"]

    def start_recording(self):
        os.system("open " + self._obs_path + " --args --minimize-to-tray")

        # Wait until the obs client is connected to the server
        while True:
            try:
                self.obs_client = obs.ReqClient(
                    host=self._host, port=self._port, password=self._password, timeout=5
                )
                break
            except ConnectionRefusedError:
                pass

        # Wait until the obs server is ready to receive requests
        while True:
            try:
                self.obs_client.get_stats()
                break
            except obs.error.OBSSDKRequestError:
                pass

        self.scene_name = "clinophilia_scene"

        try:
            self.obs_client.create_scene(self.scene_name)
        except obs.error.OBSSDKRequestError:
            self.obs_client.remove_scene(self.scene_name)
            self.obs_client.create_scene(self.scene_name)
        self.obs_client.set_current_program_scene(self.scene_name)

        self.obs_client.create_input(
            self.scene_name,
            self.scene_name + "_dummy_source",
            "screen_capture",
            {},
            False,
        )
        windows = self.obs_client.get_input_properties_list_property_items(
            self.scene_name + "_dummy_source", "window"
        )
        self.obs_client.remove_input(self.scene_name + "_dummy_source")

        teams_window_id = None
        for window in windows.property_items:
            if window["itemName"].endswith(" | Microsoft Team"):
                teams_window_id = window["itemValue"]
                break

        self.obs_client.create_input(
            self.scene_name,
            self.scene_name + "_source",
            "screen_capture",
            {
                "application": "com.microsoft.teams2",
                "show_hidden_windows": True,
                "type": 2,
                "window": teams_window_id,
            },
            True,
        )

        self.obs_client.start_record()

    def stop_recording(self):
        self.obs_client.stop_record()
        self.obs_client.remove_scene(self.scene_name)
