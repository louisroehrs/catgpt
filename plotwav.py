import scipy.io.wavfile as wavfile
import numpy as np
import matplotlib.pyplot as plt

sampling_freq, audio = wavfile.read('recording.wav')

plt.plot(audio)
plt.title('Waveform')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.show()
