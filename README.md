# Clinophilia
MS Teams bot that can be used to automatically record a meeting.

## Motivation
The project was born out of the need to record early morning online lectures by a typical student with a broken sleep schedule. At first, just a playful idea, it turned into a fully functional application. Besides from that, sometimes in life, we encounter situations where we simply cannot be present at a remote meeting, yet we would like to know what happened during it; this is where our application comes to help. Thus, at the beginning, just a playful idea, turned into a fully functional project.

## Why not use the built-in meeting recording feature in MS Teams?
When we start recording through MS Teams, all meeting participants receive a notification that recording has begun, which may not necessarily be what we intended. Therefore, we use OBS for recording. However, we do not encourage recording without prior consent from all participants.

## How to use this program?
Simply start a meeting on MS Teams and launch this application, which will automatically begin recording using OBS. Later, based on fetched parameters, the application will recognize the end of the meeting, disconnect us, and save the recording in the path you have set in OBS. For the app to function properly, the meeting window must be maximized, due to the program's operation, which live-fetches screen data such as time, number of participants, and the position of the leave meeting button. Failure to meet this requirement will trigger a warning sound. Immediately upon launching and meeting the requirements for a maximized window, the application will play a special sound signifying the loading of initial data, which takes a few seconds. Almost everything is higly-configurable through config.json file. 

## Building and running
1. Create python virtual environment and issue this command:
```
pip install -r requirements.txt
```
2. Set paths pointing to MS Teams and OBS in config.json file and your preferred settings which will be the condition for the program to recognize the end of a meeting.
3. Finally, launch the program.

## Supported platform
Currenlty, only MacOS is supported, however Windows and Linux will be added in the future.
