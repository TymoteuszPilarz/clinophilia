import pywinctl
import pyautogui
import re
import pytesseract as tes
import numpy as np
from datetime import timedelta, datetime
from typing import Optional
import cv2
from models import ElementArea, MatchedElementArea, MatchedTextElementArea
import os
from os import path as p
import json
from shutil import rmtree
from constants import (
    TEAMS_LEAVE_BUTTON_ABS_PATH,
    TEAMS_PEOPLE_ICON_ABS_PATH,
    TEAMS_SHIELD_ICON_ABS_PATH,
    TEAMS_DEBUG_IMAGES_DIR_ABS_PATH,
)


class ElementNotFoundException(Exception):
    pass


class WindowNotReadyException(Exception):
    pass


class ParticipantsNumberNotVisibleException(Exception):
    pass


class TeamsController:

    def __init__(self, screenshot_overrides: tuple[cv2.typing.MatLike] = ()) -> None:
        self._screenshot_overrides: tuple[cv2.typing.MatLike] = screenshot_overrides
        self._screenshot_overrides_index = 0
        self._screenshot: Optional[cv2.typing.MatLike] = None
        self._leave_button_templ = cv2.imread(TEAMS_LEAVE_BUTTON_ABS_PATH)
        self._shield_icon_templ = cv2.imread(TEAMS_SHIELD_ICON_ABS_PATH)
        self._people_icon_templ = cv2.imread(TEAMS_PEOPLE_ICON_ABS_PATH)
        self._leave_button_offset: Optional[ElementArea] = None
        self._shield_icon_offset: Optional[ElementArea] = None
        self._people_icon_offset: Optional[ElementArea] = None
        self._meeting_duration_text_offset: Optional[ElementArea] = None
        self._participants_number_text_offset: Optional[ElementArea] = None
        self._leave_button: Optional[MatchedElementArea] = None
        self._shield_icon: Optional[MatchedElementArea] = None
        self._people_icon: Optional[MatchedElementArea] = None
        self._meeting_duration_text: Optional[MatchedTextElementArea] = None
        self._participants_number_text: Optional[MatchedTextElementArea] = None
        self._meeting_duration: timedelta
        self._participants_number: int

        with open("config.json", "r") as json_file:
            config = json.load(json_file)
        self._teams_excluded_names = config["teams"]["excluded_names"]

        self._teams_windows = []

        windows = pywinctl.getAllWindows()
        for window in windows:
            if self._is_meeting_window(window.title):
                self._teams_windows.append(window)

        if not self._teams_windows:
            raise WindowNotReadyException("There are no meeting windows opened")

    @property
    def meeting_duration(self) -> timedelta:
        if not self._meeting_duration_text:
            self.extract_data()
        return self._meeting_duration

    @property
    def participants_number(self) -> int:
        if not self._participants_number_text:
            self.extract_data()
        return self._participants_number

    @property
    def offsets_loaded(self) -> bool:
        return (
            not self._leave_button_offset
            and not self._shield_icon_offset
            and not self._people_icon_offset
            and not self._meeting_duration_text_offset
            and not self._participants_number_text_offset
        )

    def click_leave_button(self, duration: float = 0.5):
        if not len(self._screenshot_overrides):
            self.ensure_meeting_window_is_ready()

        self._take_screenshot()

        matches = self._find_elements_areas(
            self._leave_button_templ,
            area=self._leave_button_offset,
        )
        if not len(matches):
            raise ElementNotFoundException("Leave button not found")

        ratio = pyautogui.size().width / self._screenshot.shape[1]
        pyautogui.click(
            self._leave_button.x * ratio,
            self._leave_button.y * ratio,
            duration=duration,
        )

    def extract_data(self):
        self._extract_elements()
        duration_split = tuple(map(int, self._meeting_duration_text.text.split(":")))
        if len(duration_split) == 2:
            mins, secs = duration_split
            meeting_duration = timedelta(minutes=mins, seconds=secs)
        elif len(duration_split) == 3:
            hours, mins, secs = duration_split
            meeting_duration = timedelta(hours=hours, minutes=mins, seconds=secs)
        self._meeting_duration = meeting_duration

        self._participants_number = int(
            "".join(c for c in self._participants_number_text.text if c.isdigit())
        )

    def clear_offsets(self):
        self._leave_button_offset = None
        self._shield_icon_offset = None
        self._people_icon_offset = None
        self._meeting_duration_text_offset = None
        self._participants_number_text_offset = None

    def clear_debug_images(self):
        rmtree(TEAMS_DEBUG_IMAGES_DIR_ABS_PATH, ignore_errors=True)

    def show_debug_image(self, headless: bool = False):
        if self._screenshot is None:
            print("No screenshot to show")
            return
        debug_image = self._screenshot.copy()

        def draw_rect(
            match: Optional[ElementArea], color: tuple[int, int, int] = (0, 255, 0)
        ):
            if not match:
                return
            cv2.rectangle(
                debug_image,
                (match.x, match.y),
                (match.x + match.w, match.y + match.h),
                color,
            )

        draw_rect(self._leave_button)
        draw_rect(self._people_icon)
        draw_rect(self._shield_icon)
        draw_rect(self._meeting_duration_text)
        draw_rect(self._participants_number_text)

        cyan = (255, 255, 0)  # BGR
        draw_rect(self._leave_button_offset, cyan)
        draw_rect(self._people_icon_offset, cyan)
        draw_rect(self._shield_icon_offset, cyan)
        draw_rect(self._meeting_duration_text_offset, cyan)
        draw_rect(self._participants_number_text_offset, cyan)

        if not hasattr(cv2, "imshow") or not hasattr(cv2, "waitKey"):
            print("cv2.imshow and cv2.waitKey not available, saving image instead")
            headless = True
        if not headless:
            cv2.imshow("Debug", debug_image)
            cv2.waitKey(0)
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file = f"{timestamp}.jpg"
            os.makedirs(TEAMS_DEBUG_IMAGES_DIR_ABS_PATH, exist_ok=True)
            cv2.imwrite(p.join(TEAMS_DEBUG_IMAGES_DIR_ABS_PATH, file), debug_image)

    def ensure_meeting_window_is_ready(self):
        for window in self._teams_windows:
            if window.isMaximized:
                return
        raise WindowNotReadyException("Teams window is not on full screen")

    def close_meeting_window(self):
        for window in self._teams_windows:
            window.close(True)

    def _is_meeting_window(self, title: str) -> bool:
        if not title.endswith(" | Microsoft Teams"):
            return False
        for name in self._teams_excluded_names:
            if title.startswith(name + " | "):
                return False
        return True

    def _extract_elements(self):
        if not self._screenshot_overrides:
            self.ensure_meeting_window_is_ready()

        self._take_screenshot()

        matches = self._find_elements_areas(
            self._leave_button_templ,
            area=self._leave_button_offset,
        )
        if not len(matches):
            raise ElementNotFoundException("Leave button not found")
        # upper most element
        self._leave_button = min(matches, key=lambda match: match.y)
        if not self._leave_button_offset:
            self._leave_button_offset = self._leave_button.multiplied_by(1.5)

        # offset is known, so it's unnecessary
        if not self._meeting_duration_text_offset:
            matches = self._find_elements_areas(
                self._shield_icon_templ,
                area=self._shield_icon_offset,
            )
            if not len(matches):
                raise ElementNotFoundException("Shield icon not found")
            self._shield_icon = min(matches, key=lambda match: match.y)
            if not self._shield_icon_offset:
                self._shield_icon_offset = self._shield_icon.multiplied_by(1.5)

        if not self._participants_number_text_offset:
            matches = self._find_elements_areas(
                self._people_icon_templ, area=self._people_icon_offset, threshold=0.7
            )
            if not len(matches):
                raise ElementNotFoundException("People icon not found")
            self._people_icon = min(matches, key=lambda match: match.y)
            if not self._people_icon_offset:
                self._people_icon_offset = self._people_icon.multiplied_by(1.5)

        # text elements
        if not self._meeting_duration_text_offset:
            self._meeting_duration_text_offset = ElementArea(
                x=self._shield_icon.x
                + self._shield_icon.w
                + 20 * self._shield_icon.scale,
                y=self._shield_icon.y,
                w=150 * self._shield_icon.scale,
                h=self._shield_icon.h * self._shield_icon.scale,
            )
        matches = self._find_text(area=self._meeting_duration_text_offset)
        l = len(matches)
        if not l:
            raise ElementNotFoundException("Meeting duration text not found")
        duration_regex = re.compile(r"(\d{2}:)?\d{2}:\d{2}")
        regex_match = None
        for i in range(l):
            if duration_regex.match(matches[i].text):
                regex_match = matches[i]
                break
        if not regex_match:
            raise ElementNotFoundException("Meeting duration has invalid format")
        self._meeting_duration_text = regex_match

        if is_there_red(
            self._screenshot[
                self._people_icon_offset.y : self._people_icon_offset.y
                + self._people_icon_offset.h,
                self._people_icon_offset.x : self._people_icon_offset.x
                + self._people_icon_offset.w,
            ]
        ):
            raise ParticipantsNumberNotVisibleException(
                "Hand is raised by a participant"
            )
        else:
            if not self._participants_number_text_offset:
                self._participants_number_text_offset = ElementArea(
                    x=self._people_icon.x
                    + self._people_icon.w
                    + 3 * self._people_icon.scale,
                    y=self._people_icon.y,
                    w=50 * self._people_icon.scale,
                    h=self._people_icon.h * self._people_icon.scale,
                )
            matches = self._find_text(
                area=self._participants_number_text_offset,
                config=r"--oem 3 --psm 6 digits",
            )
            l = len(matches)
            if not l:
                raise ElementNotFoundException("Participants number text not found")
            participants_regex = re.compile(r".*\d{1,}")
            regex_match = None
            for i in range(l):
                if participants_regex.match(matches[i].text):
                    regex_match = matches[i]
                    break
            if not regex_match:
                regex_match = matches[0]
                if not regex_match.text.strip():
                    regex_match.text = "1"  # no number means 1 participant
                else:
                    raise ElementNotFoundException(
                        "Participants number has invalid format"
                    )
            self._participants_number_text = regex_match

    def _take_screenshot(self):
        if len(self._screenshot_overrides):
            if self._screenshot_overrides_index >= len(self._screenshot_overrides):
                self._screenshot_overrides_index = 0
                print("All screenshot overrides used, starting over")
            screenshot = self._screenshot_overrides[self._screenshot_overrides_index]
            self._screenshot_overrides_index += 1
        else:
            screenshot = pyautogui.screenshot()  # RGB PIL image
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        self._screenshot = screenshot

    def _find_elements_areas(
        self,
        template_img: cv2.typing.MatLike,
        *,
        area: Optional[ElementArea] = None,
        threshold: float = 0.8,
        scale_min: float = 0.5,
        scale_max: float = 1.5,
        scale_steps: int = 20,
    ) -> list[MatchedElementArea]:

        img = cv2.cvtColor(self._screenshot, cv2.COLOR_BGR2GRAY)
        if area:
            img = img[area.y : area.y + area.h, area.x : area.x + area.w]

        templ_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        matches: list[MatchedElementArea] = []
        for scale in np.linspace(scale_min, scale_max, scale_steps)[::-1]:
            resized_template_img = cv2.resize(templ_img, None, fx=scale, fy=scale)
            w, h = resized_template_img.shape[::-1]
            if (
                resized_template_img.shape[0] > img.shape[0]
                or resized_template_img.shape[1] > img.shape[1]
            ):
                break
            res = cv2.matchTemplate(img, resized_template_img, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            if loc[0].size > 0:
                _, _, _, max_loc = cv2.minMaxLoc(res)
                matches.append(
                    MatchedElementArea(
                        x=max_loc[0] + (area.x if area else 0),
                        y=max_loc[1] + (area.y if area else 0),
                        w=w,
                        h=h,
                        scale=scale,
                    )
                )
        return matches

    def _find_text(
        self,
        *,
        area: Optional[ElementArea] = None,
        config: str = r"--oem 3 --psm 6",
    ) -> list[MatchedTextElementArea]:

        img = self._screenshot
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if area:
            img = img[area.y : area.y + area.h, area.x : area.x + area.w]

        _, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
        img = cv2.bitwise_not(img)
        data = tes.image_to_data(img, output_type=tes.Output.DICT, config=config)
        matches: list[MatchedTextElementArea] = []
        for i in range(len(data["text"])):
            x, y, w, h = (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )
            matches.append(
                MatchedTextElementArea(
                    x=x + (area.x if area else 0),
                    y=y + (area.y if area else 0),
                    w=w,
                    h=h,
                    text=data["text"][i],
                )
            )
        return matches


def is_there_red(img: cv2.typing.MatLike) -> bool:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    red_mask_left = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
    red_mask_right = cv2.inRange(hsv, (160, 100, 100), (179, 255, 255))

    red_mask = cv2.bitwise_or(red_mask_left, red_mask_right)
    # red = cv2.bitwise_and(img, img, mask=red_mask)
    # cv2.imshow('red', red)
    # cv2.waitKey(0)
    if np.sum(red_mask) > 0:
        return True
    return False


if __name__ == "__main__":
    import time
    import os
    from constants import TEST_IMAGES_DIR_ABS_PATH

    overrides = []
    for file in os.listdir(TEST_IMAGES_DIR_ABS_PATH):
        if file.endswith(".png"):
            overrides.append(cv2.imread(p.join(TEST_IMAGES_DIR_ABS_PATH, file)))
    # ctrl = TeamsController(screenshot_overrides=overrides)
    ctrl = TeamsController()
    ctrl.clear_debug_images()

    i = 0
    while True:
        try:
            time.sleep(2)
            print(f"i: {i}")
            ctrl.extract_data()
            print(f"Meeting duration: {ctrl.meeting_duration}")
            print(f"Participants number: {ctrl.participants_number}")
            # if i == 5:
            #   ctrl.click_leave_button()
            #   break
        except (ElementNotFoundException, WindowNotReadyException) as e:
            print(e)
            exit(1)
        except ParticipantsNumberNotVisibleException as e:
            print(e)
        finally:
            # ctrl.show_debug_image(headless=True)
            i += 1
