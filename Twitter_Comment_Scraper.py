from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
import logging
import os
import pymongo
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from webdriver_manager.chrome import ChromeDriverManager


def twitter_comment_scraper(container):
    '''Method to extract twitter reply information from comment container; returns reply information dictionary '''
    #here, comment and reply are used interchangeably

    # extract username
    if container.find('div', {'dir':'ltr'}):
        smaller_container = container.find('div', {'dir':'ltr'})
        if smaller_container.find('span', {'class':'css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0'}):
            username_cont = smaller_container.find('span', {'class':'css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0'})
            username = username_cont.text
    else:
        username = None

    # extract comment date
    twitter_comm_date = None
    if container.find("time"):
        twitter_comm_date_p1 = container.find("time")['datetime']
        twitter_comm_date = datetime.fromisoformat(twitter_comm_date_p1[:-1])

    # extract comment text
    comment_texts = container.find_all("div", {"data-testid":"tweetText"})
    comment = None
    for comment_cont in comment_texts:
        if container.find("div", {"data-testid":"tweetText"}):
            comment = container.find("div", {"data-testid":"tweetText"}).text

    # comment information dictionary
    twitter_comment = {
        "source_comment":"twitter",
        "username": username,
        "twitter_comm_date" : twitter_comm_date,
        "twitter_comm_do_date": datetime.now(),
        "twitter_comm_text": comment
    }

    return twitter_comment


def click_show_replies(driver):
    '''Method to click all "Show replies" buttons; returns driver with clicked buttons '''

    # click all "Show replies" buttons
    button_showreplies_exists = True
    while button_showreplies_exists: # click as ling as buttons exist
        try:
            driver.find_element(by=By.XPATH, value='//span[@class="css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"]')
        except NoSuchElementException:
            button_showreplies_exists = False

        if button_showreplies_exists:
            # botton location for "Show replies" buttons
            buttons_clickShow = driver.find_elements(by=By.XPATH, value='//span[@class="css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"]')
            c = 0
            d = 0
            try:
                for button in buttons_clickShow:
                    c = c+1
                    if (button.text == "Show replies") or (button.text == "Show"):
                        d = d+1
                    if (button.text == "Show replies") or (button.text == "Show"):
                        driver.execute_script("arguments[0].click();", button) # click buttons like there is no tomorrow
                        time.sleep(1)

            except StaleElementReferenceException:
                print("")

            if ((c == 0) or (d == 0)):
                button_showreplies_exists = False
        else:
            print("")

    # click all "Show more replies" buttons
    button_showMoreReplies_exists = True
    try:
        driver.find_element(by=By.XPATH, value='//div[@role="button"]')
    except NoSuchElementException:
        button_showMoreReplies_exists = False

    if button_showMoreReplies_exists:
        # botton location for "Show more replies" buttons
        button_showMoreReplies = driver.find_elements(by=By.XPATH, value='//div[@role="button"]')
        for button in button_showMoreReplies:
            try:
                if button.text == "Show more replies":
                    time.sleep(3)
                    driver.execute_script("arguments[0].click();", button) #click 'em all!
                    time.sleep(2)
            except StaleElementReferenceException:
                print("")

    return driver


def twitter_comments(url, StartCollection, outlet_url, run):
    '''Method to scrape twitter replies from a twitter tweet; directly saves replies in database (mongodb) '''
    # here, replies and comment are used interchangeably

    #open (local) database to save comment information
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    # select correct database collection to save comment information
    if StartCollection == "ArticleData_Focus":
        Comments_Twitter = db["Comments_Focus_Twitter"]
    elif StartCollection == "ArticleData_Spiegel":
        Comments_Twitter = db["Comments_Spiegel_Twitter"]
    elif StartCollection == "ArticleData_Welt":
        Comments_Twitter = db["Comments_Welt_Twitter"]
    elif StartCollection == "ArticleData_Zeit":
        Comments_Twitter = db["Comments_Zeit_Twitter"]
    else:
        print("ERROR")
        comments = []


    print("twitter comment scraping: " + url)

    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + StartCollection + "_Twitter_Scraping_Comments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)


    # tool for website access
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-logging")
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(2)

    #get all the posts by scrolling to the end of the page until scrolling is not possible anymore
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_further = True
    comments = []
    while scroll_further:

        driver = click_show_replies(driver)

        # collecting all comment container
        soup = BeautifulSoup(driver.page_source, 'lxml')
        append_commentsNAnswers = soup.find_all('div', {'class': ['css-1dbjc4n r-j5o65s r-qklmqi r-1adg3ll r-1ny4l3l', 'css-1dbjc4n r-1adg3ll r-1ny4l3l', 'css-1dbjc4n r-liusvr4 r-16y2uox r-1777fci r-ig955']})
        comments.extend(append_commentsNAnswers)

        # Scroll down to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(2)
        driver = click_show_replies(driver) ####################################################################################################################

        # collecting all comment container
        soup = BeautifulSoup(driver.page_source, 'lxml')
        append_commentsNAnswers = soup.find_all('div', {'class': ['css-1dbjc4n r-j5o65s r-qklmqi r-1adg3ll r-1ny4l3l', 'css-1dbjc4n r-1adg3ll r-1ny4l3l', 'css-1dbjc4n r-liusvr4 r-16y2uox r-1777fci r-ig955']})
        comments.extend(append_commentsNAnswers)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_further = False
            last_height = new_height
        last_height = new_height

    # collecting all comment container
    soup = BeautifulSoup(driver.page_source, 'lxml')
    append_commentsNAnswers = soup.find_all('div', {'class': ['css-1dbjc4n r-j5o65s r-qklmqi r-1adg3ll r-1ny4l3l', 'css-1dbjc4n r-1adg3ll r-1ny4l3l']})
    comments.extend(append_commentsNAnswers)
    driver.close()

    # delete duplicates because of exessive container collection
    comments = list(dict.fromkeys(comments))[1:] # first "comment" is actually tweet itself

    print("begin Twitter comment scraping")
    # save the comments in the database (mongodb)
    count = 0
    id = None
    for comment in comments:
        a = twitter_comment_scraper(comment)

        # update comment information fields
        if id == None:
            a.update({"twitter_parent":"toplevel"})
        else:
            a.update({"twitter_parent": id})
        a.update({"twitter_url":url})
        a.update({"outlet_url": outlet_url})
        a.update({"twitter_run": run})

        # only save actual comments
        if (a['twitter_comm_text'] != None):
            count = count +1
        # # to test twitter_scraper, please comment following block
        #####################################################
            if StartCollection == "ArticleData_Focus":
                x=db.Comments_Focus_Twitter.insert_one(a)
            elif StartCollection == "ArticleData_Spiegel":
                x=db.Comments_Spiegel_Twitter.insert_one(a)
            elif StartCollection == "ArticleData_Welt":
                x=db.Comments_Welt_Twitter.insert_one(a)
            elif StartCollection == "ArticleData_Zeit":
                x=db.Comments_Zeit_Twitter.insert_one(a)
            logging.info(x.inserted_id)

            # id of comment parent
            if comment['class'] == ['css-1dbjc4n', 'r-1adg3ll', 'r-1ny4l3l']:
                id = x.inserted_id
                x = None
            else:
                id = None
        ##################################################### end of block
            logging.info(a)

    logging.info("number of comments: \n" + str(count))


# test post; please comment the marked block nearly at the end of the twitter_comments function to not actually save the comments
# except the "url" (actual twitter url)
# and the "StartCollection" (selection between "ArticleData_Focus", "ArticleData_Spiegel", "ArticleData_Welt" and "ArticleData_Zeit")
# the variables are arbitrarily selectable, they can be seen in the terminal output
# the child parent relationship can't be reflected in testdata because the database inserted id is used as parent child identification

# url = "https://twitter.com/DrSchmidt5/status/1519274234849206272"
# StartCollection = "ArticleData_Focus"
# outlet_url = "https://m.focus.de/politik/experten/gastbeitrag-von-gabor-steingart-50-gepard-panzer-fuer-die-ukraine-bemerkenswert-ist-vor-allem-wie-olaf-scholz-umfaellt_id_90232904.html?utm_source=break.ma&utm_medium=break.ma"
# run = None
# twitter_comments(url, StartCollection, outlet_url, run)
