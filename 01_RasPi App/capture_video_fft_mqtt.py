# Capture video with FFT processing signal detection

import requests
import subprocess
import json
import pyaudio
import wave
import numpy as np
import cv2
import time
from datetime import datetime
import paho.mqtt.client as paho

# Initialize video capture
camera = cv2.VideoCapture(0)

# Video format
fps = int(camera.get(cv2.CAP_PROP_FPS))                    # Get FPS from camera
w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))              # Get frame width
h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))             # Get frame height
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')        # Set fourcc for mp4

# Path for video files
save_path = "./videos/"

# Set capturing frames (fps x sec)
set_time = 15 
maxframe = fps * (set_time + 1)

# Audio format 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024 * 2
l = 10 ** 7
sound_count = 0
 
data1 = []
data2 = []

freqList = np.fft.fftfreq(int(1.5 * RATE / CHUNK) * CHUNK * 2, d = 1.0 / RATE)

# Webhook URL for slack
SLACK_URL = "your_slack_url"

def send_slack(msg):
    payload = {
        "text": msg,
        "icon_emoji": ':robot_face:',
    }
    data = json.dumps(payload)
    requests.post(SLACK_URL, data)

def video_capture(filename):
    framecnt = 1
    video = cv2.VideoWriter(save_path + filename , fourcc, fps, (w, h))
    while True:
        ret, frame = camera.read() # Get frame
        # cv2.imshow('camera', frame) # Display frame
        video.write(frame) # Save frame to video file
        framecnt = framecnt + 1
        if framecnt >= maxframe:
            print("Video captured")
            break

def send_image_mqtt(filename):
    # cmdline=['mosquitto_pub','-h','https://mqtt.eclipse.org/','-q','1','-t','your_mqtt_topic','-f',save_path+filename]
    cmdline=['mosquitto_pub','-h','your_mqtt_host','-q','1','-t','your_mqtt_topic','-f',save_path+filename]
    try:
        subprocess.check_call(cmdline)
        print ("Transfer finished.")
    except:
        return "Transfer failed."

# Main program

p = pyaudio.PyAudio()
stream = p.open(format = FORMAT,
            channels = CHANNELS,
            rate = RATE,
            frames_per_buffer = CHUNK,
            input = True,
            output = False)
 
try:
    while stream.is_active():
        for i in range(int(1.5 * RATE / CHUNK)):
            d = np.frombuffer(stream.read(CHUNK, exception_on_overflow = False), dtype='int16')
            if sound_count == 0:
                data1.append(d)

            else:
                data1.append(d)
                data2.append(d)
 
        if sound_count >= 1:
            if sound_count % 2 == 1:
                data = np.asarray(data1).flatten()
                fft_data = np.fft.fft(data)
                data1 = []

            else:
                data = np.asarray(data2).flatten()
                fft_data = np.fft.fft(data)
                data2 = []
 
            fft_abs = np.abs(fft_data)

            #850Hz付近の周波数成分
            data850 = fft_abs[np.where((freqList < 900) & (freqList > 800))]
            #1700Hz付近の周波数成分
            data1700 = fft_abs[np.where((freqList < 1750) & (freqList > 1650))]

            print("850Hz: " + str(data850.max()) + \
            ", 1700Hz: " + str(data1700.max()))

            #850Hzと1700Hz付近の強度が一定以上なら、インターホンと判断
            if (data850.max() > 0.15 * l) & (data1700.max() > 0.01 * l): 
                print("Sounds detected")
                filename = "tmpvideo.mp4"
                video_capture(filename)
                send_image_mqtt(filename)
                # send_slack("誰か来たよ！ビデオを撮影しておいたよ！！")

                data1 = []
                data2 = []
                sound_count = 0

        sound_count += 1
 
except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
    camera.release()
    cv2.destroyAllWindows()
