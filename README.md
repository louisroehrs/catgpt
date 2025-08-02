https://makersportal.com/blog/2018/8/23/recording-audio-on-the-raspberry-pi-with-python-and-a-usb-microphone

lsusb -t



This output lets us know the Pi is reading the USB microphone because of its response: “Class=Audio, Driver=snd-usb-audio” - and if you are seeing a similar response, then congratulations! Your USB mic is ready to go. The Pi isn’t quite ready to use the USB mic, but I will discuss this in the next section.

We will be using the Python library ‘pyaudio’ to record and play audio data from the USB mic. Before we can get started with ‘pyaudio,’ we need to ensure that the RPi has all the necessary prerequisites by installing the following packages:

sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev

If the above is successful, then we can download the ‘pyaudio’ library (I’m installing to Python 3.x with ‘pip3’):

sudo pip3 install pyaudio

Assuming the two installs above have been successful, open Python 3.x and import pyaudio. If everythin has been successful, we are ready to head to the next section and ensure that the USB mic is functioning and the Pi has selected the correct device.

Testing the USB Mic and Pyaudio

do python3 and use the interactive thing.


import pyaudio
p = pyaudio.PyAudio()
for ii in range(p.get_device_count()):
    print(p.get_device_info_by_index(ii).get('name'))

Get lots of stuff and then:

vc4-hdmi: MAI PCM i2s-hifi-0 (hw:0,0)
USB PnP Sound Device: Audio (hw:1,0)
sysdefault
hdmi
pulse
default

Take a note of the index.   In this case, it is 1 (the second in the list)


So, let's try a newer page....


https://thelinuxcode.com/record-audio-with-raspberry-pi/

sudo nano /boot/config.txt



sudo apt install alsa-utils
alsamixer

install an editor:
sudo apt install audacity


sound card properties and capabilities:

cat /proc/asound/cards

Choosing an available card and looking at its capabilities :

cat /proc/asound/card1/stream0



for espeak:


sudo apt update && sudo apt install espeak-ng libespeak1



forget espeak,  trying piper ....

pip install piper-tts

pip[er wont work on raspberry pi 2 according to docs...


trying google tts gTTS....


sudo apt install mpg123

pip install gTTS


gtts-cli --all shows all the languages....



RASPBERRY PI SOUND SETTINGS:


In /etc/modprobe.d/alsa-base.conf

add:
options snd-usb-audio index=1

In /etc/asound.conf

add:
defaults.pcm.card 1
defaults.ctl.card 1

Then
sudo reboot




Before running the script, do:

. ~/.bash_profile

  to set the open ai key

then:

python3 catgptgoogle.py



Rebootable service:

using systemctl with /lib/systemd/system/catgpt.service


# Talking and Dancing CatGPT

## Overview

Written for the Raspberry Pi 2 Model B in python and Raspberry Pi OS as of June 30, 2025, this code will automate a dancing cat.  When the cat speaks, it dances. Otherwise, it listens attentively to what you say.  When you are done speaking, it will respond.

It uses google services for the speech-to-text and the text-to-speech conversion and OpenAI for generating responses to the questions. 

## Requirements for Dancing Cat Mode

Once the Raspberry Pi is setup, this is all that is needed to make the Dancing Cat go.

1. Raspberry Pi 2 Model B and 5V 2Amp power supply.
1. SD Card for Raspberry Pi
2. Ethernet adapter for the Raspberry Pi.  Tested with EdiMax wireless mini-dongle
2. USB Audio Device that will provide audio output and microphone input.  This software is set to use 44100Hz data rate and maybe change to match your audio device.
3. Microphone that plugs in to the USB Audio Device.  Ideally, the microphone should be able to pick up your voice at some distance for best effect of a listening cat.  Otherwise, you will need to hold the microphone close to the speaker's mouth.
4. Speaker.  The Dancing Cat supplies the speaker and amplifier that should be connected to the USB Audio Device audio output port to speak the responses.
5. Batteries for Dancing Cat.
6. Dancing Cat from EBay (or an amplified speaker and a robot of your choice)
6. You will need an Open AI Api Key to use this software.

## Requirements for setting up the Raspberry Pi

In addition to the above, you will need:
1. USB Keyboard plugged into the Raspberry Pi
2. USB Mouse plugged into the Raspberry Pi
3. HDMI Monitor plugged into the Raspberry Pi with HDMI - HDMI cable.

# Setup

Assemble the Rapsberry Pi with USB Mouse, USB Keyboard, USB Network adapter or Ethernet connected to the Internet, USB Audio device with mic and speaker (dancing cat) plugged in.

## SD Card

Use the official Raspberry Pi imager at https://www.raspberrypi.com/software/ to image the SD card on any machine that runs the imager and supports SD cards. I selected this version of the OS in the imager:
`Raspberry Pi OS (Legacy, 32-bit) A port of Debian Bullseye with security updates and desktop environment.  Released 2025-05-06.`

Put the SD Card into the Raspberry Pi.

## Power up
Plug the Raspberry Pi in to power (the mains, as the Brits call it).
It should startup and present a desktop interface.

## Connect to the internet.

Make sure the Ethernet cable or wifi dongle is connected to the Raspberry Pi. It should setup plug and play style.  For wifi, it should show a wireless icon at the top right of the desktop.  Click that to select a wifi network that is connected to the internet.  

## Setup the software.

You will need to be connected to the internet to proceed.

Open a terminal window by click the >_ icon on the top left of the screen.
We will be doing most of the work in the terminal.

Let's get the latest and greatest Raspberry Pi OS.  This was done June 31, 2025\
 for these instructions.

`sudo apt full-upgrade`

You will need your favorite text editor to continue. `nano` and `vi` are installed. `emacs` is not. I use emacs...

If you want emacs, install it with:
`sudo apt-get install emacs`

Open emacs with `emacs -nw` if you want to edit in the terminal window instead of the X display window.


Get the catgpt source code.  Create or cd into your projects directory.
Clone the repository from github. It will create the catgpt directory and put the code inside it.

`git clone https://github.com/louisroehrs/catgpt.git`

`cd catgpt`



Configure Raspberry Pi Audio to work with a plugin USB sound device that will s\
upport a 3.5mm microphone input and a 3.5mm audio output.  This involves config\
uring the alsa sound drivers.

Python comes installed as part of Raspberry OS.  We are using python 3.9.2.  Ch\
eck python version with:

`python version`

There are three parts to making a cat talk.

First, he needs to listen and translate the audio to text.  We will use google \
for that.

Then, he needs to use his brain.  For this part, we will send the text as a pro\
mpt with some system instructions to the LLM of our choice.  Here we are using \
the hosted OpenAI service.  Do not get personal with the cat as Microsoft and t\
he world will be listening in.

Next, we will get back a text response and the cat will need to speak it.  We w\
ill use the Google Text-to-Speech service, gTTS.

The great thing is that there are python libraries that support all of these st\
eps.

The first thing we need to do is install some libraries at the OS level to supp\
ort this.

We will be using the Python library ‘pyaudio’ to record and play audio data fro\
m the USB mic. Before we can get started with ‘pyaudio,’ we need to ensure that\
 the RPi has all the necessary prerequisites by installing the following packag\
es:

sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-d\
ev flac
sudo apt install alsa-utils
sudo apt install mpg123


Next we can install the python libraries.

Do a pip install to get them all.

`pip install -r requirements.txt`

Now we need to configure the audio.  The python code refers to the audio device\
 using an index such as 0, 1, 2.  We need to find that index and set it.


Testing the USB Mic and Pyaudio

do python3 and use the interactive thing.


import pyaudio
p = pyaudio.PyAudio()
for ii in range(p.get_device_count()):
    print(p.get_device_info_by_index(ii).get('name'))












