from os import path as p

PROJECT_DIR_ABS_PATH = p.abspath(p.realpath(p.dirname(__file__)))
TEAMS_DEBUG_IMAGES_DIR_ABS_PATH = p.join(PROJECT_DIR_ABS_PATH,
                                         'teams_controller_debug')
RESOURCES_DIR_ABS_PATH = p.join(PROJECT_DIR_ABS_PATH, 'resources')
TEAMS_LEAVE_BUTTON_ABS_PATH = p.join(RESOURCES_DIR_ABS_PATH,
                                     'teams_leave_button.png')
TEAMS_PEOPLE_ICON_ABS_PATH = p.join(RESOURCES_DIR_ABS_PATH,
                                    'teams_people_icon.png')
TEAMS_SHIELD_ICON_ABS_PATH = p.join(RESOURCES_DIR_ABS_PATH,
                                    'teams_shield_icon.png')
TEST_IMAGES_DIR_ABS_PATH = p.join(RESOURCES_DIR_ABS_PATH, 'test')
