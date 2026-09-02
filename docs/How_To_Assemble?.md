# How to Assemble BetterDesk

## 1. What are we building?

BetterDesk has five main pieces:

1. Programmable motion surface, a 10x10 grid of balls that can move objects around.
2. Motor + rod system, motors spin threaded rods which transfer motion through the mechanical cells.
3. AI/vision system, two cams + software.
4. Projection system, a custom projector.
5. Control panel, an Arduino small touchscreen interface.

The Pi 5 is the main computer for the overall system. Separate microcontrollers handle some of the specific system things.

The important part is to get one mechanical cell working first. There is no point assembling 100 cells and then discovering that the ball is slipping or the rod geometry is wrong!

---

# 2. Mechanical surface

## 2.1 Prepare the grid

Build the main frame according to the CAD model and create the 10x10 ball positions.

Each grid point assembly should have:

- a ball
- spring
- all the 3Dp stuff
- tubing

Use the CAD dimensions as the source of truth for spacing.

Do the same for the springs: install one spring per active cell and keep the remaining springs as spares (cus you're gonna break a lot).

## 2.2 Install the rods

Fit the threaded rods through the mechanical system according to the CAD.

The nema motors will spin a basic gear system such that 1 motor can spin 5 threaded rods and the mechanism transfers that motion to the balls.

Before doing the whole surface, get ONE cell working first. Make sure the rod spins properly, the ball moves properly and the spring returns everything to its position.

## 2.3 Motors

Mount the motors to the frame and connect them to the threaded rods. both NEMA 13 stepper motors and 28BYJ-48 motors with ULN2003 drivers. Connect the motor drivers and ESP32 boards acc to the wiring diagram (ignore that its made in canva lol)

---

# 3. Pneumatic system / piping system

SO THIS IS divided into 2 main parts, the pnuematic thingabob and the piping madness.

For the piping madness since we are printing a 2 way into a 1 way thingy i frgt the name, it will basically connect to 1 X and 1 Y pipe.

SO now u do this for all 10 + 10 pipes -> 20 pipes and then u have a XnY grid! 

Install the pumps at end of each pipe and route the tubing through the relevant parts of the mechanism.

Connect the pressure sensors to the pneumatic sections and make sure the tubing connections are secure.

Test one complete cell before connecting everything together otherwise ull build everything and realise ur pipe is too thick by 0.00000001 micrometer and u gotta redo everything.

---

# 4. Main electronics

The Raspberry Pi 5 is the main computer for BetterDesk.

It handles the overall software, AI system, vision system and communication between the different parts.

The ESP32 boards handle the motor control side.

Connect the Raspberry Pi, ESP32s and motor drivers acc to the wiring diagram, PLEASE follow the wiring diagram, i sweated it for like 3 hours.

Keep the power connections separate for the different systems and use the wiring diagram as the reference.

---

# 5. AI and vision system

Mount any phone camera and tablet camera so they can see the whole workspace.

The cameras are Auto calibrated together so the software can understand the workspace in 3D.

Place four ArUco markers around the corners of the workspace. These give the software a reference for where objects are.    

OR

u be an idiot like me and u manually take 50 pics for calibration EVERY TIME using some random ass python library

The software uses:

- stereo camera calibration
- YOLOv11 <- the GOAT
- ArUco markers 
- GPT-4o <- stinky (grok better /j)
- Whisper 
- ElevenLabs

Once the software knows where objects are, those positions can also be used by the projector to show boxes, arrows, labels, instructions, guides, yt shorts ANYTHING

---

# 6. Projector

The projector is built around a 50W COB LED.

The optical setup is:

LED -> condenser lens -> LCD -> collector lens -> projector lens

The LCD is taken from an eshants stinky farty old broken tablet and used without its original backlight)

## 6.1 LED and cooling

Mount the LED onto the aluminium cooling assembly (get it from ur uncle or js bend the metal with ur bare hands) and attach the CPU cooler.

The 50W LED produces a SHI TON of heat, so make sure the cooling system is properly mounted before running it.

## 6.2 LCD and lenses

Install the tablet LCD into its mount.

Current lenses:

- 100 mm diameter, 200 mm focal length collector lens
- 75 mm diameter, 100 mm focal length projector lens

Use the CAD dihmensions for the exact spacing.

## 6.3 Projector mount

Mount the projector onto the adjustable mechanism.

The current design uses a ratchet and pawl mechanism to hold the projector angle. The optical assembly can then be adjusted to get the image aligned with the workspace.

---

# 7. Control panel

The control panel is another thing i scrapped and saved 0.00001$

It uses:

- Arduino Uno
- Ender 3 LCD (if u dont have this , uh get a normal LCD of simmilar size and adjust CAD accordingly)
- 3.5 inch 4 wire resistive touchscreen
- TSC2046 touch controller (needed for the above)

Mount the touchscreen over the display and connect the touch controller to the Arduino.

The Arduino handles the control panel and communicates with the Pi.

---

# 8. Airtight

Some parts need to be airtight, but printing all of them in SLA would be WAY WYA WYAYW YAYWYWYAYAYY too expensive.

Instead, print the part in PLA and coat it with UV resin.

Then slowly rotate the part while curing it under the UV lights. This should give an even coating while letting us control the curing time.

Test the process on a small part first before doing important parts.
^
|
OK SO THIS IDEA IS WHAT ESHANT TOLD ME, IF IT DOESNT WORK GG FOR US

---

# 9. Final assembly

Once the individual parts work:

1. Finish the mechanical grid.
2. Install the threaded rods and motors.
3. Install the pumps, tubing and pressure sensors.
4. Connect the ESP32 motor control.
5. Connect the Raspberry Pi 5.
6. Install the cameras and ArUco markers.
7. Assemble the projector.
8. Add the control panel.
9. Run the software and calibrate the workspace.

AGAIN TO REITERATE -> The first milestone should be one complete working cell. Once that works, scale it up to the full 10x10 surface!!
