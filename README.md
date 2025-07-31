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

