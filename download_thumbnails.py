import requests
from concurrent.futures import ThreadPoolExecutor
import os

def download_image(thumbnail_to_download):
    """
    Downloads a single thumbnail image.

    :param thumbnail_to_download: A dictionary with keys 'video_id' and 'iteration'
    """
    # Create the folder for the video_id if it doesn't exist
    folder_path = f"thumbnails/{thumbnail_to_download['video_id']}"
    os.makedirs(folder_path, exist_ok=True)
    name = f"{folder_path}/{thumbnail_to_download['iteration']}.jpg"
    # Handle the case where maxresdefault thumbnail returns 404 error & placeholder image
    response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/maxresdefault.jpg")
    if response.status_code != 200:
        # If maxresdefault.jpg is not found, try hqdefault.jpg
        response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/hqdefault.jpg")
        if response != 200:
            # If maxresdefault.jpg is not found, try hqdefault.jpg
            response = requests.get(f"https://i.ytimg.com/vi/{thumbnail_to_download['video_id']}/mqdefault.jpg")
    with open(name, 'wb') as f:
        # Write the image to disk
        f.write(response.content)


def download_images(thumbnails_to_download):
    """
    Downloads multiple thumbnails in parallel using a ThreadPoolExecutor.

    :param thumbnails_to_download: A list of dictionaries with keys 'video_id' and 'iteration'
    :type thumbnails_to_download: list
    """
    with ThreadPoolExecutor() as executor:
        executor.map(download_image, thumbnails_to_download)

