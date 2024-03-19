import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from scipy.signal import resample
import time
import os
import pygame

class Synth:
    def __init__(self, window):
        self.window = window
        self.rate, self.data = None, None
        self.playback_thread = None

        # initializing the pygame mixer so that we can play multiple sounds on top of each other in different channels
        pygame.mixer.init()
        #makes sure we have enough channels for the echo
        pygame.mixer.set_num_channels(10)

        # Add file button
        ttk.Button(window, text="Select Audio File", command=self.load_file, width=15).pack(pady=5)
        
        # DEfault file button
        ttk.Button(window, text="Default Audio File", command=self.default_file, width=15).pack(pady=5)
        
        # Volume Control
        self.volume_scale = tk.Scale(window, from_=100, to=0, orient='vertical', label='Amplitude')
        self.volume_scale.set(50)
        self.volume_scale.pack(side='left', padx=5, pady=5)

        # Pitch Control
        self.pitch_scale = tk.Scale(window, from_=30, to=-30, orient='vertical', label='Pitch')
        self.pitch_scale.set(0)
        self.pitch_scale.pack(side='left', padx=5, pady=5)

        # Echo Control
        self.echo_scale = tk.Scale(window, from_=10, to=1, orient='vertical', label='Echo')
        self.echo_scale.set(1)
        self.echo_scale.pack(side='left', padx=5, pady=5)

    # Load default file
    def default_file(self):
        try:
            file_path = os.path.join(os.path.dirname(__file__), 'AudioFiles', 'default.wav')
            self.rate, self.data = wavfile.read(file_path)
            if self.data.dtype == np.int16:
                self.data = self.data.astype(np.float32, order='C') / 32768.0
            print(f"Loaded: {file_path}")
        except FileNotFoundError:
            print("Default file not found.")

    # Load selected file
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            try:
                self.rate, self.data = wavfile.read(file_path)
                if self.data.dtype == np.int16:
                    self.data = self.data.astype(np.float32, order='C') / 32768.0
                print(f"Loaded: {file_path}")
            except Exception as e:
                print(f"Error loading file: {e}")

    # Play audio
    def play(self):
        if self.data is not None:
            # this is the procedure for if the user has not selected echo
            if self.echo_scale.get() == 1:
                adjusted_data = self.apply_effects(self.data, self.volume_scale.get())
                sd.play(adjusted_data, self.rate)
            # this is the scenario where the user has decided they wanted echo
            elif self.echo_scale.get() > 1:
                echo_level = self.echo_scale.get()
                delay = 1 / echo_level
                # this resets the reaper variable to 0 in case it had been used to terminate the loop before
                self.reaper = 0
                # this loops plays the main sound and its echoes
                for i in range(echo_level):
                    print(i)
                    # this line sets the volume level to be successively lower for each echo
                    jonah = ((echo_level - i) / echo_level) * self.volume_scale.get()
                    adjusted_data = self.apply_effects(self.data, jonah)
                    # This line will turn the adjusted data back into a wav so that it can be played by pygame
                    wavfile.write('adjusted_data_wav', self.rate, adjusted_data)
                    # This line will turn the wav file for the adjusted data into a sound object for the pygame mixer
                    adjusted_data_wav_forpygame = pygame.mixer.Sound("adjusted_data_wav")
                    # now that we've done all of that, the pygame mixer can finally play our files in a free channel
                    pygame.mixer.find_channel().play(adjusted_data_wav_forpygame)
                    time.sleep(delay * 3)

    # stops whatever music might be playing, then proceeds to play new music
    def stop_and_play(self):
        self.stop()
        self.play()

    # stops music
    def stop(self):
        sd.stop()
        pygame.mixer.stop()

    # Apply any new effects
    # introducing the variable jonah to represent volume instead of volume_scale so that for the echo procedure
    # we can play each echo at decreasing volume without affecting the actual volume setting
    def apply_effects(self, data, jonah):
        volume = jonah / 100.0
        pitch_shift = self.pitch_scale.get()

        # Apply Volume
        data = data * volume

        # Apply Pitch (if pitch_shift is not zero)
        if pitch_shift != 0:
            new_length = int(data.shape[0] / (2 ** (pitch_shift / 12)))
            data = resample(data, new_length)

        return data

# gui setup
window = tk.Tk()
window.title("Synth!")
window.geometry("500x275")
synth = Synth(window)

ttk.Button(window, text="Apply Effects", command=synth.play, width=10).pack(pady=15)
ttk.Button(window, text="Stop", command=synth.stop, width=10).pack(pady=10)
ttk.Label(window, text='by Ian, Matteo, and Nick', font=('Arial', 8)).pack(pady=20)
window.mainloop()
