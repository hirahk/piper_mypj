import paho.mqtt.client as paho
import time
from datetime import datetime

save_path = "./videos/"

def on_connect(mqttc, obj, rc):
    mqttc.subscribe("$SYS/#", 0)
    print("rc: "+str(rc))

def on_message(mqttc, obj, msg):
    print(msg.topic+" "+str(msg.qos))
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".mp4"
    with open(save_path + filename, "wb") as outfile:
        outfile.write(msg.payload)
    outfile.close()

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)


if __name__ == '__main__':

    mqttc = paho.Client()
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe


    # mqttc.connect("mqtt.eclipse.org", 1883, 60)
    # mqttc.connect("test.mosquitto.org", 1883, 60)
    mqttc.connect("localhost", 1883, 60)

    mqttc.subscribe("your_mqtt_topic", 0)
    mqttc.loop_forever()