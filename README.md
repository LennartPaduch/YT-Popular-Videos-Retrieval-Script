# YouTube Popular Videos Retrieval Script

This is a python script that retrieves and stores information about the top 200 trending videos based on sepecified **category_ids**, for each country, into a postgreSQL database table **yt_videos**. The script also calculates a SHA-256 hash for each video thumbnail, detects changes in thumbnails by comparing the hashes with stored ones in the database and automatically downloads new or updated thumbnails.

## Features

- Utilizes the YouTube API to retrieve video information <br>
- Stores video information in a postgreSQL database <br>
- Calculates a sha-256 hash for video thumbnails <br>
- Detects changes in thumbnails by comparing hashes with stored ones in the database<br>
- Automatically downloads new or updated thumbnails<br>

## Requirements
- Python<br>
- postgreSQL database<br>
- A valid YouTube API key

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

For example, to create a virtual environment named venv, which is a commonly used option, run the following command: <br>
`python -m venv venv`

## Running the Script

**Note**: By default, the categories for primary and secondary starting arguments are set to **'All'**, **'Gaming'**, **'Comedy'** and **'Entertainment'**. However, you can adjust these categories in the main function of the main.py file.
<br>
When running the script with any other value for the --countries argument, it will only retrieve data from the 'All' category, which includes every category but is limited to a maximum of 200 videos.
<br>
<br>
You have several options for the **--countries** argument when running the script:
<br>
`python src/main.py --countries primary` Retrieves information about the most popular videos per category from each of the 22 primary countries.
<br>`python src/main.py --countries secondary` Retrieves information about the most popular videos per category from each of the 87 less-viewed countries.
<br>
`python src/main.py --countries all` Retrieves information about up to the top 200 trending videos from all 109 countries.
<br>
Alternatively, you can specify any number of arbitrary countries by using `python src/main.py --countries "DE, RU, FR, US"`. You need to separate each country by commas and enclose the list of countries in quotation marks if you specify more than one country. For example, `python src/main.py --countries "DE,FR"` is valid, whereas `python src/main.py --countries DE,FR` is not.
<br>
<br>
**Note:**<br>
To ensure efficient usage of the YouTube API key and avoid exceeding its daily quota limit of 10,000, the supported countries by YouTube have been separated into two subsets - **primary** and **secondary**. I configured the script to run hourly for the primary regions and every six hours for the secondary regions on an AWS EC2 instance running Debian using Linux' cron tasks. 
<br> You have the flexibility to customize the priority of countries or remove the separation altogether, depending on your specific setup, use case, and API key's quota limits.


## Documentation

For further details on the implementation and usage of the script, please refer to the inline documentation within the code.