# YouTube Popular Videos Retrieval Script
## A python script that retrieves the 200 most popular YouTube videos in various categories such as "Comedy", "Entertainment", and "Gaming" for each of the supported countries.

## Features
Retrieves videos using YouTube's API
Stores videos in a postgreSQL database
Calculates a sha-256 hash for every video thumbnail
Detects changes in thumbnails by comparing hashes with stored ones in the database
Automatically downloads new thumbnail if hashes are different
Runs automatically every hour for 22 primary regions and every six hours for 91 secondary countries
Technical Details
Script setup on an AWS EC2 instance running Debian
Automated with cron tasks
Adheres to PEP standards and industry best practices
Thoroughly documented with clear and concise code

## Requirements
Python
postgreSQL database
YouTube API key

## Getting Started
Clone the repository
Set up the postgreSQL database
Obtain a YouTube API key
Replace the placeholder values in the code with your own
Run the script

## Documentation
For further details on the implementation and usage of the script, please refer to the inline documentation within the code.