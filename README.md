# Collecting News Articles and Comments

## Description
This program is created to collect online news article data from the news outlets focus.de, spiegel.de, welt.de and zeit.de and comment data on those news articles directly from the news outlets' website, reddit and twitter.

Output:  
● A collection of news articles, comments, social media tweets and reddit posts

![Data sources](Example_pictures/Scemantic_overview_f.png "Arrows indicate the update of database with updated data structure")


## Requirements

### MongoDB
The data collected by the program is stored in a MongoDB instance.

This is how you get the MongoDB running on the computer system:
#### Installation of MongoDB
Depending on the OS, the installation of the MongoDB is necessary
https://www.MongoDB.com/docs/manual/administration/install-community/

#### Run MongoDB instance (on port 27017)
In terminal command line type:  
 ```
 mongo
 ```

#### For more help on MongoDB
https://www.MongoDB.com

### Python
* bs4 (Beautifulsoup): html access used for the data extraction from collected information containers
* pymongo: MongoDB database interface to save collected and extracted data
* selenium: access to website via url with website interaction (clicking buttons on website to show all comments)


### Optinal, but highly recommended: crontab
Regular (e.q. hourly, daily) program calls can be automated with crontab
```
crontab -e
```
to edit the crontab


while in user's crontab: for hourly (on full hour) program calls:
```
0 * * * * cd ~ ; cd [path/to/program]; python3 [program_name.py]
```
Example:
```
0 * * * * cd ~ ; cd [path/to/program]; python3 NewsArticleCollector.py
```

while in user's crontab: for daily (00:00) program calls:
```
0 0 * * * cd ~ ; cd [path/to/program]; python3 [program_name.py]
```
Example:
```
0 0 * * * cd ~ ; cd [path/to/program]; python3 CommentCollector.py
```

more information on crontab: https://crontab.guru


### Optional: Studio3T (GUI for data)
https://studio3t.com




## Usage

* [running database instance](#database)
* [running internet connection](#internet)
* [past scraping](#past)
* [continuous scraping](#cont)

<a name="database"></a>
### 1. the MongoDB instance is running
Check by typing into the terminal
```
mongo // and then while in MongoDB
show dbs
```
This should show (at least) "admin", "config" and "local" databases

![MongoDB](Example_pictures/Mongo_example.png "mongo")

<a name="internet"></a>
### 2. Check the internet connection
without internet access no data can be scraped

<a name="past"></a>
### 3. Past scraping

#### 3.1 Article collection

##### 3.1.1 Run the NewsArticleCollector (continuous article data collection)
In the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 NewsArticleCollector.py
```
**On the terminal:** the first line should show the current date and time
after that, the scraping of the RSS feeds of focus.de, spiegel.de, welt.de and zeit.de is started showing for each article, if it is already present in the database or if it was added to the database (with the DataId printed before)

![NewsArticleCollector example output](Example_pictures/NewsArticleCollector_example.png "NewsArticleCollector.py example output")

**In the RSS_Scraping.log:** every started NewsArticleCollector progess logs information if an article was added to the database (with the DataId printed before)  

**In the database:** the database is updated whenever the NewsArticleCollector finds a url that is not yet in the database. The update saves the article data structure information that could be scraped from the RSS feed.

Because most news outlets don't have an online archive for their articles, continuous RSS feed scraping brings good article collecting results. It is recommended to run the NewsArticleCollector hourly to not miss potential articles because the zeit.de RSS feed is short and changes regularly.  
For the continuous scraping, a stable, continuous internet connection is necessary. The MongoDB local server instance should also run continuously stable to prevent potential data losses.

##### 3.1.2 run the Reddit_Scraper
Before starting the program, it should be settled which period of time should be scraped: the past year, the past month, the past week or the past 24 hours. Depending on what is decided, the corresponding block of code must be uncommented.  
In the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 Reddit_Scraper.py
```

**On the terminal:** after the program successfully completed, for every method call there will be a message indicating the start of the program ("Reddit article and comment scraping in process....please wait; this could take a while"). When comment scraping takes place, the scraped post is listed after the program call that found the previously unknown reddit post.
![Reddit_Scraper example output](Example_pictures/Reddit_Scraper_example.png "Reddit_Scraper.py example output clipping")

**In the [date]_[collection_of_outlet]_Reddit_Scraping_Comments.log:** the log file has a much more detailed report of the reddit scraping process including all the found reddit links and a count thereof, the reddit link, how the post is linked to the article (e.q. "cursor found post in database" -> "post already saved") followed by the news article link. When a post is saved as article data structure, the ObjectId is logged as well.  
While saving the post, the log also lists the comments of the post that are saved as comment data structure.

**In the database:** the database is updated whenever a unknown posts is found. The posts are saved as article data structure in ArticleData_[outlet_name] with their corresponding comments saved as comment data structure in Comments_[outlet_name]_Reddit

##### 3.1.3 run the Twitter_Scraper
In the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 Twitter_Scraper.py
```
**On the terminal:** after the program successfully completed, for every method call there will be a message indicating the start of the program ("Twitter article and comment scraping in process....please wait; this could take a while"). When comment scraping takes place, the scraped post is listed after the program call that found the previously unknown twitter tweet.
![Twitter_Scraper example output](Example_pictures/Twitter_Scraper_Welt_example.png "Twitter_Scraper example output clipping")

**In the [date]_[collection_of_outlet]_Twitter_Scraping_Comments.log:** the log file has a much more detailed report of the twitter scraping process including all the found twitter links and a count thereof, the twitter link, how the post is linked to the article (e.q. "cursor found post in database" -> "post already saved") followed by the news article link. When a tweet is saved as article data structure, the ObjectId is logged as well.  
While saving the post, the log also lists the comments of the tweet that are saved as comment data structure.

**In the database:** the database is updated whenever a unknown tweet is found. The tweets are saved as article data structure in ArticleData_[outlet_name] with their corresponding comments saved as comment data structure in Comments_[outlet_name]_Twitter


### 3.2 Comment collection
At the end of the CommentCollector.py, in the *individual time frame block*, a time frame for the comment collection and the news outlet can be determined manually. The datetime format id datetime([year], [month], [day], [hour], [minute], [second]).
In the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 CommentCollector.py
```

**On the terminal:** for each found article of the manually appointed time frame, the article link are shown. Firstly, the outlet comments are scraped indicated by the "Direct comment scraping:" message, followed by the reddit scraping indicated by "Reddit comment scraping:" and Twitter Scraping indicated by "Twitter comment scraping:". If there are reddit posts, every post comment scraping is indicated by "reddit comment scraping: [url]", and if there are Twitter tweets, every tweet comment scraping is indicated by "tweet comment scraping: [url]". For a better overview, the number of found articles is printed out before the scraping of the article comments.
![CommentCollector example output](Example_pictures/Direct_Comment_Scraper_Focus_example.png "CommentCollector.py example output clipping")

**In the [date]_[outlet_name]Comments.log:** the process of the comment scraping, including the scraped comments with their corresponding outlet, reddit and twitter links and inserted_id, can be viewed in the log file.

**In the database:**  the database is updated with all the direct news outlet comments, reddit comments and twitter comments of the news articles for the determined time frame.

<a name="cont"></a>
### 4. Continuous scraping

#### 4.1 Article collection: run the NewsArticleCollector (continuous article data collection)

Decomment the continuous program block in the NewsArticleCollector
in the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 NewsArticleCollector.py
```
**On the terminal:** the first line should show the current date and time, after that, the scraping of the RSS feeds of focus.de, spiegel.de, welt.de and zeit.de is started showing for each article, if it is already present in the database or if it was added to the database (with the DataId printed before)
Additionaly, for every reddit article scraping method call there will be a message indicating the start of the program ("Reddit article scraping in process....please wait; this could take a while"). When comment scraping takes place, the scraped post is listed after the program call that found the previously unknown reddit post.

**In the RSS_Scraping.log:** every started NewsArticleCollector progress logs information if an article was added to the database (with the DataId printed before)

**In the [date]_[collection_of_outlet]_Reddit_Scraping.log:** the log file has a much more detailed report of the reddit scraping process including all the found reddit links and a count thereof, the reddit link, how the post is linked to the article (e.q. "cursor found post in database" -> "post already saved") followed by the news article link. When a post is saved as article data structure, the ObjectId is logged as well.  

**In the [date]_[collection_of_outlet]_Twitter_Scraping.log:** the log file has a much more detailed report of the twitter scraping process including all the found twitter links and a count thereof, the twitter link, how the post is linked to the article (e.q. "cursor found post in database" -> "post already saved") followed by the news article link. When a tweet is saved as article data structure, the ObjectId is logged as well.  

**In the database:** the database is updated whenever the NewsArticleCollector, the reddit scraping or the twitter scraping finds a url that is not yet in the database. The update saves the article data structure information that could be scraped from the RSS feed.

Because most news outlets don't have an online archive for their articles, continuous RSS feed scraping brings good article collecting results. It is recommended to run the NewsArticleCollector hourly to not miss potential articles because the zeit.de RSS feed is short and changes regularly. The program is build so the reddit and twitter scraping can only be triggered between 00:00 and 00:59, in line with the automated hourly RSS feed scraping, it will be triggered once a day.
For the continuous scraping, a stable, continuous internet connection is necessary. The MongoDB local server instance should also run continuously stable to prevent potential data losses.

### 4.2 Comment collection
Decomment the *continuous scraping block* of the CommentCollector.py to have the time frames for a day ago, a week ago and a month ago automatically calculated.
In the terminal, navigate to the repository with all the subprograms
type into the terminal
```
python3 CommentCollector.py
```

**On the terminal:** for each found article of calculated time frames a "day"ago, a "week" ago, and a "month" ago, the article link are shown for these days. Firstly, the outlet comments are scraped indicated by the "Direct comment scraping:" message, followed by the reddit scraping indicated by "Reddit comment scraping:" and twitter scraping indicated by "Twitter comment scraping:". If there are reddit posts, every post comment scraping is indicated by "reddit comment scraping: [url]", and if there are twitter tweets, every tweet comment scraping is indicated by "tweet comment scraping: [url]". For a better overview, the number of found articles is printed out before the scraping of the article comments.

**In the [date]_[outlet_name]Comments.log:** the process of the comment scraping, including the scraped comments with their corresponding outlet, reddit and twitter links and inserted_id, can be viewed in the log file.

**In the Database:**  the database is updated with all the direct news outlet comments, reddit comments and twitter comments of the news articles for the determined time frames.
