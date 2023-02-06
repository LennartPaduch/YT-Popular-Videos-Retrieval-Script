import requests
from concurrent.futures import ThreadPoolExecutor
import os

def download_image(thumbnail_to_download):
    # Create the folder for the video_id if it doesn't exist
    folder_path = f"thumbnails/{thumbnail_to_download['video_id']}"
    os.makedirs(folder_path, exist_ok=True)
    name = f"{folder_path}/{thumbnail_to_download['iteration']}.jpg"
    response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/maxresdefault.jpg")
    if response.status_code != 200:
        response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/hqdefault.jpg")
        if response != 200:
            response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/mqdefault.jpg")
    with open(name, 'wb') as f:
        f.write(response.content)


def download_images(thumbnails_to_download):
    with ThreadPoolExecutor() as executor:
        executor.map(download_image, thumbnails_to_download)

