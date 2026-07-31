REVIEWER NOTE: PLEASE read the final journal as it contains a lot of clarification

# BetterDesk

A workbench that can **see**, **understand** and **physically interact** with everything on your desk.

---

## What is BetterDesk?

BetterDesk is an interactive workbench designed to make building electronics, robotics, hardware projects, art, etc much easier and more importantly COOLER!

Instead of just sitting there like a normal desk, BetterDesk knows whats on your workspace using multiple cameras and computer vision. It can identify components, answer questions, guide you through builds, organize your parts and even **move objects around the desk itself** using a custom built programmable motion surface.

Its like a mix between an electronics workbench, an AI assistant like clawdbot, a giant programmable trackpad, and a pick and place machine but with conveyer built technology for real world objects.

I KNOW IT SOUNDS CONFUSING BUT TRUST ME you'll understand.

---

## Why?

We all have spend a lot of time building electronics projects and somehow always the desk, laptop and brain always jumble up into 1 confusing mess of switching between videos, pin outputs, code and the physical parts randomly getting lost in the jumble of jumper wires u refuse to untangle.

Current AIs can answer questions but they ofc can't actually interact with your physical workspace.

SO after not watching the iron man movie but instead watching a yt short summary about it. I realised...

**What if the desk could become jarvis?** 
not that the desk would start flying or whatever jarvis does. But what if it could see what you're building , help you by showing instructions ON the desk itself and move components for you. 

Instead of opening another browser tab, the desk should know what you're building, point at the correct components, organize everything automatically and even move parts around for you.

---

# 4 main parts:

### 1. The software:

Ok so this is the part that makes the entire project smart. We use 2 cameras -> 1 ipad camera and 1 iphone camera (in reality you would use smaller independant cameras but we dont have budget lol) which can basically see the entire desk area. The 2 cameras are then calibrated together to create a single 3D grid using simple triangulation from calibration. This helps improve depth perception while keeping the images clear.

After getting these pics, we trained a big YOLOv11 model on approximately 4000 pictures of manually annotated electric component pics, by doing this the we find the position of the electric components on the desk as it gives cords relative to the camera visible area. So as we place 4 Araku markers around the corners with some simple subtraction it knows the exact position. All of this with the image is sent to a GPT4o api call. It identifies whats generally happening and then we pair this with our voice assistant which is just a simple open AI whispr transcriber which sends the text to the same APi call and then the response is said outloud by elevenLabs.

BUT the main thing is since we have the position of the components we can draw bounding boxes around them and then draw boxes arrows and text to where the component should be placed/ already is placed and other instructions. Also i plan to implement a feature such that the AI can look up guides and show part of the website but before that i want the projector working first as it would be much easier to know where/when/how to place the instructions. SO all of this is planned to run on the main raspberry pi 5

---

### 2. The Projector:

The projector is probably one of the weirdest parts of the project. Instead of buying a normal projector (way too expensive ), we're building one completely from scratch. It uses a 50W COB LED as the light source, which is bright enough to project onto roughly a 50cm × 50cm workspace even in a reasonably lit room. Since a 50W LED gets ridiculously hot, it's mounted to an aluminium heatsink with a CPU cooler so nothing melts. The image itself comes from the LCD panel salvaged from an old broken tablet. We literally took the tablet apart, removed the LCD (and removed it from its backlight) and use it as the projector's imaging panel. A Raspberry Pi Zero drives the LCD through a TTL display controller board.

Light from the LED passes through a condenser lens, then through the tablet LCD, before being focused by a collector lens and finally projected using a larger projection lens. Because the projector can't be mounted directly above the desk, the entire optical assembly is mounted on an adjustable mechanism with a ratchet-and-pawl locking system. A stepper motor adjusts distances between the projector and collector lens. Every mount for the lenses, LCD, LED, cooling system and adjustment mechanism is being custom designed in CAD so everything stays aligned while still being as compact (and cheap) as possible. It definitely isn't the easiest way to build a projector but it's a lot more fun.

---

### 3. The Desk:

The desk movement system is one of the most complex parts of this project. It uses a grid of x and y belts moving with a suspended ball between them. A piston below the ball controls whether it touches the x belt on top or the y belt below. Each piston system is controlled in a sort of coordinate grid, in a grid formed by 10 x and 10 y pressure pipes running below the whole belt system. Suppose at a point, the system gets a positive pressure from the x pressure pipe and a positive pressure from the y pressure pipe. Then the ball moves up. If both pipes have negative pressure, the ball moves down. If both are opposite [like on positive and one negative], the ball stays stationary. The pressure in the pressure pipes are controlled by pumps, which are controlled by an ESP32. The ESP32 also controls the NEMA17 motors, which move the belts. There are a total 100 ball units, forming a grid of 10x10

---

### 4. The Control Panel:

Ok so for some basic controls like controlling volume and switching between modes. We are going to build a small control panel which will connect directly to the raspberry pi. Its made up of a touch sensor layer + the LCD screen from my ender3 + arduino uno.

---

# Gallery

---

## Full CAD Assembly of Desk

---


## Full CAD Assembley of Projector

---

## FULL Wiring Diagram

![Wiring](images/Wiring.png)

---

## Current Software
<p align="center">
  <img src="images/software.png" width="45%" />
  <img src="images/software2.png" width="45%" />
</p>

---

# Bill Of Materials

<!-- BOM_START -->

| Item | Specific part | Unit Price (inr) | Quantity | Total Price | URL | Running Total |
| --- | --- | --- | --- | --- | --- | --- |
| Balls | Polypropylene Balls | ₹5.00 | 110 | ₹550.00 | [Link](https://dir.indiamart.com/impcat/polypropylene-balls.html) | ₹550.00 |
| Belts | GT2 Toothed Belt Rubber Belt 5m | ₹699.00 | 4 | ₹2,796.00 | [Link](https://www.amazon.in/3DINNOVATIONS-Toothed-Abrasion-Resistance-Printers/dp/B09327BB7V?th=1) | "₹3,346.00" |
| Mosfets, Schottky diodes, Resistors | IRFZ44N IRF9540 BC547 | ₹0.00 | 10 | ₹0.00 |  | "₹3,346.00" |
| Motors | NEMA 13 STEPPER (already have from ender) | ₹0.00 | 4 | ₹0.00 |  | "₹3,346.00" |
| Motor driver | A4988 motor driver with heat sink | ₹699.00 | 1 | ₹699.00 | [Link](https://www.amazon.in/TESTIN-ELECTRONICS-Stepper-Heatsink-Printer/dp/B0GGTFJJT7) | "₹4,045.00" |
| Pumps | 6V to 12V Mini | ₹89.00 | 23 | ₹2,047.00 | [Link](https://quartzcomponents.com/products/12v-dc-1-2l-min-mini-vacuum-pump?srsltid=AfmBOoq1d-z9DCiYFECv1LNLPBb3ClF3fsWmVBt2qGRkRinZDS05aquH) | "₹6,092.00" |
| Pressure Sensor | BMP280 | ₹32.00 | 25 | ₹800.00 | [Link](https://www.flyrobo.in/bmp280-barometric-pressure-and-altitude-sensor-i2c-spi-module?srsltid=AfmBOopaK0VeQkgpDOZl1-qdyk8WUkgL2_zQ5x4lKVd9bb6Lktvidx93) | "₹6,892.00" |
| LED | 50W 32V Natural White SMD COB LED | ₹699.00 | 1 | ₹699.00 | [Link](https://probots.co.in/50w-32v-natural-white-smd-cob-led-rectangle-light.html) | "₹7,591.00" |
| Cooler | Cooler Master i30 CPU Cooler | ₹655.00 | 1 | ₹655.00 | [Link](https://www.amazon.in/Cooler-Master-i30-CPU-Aluminum/dp/B09V4PN9MX?source=ps-sl-shoppingads-lpcontext&smid=A1A1JBOUJEFFNA&th=1) | "₹8,246.00" |
| Condensor Lens | High Power LED 20-100W Lens | ₹300.00 | 1 | ₹300.00 | [Link](https://roboman.in/product/high-power-led-20-100w-lamp-bead-lens-44mm-optical-glass-lens-50-mm-reflective-collimator-fixed-bracket-60-120-degree-led-lens/) | "₹8,546.00" |
| Collector Lens | Convex Lens F20 D100 | ₹300.00 | 1 | ₹300.00 | [Link](https://www.amazon.in/ERH-India-Magnifier-Convex-Length/dp/B09BNTC9F5?source=ps-sl-shoppingads-lpcontext&psc=1&smid=A1KKHARUWH0JG) | "₹8,846.00" |
| Projector Lens | Convex Lens F10 D75 | ₹270.00 | 1 | ₹270.00 | [Link](https://www.amazon.in/Diameter-75-Science-Experiments-Projects-Microscopes/dp/B0C576XYVT?crid=378DJOR5RDQTX&dib=eyJ2IjoiMSJ9.jJLF1iHCvtPAbifj-IEcJvwmZKhfyjBUhp-5MPEKz8TykW9M1-aSITZ-6le2cAi5KoS2zFdlW54zPszDfxvu-MuEE7ZhdbVp4fCCVVYk7S1i1pGUlJTYhuSBYRYok8GqzpzrfwTCUk5D3NmVbHC-zPPoFq6ldOuNXy05ZWoQ9iwYUq6rrTB9mlPNi2SfBsWO.pA4xyLO7_SKg6Qjny2UQc4vraaFKkMVhhSD85HOlWA4&dib_tag=se&keywords=100+mm+focal+length+biconvex+lens&qid=1782578343&sprefix=100+mm+focal+length+biconvex+le,aps,273&xpid=PNhMk0UkOY3Z4) | "₹9,116.00" |
| LCD display without backlight | Eshants fart filled tablet | ₹0.00 | 1 | ₹0.00 |  | "₹9,116.00" |
| LED driver | 50W LED driver | ₹150.00 | 1 | ₹150.00 | [Link](https://makerbazar.in/products/50w-led-driver-1500ma-300ma-750ma) | "₹9,266.00" |
| 60 pin RGB TTL breakout board | FPC FFC 60 Pin Adapter | ₹101.00 | 1 | ₹101.00 | [Link](https://roboticsdna.in/product/fpc-60pin-cable-pitch-0-5mm-to-dip-pitch-2-54mm-smt-adapter-pcb-board/?srsltid=AfmBOor3ykh8ym4aLEzaiyzvzlYi7wKRnOwV8cFBtz1cFzFLhiNlyNFLD7E) | "₹9,367.00" |
| Controller of LCD screen | Raspberry Pi 0 | ₹1,299.00 | 1 | ₹1,299.00 | [Link](https://robu.in/product/raspberry-pi-zero-v1-3-development-board/?gad_source=1&gad_campaignid=17416544847&gclid=CjwKCAjwj7HTBhBiEiwA8s35OqpUuB_Rtrcf12BnWGZDf_nnS0EhUMToca90b4wwzxZxcTHOLFYC0xoCoKQQAvD_BwE) | "₹10,666.00" |
| Stepper Motors | 28BYJ-48 Stepper Motor + ULN2003 Driver | ₹139 | 4 | ₹560 | [Link](https://probots.co.in/28byj-48-stepper-motor-and-uln2003-stepper-motor-driver.html?gad_source=1&gad_campaignid=15283483193&gclid=CjwKCAjwj7HTBhBiEiwA8s35OrzTDwpKqhs8q5qIXjCfNBawpBMg9aN4UWgQbE17EbHu-wku3NBP2hoCDxgQAvD_BwE) | "₹11,226.00" |
| Control Board for motors | ESP32 | ₹500.00 | 2 | ₹1,000.00 | [Link](https://www.amazon.in/SquadPixel-ESP-32-Bluetooth-Development-Board/dp/B071XP56LM/ref=sr_1_2?crid=1DB18TWXHT64F&dib=eyJ2IjoiMSJ9.7tHski1_or_OvY6xQRgEf-AJs3OUhV7ZdzXc0Obc9YP4kvPpc1oLBq0zUI2L6Bp2U_VBEFeNf9hIrVxYdYFe37K9e0VbkSfFIqD6Y6qCfsuLKl8qhbuVtdeVOSWtOHLXVzhu2JNyNZH3XD5hzKNjKkNla6ZplYY5n4-MmLigt0Ebb92oEwiiH8Z1q0imSLV6gGBSj-8CMLMVlhlh0b4zoU0ahL15BUr0T4PDxCMF5Z_Oq-o4XBN4enprlz70zeRl6wINhQ2hitzAz5Ve_2aCB6IWtbic5sHp5GqzxWZrpX8.1SIQMXip-dlcwOIPKbZg0adfgNB8zQz2CRSgbj2aqoQ&dib_tag=se&keywords=esp32+devkit+v1&qid=1782751207&s=industrial&sprefix=esp32+dev%2Cindustrial%2C314&sr=1-2) | "₹12,226.00" |
| Main Control Board | Raspberry pi 5 | ₹0.00 | 1 | ₹0.00 |  | "₹12,226.00" |
| Springs | Stainless Steel Mini Compression Springs | ₹1.00 | 110 | ₹110.00 | [Link](https://www.indiamart.com/proddetail/mini-compression-springs-21559716612.html?utm_medium=prd_ads&utm_campaign=22486366449&utm_ad_group=202576351852&utm_content=product&utm_source=google&gclsrc=aw.ds&gad_source=1&gad_campaignid=22486366449&gclid=Cj0KCQjwr4jSBhCSARIsAOX1E-I4u_rEpNtxYpND3rpCS6pig6dCLbhtsXnaPAd6cAHMuX80MDCoqcYaAj8UEALw_wcB) | "₹12,336.00" |
| Camera (already have) | Web camera + ipad camera | ₹0.00 | 1 | ₹0.00 |  | "₹12,336.00" |
| SLA Printing | lots of parts | ₹0.00 | 1 | ₹0.00 |  | "₹12,336.00" |
| 3D Printing | lots of parts (cost negligible) | ₹0.00 | 1 | ₹0.00 |  | "₹12,336.00" |
| Control Panel Board | Arduino Uno | ₹0.00 | 1 | ₹0.00 |  | "₹12,336.00" |
| Control Panel Display | Scrapped from Ender 3 LCD | ₹0.00 | 1 | ₹0.00 |  | "₹12,336.00" |
| Control Panel Touchscreen | 3.5 inch 4 Wire Resistive Touch Screen Panel | ₹150.00 | 1 | ₹150.00 | [Link](https://kitsguru.com/products/3-5-inch-4-wire-resistive-touch-screen-panel?variant=40708852580533&country=IN&currency=INR.com) | "₹12,486.00" |
| Control Panel Touch controller | 5767 TSC2046 SPI Resistive Touch | ₹581.00 | 1 | ₹581.00 | [Link](https://www.fabtolab.com/adafruit-5767-tsc2046-spi-resistive-touch-screen-controller) | "₹13,067.00" |
|  |  |  |  | ₹0.00 |  | "₹13,067.00" |

<!-- BOM_END -->

---

# Future Plans

Ofc build the full thing in build review but also make software more capable than simply drawing boxes and arrows. But as i mentioned id prefer to do that after the projector is built so i can get a feel of how the instructions will look best

If You Want to run the code ,in the .env Please put an OpenAi key and a elevenlabs key and then run python src/core/detector.py