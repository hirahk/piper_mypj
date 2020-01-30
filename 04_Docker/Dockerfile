FROM python:3

ENV DEBCONF_NOWARNINGS yes

RUN apt-get update
RUN apt-get install -y portaudio19-dev

RUN pip install requests
RUN pip install pyaudio
RUN pip install wave
RUN pip install numpy
RUN pip install opencv-python
RUN pip install datetime
RUN pip install paho-mqtt

ADD capture_video_fft_mqtt.py /var/lib/app/

WORKDIR /var/lib/app/

CMD [ "python", "-u", "./capture_video_fft_mqtt.py" ]