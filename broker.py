import paho.mqtt.client as mqtt
import json
import sqlite3
import time
from detect import generate_recognized_image

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("frigate/events")


def on_message(client, userdata, msg):
    
    payload = msg.payload.decode()

    # print(f"Received message '{msg.payload.decode()}' on topic '{msg.topic}' with QoS {msg.qos}")
    
    try:
        data = json.loads(payload)
        print("Payload as JSON:", data)

        # Accessing the 'id' of 'before'
        before_id = data.get('before', {}).get('id', None)
        if before_id:
            print("ID of 'before':", before_id)

            if 'person' in data.get('before', {}).get('label', None):
                print("Person detected!")

                handle_person_detected(data)

                # need to alter later
                event_id = before_id
                print("event_id", event_id)

                process_event(event_id)

    except json.JSONDecodeError:
        print("Payload is not in JSON format")

    if 'motion' in payload:
        print("Motion detected!")

def handle_person_detected(data):

    print("Handling person detection with data:", data)

    if 'bbox' in data:
        print("Bounding bos coordinates:", data['bbox'])

# def getEventsFromDB(event_id):
#     frigate_db_con = sqlite3.connect('/home/admin/config/frigate.db')
#     cursor = frigate_db_con.cursor()
#     cursor.execute(f"SELECT * FROM event WHERE id='{event_id}'")
#
#     rows = cursor.fetchall()
#     for row in rows:
#         print(row)
#
#     cursor.execute("PRAGMA table_info(event)")
#     columns = [column[1] for column in cursor.fetchall()]
#
#     # fields to be added.
#     fieldsToBeAdded = ['recording_path', 'face', 'recognized_path']
#
#     for fieldName in fieldsToBeAdded:
#         if fieldName not in columns:
#             cursor.execute(f"ALTER TABLE event ADD COLUMN {fieldName} TEXT")
#             print(f"Column '{fieldName}' added.")
#
#     face_name = generate_recognized_image(
#         f'/home/admin/storage/clips/GarageCamera-{event_id}.jpg',
#         f'/home/admin/storage/clips/GarageCamera-{event_id}-rec.jpg'
#     )
#
#     cursor.execute("""
#         UPDATE event
#         SET recording_path = (
#             SELECT path
#             FROM recordings
#             WHERE event.start_time >= recordings.start_time
#               AND event.start_time <= recordings.end_time
#             ORDER BY recordings.start_time DESC
#             LIMIT 1
#         )
#         WHERE id = ? AND EXISTS (
#             SELECT 1
#             FROM recordings
#             WHERE event.start_time >= recordings.start_time
#               AND event.start_time <= recordings.end_time
#         );
#     """, (event_id,))
#
#     # update the recognized path
#     cursor.execute("""
#         UPDATE event
#         SET recognized_path = ?, face = ?
#         WHERE id = ?;
#     """, (f'/home/admin/storage/clips/GarageCamera-{event_id}-rec.jpg', face_name, event_id))
#
#     frigate_db_con.commit()
#     frigate_db_con.close()


def process_event(event_id):

    time.sleep(5)

    name = generate_recognized_image(
        f'/home/admin/storage/clips/GarageCamera-{event_id}-clean.png',
        f'/home/admin/storage/clips/GarageCamera-{event_id}-rec.jpg'
    )
    print("name", name)
    publish_face_labels(client, name, topic)

    # Open connection to the existing Frigate database
    frigate_db_con = sqlite3.connect('/home/admin/config/frigate.db')
    cursor = frigate_db_con.cursor()

    # Fetch event data
    cursor.execute("SELECT id, label, camera, sub_label, score, top_score FROM event WHERE id = ?",
                   (event_id,))
    event_data = cursor.fetchone()

    # Fetch recording data where the event falls within the recording duration
    cursor.execute("""
        SELECT id, path, start_time, end_time, duration FROM recordings
        WHERE start_time <= (SELECT start_time FROM event WHERE id = ?)
          AND end_time >= (SELECT end_time FROM event WHERE id = ?)
    """, (event_id, event_id))
    recording_data = cursor.fetchall()

    # Close connection to the Frigate database
    frigate_db_con.close()

    # Create and connect to the new Events database
    events_db_con = sqlite3.connect('/home/admin/config/events.db')
    events_cursor = events_db_con.cursor()

    # Create tables if they don't exist
    events_cursor.execute("""
        CREATE TABLE IF NOT EXISTS event (
            id TEXT, label TEXT, camera TEXT, sub_label TEXT, score REAL, 
            top_scor REAL
        )
    """)
    events_cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id TEXT, path TEXT, start_time TEXT, end_time TEXT, duration REAL
        )
    """)

    # Insert data into the new database
    events_cursor.execute("INSERT INTO event VALUES (?, ?, ?, ?, ?, ?)", event_data)
    events_cursor.executemany("INSERT INTO recordings VALUES (?, ?, ?, ?, ?)", recording_data)
    events_db_con.commit()
    events_db_con.close()


# event_id = '1720132207.804948-3r5wOf'
# getEventsFromDB(event_id)
# process_event(event_id)


def publish_face_labels(client, label, topic):
    message = json.dumps({"label": label})
    client.publish(topic, payload=message)
    print(f"Published {label} to {topic}")


topic = "frigate/facenet/faces"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("admin", "1BeachHouse@2023")

client.connect("192.168.0.63", 1883, 60)

# label = "unknown"
#
# publish_face_labels(client, label, topic)

client.loop_forever()
