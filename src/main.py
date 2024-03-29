# This is a python script that retrieves and stores information about the top 200 trending videos 
# based on sepecified category_ids, for each country, into a postgreSQL database table 'yt_videos'. 
# The script also calculates a SHA-256 hash for each video thumbnail, detects changes in thumbnails 
# by comparing the hashes with stored ones in the database and automatically downloads new or updated thumbnails. 

# Import the required module for calling the YouTube API
from googleapiclient.discovery import build, Resource

# Import the required modules for connecting to and working with PostgreSQL
import psycopg2, psycopg2.extras

# Import the configuration for connecting to the database
from utils.config import config

# Import a list of countries for which videos can be fetched
from countries import COUNTRIES

# Import a dict of categories for easier manangement of categoryIds, mapping categoryIds to category names
from categories import CATEGORIES

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

# argparse module to use args such as `--countries PRIMARY` when running this script
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
            _raise_value_error("Failed to connect to the database", error)


async def insert_videos_into_db(data, conn: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor) -> None:
    """
    This function inserts the data of videos into a PostgreSQL database.

    :param videos: A list of dictionaries, where each dictionary contains information about a video.
    :param conn: The connection object to the PostgreSQL database.
    :param cur: The cursor object to interact with the PostgreSQL database.
    :return: None
    """
    insert_query_yt_videos = ("""INSERT INTO yt_videos
                    (video_id, channel_id, view_count, comment_count, like_count, published_at, title, 
                    description, thumbnails, channel_title, tags, category_id, duration, definition, caption,
                    licensed_content, dimension, embeddable, made_for_kids, default_audio_language, blocked_regions,
                    thumbnail_hash, trending_regions, timestamp, thumbnail_iteration)
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
                    thumbnail_iteration = EXCLUDED.thumbnail_iteration
                    """)

    try:
        # Execute the insertion query with values and commit the transaction
        psycopg2.extras.execute_values(cur, insert_query_yt_videos, data, template=
        "(%(video_id)s, %(channel_id)s, %(view_count)s, %(comment_count)s, %(like_count)s, %(published_at)s,"
        "%(title)s, %(description)s, %(thumbnails)s, %(channel_title)s, %(tags)s, %(category_id)s, %(duration)s,"
        "%(definition)s, %(caption)s, %(licensed_content)s, %(dimension)s, %(embeddable)s, %(made_for_kids)s,"
        "%(default_audio_language)s, %(blocked_regions)s, %(thumbnail_hash)s, %(trending_regions)s, "
        "%(timestamp)s, %(thumbnail_iteration)s)", page_size=200)               
        conn.commit()
    except Exception as e:
        # Log an error message and rollback the transaction in case of an exception
        conn.rollback()
        _raise_value_error("Error inserting videos into the database", e)
    insert_query_yt_videos_history = ("""INSERT INTO yt_videos_history
                    (video_id, like_count, view_count, comment_count, timestamp, title, thumbnail_hash, 
                    thumbnail_iteration, embeddable, caption, blocked_regions, trending_regions)
                    VALUES %s
                    """)
    try: 
        # Execute the insertion query with values and commit the transaction
        psycopg2.extras.execute_values(cur, insert_query_yt_videos_history, data, template=
            "(%(video_id)s, %(like_count)s, %(view_count)s, %(comment_count)s, %(timestamp)s, "
            "%(title)s, %(thumbnail_hash)s, %(thumbnail_iteration)s, %(embeddable)s, %(caption)s, "
            "%(blocked_regions)s, %(trending_regions)s)", page_size=200)               
        conn.commit()
    except Exception as e:
        # Log an error message and rollback the transaction in case of an exception
        conn.rollback()    
        _raise_value_error("Error inserting videos into the database", e)


async def get_trending_videos(service: Resource, countries, category_ids) -> List[Dict]:
    """
    Asynchronously fetches the trending videos from YouTube for a list of countries (max. 200 per category, per country).

    :param service: The YouTube service object (from googleapiclient.discovery).
    :param countries: A list of dictionaries representing countries. Each dictionary contains information
                      about the country, such as its name and code.
    :param category_ids: A list of video category IDs to search for in each country.
    :return: A tuple of two items:
             1. A list of dictionaries containing information about the trending videos.
             2. A dictionary mapping video IDs to a list of country codes where the video is trending.
    """
    videos = []
    seen_video_ids = set()
    video_trending_regions = dict()

    def build_request(region_code, video_category_id, page_token=None):
        return service.videos().list(
            part='contentDetails,id,liveStreamingDetails,localizations,player,snippet,statistics,status,topicDetails',
            chart='mostPopular',
            regionCode=region_code,
            videoCategoryId=video_category_id,
            pageToken=page_token,
            maxResults=50
        )

    # Iterate through countries and categories, fetching trending videos
    for country in countries:
        video_count = len(videos)
        for category in category_ids:
            response = build_request(country['code'], category).execute()
            while response:
                for video in response.get("items", []):
                    video_id = video["id"]

                    if video_id not in video_trending_regions:
                        video_trending_regions[video_id] = []
                    if country['code'] not in video_trending_regions[video_id]:
                        video_trending_regions[video_id].append(country['code'])

                    if video_id not in seen_video_ids:
                        videos.append(video)
                        seen_video_ids.add(video_id)

                if "nextPageToken" not in response:
                    break
                response = build_request(country['code'], category, response["nextPageToken"]).execute()

        logging.info(f"Fetched {len(videos) - video_count} videos for {country['name']}")
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
        return hashlib.sha256(image_data).hexdigest()


def generate_thumbnail_iteration(cur: psycopg2.extensions.cursor, video_ids, thumbnail_hashes):
    """
    Generates a dictionary mapping video_ids to their respective thumbnail iteration. 
    If the video_id is already in the database, but with a different hash, the thumbnail has changed,
    resulting in an increment in that video's thumbnail_iteration count.
    If the thumbnail changes or the video_id wasn't in the database,
    add it to the list of thumbnails that will be downloaded afterwards.

    :param cur: A psycopg2 cursor object for executing database queries.
    :param video_ids: A list of video ids.
    :param thumbnail_hashes: A list of thumbnail hashes corresponding to the video ids.
    :return: A tuple of two items:
             1. A dictionary mapping video ids to thumbnail iterations.
             2. A list of dictionaries containing video ids and their corresponding thumbnail iterations that need to be downloaded.
    """
    if not video_ids:
        return {}, []
    placeholders = ', '.join(['%s'] * len(video_ids))
    query = f"""
        WITH max_iterations AS 
            (SELECT yt_videos_history.video_id, MAX(thumbnail_iteration) AS max_iteration 
                FROM yt_videos_history
                WHERE video_id IN ({placeholders}) 
                GROUP BY video_id) 
        SELECT yt_videos_history.video_id, thumbnail_hash, thumbnail_iteration 
        FROM yt_videos_history
        JOIN max_iterations ON yt_videos_history.video_id = max_iterations.video_id 
                            AND yt_videos_history.thumbnail_iteration = max_iterations.max_iteration
        """
    # Execute the SQL query and fetch the results
    with cur: # ensures that if an exception occurs during the cur.execute() or cur.fetchall() calls, the transaction will be rolled back.
        try:
            cur.execute(query, video_ids)
            results = cur.fetchall()
        except Exception as e:
            _raise_value_error("Error while fetching thumbnail iterations from database", e)

    thumbnails_to_download = []
    # Create a dictionary mapping video_ids to their respective thumbnail iteration and hash.
    # results' format: [(video_id, thumbnail_hash, thumbnail_iteration), ...]
    iteration_dict = {row[0]: {"iteration": row[2], "hash": row[1]} for row in results}
    for video_id, thumbnail_hash in zip(video_ids, thumbnail_hashes):
        # If the video_id is not in the database, add it to the dictionary with a thumbnail iteration of 0
        thumbnail = iteration_dict.get(video_id, {"iteration": 0, "hash": None})
        # If the thumbnail hash is different from the one in the database, increment the thumbnail iteration
        if thumbnail["hash"] != thumbnail_hash:
            thumbnail["iteration"] += 1
            thumbnails_to_download.append({"video_id": video_id, "iteration": thumbnail["iteration"]})
        # Update the dictionary with the new thumbnail iteration
        iteration_dict[video_id] = thumbnail["iteration"]

    return iteration_dict, thumbnails_to_download


async def prepare_data(cur: psycopg2.extensions.cursor, videos, video_trending_regions: Dict) ->  List[Dict]:
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
        semaphore = asyncio.Semaphore(20)
        hashes = await asyncio.gather(*[generate_hash_async(session, video['id'], semaphore) for video in videos])
        thumnail_iterations, thumbnails_to_download = generate_thumbnail_iteration(cur, video_ids, hashes)
        data = []
        for index, video in enumerate(videos):
            video_id = video['id']
            if video_id not in [video["video_id"] for video in data]:
                data.append({        
                "video_id": video['id'],
                "channel_id": video['snippet']['channelId'],
                "view_count": video.get('statistics', {}).get('viewCount', None),
                "comment_count": video.get('statistics', {}).get('commentCount', None),
                "like_count": video.get('statistics', {}).get('likeCount', None),
                "published_at": datetime.datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                "title": re.sub("\'", "''", video['snippet']['title']),
                "description": re.sub("\'", "''", video['snippet']['description']),
                "thumbnails": json.dumps(video['snippet']['thumbnails']),
                "channel_title": re.sub("\'", "''", video["snippet"]["channelTitle"]),
                "category_id": video.get('snippet', {}).get('categoryId', None),
                "duration": video.get('contentDetails', {}).get('duration', None),
                "definition": video.get('contentDetails', {}).get('definition', None),
                "caption": video.get('contentDetails', {}).get('caption'),
                "licensed_content": video.get('contentDetails', {}).get('licensedContent', None),
                "dimension": video.get('contentDetails', {}).get('dimension', None),
                "embeddable": video.get('status', {}).get('embeddable', None),
                "made_for_kids": video.get('status', {}).get('madeForKids', None),
                "tags": video.get('snippet', {}).get('tags', []), 
                "blocked_regions": video.get('contentDetails', {}).get('regionRestriction', {}).get('blocked', []),
                "default_audio_language": video.get('snippet', {}).get('defaultAudioLanguage', None),
                "thumbnail_hash": hashes[index],
                "timestamp": datetime.datetime.now(),
                "trending_regions": video_trending_regions.get(video['id'],[]),
                "thumbnail_iteration": thumnail_iterations.get(video['id'], 1),
                })

    return data, thumbnails_to_download    


def _raise_value_error(text, error=None):
    message = f"{text}: {error}" if error else text
    logging.error(message)
    raise ValueError(message)
 
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f"logs/{today}.log"
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", type=str, default='US')
    args = parser.parse_args()
    args.countries = args.countries.upper()
    
    return args


async def main() -> None:
    """
    This function retrieves trending YouTube videos for a set of countries (max. 200 per category, per country), 
    stores the video information in a PostgreSQL database and downloads new and changed thumbnails.
    
    YT_V3_KEY    -- The YouTube API key.
    conn, cur    -- Connection and cursor objects for the PostgreSQL database.
    service      -- Service object from the YouTube API.
    """
    start_time = time.time()
    logger = setup_logger()
    args = parse_arguments()
    countries = COUNTRIES.get(args.countries, [])
  
    # If countries is 'PRIMARY', retrieve categories 'Gaming', 'Comedy', 'Entertainment' and 'All'
    # If countries is not 'PRIMARY', retrieve only category 'All'
    # This is to avoid exceeding the API quota limit of 10,000 per day.
    category_ids = [CATEGORIES['All']]

    if args.countries == 'PRIMARY':
        category_ids.extend([CATEGORIES['Gaming'], CATEGORIES['Comedy'], CATEGORIES['Entertainment']])
    elif args.countries != 'SECONDARY':
        country_codes = args.countries.replace(" ", "").split(',')
        countries = [{'code': country_code, 'name': COUNTRIES['ALL'].get(country_code, {'name': country_code})['name']}
             if country_code in COUNTRIES['ALL'] else _raise_value_error(f"{country_code} is not a valid country code.")
             for country_code in country_codes]

    if not countries:
        _raise_value_error("No valid country codes provided.")

    # Get the YouTube API key and connect to the postgreSQ database
    YT_V3_KEY = os.environ.get("YT_v3_API_KEY")
    conn, cur = PostgreSQL.connect()
    # Create a service object from the YouTube API
    service = build('youtube', 'v3', developerKey=YT_V3_KEY)
    # Retrieve trending videos and insert them into the database
    videos, video_trending_regions, = await get_trending_videos(service, countries, category_ids)
    data, thumbnails_to_download = await prepare_data(cur, videos, video_trending_regions)
    await insert_videos_into_db(data, conn, cur)

    # Close the service and database connections
    service.close() 
    conn.close()

    # Download video thumbnails and log code runtime
    download_images(thumbnails_to_download, logger)
    logger.info("Code runtime: %s seconds", time.time() - start_time)


if __name__ == '__main__':
    asyncio.run(main())
 