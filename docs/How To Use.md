How to Use

BetterDesk is designed to be used as an interactive computer-vision workbench. Once the software and required hardware are connected, position the cameras so that the working area of the desk
is visible and place the ArUco markers around the workspace. The cameras provide the visual input used by the detection system, while the markers define the physical workspace and allow
detected component positions to be mapped to locations on the desk.


Start the BetterDesk software from the project environment and allow the camera feeds to initialise. The computer-vision pipeline continuously analyses the camera frames and searches for 
supported electronic components using the trained YOLOv11 detection model. When a component is detected, BetterDesk places a bounding box around it and identifies the component. 
The detection information can then be used by the rest of the system to understand what is currently on the workspace and where it is located.
To inspect a component, point toward it within the camera's view. The interface can select the detected component and display an information panel containing its name, image, description,
specifications, warnings, and examples of projects it can be used in. The visual interface also displays the current system status and processing FPS, while the bottom status bar provides
feedback about what the system is currently doing. If the system is organising the workspace, the interface displays an “Organising Desk...” status.
BetterDesk can also be interacted with using voice. Speak a question or command through the connected microphone and the voice system transcribes the speech before passing the text
along with the detected workspace information to the AI system. This allows the user to ask about components or the current workspace without having to manually identify every part. 
Responses can then be returned through the voice interface.
For physical workspace interaction, the detected component coordinates are converted into desk-space positions using the camera calibration and ArUco reference points. These coordinates are
intended to allow BetterDesk to determine where objects are located and provide instructions for where they should be placed. The programmable desk mechanism can then move its individual ball
units using the X/Y motion system. The physical system uses an ESP32 to control the motors and pressure system, allowing objects on the workspace to be moved across the desk.
The projection system is used to extend the computer-vision interface onto the physical workspace. Once the projector is connected and calibrated, visual information such as bounding boxes,
arrows, labels, and placement instructions can be projected directly onto the desk rather than requiring the user to constantly look at a separate screen. The projection subsystem contains
the ArUco calibration helper, overlay manager, renderer, and server components used to create and manage these projected overlays.

A typical BetterDesk session therefore follows this workflow:
Prepare the workspace — Place the cameras so the required desk area is visible and position the ArUco markers at the defined workspace reference points.
Start the software — Launch the BetterDesk computer-vision system and wait for the camera and detection pipeline to initialise.
Place components on the desk — Put the electronic components you want BetterDesk to recognise inside the calibrated workspace.
Allow detection — The YOLOv11 model analyses the camera feed and generates detections for supported components.
Inspect components — Point toward a detected component to select it and view its information, specifications, warnings, and project information in the BetterDesk interface.
Ask questions by voice — Use the voice interface to ask about the detected components or what you are working on.
Follow visual guidance — When projection is enabled, use the projected labels, boxes, arrows, and instructions to identify components and understand where they should be placed.
Organise the workspace — When the physical motion system is available, BetterDesk can use the detected component positions to determine movement/organisation actions for the programmable desk surface.
Build and interact — Continue working on the project while BetterDesk observes the workspace and provides computer-vision, AI, voice, and physical interaction features.
Current Prototype

The repository represents an actively developed prototype, so not every part of the complete physical system is necessarily required or operational at the same time. The software is divided into separate components for detection, UI rendering, voice interaction, projection, and model training. The physical desk, projector, and control-panel systems are developed as separate subsystems and can be integrated progressively as the hardware is completed.
