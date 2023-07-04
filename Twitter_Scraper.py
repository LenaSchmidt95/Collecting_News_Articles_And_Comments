from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
import logging
import os
import pymongo
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager

from RSS_Focus import extract_FocusData
from RSS_Spiegel import extract_SpiegelData
from RSS_Welt import extract_WeltData
from RSS_Zeit import extract_ZeitData

from Twitter_Comment_Scraper import twitter_comments

def link_og(url):
    '''Method to extract the news outlet link from a internal twitter link'''

    # call url to extract news outlet url
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    try:
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    except Exception as e:
        print(e)
        time.sleep(10)
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    try:
        driver.get(url)
        time.sleep(0.5)
    except WebDriverException:
        print("page not responding")
        time.sleep(10)
        driver.get(url) # try again

    try: # zeit.de has a ad consent wall when calling the article url; consent must be given to access article site
        if driver.find_element(by=By.XPATH, value='//div[@class="option__accbtn box__accbtn"]'):
            consent_butt = driver.find_element(by=By.XPATH, value='//div[@class="option__accbtn box__accbtn"]')
            soup = BeautifulSoup(driver.page_source, 'lxml')
            consent_butt_text = soup.find("div", {"class":"option__accbtn box__accbtn"})
            if consent_butt_text.find("iframe"):
                iFrame_conatiner = consent_butt_text.find("iframe")
                iFrame_id = iFrame_conatiner["id"]
                driver.switch_to.frame(iFrame_id)
                consent_butt_toClick=driver.find_element(by=By.XPATH, value='//button[@title="I Agree"]')
                driver.execute_script("arguments[0].click();",consent_butt_toClick)
                time.sleep(2)
            else:
                print("could not give ad consent")
    except NoSuchElementException:
        if "https://zeit.de" in url:
            print("No Ad consent needed")

    # find url
    soup = BeautifulSoup(driver.page_source, 'lxml')
    link_meta = soup.find('meta', {'property':'og:url'})
    driver.close()

    # return news outlet url
    if link_meta:
        print("link: " + link_meta['content'])
        return link_meta['content']
    else:
        print("cound not find link")
        return None



def extract(posts):
    '''Method to extract article information; returns document with article information'''

    posts_WoDups = list(dict.fromkeys(posts)) # delete dublictaes
    extracted_posts = [] # initialization of list where the article document informations are saved
    for p in posts_WoDups:
        # empty initialization if variables
        link = None
        outlet_link = None
        outlet_link_og = None
        tweet_date = None
        comment = None

        # extract twitter link and tweet post date
        link_cont = p.find('a', {'class': 'css-4rbku5 css-18t94o4 css-901oao r-14j79pv r-1loqt21 r-1q142lx r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0'})
        if link_cont:
            if link_cont['href'] != None:
                link = "https://twitter.com" + link_cont['href'] # extracted twitter link
            else:
                print("extract tweet data: no href of twitter link found")
            # extract tweet date information
            tweet_date_cont = link_cont.find('time')
            tweet_date = tweet_date_cont['datetime']
            tweet_date_f = datetime.fromisoformat(tweet_date[:-1]) # extracted, final tweet date information
        else:
            print("extract tweet data: no twitter link and date container found")

        ## extract news outlet link
        if p.find('a', {'class': 'css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-1ny4l3l r-1udh08x r-o7ynqc r-6416eg r-13qz1uu'}):
            link_out = p.find('a', {'class': 'css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-1ny4l3l r-1udh08x r-o7ynqc r-6416eg r-13qz1uu'})
            if link_out['href']:
                outlet_link = link_out['href']
                outlet_link_og = link_og(outlet_link)
        elif p.find('a', {'class': 'css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-18u37iz r-16y2uox r-1wtj0ep r-1ny4l3l r-o7ynqc r-6416eg'}):
            link_out = p.find('a', {'class': 'css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-18u37iz r-16y2uox r-1wtj0ep r-1ny4l3l r-o7ynqc r-6416eg'})
            if link_out['href']:
                outlet_link = link_out['href']
                outlet_link_og = link_og(outlet_link)
        else:
            print("extract tweet data: no tweet outlet link found")

        # spiegel link adjustment needed; if not adjusted the url can't be found in database
        if outlet_link_og:
            if "https://www.spiegel.de" in outlet_link_og:
                outlet_link_og = outlet_link_og + "#ref=rss"

        # comment text extraction
        if p.find('div', {'data-testid':'tweetText'}):
            text_cont = p.find('div', {'data-testid':'tweetText'})
            text_text = text_cont.find_all('span')
            comment = ""
            for text in text_text:
                comment = comment + text.text

        # twitter tweet data dictionary with extracted tweet data
        twitter_tweetcollector = {
            "twitter_tweetLink" : link,
            "twitter_internalOutLink" : outlet_link,
            "twitter_outletLink" : outlet_link_og,
            "twitter_findDate" : datetime.now(),
            "twitter_tweetDate" : tweet_date_f,
            "twitter_tweettext": comment
        }
        extracted_posts.append(twitter_tweetcollector)

    return extracted_posts


def twitter_scraper_article(url, StartCollection):
    '''Method to scrape twitter tweets'''

    print("Twitter article scraping in process....please wait; this could take a while")

    #open (local) database to save the information of the extracted tweets
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Collection = db[StartCollection]

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + StartCollection + "_Twitter_Scraping.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info(url)


    # accessing website
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(5)

    # first tweet container extraction before scrolling
    soup = BeautifulSoup(driver.page_source, 'lxml')
    posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})

    #get all the posts by scrolling to the end of the page until scrolling is not possible anymore
    logging.info("begin website scrolling")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_height = 0
    scroll_max = driver.execute_script("return document.body.scrollHeight")
    scroll_further = True
    while scroll_further:
        # scroll until no scrolling is possible and bottom of page is reached
        # to not miss tweets the scroll intervall can't be to the bottom of the page (until reload) but must be smaller so all twwwt container are saved
        while (scroll_height-1500) < scroll_max:
            # scrolling
            scroll_diff = scroll_height + 1500
            scriptString = "window.scrollTo(" + str(scroll_height) + ", " + str(scroll_diff) + ");"
            driver.execute_script(scriptString)

            # save tweet container
            soup = BeautifulSoup(driver.page_source, 'lxml')
            append_posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})
            posts.extend(append_posts)

            # continuously, more tweet container are loaded
            scroll_height = scroll_diff
            scroll_max = driver.execute_script("return document.body.scrollHeight")
            time.sleep(1.5)

        # Calculate new scroll height and compare with last scroll height --> scrolling until the absolute bottom of the page is reached
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_further = False
            last_height = new_height
        last_height = new_height

    logging.info("website scrolling completed")

    # to make sure one last tweet container save
    soup = BeautifulSoup(driver.page_source, 'lxml')
    append_posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})
    posts.extend(append_posts)

    driver.close() # all tweet container should be saved from the website, the website access can be closed

    # extract the tweet information from the tweet containers
    logging.info("begin tweet extraction")
    extracted_posts = extract(posts)
    logging.info("tweet extraction completed")

    # show all the extracted tweets (optional)
    count_posts = 0
    for print_post in extracted_posts:
        logging.info(print_post)
        count_posts = count_posts +1
        logging.info(count_posts)


    # save the tweet replies
    logging.info("begin saving tweets in article data structure")
    for post in extracted_posts:
        cursor = Collection.find({"url":post['twitter_outletLink']}) # number of matching articles in database (should be either 0 or 1)
        cursor_len = len(list(cursor.clone())) # will not consume cursor (hopefully)

        if cursor_len > 0: # if cursor_len > 0 a matching article was found
            logging.info("cursor found article url in database")

            for found in cursor:# for every mathing article
                if found:
                    if found['url'] == post['twitter_outletLink']:# check to make sure the tweet link really matches the found article link
                        # when the "twitter_tweets" data field already exists check if the tweet is already saved
                        if "twitter_tweets" in found:
                            found_tweets = found['twitter_tweets']
                            find_tweet = False
                            for tweet_in_article in found_tweets:#check if tweet is already in list of tweets
                                # the tweet is in the list: do nothing
                                if tweet_in_article['twitter_tweetLink'] == post['twitter_tweetLink']:
                                    logging.info("tweet already saved in database: " + post['twitter_tweetLink'])
                                    find_tweet = True

                            if not find_tweet:
                                logging.info("pushed tweet onto tweetLinkList: " )
                                logging.info(found['_id'])

                                # select the right database collection to dave the tweet information
                                if StartCollection == "ArticleData_Focus":
                                    db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Spiegel":
                                    db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Welt":
                                    db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Zeit":
                                    db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})

                        else:
                            logging.info("no twitter tweets field " + post['twitter_outletLink'])

                            # select the right database to update tweet information
                            if StartCollection == "ArticleData_Focus":
                                db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Spiegel":
                                db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Welt":
                                db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Zeit":
                                db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})

                    else: # just to make sure but this case should not reachable
                        logging.info("no link found: " + post['twitter_outletLink'])
                        #depending on the news outlet:
                        if StartCollection == "ArticleData_Focus":
                            a = extract_FocusData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Focus.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Focus article found on Twitter; added to database:" + post['twitter_outletLink'] )

                        elif StartCollection == "ArticleData_Spiegel":
                            a = extract_SpiegelData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Spiegel.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Spiegel article found on Twitter added to database: " + post['twitter_outletLink'] )

                        elif StartCollection == "ArticleData_Welt":
                            a = extract_WeltData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Welt.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Welt article found on Twitter added to database: " + post['twitter_outletLink'] )

                        elif StartCollection == "ArticleData_Zeit":
                            a = extract_ZeitData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Zeit.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Zeit article found on Twitter added to database: " + post['twitter_outletLink'])

        else: # link does not yet exist in database
            #depending on the news outlet:
            if StartCollection == "ArticleData_Focus":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_FocusData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Focus.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Focus article added to database: " + post['twitter_outletLink'])

            elif StartCollection == "ArticleData_Spiegel":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_SpiegelData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Spiegel.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Spiegel article added to database: " + post['twitter_outletLink'])

            elif StartCollection == "ArticleData_Welt":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_WeltData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Welt.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Welt article added to database: " + post['twitter_outletLink'])

            elif StartCollection == "ArticleData_Zeit":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_ZeitData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Zeit.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Zeit article added to database: " + post['twitter_outletLink'])

    logging.info("saving tweets in article data structure completed")



def twitter_scraper(url, StartCollection):
    '''Method to scrape twitter tweets and their comments'''

    print("Twitter article and comment scraping in process....please wait; this could take a while")

    #open (local) database to save the information of the extracted tweets
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Collection = db[StartCollection]

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + StartCollection + "_Twitter_Scraper_Comments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)

    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info(url)


    # accessing website
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-logging")
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(5)

    # first tweet container extraction before scrolling
    soup = BeautifulSoup(driver.page_source, 'lxml')
    posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})

    #get all the posts by scrolling to the end of the page until scrolling is not possible anymore
    logging.info("begin website scrolling")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_height = 0
    scroll_max = driver.execute_script("return document.body.scrollHeight")
    scroll_further = True
    while scroll_further:
        # scroll until no scrolling is possible and bottom of page is reached
        # to not miss tweets the scroll intervall can't be to the bottom of the page (until reload) but must be smaller so all twwwt container are saved
        while (scroll_height-1500) < scroll_max:
            # scrolling
            scroll_diff = scroll_height + 1500
            scriptString = "window.scrollTo(" + str(scroll_height) + ", " + str(scroll_diff) + ");"
            driver.execute_script(scriptString)

            # save tweet container
            soup = BeautifulSoup(driver.page_source, 'lxml')
            append_posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})
            posts.extend(append_posts)

            # continuously, more tweet container are loaded
            scroll_height = scroll_diff
            scroll_max = driver.execute_script("return document.body.scrollHeight")
            time.sleep(1.5)

        # Calculate new scroll height and compare with last scroll height --> scrolling until the absolute bottom of the page is reached
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_further = False
            last_height = new_height
        last_height = new_height

    logging.info("website scrolling completed")

    # to make sure one last tweet container save
    soup = BeautifulSoup(driver.page_source, 'lxml')
    if soup.find('div', {'data-testid':'cellInnerDiv'}):
        append_posts = soup.find_all('div', {'data-testid':'cellInnerDiv'})
        posts.extend(append_posts)

    driver.close() # all tweet container should be saved from the website, the website access can be closed

    # extract the tweet information from the tweet containers
    logging.info("begin tweet extraction")
    extracted_posts = extract(posts)
    logging.info("tweet extraction completed")

    # show all the extracted tweets (optional)
    count_posts = 0
    for print_post in extracted_posts:
        logging.info(print_post)
        count_posts = count_posts +1
        logging.info(count_posts)


    # save the tweet replies
    logging.info("begin saving tweets in article data structure")
    for post in extracted_posts:
        cursor = Collection.find({"url":post['twitter_outletLink']}) # number of matching articles in database (should be either 0 or 1)
        cursor_len = len(list(cursor.clone())) # will not consume cursor (hopefully)

        if cursor_len > 0: # if cursor_len > 0 a matching article was found
            logging.info("cursor found article url in database")

            for found in cursor:# for every mathing article
                if found:
                    if found['url'] == post['twitter_outletLink']:# check to make sure the tweet link really matches the found article link
                        # when the "twitter_tweets" data field already exists check if the tweet is already saved
                        if "twitter_tweets" in found:
                            found_tweets = found['twitter_tweets']
                            find_tweet = False
                            for tweet_in_article in found_tweets:#check if tweet is already in list of tweets
                                # the tweet is in the list: do nothing
                                if tweet_in_article['twitter_tweetLink'] == post['twitter_tweetLink']:
                                    logging.info("tweet already saved in database: " + post['twitter_tweetLink'])
                                    find_tweet = True

                            if not find_tweet:
                                logging.info("pushed tweet onto tweetLinkList: ")
                                logging.info(found['_id'])

                                # select the right database collection to dave the tweet information
                                if StartCollection == "ArticleData_Focus":
                                    db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Spiegel":
                                    db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Welt":
                                    db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                                elif StartCollection == "ArticleData_Zeit":
                                    db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})

                                print("article tweet comments of existing article: " + post['twitter_tweetLink'])
                                twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None) # scrape tweet replies

                        else:
                            logging.info("no twitter tweets field " + post['twitter_outletLink'])

                            # select the right database to update tweet information
                            if StartCollection == "ArticleData_Focus":
                                db.ArticleData_Focus.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Spiegel":
                                db.ArticleData_Spiegel.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Welt":
                                db.ArticleData_Welt.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})
                            elif StartCollection == "ArticleData_Zeit":
                                db.ArticleData_Zeit.update_one({"_id":found['_id']}, {"$push":{"twitter_tweets":post}})

                            print("article tweet comments of existing article without tweets until now: " + post['twitter_tweetLink'])
                            twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)# scrape tweet replies


                    else: # just to make sure but this case should not reachable
                        logging.info("no link found: " + post['twitter_outletLink'])
                        #depending on the news outlet:
                        if StartCollection == "ArticleData_Focus":
                            a = extract_FocusData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Focus.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Focus article found on Twitter; added to database:" + post['twitter_outletLink'] )

                            # scrape tweet comments
                            print("article tweet comments of new article: " + post['twitter_outletLink'] )
                            twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

                        elif StartCollection == "ArticleData_Spiegel":
                            a = extract_SpiegelData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Spiegel.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Spiegel article found on Twitter added to database: " + post['twitter_outletLink'] )

                            # scrape tweet comments
                            print("article tweet comments of new article:" + post['twitter_outletLink'])
                            twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

                        elif StartCollection == "ArticleData_Welt":
                            a = extract_WeltData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Welt.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Welt article found on Twitter added to database: " + post['twitter_outletLink'] )

                            # scrape tweet comments
                            print("article tweet comments of new article: " + post['twitter_outletLink'])
                            twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

                        elif StartCollection == "ArticleData_Zeit":
                            a = extract_ZeitData(post['twitter_outletLink'])
                            a.update({"twitter_tweets":[post]})
                            a.update({"source":"twitter"})
                            x = db.ArticleData_Zeit.insert_one(a)
                            logging.info(x.inserted_id)
                            logging.info("Zeit article found on Twitter added to database: " + post['twitter_outletLink'])

                            # scrape tweet comments
                            print("article tweet comments of new article: " + post['twitter_outletLink'])
                            twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)


        else: # link does not yet exist in database
            #depending on the news outlet:
            if StartCollection == "ArticleData_Focus":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_FocusData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Focus.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Focus article added to database: " + post['twitter_outletLink'])

                    # scrape tweet comments
                    print("article tweet comments of new article: " + post['twitter_outletLink'])
                    twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

            elif StartCollection == "ArticleData_Spiegel":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_SpiegelData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Spiegel.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Spiegel article added to database: " + post['twitter_outletLink'])

                    # scrape tweet comments
                    print("article tweet comments of new article: " + post['twitter_outletLink'])
                    twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

            elif StartCollection == "ArticleData_Welt":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_WeltData(post['twitter_outletLink'])
                    if a:
                        a.update({"twitter_tweets":[post]})
                        a.update({"source":"twitter"})
                        x = db.ArticleData_Welt.insert_one(a)
                        logging.info(a['url'])
                        logging.info(x.inserted_id)
                        logging.info("Welt article added to database: " + post['twitter_outletLink'])

                        # scrape tweet comments
                        print("article tweet comments of new article: " + post['twitter_outletLink'])
                        twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

            elif StartCollection == "ArticleData_Zeit":
                logging.info("new article: " )
                logging.info(post['twitter_outletLink'] )
                logging.info(post['twitter_tweetLink'] )

                if (post['twitter_outletLink'] != None):
                    a = extract_ZeitData(post['twitter_outletLink'])
                    a.update({"twitter_tweets":[post]})
                    a.update({"source":"twitter"})
                    x = db.ArticleData_Zeit.insert_one(a)
                    logging.info(a['url'])
                    logging.info(x.inserted_id)
                    logging.info("Zeit article added to database: " + post['twitter_outletLink'])

                    # scrape tweet comments
                    print("article tweet comments of new article: " + post['twitter_outletLink'])
                    twitter_comments(post['twitter_tweetLink'], StartCollection, post['twitter_outletLink'], None)

    logging.info("saving tweets in article data structure completed")

# scraped from 01.01.2022 to 30.06.2022

# url = "https://twitter.com/search?q=focus.de%20until%3A2022-06-30%20since%3A2022-05-30%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
# twitter_scraper(url, "ArticleData_Focus")

# url = "https://twitter.com/search?q=spiegel.de%20until%3A2022-06-30%20since%3A2022-05-30%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
# twitter_scraper(url, "ArticleData_Spiegel")

# url = "https://twitter.com/search?q=welt.de%20until%3A2022-06-30%20since%3A2022-05-30%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
# twitter_scraper(url, "ArticleData_Welt")

# url = "https://twitter.com/search?q=zeit.de%20until%3A2022-06-30%20since%3A2022-05-30%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
# twitter_scraper(url, "ArticleData_Zeit")
