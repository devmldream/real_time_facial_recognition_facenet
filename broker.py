import paho.mqtt.client as mqtt
import json
import sqlite3
import time
import os
from detect import generate_recognized_image


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("frigate/events")


def on_message(client, userdata, msg):
    
    payload = msg.payload.decode()

    try:
        data = json.loads(payload)
        print("Payload as JSON:", data)

        # Accessing the 'id' of 'before'
        before_id = data.get('before', {}).get('id', None)
        if before_id:
            print("ID of 'before':", before_id)

            if 'person' in data.get('before', {}).get('label', None):
                print("Person detected!")

                # need to alter later
                event_id = before_id
                print("event_id", event_id)
                process_event(event_id)

    except json.JSONDecodeError:
        print("Payload is not in JSON format")

    if 'motion' in payload:
        print("Motion detected!")


def handle_person_detected(event_id):

    # Assuming the function generate_recognized_image returns the recognized name
    recognized_name = generate_recognized_image(
        f'/home/admin/storage/clips/GarageCamera-{event_id}-clean.png',
        f'/home/admin/storage/clips/GarageCamera-{event_id}-rec.jpg'
    )
    print("Recognized name:", recognized_name)
    return recognized_name


def setup_database(connection):
    """ Set up the database tables if they do not exist. """
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event (
            id TEXT PRIMARY KEY, 
            label TEXT, 
            camera TEXT, 
            sub_label TEXT, 
            score REAL, 
            top_score REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id TEXT PRIMARY KEY, 
            event_id TEXT,
            path TEXT, 
            start_time TEXT, 
            end_time TEXT, 
            duration REAL,
            FOREIGN KEY (event_id) REFERENCES event(id)
        )
    """)
    connection.commit()


def insert_event_if_not_exists(cursor, event_data):
    if len(event_data) != 6:
        print("Error: Incorrect number of data elements supplied for the event.")
        return

    cursor.execute("SELECT id FROM event WHERE id = ?", (event_data[0],))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO event (id, label, camera, sub_label, score, top_score) VALUES (?, ?, ?, ?, ?, ?)", event_data)
        print("Inserted new event:", event_data)
    else:
        print("Event already exists:", event_data[0])


def insert_recordings(cursor, recordings_data, event_id):
    """ Insert new recordings into the database. """
    for record in recordings_data:
        cursor.execute("SELECT id FROM recordings WHERE id = ?", (record[0],))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO recordings VALUES (?, ?, ?, ?, ?, ?)", (record[0], event_id) + record[1:])
            print("Inserted new recording for event_id:", event_id)


def process_event(event_id):

    path = f'/home/admin/storage/clips/GarageCamera-{event_id}-clean.png'
    if wait_for_file_creation(path):
        print("Proceed with file processing.")

        # Connect to the existing Frigate database
        frigate_db_con = sqlite3.connect('/home/admin/config/frigate.db')
        cursor = frigate_db_con.cursor()

        # Fetch event data
        cursor.execute("SELECT id, label, camera, score, top_score FROM event WHERE id = ?", (event_id,))
        event_data = cursor.fetchone()

        if event_data is None:
            print("No event data found for event_id:", event_id)
            return

        # Include recognized name as sub_label
        recognized_name = handle_person_detected({"event_id": event_id})  # Add more parameters if needed
        if recognized_name is None:
            print("No recognized name found for event_id:", event_id)
            return

        # Ensure the tuple has exactly 6 elements
        event_data_with_sub_label = (
        event_data[0], event_data[1], event_data[2], recognized_name, event_data[3], event_data[4])

        frigate_db_con.close()

        # Connect to the Events database
        events_db_con = sqlite3.connect('/home/admin/config/events.db')
        setup_database(events_db_con)
        events_cursor = events_db_con.cursor()

        # Insert the event and recordings into the database
        insert_event_if_not_exists(events_cursor, event_data_with_sub_label)
        events_db_con.commit()
        events_db_con.close()

        print("Event processing completed for:", event_id)

    else:
        print("File was not created in time.")


def publish_face_labels(client, label, topic):
    message = json.dumps({"label": label})
    client.publish(topic, payload=message)
    print(f"Published {label} to {topic}")


def wait_for_file_creation(file_path, timeout=300, check_interval=1):
    """
    Waits for a specific file to be created within a given timeout.

    Parameters:
    file_path (str): The path to the file to wait for.
    timeout (int): The maximum time to wait in seconds. Defaults to 300 seconds.
    check_interval (int): How often to check for the file in seconds. Defaults to 2 seconds.

    Returns:
    bool: True if the file is created within the timeout, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            print(f"File found: {file_path}")
            return True
        else:
            print(f"File not found: {file_path}, checking again in {check_interval} seconds.")
            time.sleep(check_interval)
    print(f"Timeout reached. File not found: {file_path}")
    return False


topic = "frigate/facenet/faces"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set("admin", "1BeachHouse@2023")

client.connect("192.168.0.63", 1883, 60)

client.loop_forever()
