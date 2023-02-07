# YouTube Popular Videos Retrieval Script
### A python script that retrieves the 200 most popular YouTube videos in various categories such as "Comedy", "Entertainment", and "Gaming" for each of the supported countries.

## Features
Retrieves videos using YouTube's API <br>
Stores videos in a postgreSQL database <br>
Calculates a sha-256 hash for every video thumbnail <br>
Detects changes in thumbnails by comparing hashes with stored ones in the database<br>
Automatically downloads new thumbnail if hashes are different<br>
Inserts channel IDs with their corresponding channel titles into the 'youtubechannel' table for further use from the beastly intelligence website.

## Requirements
Python<br>
postgreSQL database<br>
YouTube API key<br>

## Getting Started
Clone the repository <br>
Set up the postgreSQL database<br>
Obtain a YouTube API key<br>
Replace the placeholder values in the code with your own<br>
Activate the virtual environment .venv or create your own and install the dependencies listed in requirements.txt
Run the script using the command `python main.py --countries primary` or `python main.py --countries secondary`

## Documentation
For further details on the implementation and usage of the script, please refer to the inline documentation within the code.