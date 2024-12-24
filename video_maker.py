import argparse

import cv2
import os

def make_video(image_folder: str, output_video: str, frame_rate: float = 5):

    image_files = sorted([img for img in os.listdir(image_folder) if img.endswith(".png")], key=lambda x: int(os.path.splitext(x)[0]))

    first_image_path = os.path.join(image_folder, image_files[0])
    print(first_image_path)
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
    video = cv2.VideoWriter(os.path.join(image_folder, output_video+".mp4"), fourcc, frame_rate, (width, height))

    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        frame = cv2.imread(image_path)
        video.write(frame)

    video.release()
    print(f"Video should be saved as {output_video}.mp4")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ECS Maze Runner Video Maker")

    parser.add_argument("image_directory", help='The absolute path to the directory containing the images.')
    parser.add_argument("output_name", help='The the file name of the generated video.')
    parser.add_argument("--frame_rate", help='The amount of time the image is displayed.', default=1.)

    args = parser.parse_args()

    print(args.image_directory, args.output_name, args.frame_rate)

    make_video(args.image_directory, args.output_name, float(args.frame_rate))