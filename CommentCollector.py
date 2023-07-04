from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pymongo

from Comments_Focus import focusCommentScraper
from Comments_Spiegel import spiegelCommentScraper
from Comments_Welt import weltCommentScraper
from Comments_Zeit import zeitCommentScraper
from Reddit_Comment_Scraper import reddit_comment_scraper
from Twitter_Comment_Scraper import twitter_comments

def focus_Comment_Collection(date_start, date_end, run):
    '''Method to collect focus.de article comments on zeit.de, reddit and twitter'''    

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Focus = db["ArticleData_Focus"]

    db.ArticleData_Focus.create_index([("publicated", pymongo.ASCENDING)])
    # search query for mongodb
    articles = ArticleData_Focus.find({"publicated": {"$gt":date_start, "$lt":date_end}, "premium_content":False}, no_cursor_timeout=True).sort('publicated', pymongo.ASCENDING)

    count = 0
    for article in articles:
        url = article['url']

        # information for the terminal to get a better overview
        print("CommentCollector " + url)
        print(article['publicated'])
        print(count)

        # direct comment scraping
        print("Direct comment scraping: ")
        if article["commentable"] == True:
            print("Article comment scraping")
            focusCommentScraper(url, run)
        else:
            print("Article not commentable on news outlet website")
        count = count +1

        # reddit comment scraping
        print("Reddit comment scraping: ")
        if 'reddit_posts' in article.keys():
            for reddit_post in article['reddit_posts']:
                comments = reddit_comment_scraper(reddit_post['reddit_postlink'], run)

                for comment in comments:
                    if comment:
                        if 'username' in comment.keys():
                            comment.update({"outlet_url":article['url']})
                            y = db.Comments_Focus_Reddit.insert_one(comment)

        # twitter comment scraping
        print("Twitter comment scraping: ")
        if 'twitter_tweets' in article.keys():
            for twitter_tweet in article['twitter_tweets']:
                twitter_comments(twitter_tweet['twitter_tweetLink'], "ArticleData_Focus", twitter_tweet['twitter_outletLink'], run)

    articles.close()



def spiegel_Comment_Collection(date_start, date_end, run):
    '''Method to collect spiegel.de article comments on zeit.de, reddit and twitter'''

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Spiegel = db["ArticleData_Spiegel"]

    db.ArticleData_Spiegel.create_index([("publicated", pymongo.ASCENDING)])
    # search query for mongodb
    articles = ArticleData_Spiegel.find({"publicated": {"$gt":date_start, "$lt":date_end}, "premium_content":False}, no_cursor_timeout=True).sort('publicated', pymongo.ASCENDING)

    count = 0
    for article in articles:
        url = article['url']

        # information for the terminal to get a better overview
        print("CommentCollector " + url)
        print(article['publicated'])
        print(count)

        # direct comment scraping
        print("Direct comment scraping: ")
        if article["commentable"] == True:
            print("Article comment scraping")
            spiegelCommentScraper(url, run)
        else:
            print("Article not commentable on news outlet website")
        count = count +1

        # reddit comment scraping
        print("Reddit comment scraping: ")
        if 'reddit_posts' in article.keys():
            for reddit_post in article['reddit_posts']:
                comments = reddit_comment_scraper(reddit_post['reddit_postlink'], run)

                for comment in comments:
                    if comment:
                        if 'username' in comment.keys():
                            comment.update({"outlet_url":article['url']})
                            y = db.Comments_Spiegel_Reddit.insert_one(comment)

        # twitter comment scraping
        print("Twitter comment scraping: ")
        if 'twitter_tweets' in article.keys():
            for twitter_tweet in article['twitter_tweets']:
                twitter_comments(twitter_tweet['twitter_tweetLink'], "ArticleData_Spiegel", twitter_tweet['twitter_outletLink'], run)

    articles.close()



def welt_Comment_Collection(date_start, date_end, run):
    '''Method to collect zeit.de article comments on welt.de, reddit and twitter'''

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Welt = db["ArticleData_Welt"]

    db.ArticleData_Welt.create_index([("publicated", pymongo.ASCENDING)])
    # search query for mongodb
    articles = ArticleData_Welt.find({"publicated": {"$gt":date_start, "$lt":date_end}, "premium_content":False}, no_cursor_timeout=True).sort('publicated', pymongo.ASCENDING)

    count = 0
    for article in articles:
        url = article['url']

        # information for the terminal to get a better overview
        print("CommentCollector " + url)
        print(article['publicated'])
        print(count)

        # direct comment scraping
        print("Direct comment scraping: ")
        if article["commentable"] == True:
            print("Article comment scraping")
            weltCommentScraper(url, run)
        else:
            print("Article not commentable on news outlet website")
        count = count +1

        # reddit comment scraping
        print("Reddit comment scraping: ")
        if 'reddit_posts' in article.keys():
            for reddit_post in article['reddit_posts']:
                comments = reddit_comment_scraper(reddit_post['reddit_postlink'], run)

                for comment in comments:
                    if comment:
                        if 'username' in comment.keys():
                            comment.update({"outlet_url":article['url']})
                            y = db.Comments_Welt_Reddit.insert_one(comment)

        # twitter comment scraping
        print("Twitter comment scraping: ")
        if 'twitter_tweets' in article.keys():
            for twitter_tweet in article['twitter_tweets']:
                twitter_comments(twitter_tweet['twitter_tweetLink'], "ArticleData_Welt", twitter_tweet['twitter_outletLink'], run)

    articles.close()



def zeit_Comment_Collection(date_start, date_end, run):
    '''Method to collect zeit.de article comments on zeit.de, reddit and twitter'''

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Zeit = db["ArticleData_Zeit"]

    db.ArticleData_Zeit.create_index([("publicated", pymongo.ASCENDING)])
    # search query for mongodb
    articles = ArticleData_Zeit.find({"publicated": {"$gt":date_start, "$lt":date_end}, "premium_content":False}, no_cursor_timeout=True).sort('publicated', pymongo.ASCENDING)


    count = 0
    for article in articles:
        url = article['url']

        # information for the terminal to get a better overview
        print("CommentCollector " + url)
        print(article['publicated'])
        print(count)

        # direct comment scraping
        print("Direct comment scraping: ")
        if article["commentable"] == True:
            print("Article comment scraping")
            zeitCommentScraper(url, run)
        else:
            print("Article not commentable on news outlet website")
        count = count +1

        # reddit comment scraping
        print("Reddit comment scraping: ")
        if 'reddit_posts' in article.keys():
            for reddit_post in article['reddit_posts']:
                comments = reddit_comment_scraper(reddit_post['reddit_postlink'], run)

                for comment in comments:
                    if comment:
                        if 'username' in comment.keys():
                            comment.update({"outlet_url":article['url']})
                            y = db.Comments_Zeit_Reddit.insert_one(comment)

        # twitter comment scraping
        print("Twitter comment scraping: ")
        if 'twitter_tweets' in article.keys():
            for twitter_tweet in article['twitter_tweets']:

                twitter_comments(twitter_tweet['twitter_tweetLink'], "ArticleData_Zeit", twitter_tweet['twitter_outletLink'], run)

    articles.close()

# # continuous scraping block #############################################################################
# # day run
#
# date_today = datetime.now()
#
# date_day = date_today - timedelta(days=1)
# date_start = datetime(date_day.year,date_day.month, date_day.day, 0,0,0)
# date_end = datetime(date_today.year, date_today.month, date_today.day, 0,0,0)
#
# #focus_Comment_Collection(date_start, date_end, "day")
# #spiegel_Comment_Collection(date_start, date_end, "day")
# #welt_Comment_Collection(date_start, date_end, "day")
# #zeit_Comment_Collection(date_start, date_end, "day")
#
# # week run
# date_week_start = date_today - timedelta(days = 1, weeks=1)
# date_week_end = date_today - timedelta(weeks=1)
# date_start = datetime(date_week_start.year,date_week_start.month, date_week_start.day, 0,0,0)
# date_end = datetime(date_week_end.year, date_week_end.month, date_week_end.day, 0,0,0)
#
# #focus_Comment_Collection(date_start, date_end, "week")
# #spiegel_Comment_Collection(date_start, date_end, "week")
# #welt_Comment_Collection(date_start, date_end, "week")
# #zeit_Comment_Collection(date_start, date_end, "week")
#
#
# # month run
# date_month_start = date_today - timedelta(days=31)
# date_month_end = date_today - timedelta(days=30)
# date_start = datetime(date_month_start.year,date_month_start.month, date_month_start.day, 0,0,0)
# date_end = datetime(date_month_end.year, date_month_end.month, date_month_end.day, 0,0,0)
#
# #focus_Comment_Collection(date_start, date_end, "month")
# #spiegel_Comment_Collection(date_start, date_end, "month")
# #welt_Comment_Collection(date_start, date_end, "month")
# #zeit_Comment_Collection(date_start, date_end, "month")
# # End of continuous scraping block ######################################################################



# # individual timeframe block ############################################################################
# # "test" comments can be easily filtered for deletion
# # None indicates past scraping while "test" is to test the comment collection process
# date_start = datetime(2009, 1, 1, 0, 0, 0)
# date_end = datetime(2022, 6, 30, 0, 0, 0)
# focus_Comment_Collection(date_start, date_end, "test")
# spiegel_Comment_Collection(date_start, date_end, "test")
# welt_Comment_Collection(date_start, date_end, "test")
# zeit_Comment_Collection(date_start, date_end, "test")
# # End of individual timeframe block #####################################################################
