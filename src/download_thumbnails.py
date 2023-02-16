# This script downloads YouTube video thumbnail images in parallel. 
# The `download_images` function takes a list of dictionaries, where each dictionary 
# has keys 'video_id' and 'iteration' and downloads all the thumbnails simultaneously. 
# The thumbnails are saved in a folder named 'thumbnails' with a naming format of 
# [video_id]/[iteration].jpg. If a folder for a specific video_id does not exist, it is created. 

import requests
import concurrent.futures
import os

def download_image(thumbnail, logger):
    """
    Downloads a single thumbnail image.

    :param thumbnail: A dictionary with keys 'video_id' and 'iteration'
    :param logger: A logger instance
    """
    # Create the folder for the video_id if it doesn't exist
    folder_path = f"thumbnails/{thumbnail['video_id']}"
    os.makedirs(folder_path, exist_ok=True)
    name = f"{folder_path}/{thumbnail['iteration']}.jpg"
    try: 
        response = requests.get(f"https://i.ytimg.com/vi/{thumbnail['video_id']}/maxresdefault.jpg")
        # Handle the case where maxresdefault thumbnail returns 404 error & placeholder image
        if response.status_code != 200:
            # If maxresdefault.jpg is not found, try hqdefault.jpg
            response = requests.get(f"https://i.ytimg.com/vi/{thumbnail['video_id']}/hqdefault.jpg")
            if response.status_code != 200:
                # If maxresdefault.jpg is not found, try hqdefault.jpg
                response = requests.get(f"https://i.ytimg.com/vi/{thumbnail['video_id']}/mqdefault.jpg")
        with open(name, 'wb') as f:
            # Write the image to disk
            f.write(response.content)
        return 1
    except Exception as e:
        logger.error(f"Error downloading thumbnail for video {thumbnail['video_id']}: {e}")
        return 0


def download_images(thumbnails_to_download, logger):
    """
    Downloads multiple thumbnails in parallel using a ThreadPoolExecutor.

    :param thumbnails_to_download: A list of dictionaries with keys 'video_id' and 'iteration'
    :type thumbnails_to_download: list
    :param logger: A logger instance
    """
    total_downloads = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_image, thumbnail, logger) for thumbnail in thumbnails_to_download]
        for future in concurrent.futures.as_completed(futures):
            total_downloads += future.result()
    logger.info(f"Downloaded {total_downloads} thumbnails")
