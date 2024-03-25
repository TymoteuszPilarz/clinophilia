from obs_controller import OBSController
from teams_controller import *
import json
from datetime import timedelta
from datetime import datetime
import pygame.mixer
import platform


class App:
    def __init__(self):
        with open("config.json", "r") as json_file:
            config = json.load(json_file)

        min_time_str = config["settings"]["min_time"]
        hours, minutes, seconds = map(int, min_time_str.split(":"))
        self._min_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        max_time_str = config["settings"]["max_time"]
        hours, minutes, seconds = map(int, max_time_str.split(":"))
        self._max_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)

        self._min_participants = config["settings"]["min_participants"]
        self._min_participants_ratio = config["settings"]["min_participants_ratio"]
        self._moving_avg_len = config["settings"]["moving_avg_len"]
        self._avg_participants = 0

        self._loading_sound_path = config["settings"]["loading_sound_path"]
        self._warning_sound_path = config["settings"]["warning_sound_path"]

        self._teams_controller = TeamsController()
        self._teams_controller.clear_debug_images()

        self._obs_controller = OBSController()

        pygame.mixer.init()
        self._loading_sound = pygame.mixer.Sound(self._loading_sound_path)
        self._warning_sound = pygame.mixer.Sound(self._warning_sound_path)

    def _calc_avg_participants(self, participants):
        self._avg_participants = (
            self._avg_participants * (self._moving_avg_len - 1) + participants
        ) / self._moving_avg_len

    def _check_disconnect(self) -> bool:
        duration = self._teams_controller.meeting_duration
        participants = self._teams_controller.participants_number

        self._calc_avg_participants(participants)

        if duration < self._min_time:
            return False

        if duration > self._max_time:
            return True

        if (participants / self._avg_participants < self._min_participants_ratio) or (
            participants < self._min_participants
        ):
            return True

        return False

    def update(self):
        try:
            if self._teams_controller.offsets_loaded:
                self._teams_controller.ensure_meeting_window_is_ready()
                self._warning_sound.stop()
                self._loading_sound.play()
                self._obs_controller.start_recording()

            self._teams_controller.extract_data()
            self._loading_sound.stop()
            self._warning_sound.stop()

            if self._check_disconnect():
                self._obs_controller.stop_recording()

                try:
                    self._teams_controller.click_leave_button(0.2)
                except:
                    pass

                system_name = platform.system()
                if system_name == "Darwin":
                    os.system("pmset sleepnow")
                if system_name == "Linux":
                    os.system("systemctl suspend")
                if system_name == "Windows":
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return False

        except (ElementNotFoundException, WindowNotReadyException) as e:
            self._loading_sound.stop()
            if not pygame.mixer.get_busy():
                self._warning_sound.play()
            print(e)
            self._teams_controller.show_debug_image(True)
        except ParticipantsNumberNotVisibleException as e:
            print(e)

        return True


if __name__ == "__main__":
    app = App()
    while app.update():
        pass
