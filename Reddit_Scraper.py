
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import logging
import pymongo
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time

from RSS_Focus import extract_FocusData
from RSS_Spiegel import extract_SpiegelData
from RSS_Welt import extract_WeltData
from RSS_Zeit import extract_ZeitData
from Reddit_Comment_Scraper import reddit_comment_scraper


def extract_reddit_post(p):
    '''Method to extract post information from a reddit post; returns post information in form of a dictionary '''

    # datetime reference to log the time the information was extracted
    date_ref = datetime.now()
    link = p.find('a', {'data-testid':'outbound-link'})

    if "spiegel.de" in link['href']: # spiegel articles in the database are saved with a "#ref=rss" ending
        link_f_p = link['href'].split("#ref=rss")
        link_f = link_f_p[0] + "#ref=rss"
    else:
        link_f = link['href']

    if p.find('a', {'data-click-id':'body'}):
        reddit_link = p.find('a', {'data-click-id':'body'})
        reddit_link_f = "https://www.reddit.com" + reddit_link['href']
    else:
        reddit_link_f = None

    # calculation of post date from post container
    if p.find("span", {'data-testid':'post_timestamp'}):
        date_calc = p.find("span", {'data-testid':'post_timestamp'}).text
        comm_date_p1 = date_calc.split()
        if "minute" in comm_date_p1[1]:
            minute = timedelta(minutes = int(comm_date_p1[0]))
            reddit_date = date_ref - minute
        elif "hour" in comm_date_p1[1]:
            hour = timedelta(hours = int(comm_date_p1[0]))
            reddit_date = date_ref - hour
        elif "day" in comm_date_p1[1]:
            day = timedelta(days = int(comm_date_p1[0]))
            reddit_date = date_ref - day
        elif "week" in comm_date_p1[1]:
            week = timedelta(weeks = int(comm_date_p1[0]))
            reddit_date = date_ref - week
        elif "month" in comm_date_p1[1]:
            week = timedelta(weeks = 1)
            reddit_date = date_ref - (int(comm_date_p1[0])*4*week)
        elif "year" in comm_date_p1[1]:
            week = timedelta(weeks = 1)
            reddit_date = date_ref - (int(comm_date_p1[0])*52*week)
        else:
            reddit_date = None
    else:
        reddit_date = None

    if p.find("a", {"data-click-id":"body"}):
        bod_cont = p.find("a", {"data-click-id":"body"})
        text = bod_cont.find("h3").text

    # extracted reddit post information
    reddit_scraping = {
        "reddit_postlink" : reddit_link_f,
        "outlet_link" : link_f,
        "post_findDate" : datetime.now(),
        "post_postDate" : reddit_date,
        "post_posttext": text
    }

    return reddit_scraping



def reddit_scraper_article(url, StartCollection):
    '''Method to scrape posts with news article links from reddit '''
    # more detailed comments can be found in the reddit_scraper() function
    print("Reddit article scraping in process....please wait; this could take a while")

    #save data in database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Collection = db[StartCollection]

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + StartCollection + "_Reddit_Scraping_ArticleInfo.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(date_today.strftime("%d/%m/%Y %H:%M:%S"))
    logging.info(url)
    logging.info(StartCollection)

    # Get data from website
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_further = True
    logging.info("begin website scrolling")
    while scroll_further:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_further = False
            last_height = new_height
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.close()
    logging.info("website scrolling completed")
    posts_cont = soup.find_all('div', {'data-testid':'post-container'})

    # extract data
    extracted_posts = []
    count = 0
    logging.info("begin post extraction")
    for p in posts_cont:
        p_extracted = extract_reddit_post(p)
        logging.info(p_extracted)
        extracted_posts.append(p_extracted)
        logging.info(count)
        count = count + 1

    logging.info("completed post extraction of " + str(count) + " reddit posts")
    logging.info("begin saving posts in database (mongodb)")
    for post in extracted_posts:
        if StartCollection == "ArticleData_Focus":
            cursor = db.ArticleData_Focus.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Spiegel":
            cursor = db.ArticleData_Spiegel.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Welt":
            cursor = db.ArticleData_Welt.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Zeit":
            cursor = db.ArticleData_Zeit.find({"url":post['outlet_link']})

        cursor_len = len(list(cursor.clone()))
        if cursor_len > 0:
            logging.info("cursor found post url reference in database")

            for found in cursor:
                if found:
                    if found['url'] == post['outlet_link']:
                        if "reddit_posts" in found:
                            found_posts = found['reddit_posts']

                            find_post = False
                            for post_in_article in found_posts:
                                if post_in_article['reddit_postlink'] == post['reddit_postlink']:
                                    logging.info("post already saved: " + post['reddit_postlink'])
                                    find_post = True

                            if not find_post:
                                logging.info("pushed post onto postLinkList: ")
                                logging.info(found['_id'])

                                if StartCollection == "ArticleData_Focus":
                                    db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                elif StartCollection == "ArticleData_Spiegel":
                                    db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                elif StartCollection == "ArticleData_Welt":
                                    db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                elif StartCollection == "ArticleData_Zeit":
                                    db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                            else:
                                logging.info("post already in data structure")
                                logging.info(post['outlet_link'])

                        else:
                            logging.info("no reddit post field")
                            if StartCollection == "ArticleData_Focus":
                                db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                            elif StartCollection == "ArticleData_Spiegel":
                                db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                            elif StartCollection == "ArticleData_Welt":
                                db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                            elif StartCollection == "ArticleData_Zeit":
                                db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])

                    else:
                        logging.info("no link found")

                        if StartCollection == "ArticleData_Focus":
                            a = extract_FocusData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Focus.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Focus article found on reddit added to database")

                        elif StartCollection == "ArticleData_Spiegel":
                            a = extract_SpiegelData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Spiegel.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Spiegel article found on reddit added to database")

                        elif StartCollection == "ArticleData_Welt":
                            a = extract_WeltData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Welt.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Welt article found on reddit added to database")

                        elif StartCollection == "ArticleData_Zeit":
                            a = extract_ZeitData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Zeit.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Zeit article found on reddit added to database")

        else:
            if StartCollection == "ArticleData_Focus":
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_FocusData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Focus.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Focus article added to database")

            elif StartCollection == "ArticleData_Spiegel":
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_SpiegelData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Spiegel.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Spiegel article added to database")

            elif StartCollection == "ArticleData_Welt":
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_WeltData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Welt.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Welt article added to database")

            elif StartCollection == "ArticleData_Zeit":
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_ZeitData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Zeit.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Zeit article added to database")

    logging.info("completed saving posts in database (mongodb)")


def reddit_scraper(url, StartCollection):
    '''Method to scrape posts (and the posts' comments) with news article links from reddit '''

    print("Reddit article and comment scraping in process....please wait; this could take a while")

    #open (local) database to save extracted post information
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Collection = db[StartCollection]

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d")+"_" + StartCollection + "_Reddit_Scraping_Comments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(date_today.strftime("%d/%m/%Y %H:%M:%S"))
    logging.info(url)
    logging.info(StartCollection)

    # tool to access website
    chrome_options = Options()
    chrome_options.add_argument("--headless") # to not show website
    chrome_options.add_argument("--disable-notifications") # reject nofifications the website inquires
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(2)

    # Get scroll height of website window
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_further = True
    logging.info("begin scrolling")
    while scroll_further: # while scrolling, the height of the website window changes; with this it is possible to scroll to "the end" by scrolling until the height does not change anymore
        # Scroll down to bottom and wait shortly (for page to load)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_further = False
            last_height = new_height
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.close()
    logging.info("scrolling completed")
    posts_cont = soup.find_all('div', {'data-testid':'post-container'}) # location of conatiners containing post information

    # extract post information from post conatiners
    extracted_posts = []
    count = 0
    logging.info("begin post extraction")
    for p in posts_cont:
        p_extracted = extract_reddit_post(p)
        logging.info(p_extracted)
        extracted_posts.append(p_extracted)
        logging.info(count)
        count = count + 1

    logging.info("completed post extraction of " + str(count) + " reddit posts")
    logging.info("begin saving posts in database (mongodb)")
    for post in extracted_posts:
        # selection of the correct mongodb collection
        if StartCollection == "ArticleData_Focus":
            cursor = db.ArticleData_Focus.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Spiegel":
            cursor = db.ArticleData_Spiegel.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Welt":
            cursor = db.ArticleData_Welt.find({"url":post['outlet_link']})
        elif StartCollection == "ArticleData_Zeit":
            cursor = db.ArticleData_Zeit.find({"url":post['outlet_link']})

        cursor_len = len(list(cursor.clone())) # will not consume cursor (hopefully)
        if cursor_len > 0:
            logging.info("cursor found post in database")
            for found in cursor:
                if found:
                    if found['url'] == post['outlet_link']:
                        if "reddit_posts" in found:
                            found_posts = found['reddit_posts']

                            #check if post is already in list of posts
                            find_post = False
                            for post_in_article in found_posts:
                                # the post is in the list: do nothing
                                if post_in_article['reddit_postlink'] == post['reddit_postlink']:
                                    logging.info("post already saved: " + post['reddit_postlink'])
                                    find_post = True

                            if not find_post: # article data structure does not know post yet
                                logging.info("pushed post onto postLinkList: ")
                                logging.info(found['_id'])

                                if StartCollection == "ArticleData_Focus": # selection of correct database collection to save the data
                                    db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                    logging.info("article post comments of existing article:")
                                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                    if len(comments) > 0:
                                        for comment in comments:
                                            if comment:
                                                if 'username' in comment.keys(): # only add actual comments
                                                    comment.update({"outlet_url":post['outlet_link']})
                                                    logging.info(comment)
                                                    y = db.Comments_Focus_Reddit.insert_one(comment)
                                                    logging.info(y.inserted_id)

                                elif StartCollection == "ArticleData_Spiegel": # selection of correct database collection to save the data
                                    db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                    logging.info("article post comments of existing article:")
                                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                    if len(comments) > 0:
                                        for comment in comments:
                                            if comment:
                                                if 'username' in comment.keys(): # only add actual comments
                                                    comment.update({"outlet_url":post['outlet_link']})
                                                    logging.info(comment)
                                                    y = db.Comments_Spiegel_Reddit.insert_one(comment)
                                                    logging.info(y.inserted_id)

                                elif StartCollection == "ArticleData_Welt": # selection of correct database collection to save the data
                                    db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                    logging.info("article post comments of existing article:")
                                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                    if len(comments) > 0:
                                        for comment in comments:
                                            if comment:
                                                if 'username' in comment.keys(): # only add actual comments
                                                    comment.update({"outlet_url":post['outlet_link']})
                                                    logging.info(comment)
                                                    y = db.Comments_Welt_Reddit.insert_one(comment)
                                                    logging.info(y.inserted_id)

                                elif StartCollection == "ArticleData_Zeit": # selection of correct database collection to save the data
                                    db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                    logging.info("article post comments of existing article:")
                                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                    if len(comments) > 0:
                                        for comment in comments:
                                            if comment:
                                                if 'username' in comment.keys(): # only add actual comments
                                                    comment.update({"outlet_url":post['outlet_link']})
                                                    logging.info(comment)
                                                    y = db.Comments_Zeit_Reddit.insert_one(comment)
                                                    logging.info(y.inserted_id)

                            else:
                                logging.info("post already in data structure")
                                logging.info(post['outlet_link'])

                        else:
                            logging.info("no reddit post field")
                            if StartCollection == "ArticleData_Focus":# selection of correct database collection to save the data
                                db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info("article post comments of existing article:")
                                comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                if len(comments) > 0:
                                    for comment in comments:
                                        if comment:
                                            if 'username' in comment.keys(): # only add actual comments
                                                comment.update({"outlet_url":post['outlet_link']})
                                                logging.info(comment)
                                                y = db.Comments_Focus_Reddit.insert_one(comment)
                                                logging.info(y.inserted_id)

                            elif StartCollection == "ArticleData_Spiegel":# selection of correct database collection to save the data
                                db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                                logging.info("article post comments of existing article without former postfield:")
                                comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                if len(comments) > 0:
                                    for comment in comments:
                                        if comment:
                                            if 'username' in comment.keys():# only add actual comments
                                                comment.update({"outlet_url":post['outlet_link']})
                                                logging.info(comment)
                                                y = db.Comments_Spiegel_Reddit.insert_one(comment)
                                                logging.info(y.inserted_id)

                            elif StartCollection == "ArticleData_Welt":# selection of correct database collection to save the data
                                db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                                logging.info("article post comments of existing article without former postfield:")
                                comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                if len(comments) > 0:
                                    for comment in comments:
                                        if comment:
                                            if 'username' in comment.keys():# only add actual comments
                                                comment.update({"outlet_url":post['outlet_link']})
                                                logging.info(comment)
                                                y = db.Comments_Welt_Reddit.insert_one(comment)
                                                logging.info(y.inserted_id)

                            elif StartCollection == "ArticleData_Zeit":# selection of correct database collection to save the data
                                db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"reddit_posts":post}})
                                logging.info(found['_id'])
                                logging.info("article post comments of existing article without former postfield:")
                                comments = reddit_comment_scraper(post['reddit_postlink'], None)
                                if len(comments) > 0:
                                    for comment in comments:
                                        if comment:
                                            if 'username' in comment.keys():# only add actual comments
                                                comment.update({"outlet_url":post['outlet_link']})
                                                logging.info(comment)
                                                y = db.Comments_Zeit_Reddit.insert_one(comment)
                                                logging.info(y.inserted_id)

                    else:
                        logging.info("no link found")

                        #depending on the news outlet:
                        if StartCollection == "ArticleData_Focus":# selection of correct database collection to save the data
                            a = extract_FocusData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Focus.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Focus article found on reddit added to database")

                            # scrape post comments
                            logging.info("article post comments of new article:")
                            comments = reddit_comment_scraper(post['reddit_postlink'], None)
                            if len(comments) > 0:
                                for comment in comments:
                                    if comment:
                                        if 'username' in comment.keys():# only add actual comments
                                            comment.update({"outlet_url":post['outlet_link']})
                                            logging.info(comment)
                                            y = db.Comments_Focus_Reddit.insert_one(comment)
                                            logging.info(y.inserted_id)

                        elif StartCollection == "ArticleData_Spiegel":# selection of correct database collection to save the data
                            a = extract_SpiegelData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Spiegel.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Spiegel article found on reddit added to database")

                            # scrape post comments
                            logging.info("article post comments of new article:")
                            comments = reddit_comment_scraper(post['reddit_postlink'], None)
                            if len(comments) > 0:
                                for comment in comments:
                                    if comment:
                                        if 'username' in comment.keys():# only add actual comments
                                            comment.update({"outlet_url":post['outlet_link']})
                                            logging.info(comment)
                                            y = db.Comments_Spiegel_Reddit.insert_one(comment)
                                            logging.info(y.inserted_id)

                        elif StartCollection == "ArticleData_Welt":# selection of correct database collection to save the data
                            a = extract_WeltData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Welt.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Welt article found on reddit added to database")

                            # scrape post comments
                            logging.info("article post comments of new article:")
                            comments = reddit_comment_scraper(post['reddit_postlink'], None)
                            if len(comments) > 0:
                                for comment in comments:
                                    if comment:
                                        if 'username' in comment.keys():# only add actual comments
                                            comment.update({"outlet_url":post['outlet_link']})
                                            logging.info(comment)
                                            y = db.Comments_Welt_Reddit.insert_one(comment)
                                            logging.info(y.inserted_id)

                        elif StartCollection == "ArticleData_Zeit":# selection of correct database collection to save the data
                            a = extract_ZeitData(post['outlet_link'])
                            a.update({"reddit_posts":[post]})
                            a.update({"source":"reddit"})
                            x = db.ArticleData_Zeit.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Zeit article found on reddit added to database")

                            # scrape post comments
                            logging.info("article post comments of new article:")
                            comments = reddit_comment_scraper(post['reddit_postlink'], None)
                            if len(comments) > 0:
                                for comment in comments:
                                    if comment:
                                        if 'username' in comment.keys():# only add actual comments
                                            comment.update({"outlet_url":post['outlet_link']})
                                            logging.info(comment)
                                            y = db.Comments_Zeit_Reddit.insert_one(comment)
                                            logging.info(y.inserted_id)

        else:
            #depending on the news outlet:
            if StartCollection == "ArticleData_Focus":# selection of correct database collection to save the data
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_FocusData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Focus.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Focus article added to database")

                    # scrape post comments
                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                    if len(comments) > 0:
                        for comment in comments:
                            if comment:
                                if 'username' in comment.keys():
                                    comment.update({"outlet_url":post['outlet_link']})
                                    logging.info(comment)
                                    y = db.Comments_Focus_Reddit.insert_one(comment)
                                    logging.info(y.inserted_id)

            elif StartCollection == "ArticleData_Spiegel":# selection of correct database collection to save the data
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_SpiegelData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Spiegel.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Spiegel article added to database")

                    # scrape post comments
                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                    if len(comments) > 0:
                        for comment in comments:
                            if comment:
                                if 'username' in comment.keys():# only add actual comments
                                    comment.update({"outlet_url":post['outlet_link']})
                                    logging.info(comment)
                                    y = db.Comments_Spiegel_Reddit.insert_one(comment)
                                    logging.info(y.inserted_id)

            elif StartCollection == "ArticleData_Welt":# selection of correct database collection to save the data
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_WeltData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Welt.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Welt article added to database")

                    # scrape post comments
                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                    if len(comments) > 0:
                        for comment in comments:
                            if comment:
                                if 'username' in comment.keys():# only add actual comments
                                    comment.update({"outlet_url":post['outlet_link']})
                                    logging.info(comment)
                                    y = db.Comments_Welt_Reddit.insert_one(comment)
                                    logging.info(y.inserted_id)

            elif StartCollection == "ArticleData_Zeit":# selection of correct database collection to save the data
                logging.info("new article: ")
                logging.info(post['outlet_link'])
                logging.info(post['reddit_postlink'])

                if (post['outlet_link'] != None):
                    a = extract_ZeitData(post['outlet_link'])
                    a.update({"reddit_posts":[post]})
                    a.update({"source":"reddit"})
                    x = db.ArticleData_Zeit.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Zeit article added to database")

                    # scrape post comments
                    comments = reddit_comment_scraper(post['reddit_postlink'], None)
                    if len(comments) > 0:
                        for comment in comments:
                            if comment:
                                if 'username' in comment.keys():# only add actual comments
                                    comment.update({"outlet_url":post['outlet_link']})
                                    logging.info(comment)
                                    y = db.Comments_Zeit_Reddit.insert_one(comment)
                                    logging.info(y.inserted_id)

    logging.info("completed saving posts and comments in database (mongodb)")

# # year block ###########################################################################
#
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=year&sort=relevance"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=year&sort=top"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=year&sort=comments"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=year&sort=new"
# reddit_scraper(url, "ArticleData_Spiegel")
#
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=year&sort=relevance"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=year&sort=top"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=year&sort=comments"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=year&sort=new"
# reddit_scraper(url, "ArticleData_Focus")
#
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=year&sort=relevance"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=year&sort=top"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=year&sort=comments"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=yeark&sort=new"
# reddit_scraper(url, "ArticleData_Welt")
#
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=year&sort=relevance"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=year&sort=top"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=year&sort=comments"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=year&sort=new"
# reddit_scraper(url, "ArticleData_Zeit")


# # month block ###########################################################################
#
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=month&sort=relevance"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=month&sort=top"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=month&sort=comments"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=month&sort=new"
# reddit_scraper(url, "ArticleData_Spiegel")
#
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=month&sort=relevance"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=month&sort=top"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=month&sort=comments"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=month&sort=new"
# reddit_scraper(url, "ArticleData_Focus")
#
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=month&sort=relevance"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=month&sort=top"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=month&sort=comments"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=monthk&sort=new"
# reddit_scraper(url, "ArticleData_Welt")
#
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=month&sort=relevance"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=month&sort=top"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=month&sort=comments"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=month&sort=new"
# reddit_scraper(url, "ArticleData_Zeit")


# # week block ###########################################################################
#
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=week&sort=relevance"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=week&sort=top"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=week&sort=comments"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=week&sort=new"
# reddit_scraper(url, "ArticleData_Spiegel")
#
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=week&sort=relevance"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=week&sort=top"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=week&sort=comments"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=week&sort=new"
# reddit_scraper(url, "ArticleData_Focus")
#
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=week&sort=relevance"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=week&sort=top"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=week&sort=comments"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=week&sort=new"
# reddit_scraper(url, "ArticleData_Welt")
#
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=week&sort=relevance"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=week&sort=top"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=week&sort=comments"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=week&sort=new"
# reddit_scraper(url, "ArticleData_Zeit")


# # day block ###########################################################################
#
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=relevance"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=top"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=comments"
# reddit_scraper(url, "ArticleData_Zeit")
# url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=new"
# reddit_scraper(url, "ArticleData_Zeit")
#
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=relevance"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=top"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=comments"
# reddit_scraper(url, "ArticleData_Welt")
# url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=new"
# reddit_scraper(url, "ArticleData_Welt")
#
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=relevance"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=top"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=comments"
# reddit_scraper(url, "ArticleData_Spiegel")
# url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=new"
# reddit_scraper(url, "ArticleData_Spiegel")
#
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=relevance"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=top"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=comments"
# reddit_scraper(url, "ArticleData_Focus")
# url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=new"
# reddit_scraper(url, "ArticleData_Focus")
