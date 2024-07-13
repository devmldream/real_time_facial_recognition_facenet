import cv2 
import numpy as np
import mtcnn
from architecture import *
from train_v2 import normalize,l2_normalizer
from scipy.spatial.distance import cosine
from tensorflow.keras.models import load_model
import pickle
import os

from image_pre_procee import process_image


confidence_t=0.99
recognition_t=0.5
required_size = (160,160)

def get_face(img, box):
    x1, y1, width, height = box
    x1, y1 = abs(x1), abs(y1)
    x2, y2 = x1 + width, y1 + height
    face = img[y1:y2, x1:x2]
    return face, (x1, y1), (x2, y2)

def get_encode(face_encoder, face, size):
    face = normalize(face)
    face = cv2.resize(face, size)
    encode = face_encoder.predict(np.expand_dims(face, axis=0))[0]
    return encode


def load_pickle(path):
    with open(path, 'rb') as f:
        encoding_dict = pickle.load(f)
    return encoding_dict

def detect(img ,detector,encoder,encoding_dict):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = detector.detect_faces(img_rgb)
    name = ''
    for res in results:
        if res['confidence'] < confidence_t:
            continue
        face, pt_1, pt_2 = get_face(img_rgb, res['box'])
        encode = get_encode(encoder, face, required_size)
        encode = l2_normalizer.transform(encode.reshape(1, -1))[0]
        name = 'unknown'

        distance = float("inf")
        for db_name, db_encode in encoding_dict.items():
            dist = cosine(db_encode, encode)
            if dist < recognition_t and dist < distance:
                name = db_name
                distance = dist

        if name == 'unknown':
            cv2.rectangle(img, pt_1, pt_2, (0, 0, 255), 2)
            cv2.putText(img, name, pt_1, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
        else:
            cv2.rectangle(img, pt_1, pt_2, (0, 255, 0), 2)
            cv2.putText(img, name + f'__{distance:.2f}', (pt_1[0], pt_1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 200, 200), 2)
    return img, name


def generate_recognized_image(source_img_path, save_path):
    img_path = process_image(source_img_path, )
    required_shape = (160, 160)
    face_encoder = InceptionResNetV2()
    path_m = "facenet_keras_weights.h5"
    face_encoder.load_weights(path_m)
    encodings_path = 'encodings/encodings.pkl'
    face_detector = mtcnn.MTCNN()
    encoding_dict = load_pickle(encodings_path)

    # img = cv2.imread('IMG_9520.PNG')
    img = cv2.imread(img_path)

    if img is None:
        print("Image not loaded. Check the path.")
    else:
        image, name = detect(img, face_detector, face_encoder, encoding_dict)

        screen_res = 1280, 720  # Example screen resolution, adjust as needed
        scale_width = screen_res[0] / image.shape[1]
        scale_height = screen_res[1] / image.shape[0]
        scale = min(scale_width, scale_height)
        window_width = int(img.shape[1] * scale)
        window_height = int(img.shape[0] * scale)

        resized_image = cv2.resize(image, (window_width, window_height))
        # cv2.imshow('Resized Image', resized_image)
        #
        # # cv2.imshow('camera', image)
        # cv2.waitKey(0)  # Wait indefinitely for a key press
        # cv2.destroyAllWindows()  # Close all OpenCV windows
        # print("Window closed. Exiting program.")

        result = cv2.imwrite(save_path, resized_image)
        if result:
            print(f"Image successfully saved at {save_path}.jpg")
        else:
            print("Failed to save the image.")

        print("name", name)
        if name is None:
            name = "Unkown"
        return name

    # # Load your video
    # input_video_path = 'path_to_your_input_video.mp4'
    # cap = cv2.VideoCapture(input_video_path)
    #
    # # Check if video opened successfully
    # if not cap.isOpened():
    #     print("Error opening video file")
    #     exit(1)
    #
    # # Setup Video Writer to save output
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec used to compress the frames
    # frame_width = int(cap.get(3))
    # frame_height = int(cap.get(4))
    # frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    #
    # output_video_path = os.path.join(save_dir, 'output_video.avi')
    # out = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (frame_width, frame_height))
    #
    # while cap.isOpened():
    #     ret, frame = cap.read()
    #
    #     if not ret:
    #         print("End of video file reached or can't fetch the frames")
    #         break
    #
    #     # Process the frame for face detection
    #     processed_frame = detect(frame, face_detector, face_encoder, encoding_dict)
    #
    #     # Display the frame
    #     cv2.imshow('Processed Video', processed_frame)
    #
    #     # Write the frame into the file 'output_video.avi'
    #     out.write(processed_frame)
    #
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    #
    # # Release everything when done
    # cap.release()
    # out.release()
    # cv2.destroyAllWindows()
    # print(f"Processed video is saved at {output_video_path}")

#
# # Specify the directory containing the images
# image_directory = 'processed'
# output_directory = 'recognized_4'
#
# # Create output directory if it doesn't exist
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)
#
# # Loop through all files in the directory
# for filename in os.listdir(image_directory):
#     # Check for file extension
#     if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
#         file_path = os.path.join(image_directory, filename)
#         generate_recognized_image(file_path, output_directory)
#         print(f'Processed {filename}')
#
# print("done")


# if __name__ == "__main__":
#     generate_recognized_image('images/20.jpg', '/home/artem/dev/project/Real-time-face-recognition-Using-Facenet')
