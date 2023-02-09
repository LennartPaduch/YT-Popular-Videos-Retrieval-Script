# YouTube Popular Videos Retrieval Script
This is a python script that retrieves and stores information about the top 200 trending videos based on sepecified category_ids, for each country, into a postgreSQL database table 'yt_videos'. The script also calculates a SHA-256 hash for each video thumbnail, detects changes in thumbnails by comparing the hashes with stored ones in the database and automatically downloads new or updated thumbnails. <br> Additionally, it caputes and stores the channel information of the video uploaders into a seperate table 'yt_channel' including details such as the trending history and frequency of the channel in different regions.  

## Features
Utilizes the YouTube API to retrieve video information <br>
Stores the video information in a postgreSQL database <br>
Calculates a sha-256 hash for every video thumbnail <br>
Detects changes in thumbnails by comparing hashes with stored ones in the database<br>
Automatically downloads thumbnails of new uploads and updated thumbnails if changes are detected <br>
Inserts channel IDs and their corresponding titles into the 'yt_channel' table for future reference

## Requirements
Python<br>
postgreSQL database<br>
A valid YouTube API key

## Getting Started
1. Clone the repository <br>
2. Set up the postgreSQL database<br>
3. Obtain a valid YouTube API key<br>
4. Replace the placeholder values in `main.py` and `database.ini` with your own credentials<br>
5. Activate the virtual environment `.venv` or create your own and install the dependencies listed in requirements.txt
6. Run the script using the command `python main.py --countries primary` or `python main.py --countries secondary`

## Documentation
For further details on the implementation and usage of the script, please refer to the inline documentation within the code.