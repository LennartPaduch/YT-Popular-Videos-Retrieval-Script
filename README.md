# YouTube Popular Videos Retrieval Script
This is a python script that retrieves and stores information about the top 200 trending videos based on sepecified **category_ids**, for each country, into a postgreSQL database table **yt_videos**. The script also calculates a SHA-256 hash for each video thumbnail, detects changes in thumbnails by comparing the hashes with stored ones in the database and automatically downloads new or updated thumbnails. <br> Additionally, it caputes and stores the channel information of the video uploaders into a seperate **yt_channel** table, including details such as the trending history and frequency of the channel in different regions.  

## Features
-Utilizes the YouTube API to retrieve video information <br>
-Stores video information in a postgreSQL database <br>
-Calculates a sha-256 hash for video thumbnails <br>
-Detects changes in thumbnails by comparing hashes with stored ones in the database<br>
-Automatically downloads new or updated thumbnails<br>
-Stores channel information in the **yt_channel** table

## Requirements
-Python<br>
-postgreSQL database<br>
-A valid YouTube API key

## Getting Started
1. Clone the repository <br>
2. Set up the postgreSQL database using the SQL table creation commands provided in the **SQL tables** folder. You may adjust these tables to your specific use case, in which case you would also need to modify some parts of the main.py script accordingly. This can include changes to the table structure, query conditions, or any other relevant parts.<br>
3. Obtain a valid YouTube API key<br>
4. Replace the placeholder values in `main.py` and `database.ini` with your own credentials<br>
5. Activate the [virtual environment](#virtual-environment) `.venv` or create your own and install the dependencies listed in **requirements.txt**
6. [Run the script](#running-the-script)

## Virtual Environment 
To activate an existing virtual environment, run the activate file in the Scripts folder of the virtual environment directory. You can activate the virtual environment **.venv** from this repository by typing `.venv/Scripts/activate` in the terminal or command line while in the directory where the **.venv** folder is located.

To create a new virtual environment, run the following command in your terminal or command line: <br>
`python -m venv <directory>`

For example, to create a virtual environment named venv, which is a commonly used optiopn, run the following command: <br>
`python -m venv venv`

## Running the Script
You can run the script using the command `python main.py --countries primary` or `python main.py --countries secondary`. By default, the primary option includes data from 22 countries such as **US**, **DE**, **IN**, and **JP**. The secondary option includes data from 91 countries including **MN**, **BD**, **QA**, and **DZ**. You can find a complete list of countries in the **countries.py** file.
<br>
**Note:**<br>
To ensure efficient usage of the YouTube API key and avoid exceeding its daily quota limit of 10,000, the supported countries by YouTube have been separated into two subsets - **primary** and **secondary**. I configured the script to run hourly for the primary regions and every six hours for the secondary regions on an AWS EC2 instance running Debian using Linux' cron tasks. 
<br> You have the flexibility to customize the priority of countries or remove the separation altogether, depending on your specific setup, use case, and API key's quota limits.


## Documentation
For further details on the implementation and usage of the script, please refer to the inline documentation within the code.