import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("frigate/GarageCamera/motion")

def on_message(client, userdata, msg):
    
    payload = msg.payload.decode()
   
    print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}' with QoS {msg.qos}")
    
    try:
        data = json.loads(payload)

        if 'person' in data.get('label', ''):
            print("Person detected!")

            handle_person_detected(data)

        print("Payload as JSON:", data)

    except json.JSONDecodeError:
        print("Payload is not in JSON format")


    if 'motion' in payload:
        print("Motion detected!")

def handle_person_detected(data):

    print("Handling person detection with data:", data)

    if 'bbox' in data:
        print("Bounding bos coordinates:", data['bbox'])

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("admin", "1BeachHouse@2023")

client.connect("192.168.0.63", 1883, 60)
client.loop_forever()
