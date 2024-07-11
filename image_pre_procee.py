import cv2
import numpy as np
import os


def filter_resize(image):
    # Create a sharpening kernel
    kernel = np.array([[-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1]])

    processed_image = cv2.filter2D(image, -1, kernel)
    final_image = cv2.medianBlur(processed_image, 5)
    # cv2.imshow('processed', blurred_image)
    height, width = final_image.shape[:2]

    # Define the new width (for example, increasing by 50%)
    new_width = int(width * 2)

    # Resize the image
    resized_image = cv2.resize(final_image, (new_width, height), interpolation=cv2.INTER_LINEAR)

    return final_image


def auto_exposure(image):
    # Convert to Lab color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Split the channels
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L-channel
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)

    # Merge the CLAHE enhanced L-channel back with a and b channels
    lab_clahe = cv2.merge((l_clahe, a, b))

    # Convert back to RGB color space
    image_clahe = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    return image_clahe


def histogram_equlization(image):
    # Convert the image to YUV color space
    yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)

    # Apply histogram equalization to the luminance channel (Y channel)
    yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])

    # Convert the image back to BGR color space
    equalized_image = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    return equalized_image


def adjust_brightness_contrast(image, alpha=1.0, beta=50):
    """
    Adjust the brightness and contrast of an image.
    alpha: Contrast control (1.0-3.0).
    beta: Brightness control (0-100).
    """
    adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return adjusted


def process_image(img_path, output_path):
    # Read the image
    image = cv2.imread(img_path)

    # Here you can apply your existing processing function
    # For example, let's say you have a function called histogram_equalization
    processed_image = histogram_equlization(image)
    # processed_image = adjust_brightness_contrast(processed_image_1)

    # Construct the output path with the file name and an extension
    output_file_path = os.path.join(output_directory, os.path.basename(img_path))

    cv2.imwrite(output_file_path, processed_image)


# Specify the directory containing the images
image_directory = 'images'
output_directory = 'processed'

# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Loop through all files in the directory
for filename in os.listdir(image_directory):
    # Check for file extension
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        file_path = os.path.join(image_directory, filename)
        process_image(file_path, output_directory)
        print(f'Processed {filename}')

print("done")
