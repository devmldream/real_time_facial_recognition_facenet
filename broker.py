import paho.mqtt.client as mqtt
import json
import sqlite3
from detect import generate_recognized_image

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("frigate/events")

def on_message(client, userdata, msg):
    
    payload = msg.payload.decode()

    print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}' with QoS {msg.qos}")
    
    try:
        data = json.loads(payload)

        if 'person' in data.get('label', ''):
            print("Person detected!")

            handle_person_detected(data)

            # need to alter later
            event_id = data.get('event_id')
            event_id = '1720130351.981161-u1vlel'

        print("Payload as JSON:", data)

    except json.JSONDecodeError:
        print("Payload is not in JSON format")


    if 'motion' in payload:
        print("Motion detected!")

def handle_person_detected(data):

    print("Handling person detection with data:", data)

    if 'bbox' in data:
        print("Bounding bos coordinates:", data['bbox'])

def getEventsFromDB(event_id):
    frigate_db_con = sqlite3.connect('/home/admin/config/frigate.db')
    cursor = frigate_db_con.cursor()
    cursor.execute(f"SELECT * FROM event WHERE id='{event_id}'")

    rows = cursor.fetchall()
    for row in rows:
        print(row)

    generate_recognized_image(
        f'home/admin/storage/clips/GarageCamera-{event_id}.jpg',
        f'home/admin/storage/clips/GarageCamera-{event_id}-rec.jpg'
    )

    frigate_db_con.close()



event_id = '1720130351.981161-u1vlel'
getEventsFromDB(event_id)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("admin", "1BeachHouse@2023")

client.connect("192.168.0.63", 1883, 60)
client.loop_forever()
