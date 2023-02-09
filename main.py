# This is a python script that retrieves and stores information about the top 200 trending videos 
# based on sepecified category_ids, for each country, into a postgreSQL database table 'yt_videos'. 
# The script also calculates a SHA-256 hash for each video thumbnail, detects changes in thumbnails 
# by comparing the hashes with stored ones in the database and automatically downloads new or updated thumbnails. 
# Additionally, it caputes and stores the channel information of the video uploaders seperate table 'yt_channel' 
# including details such as the trending history and frequency of the channel in different regions.  

# Import the required module for calling the YouTube API
from googleapiclient.discovery import build, Resource

# Import the required modules for connecting to and working with PostgreSQL
import psycopg2, psycopg2.extras

# Import the configuration for connecting to the database
from config import config

# Import a list of countries for which videos need to be fetched
from countries import COUNTRIES

# Import the datetime and time module to work with dates
import datetime, time

# Import the json module to work with JSON data
import json

#Import the os module to access api keys saved in an env variable
import os

# Import the re (regular expression) module to work with strings
import re

# Import the typing module to add type hints
from typing import Tuple, List, Dict

# asyncio library is imported to handle asynchronous programming
import asyncio

# ClientSession from the aiohttp library is used to make HTTP requests asynchronously
from aiohttp import ClientSession

# hashlib library is imported to generate a hash of the video thumbnail URL
import hashlib

# download_thumbnails is a module containing the download_images function
from download_thumbnails import download_images

# logging module is imported to log information about the script's execution,
import logging

import argparse


class PostgreSQL:
    """Class for connecting to postgreSQL database."""
    @staticmethod
    def connect() -> Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
        """
        Connects to postgreSQL database using configuration details.
        
        :return: A tuple containing the connection and cursor objects.
        :raises:
            Exception: If connection to the database fails.
            psycopg2.DatabaseError: If the connection to the database encounters an error.
        """
        try:
            conn = psycopg2.connect(**config())
            cur = conn.cursor()
            logging.info("Connected to PostgreSQL")
            return conn, cur
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Failed to connect to the database: {error}")


def format_list(lst: List[str]) -> str:
    """
    Format a list of tags or blocked regions into a string for storage in a database.
    
    :param lst: list of tags or regions to be formatted
    :return: formatted string of the list in the format {'tag1', 'tag2', ...}
    """
    # Convert the list of tags or blocked regions into a string of format {'tag1', 'tag2', ...}.
    formatted_str = '{' + ','.join(f"'{element}'" for element in lst) + '}'
    
    # Escape any single quotes within the string to be inserted into the database, 
    # since single quotes are used as string delimiters in SQL.
    formatted_str = re.sub("\'", "''", formatted_str)
    
    # Escape any double quotes within the string to be inserted into the database, 
    # since double quotes may cause syntax errors in SQL.
    formatted_str = re.sub('"', "\"", formatted_str)
    
    return formatted_str
 

def get_tags(video: Dict) -> str:
    """
    Extract the list of tags from a video dict object
    
    :param video: a dict object representing a video
    :return: a formatted string of tags in the format of {'tag1', 'tag2', ...}
    
    The function uses the `.get` method to check if the 'snippet' and 'tags' keys exist in the `video` dict object. 
    If the keys don't exist, an empty list is returned to avoid raising a keyError exception.
    """
    tags = video.get('snippet', {}).get('tags', [])
    return format_list(tags)


async def insert_videos_into_db(data, conn: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor, channel_data: List[Tuple]) -> None:
    """
    This function inserts the data of videos into a PostgreSQL database.

    :param videos (list): A list of dictionaries, where each dictionary contains information about a video.
    :param conn (psycopg2 connection object): The connection object to the PostgreSQL database.
    :param cur (psycopg2 cursor object): The cursor object to interact with the PostgreSQL database.
    :return: None
    """
    insert_query_yt_videos = ("""INSERT INTO yt_videos
                    (video_id, channel_id, view_count, comment_count, like_count, published_at, title, 
                    description, thumbnails, channel_title, tags, category_id, duration, definition, caption,
                    licensed_content, dimension, embeddable, made_for_kids, default_audio_language, blocked_regions,
                    thumbnail_hash, idx, trending_regions, timestamp, thumbnail_iteration)
                    VALUES %s
                    ON CONFLICT (video_id) DO UPDATE SET
                    view_count = EXCLUDED.view_count,
                    comment_count = EXCLUDED.comment_count,
                    like_count = EXCLUDED.like_count,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category_id = EXCLUDED.category_id,
                    duration = EXCLUDED.duration,
                    definition = EXCLUDED.definition,
                    caption = EXCLUDED.caption,
                    licensed_content = EXCLUDED.licensed_content,
                    dimension = EXCLUDED.dimension,
                    embeddable = EXCLUDED.embeddable,
                    made_for_kids = EXCLUDED.made_for_kids,
                    default_audio_language = EXCLUDED.default_audio_language,
                    blocked_regions = EXCLUDED.blocked_regions,
                    trending_regions = EXCLUDED.trending_regions,
                    timestamp = EXCLUDED.timestamp,
                    thumbnail_hash = EXCLUDED.thumbnail_hash,
                    thumbnail_iteration = EXCLUDED.thumbnail_iteration,
                    idx = EXCLUDED.idx;
                    """)

    try:
        # Execute the insertion query with values and commit the transaction
        psycopg2.extras.execute_values(cur, insert_query_yt_videos, data, template=
        "(%(video_id)s, %(channel_id)s, %(view_count)s, %(comment_count)s, %(like_count)s, %(published_at)s,"
        "%(title)s, %(description)s, %(thumbnails)s, %(channel_title)s, %(tags)s, %(category_id)s, %(duration)s,"
        "%(definition)s, %(caption)s, %(licensed_content)s, %(dimension)s, %(embeddable)s, %(made_for_kids)s,"
        "%(default_audio_language)s, %(blocked_regions)s, %(thumbnail_hash)s, %(idx)s, %(trending_regions)s, "
        "%(timestamp)s, %(thumbnail_iteration)s)", page_size=200)               
        conn.commit()
    except Exception as e:
        # Log an error message and rollback the transaction in case of an exception
        logging.error("Error inserting videos into the database: ", e)
        conn.rollback()
    insert_query_yt_videos_history = ("""INSERT INTO yt_videos_history
                    (video_id, like_count, view_count, comment_count, timestamp, title, thumbnail_hash, 
                    thumbnail_iteration, embeddable, caption, blocked_regions, trending_regions, idx)
                    VALUES %s
                    """)
    try: 
        # Execute the insertion query with values and commit the transaction
        psycopg2.extras.execute_values(cur, insert_query_yt_videos_history, data, template=
            "(%(video_id)s, %(like_count)s, %(view_count)s, %(comment_count)s, %(timestamp)s, "
            "%(title)s, %(thumbnail_hash)s, %(thumbnail_iteration)s, %(embeddable)s, %(caption)s, "
            "%(blocked_regions)s, %(trending_regions)s, %(idx)s)", page_size=200)               
        conn.commit()
    except Exception as e:
        # Log an error message and rollback the transaction in case of an exception
        logging.error("Error inserting videos into the database: ", e)
        conn.rollback()    

    insert_query_yt_channel = ("""INSERT INTO yt_channel
                    (id, title, last_updated, category_ids, trended_countries, trending_cnt) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                    last_updated = EXCLUDED.last_updated,
                    title = EXCLUDED.title,
                    trended_countries = (
                        SELECT array_agg(DISTINCT x)
                        FROM unnest(array_cat(yt_channel.trended_countries, EXCLUDED.trended_countries)) x
                    ),
                    category_ids = (
                        SELECT array_agg(DISTINCT x)
                        FROM unnest(array_cat(yt_channel.category_ids, EXCLUDED.category_ids)) x
                    ),
                    trending_cnt = yt_channel.trending_cnt + EXCLUDED.trending_cnt
                    """)

    try: 
        # Execute the insertion query with values and commit the transaction
        psycopg2.extras.execute_values(cur, insert_query_yt_channel, channel_data, template=
            "(%(id)s, %(title)s, %(timestamp)s, %(category_ids)s, %(trended_countries)s, %(trending_cnt)s)", page_size=200)               
        conn.commit()
    except Exception as e:
        # Log an error message and rollback the transaction in case of an exception
        logging.error("Error inserting videos into the database: ", e)
        conn.rollback()                 


async def get_trending_videos(service: Resource, countries, category_ids) -> List[Dict]:
    """
    Fetches the trending videos from YouTube for a list of countries (max. 200 per country).
    
    :param service: The YouTube service object.
    :param countries: A list of dictionaries representing countries. Each dictionary contains information
                     about the country, such as its name and code.
    :param category_ids: A list of video category IDs to search for in each country.
    :return: A tuple of two items:
             1. A list of dictionaries containing information about the trending videos.
             2. A dictionary mapping video IDs to a list of country codes where the video is trending.
    """
    # Initialize lists to store the videos and a set to keep track of seen video IDs
    videos = []
    seen_video_ids = set()
    video_trending_regions = dict()

    # Loop through each country and fetch the trending videos for each video category
    for country in countries:
        logging.info(f"Fetching trending videos for: {country['name']} ({country['code']})")
        for category in category_ids:
            # Execute the first request to get the trending videos for the current country and video category
            request = service.videos().list(
                part='contentDetails,id,liveStreamingDetails,localizations,player,snippet,statistics,status,topicDetails',
                chart='mostPopular',
                regionCode=country['code'],
                videoCategoryId=category,
                maxResults=50
            )
            response = request.execute()
            while True:
                # Loop through each video in the response and store it if it hasn't been seen before
                for video in response["items"]:
                    video_id = video["id"]
                    if country['code'] not in video_trending_regions.setdefault(video_id, []):
                        video_trending_regions[video_id].append(country['code'])
                    if video_id in seen_video_ids:
                        continue
                    videos.append(video)
                    seen_video_ids.add(video_id)
                    # Update the `video_trending_regions` dictionary to record the country code for the current video
                # If there is a next page of results, fetch it and store the videos in the same way as before
                if "nextPageToken" not in response:
                    break
                request = service.videos().list(
                    part='contentDetails,id,liveStreamingDetails,localizations,player,snippet,statistics,status,topicDetails',
                    chart='mostPopular',
                    regionCode=country['code'],
                    pageToken=response["nextPageToken"],
                    maxResults=50
                )
                response = request.execute()
    logging.info(f"Fetched a total of {len(videos)} videos")
    return videos, video_trending_regions

    

async def get_image_data(session, url):
    """
    Retrieve the image data from the given URL.
    
    :param session: aiohttp ClientSession object
    :param url: URL of the image to be retrieved
    :return: image data in bytes
    """
    async with session.get(f"https://i.ytimg.com/vi/{url}/hqdefault.jpg") as response:
        return await response.read()


def generate_hash(image_data):
    """
    Generate a SHA-256 hash of the given image data.
    
    :param image_data: image data in bytes
    :return: SHA-256 hash of the image data
    """
    return hashlib.sha256(image_data).hexdigest()


async def generate_hash_async(session, url: str, semaphore):
    """
    Asynchronously generate a SHA-256 hash of the image data from the given URL.
    
    :param session: aiohttp ClientSession object
    :param url: URL of the image to be retrieved
    :param semaphore: asyncio Semaphore object
    :return: SHA-256 hash of the image data
    """
    async with semaphore:
        image_data = await get_image_data(session, url)
        return generate_hash(image_data)


def generate_idx(cur: psycopg2.extensions.cursor, video_ids):
    """
    Generate an index n for every video_id indicating the n-th insert for the given video_id into the database

    :param cur: psycopg2 cursor object used to execute the query
    :param video_ids: list of video IDs to generate indices for
    :return: dictionary mapping video IDs to their respective indices
    """
    placeholders = ', '.join(['%s'] * len(video_ids))
    cur.execute(f"SELECT video_id, coalesce(max(idx), 0) + 1 as idx FROM yt_videos_history WHERE video_id in ({placeholders}) group by video_id", video_ids)
    results = cur.fetchall()
    idx_dict = {row[0]: row[1] for row in results}
    return idx_dict


def generate_thumbnail_iteration(cur: psycopg2.extensions.cursor, video_ids, thumbnail_hashes):
    """
    Generates a dictionary mapping video_ids to their respective thumbnail iteration. 
    If the video_id is already in the database, but with a different hash, the thumbnail changed,
    resulting in an increment in that video's thumbnail_iteration count.
    If the thumbnail changes or the video_id wasn't in the database,
    add it it the list of thumbnails that will be downloaded afterwards
    
    :param cur: psycopg2 cursor object
    :param video_ids: list of video ids
    :param thumbnail_hashes: list of thumbnail hashes
    :return: a dictionary mapping video ids to thumbnail iterations and a list of thumbnails to download
    """
    placeholders = ', '.join(['%s'] * len(video_ids))
    cur.execute(f"WITH max_iterations AS (SELECT yt_videos_history.video_id, MAX(thumbnail_iteration) AS max_iteration FROM yt_videos_history WHERE video_id IN ({placeholders}) GROUP BY video_id) SELECT yt_videos_history.video_id, thumbnail_hash, thumbnail_iteration FROM yt_videos_history JOIN max_iterations ON yt_videos_history.video_id = max_iterations.video_id AND yt_videos_history.thumbnail_iteration = max_iterations.max_iteration", video_ids)
    results = cur.fetchall()
    iteration_dict = {}
    thumbnails_to_download = list()
    for row in results:
        video_id, hash, thumbnail_iteration = row
        iteration_dict[video_id] = {"thumbnail_iteration": thumbnail_iteration, "thumbnail_hash": hash}
    for video_id, thumbnail_hash in zip(video_ids, thumbnail_hashes):
        if video_id in iteration_dict:
            if(iteration_dict[video_id]["thumbnail_hash"] == thumbnail_hash):
                thumbnail_iteration = iteration_dict[video_id]["thumbnail_iteration"]
            else:
                thumbnail_iteration = iteration_dict[video_id]["thumbnail_iteration"] + 1
                thumbnails_to_download.append({"video_id": video_id, "iteration": iteration_dict[video_id]["thumbnail_iteration"] + 1})
        else:
            thumbnail_iteration = 1
            thumbnails_to_download.append({"video_id": video_id, "iteration": 1})
        iteration_dict[video_id] = thumbnail_iteration
    return iteration_dict, thumbnails_to_download


async def get_data(cur: psycopg2.extensions.cursor, videos, video_trending_regions: Dict) ->  List[Dict]:
    """
    Format video data for insertion into the database and generate a list of new thumbnails that will be downloaded after
    insertion into the database.
    
    :param cur: psycopg2 cursor object used to execute SQL queries
    :param videos: list of videos from YouTube API
    :param video_trending_regions: dictionary mapping video ids to trending regions
    :return: list of dictionaries containing the data for each video, and a list of thumbnails to download
    """
    async with ClientSession() as session:
        video_ids = [video['id'] for video in videos]
        idx_dict = generate_idx(cur, video_ids)
        semaphore = asyncio.Semaphore(20)
        hashes = await asyncio.gather(*[generate_hash_async(session, video['id'], semaphore) for video in videos])
        thumnail_iterations, thumbnails_to_download = generate_thumbnail_iteration(cur, video_ids, hashes)
        unique_video_ids = set()
        data = []
        channel_arr = []
        channel_dict = dict()
        trending_cnt = dict()
        category_ids = dict()
        trended_countries = dict()
        for index, video in enumerate(videos):
            if video['id'] in unique_video_ids:
                continue

            # Add to channel_data
            channel_id = video['snippet']['channelId']

            # 
            trending_cnt[channel_id] = trending_cnt.get(channel_id, 0) + 1
            category_ids[channel_id] = list(set(category_ids.get(channel_id, [])) | {int(video.get('snippet', {}).get('categoryId', -1))})
            trended_countries[channel_id] = list(set(trended_countries.get(channel_id, [])) | set(video_trending_regions.get(video['id'], [])))
            
            channel_dict[channel_id] = {
                    "id": channel_id, 
                    "title": re.sub("\'", "''", video["snippet"]["channelTitle"]),
                    "timestamp": datetime.datetime.now(),
                    "trending_cnt": trending_cnt[channel_id],
                    "category_ids": category_ids[channel_id],
                    "trended_countries": trended_countries[channel_id]
                }
                    
            # Add to unique video_ids
            unique_video_ids.add(video['id'])

            # Add to data
            data.append({        
            "video_id": video['id'],
            "channel_id": video['snippet']['channelId'],
            "view_count": video.get('statistics', None).get('viewCount', None),
            "comment_count": video.get('statistics', None).get('commentCount', None),
            "like_count": video.get('statistics', None).get('likeCount', None),
            "published_at": datetime.datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
            "title": re.sub("\'", "''", video['snippet']['title']),
            "description": re.sub("\'", "''", video['snippet']['description']),
            "thumbnails": json.dumps(video['snippet']['thumbnails']),
            "channel_title": re.sub("\'", "''", video["snippet"]["channelTitle"]),
            "category_id": video.get('snippet', None).get('categoryId', None),
            "duration": video.get('contentDetails', None).get('duration', None),
            "definition": video.get('contentDetails', None).get('definition', None),
            "caption": video.get('contentDetails', None).get('caption'),
            "licensed_content": video.get('contentDetails', None).get('licensedContent', None),
            "dimension": video.get('contentDetails', None).get('dimension', None),
            "embeddable": video.get('status', None).get('embeddable', None),
            "made_for_kids": video.get('status', None).get('madeForKids', None),
            "tags": get_tags(video), 
            "blocked_regions": video.get('contentDetails', {}).get('regionRestriction', {}).get('blocked', []),
            "default_audio_language": video.get('snippet', None).get('defaultAudioLanguage', None),
            "thumbnail_hash": hashes[index],
            "idx": idx_dict.get(video['id'], 1),
            "timestamp": datetime.datetime.now(),
            "trending_regions": video_trending_regions.get(video['id'],[]),
            "thumbnail_iteration": thumnail_iterations.get(video['id'], 1),
            })
    
    # Appends each channel from the channel dictionary to the channel array, 
    # so that it can be used for insertion into the database
    for _, value in channel_dict.items():
        channel_arr.append(value)
    return data, thumbnails_to_download, channel_arr    


async def main() -> None:
    """
    Main function
    This function retrieves trending YouTube videos for a set of countries (max. 200 per country), 
    stores the video information in a PostgreSQL database and closes the database connection.
    
    Keyword arguments:
    yt_v3_key    -- The YouTube API key.
    max_results  -- The maximum number of results per country.
    conn, cur    -- Connection and cursor objects for the PostgreSQL database.
    service      -- Service object from the YouTube API.
    """
    start_time = time.time()

    # 'countries' arg that's passed when running this script i.e. main.py --countries primary
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", type=str)
    countries = parser.parse_args().countries
    category_ids = [20, 23, 24, 0] if countries == 'primary' else [0] # 20 = gaming, 23 = comedy, 24 = entertainment, 0 = all

    # Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"logs/{today}.log"

    # Check if logs directory exists, create it if not
    if not os.path.exists("logs"):
        os.makedirs("logs") 

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Get the YouTube API key and connect to the postgreSQL database
    yt_v3_key = os.environ.get("YT_v3_API_KEY")
    conn, cur = PostgreSQL.connect()

    # Create a service object from the YouTube API
    service = build('youtube', 'v3', developerKey=yt_v3_key)

    # Retrieve trending videos and insert them into the database
    videos, video_trending_regions, = await get_trending_videos(service, COUNTRIES[countries], category_ids)
    data, thumbnails_to_download, channelData = await get_data(cur, videos, video_trending_regions)
    await insert_videos_into_db(data, conn, cur, channelData)

    # Close the service and database connections
    service.close() 
    conn.close()

    # Download video thumbnails and log code runtime
    download_images(thumbnails_to_download)
    logger.info("Code runtime: %s seconds", time.time() - start_time)


if __name__ == '__main__':
    asyncio.run(main())