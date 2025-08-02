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


## Get the catgpt source code.  
Create or cd into your projects directory.
Clone the repository from github. It will create the catgpt directory and put the code inside it.

`git clone https://github.com/louisroehrs/catgpt.git`

`cd catgpt`

The catgpt source code includes tests so that we can verify each step of the process and the relevant hardware connections.

Check the version of python that should already be installed with the Raspberry Pi OS.

`python --version`

It should be version 3.9.2 or higher.

## CatGPT architecture

We will now take a paws and explain the architecture.

There are three parts to making a cat talk.

First, he needs to listen and translate the audio to text.  We will use Google Speech-to-Text for that.  Free as of this writing with no need for an API key.

Then, he needs to use his brain.  For this part, we will send the text as a prompt with some system instructions to the LLM of our choice.  Here we are using the hosted OpenAI service.  Do not get too personal with the cat if you are using a hosted LLM as Microsoft and the world will be listening in.  This software is using OpenAI and you will need to set and export your OpenAI Api Key as an environment variable OPENAI_API_KEY.

Next, we will get back a text response and the cat will need to speak it.  We will use the Google Text-to-Speech service, gTTS.

## Install the sound drivers for the OS and the python libraries to connect to them.

The great thing is that there are python libraries that support all of these steps.

The first thing we need to do is install some libraries at the OS level to support this.

We will be using the Python library ‘pyaudio’ to record and play audio data from the USB mic. Before we can get started with ‘pyaudio,’ we need to ensure that the RPi has all the necessary prerequisites by installing the following packages:  This code will use the alsa sound drivers and mpg123 to play the response.

`sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev flac`
`sudo apt install alsa-utils`
`sudo apt install mpg123`

Next we can install the python libraries.

Do a pip install to get them all.

`pip install -r requirements.txt`

## Configure the audio

### Find the device id for the USB Audio Device

Now we need to configure the audio.  The python code refers to the audio device using an index such as 0, 1, 2.  We need to find that index and set it.

Run the following script to find the device id for the USB AUdio Device.

`python find_device_id.py`

You may see a bunch of ALSA messages, let that scroll.

At the bottom you should see an indexed list of audio devices.

Find the line that mentions the USB Audio Device and note the number preceding the device name; that is the index number.

Now we can configure the Raspberry Pi Audio.

## Configure the Raspberry Pi Sound Settings

We will edit the OS configuration files. You may need to start your editor with `sudo` to edit these files.

In `/etc/modprobe.d/alsa-base.conf`

add the line:

`options snd-usb-audio index=<index number>`

where \<index number\> is the index found in the previous section.

Example:

`options snd-usb-audio index=1`


In `/etc/asound.conf`

add:

```
defaults.pcm.card <index number>
defaults.ctl.card <index number>
```
where \<index number> is the index found in the previous section.

Example:
```
defaults.pcm.card 1
defaults.ctl.card 1
```

Then reboot the raspberry pi for the settings to take effect.

`sudo reboot`

## Setup your open api key.

For ease of use and the ability to have the Raspberry Pi start up and beginning talking without using a keyboard, monitor, and mouse, it is recommended to set the OPENAI_API_KEY in file that can be sourced.

To do this, create a file called `.bash_profile` in the user's root directory and add the following line, replacing the \<your openai api key> with your key:
`export OPENAI_API_KEY=<your openai api key>`



## Let's give it a go!

Run `./start.sh`.

You may see lots of ALSA output and then the line:

`Listening for a question...`

Pick up and speak into the mic slowly your question and pause.

The next line should read 

`CATCAT Recognizing...`

And if the speech is recognized it should say:

`CATCAT Question: <an interpretation of your question from the speech recognizer>`

If you see instead:

`CATCAT Sorry, I did not understand that`

it means that the sound did get sent to Google and Google could not translate it into text.  You may want to speak slower, closer to the microphone and in a quieter location.

Give it a couple of tries.

If you got the line showing `Question`, you should see a line beginning with:
`CATCAT Answer: <your answer with a possible MEOW included>`

If not, check to make sure your OPENAI_API_KEY is set correctly in the ~/.bash_profile file.

If you see: `sh: 1: mpg123: not found`, do `sudo apt install mpg123`

To quit the program, type a `CTRL-c` once or twice.

# Troubleshooting.

On the Raspbarry Pi desktop, make sure the speaker volume is set to maximum.

Make sure the microphone input is set to USB Audio Device.

# Make it run on startup.

We have already created a service file at catgpt.service in the same directory.

Change to the catgpt directory and run the following to make the service start up on boot.

```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable myscript.service
```

This will add the file into `/etc/systemd/system/multi-user.target.wants/catgpt.service`

Now you can start the service with either:

`sudo systemctl start myscript.service`

or reboot.

`sudo reboot`

Remember, though, the cats will listen and consume your money at openai.com while running.  But this will let you run the cats headless.

To see the logs:

`journalctl -u myscript.service -b`

Breakdown:

 -u myscript.service: filters for your service

 -b: only show logs from this boot

You can follow logs in real time with:

`journalctl -u myscript.service -f`


# References


* https://makersportal.com/blog/2018/8/23/recording-audio-on-the-raspberry-pi-with-python-and-a-usb-microphone
