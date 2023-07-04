from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging
import os
import pymongo
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager


def extractComment(container, parent, depth, url, run):
    '''Method to extract data from a given comment container; method saves the data in mongodb (local instance) '''

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Comments_Spiegel_Direct = db["Comments_Spiegel_Direct"]

    
    # extraction of comment username data
    if container.find("span", {"class":"AuthorName__name___3O4jF"}):
        username_find = container.find("span", {"class":"AuthorName__name___3O4jF"})
        username = username_find.text
    else:
        username = None

    # extraction of the date the comment was made
    if container.find("span", {"class":"CommentTimestamp__timestamp___2Ejbf talk-comment-timestamp TimeAgo__timeago___3aHze talk-comment-timeago"}):
        date_calc_cont = container.find("span", {"class":"CommentTimestamp__timestamp___2Ejbf talk-comment-timestamp TimeAgo__timeago___3aHze talk-comment-timeago"})
        date_calc_all = date_calc_cont['title']
        art_comm_date_p1 = date_calc_all.split()
        art_comm_date_p3 = art_comm_date_p1[0].split("/")
        art_comm_date_p4 = art_comm_date_p3[0] + "/" + art_comm_date_p3[1] + "/" + art_comm_date_p3[2][2:-1]
        if len(art_comm_date_p4) < 8:
            date_calc = "0" +  art_comm_date_p4 + " " + art_comm_date_p1[1]
            art_comm_date_p4 = "0" +  art_comm_date_p4
        else:
            date_calc = art_comm_date_p4 + " " + art_comm_date_p1[1]
        if len(art_comm_date_p1[-2]) < 8:
            date_calc = art_comm_date_p4 + " 0" + art_comm_date_p1[1]
        else:
            date_calc = art_comm_date_p4 + " " + art_comm_date_p1[1]

        art_comm_date = datetime.strptime(date_calc, '%m/%d/%y %H:%M:%S')
        if art_comm_date_p1[-1] == "PM":
            twelve_hours = timedelta(hours = 12)
            art_comm_date = art_comm_date + twelve_hours

    else:
        art_comm_date = None

    # download date is RIGHT NOW
    date_ref = datetime.now()

    # extraction of comment text data
    search_string = "talk-stream-comment talk-stream-comment-level-" + str(depth) + " (.*)"
    if container.find("div",{"class":re.compile(search_string)}):
        if container.find("span", {"class":"Linkify"}):
            container_find_cont = container.find("div",{"class":re.compile(search_string)})
            comment_find = container_find_cont.find_all("span", {"class":"Linkify"})
            comment = ""
            for comment_text in comment_find:
                comment = comment + " \n " + comment_text.text
        else:
            comment = None
    else:
        comment = None

    # collection of extracted data in spiegel_comment dictionary
    spiegel_comment = {
        "source_comment": "direct",
        "source_article": url,
        "username" : username,
        "art_parent": parent,
        "art_comm_date":art_comm_date,
        "art_comm_do_date": date_ref,
        "art_comm_text": comment,
        "direct_run": run
    }
    logging.info(spiegel_comment)

    # save creates comment instance in database, and return instance id
    x=db.Comments_Spiegel_Direct.insert_one(spiegel_comment)
    logging.info(x.inserted_id)

    # recursive call of nested comment instances with parent (returned id)
    depth = depth+1
    search_string = "talk-stream-comment-wrapper talk-stream-comment-wrapper-level-" + str(depth) + " (.*)"
    answers = container.find_all("div", {"class":re.compile(search_string)})
    for a in answers:
        parent = "Parent " + str(depth) + "-1"
        extractComment(a, x.inserted_id, depth, url, run)



def spiegelCommentScraper(url, run):
    '''Method to scrape comments from articles of the focus news outlet '''
    # the scraping is logged for a better overview and error handling

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + "SpiegelComments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(" ")
    logging.info(url)

    # initiation of scraping tool (selenium) with check of website availability
    # after calling a website a short (two seconds) waiting (sleeping) period is executed to not run into website access problems
    # potential problems are logged as warning
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    try: # the initiation of the webdriver can throw an exception, for a more stable execution of the program the exception is expected
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
        pagerun = True
    except requests.exceptions.RequestException as e:
        logging.warning(e)
        print(e)
        time.sleep(5)
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
        pagerun = True
    try:
        driver.get(url)
        time.sleep(2)
        logging.info(url)
    except WebDriverException as site_down:
        logging.warning("page down")
        logging.warning(site_down)
        print(site_down)
        print("page down")
        pagerun = False

    # when the website is actually running and could be reached with the access tool the scraping process starts
    if pagerun:
        # check if there are buttons that give access to more comments
        commentable = True
        try:
            driver.find_element(by=By.XPATH, value='//button[@class="leading-normal font-bold bg-primary-base dark:bg-dm-primary-base inline-block border border-primary-base dark:border-dm-primary-base hover:border-primary-dark focus:border-primary-darker disabled:border-shade-lighter hover:bg-primary-dark focus:bg-primary-darker disabled:bg-shade-lighter dark:disabled:bg-shade-darker disabled:text-shade-dark dark:disabled:text-shade-light disabled:cursor-not-allowed text-white dark:text-shade-lightest font-sansUI pl-24 pr-20 py-12 my-8 text-base rounded outline-focus"]')
        except NoSuchElementException:
            commentable = False

        if commentable: # only when article is commentable
            button_discussion = driver.find_element(by=By.XPATH, value='//button[@class="leading-normal font-bold bg-primary-base dark:bg-dm-primary-base inline-block border border-primary-base dark:border-dm-primary-base hover:border-primary-dark focus:border-primary-darker disabled:border-shade-lighter hover:bg-primary-dark focus:bg-primary-darker disabled:bg-shade-lighter dark:disabled:bg-shade-darker disabled:text-shade-dark dark:disabled:text-shade-light disabled:cursor-not-allowed text-white dark:text-shade-lightest font-sansUI pl-24 pr-20 py-12 my-8 text-base rounded outline-focus"]')
            driver.execute_script("arguments[0].click();",button_discussion )
            time.sleep(2)

            # extract link to comments
            soup = BeautifulSoup(driver.page_source, 'lxml')
            commentLinkO = soup.find("div", {"class":"Talk-embedRoot"})
            if not commentLinkO.iframe is None:
                commentLink = commentLinkO.iframe['src']
            else:
                time.sleep(10)
                commentLinkO = soup.find("div", {"class":"Talk-embedRoot"})
                if not commentLinkO.iframe is None:
                    commentLink = commentLinkO.iframe['src']
                    print(commentLink)
                else:
                    logging.warning("commentlink couldn't be found")
                    time.sleep(15)
                    c = 0
                    while not commentLinkO.iframe is None or c < 5:
                        print("waiting")
                        c = c + 1
                        time.sleep(5)
                commentLink = commentLinkO.iframe['src']

            # switch to comment site
            driver.get(commentLink)
            time.sleep(1)

            # click all "weitere Kommentare" and "weitere Antworten" buttons until there are no buttons left to click
            exists = True
            earlier = time.time() # set time limit in case there is a stubborn button that does not go away, leading to a endless loop
            overtime = False
            while exists:
                try:
                    driver.find_element(by=By.XPATH, value='//div[@class="talk-load-more"] ')
                except NoSuchElementException:
                    exists = False

                later = time.time()
                time_diff = later - earlier
                logging.info("time_diff: " + str(time_diff))

                c = 0 # counting all relevant "Kommentare" and "Antworten" buttons
                d = 0 # counting all clicked buttons
                if exists:
                    button_clickForComments = driver.find_elements(by=By.XPATH, value='//div[@class="talk-load-more"]')
                    c = 0
                    d = 0
                    for a_button in button_clickForComments:
                        try:
                            if a_button.text == ("Weitere Kommentare anzeigen" or "Weitere Antworten anzeigen"):
                                c = c+1

                            button_to_click = a_button.find_element(by=By.XPATH, value='//div[@class="talk-load-more"]/button')
                            try:
                                if (button_to_click.text == "Weitere Kommentare anzeigen") or (button_to_click.text == "Weitere Antworten anzeigen"):
                                    driver.execute_script("arguments[0].click();", button_to_click) # click all the buttons to get all the comments
                                    d = d+1
                            except WebDriverException as e:
                                logging.warning(e)
                                print(e)
                                return None
                            time.sleep(0.5) # wait a little after clicking buttons

                        except StaleElementReferenceException as er:
                            logging.warning(er)
                            print(er)

                if ((c == 0) or (d == 0)): # when all the relevant buttons are clicked move on by leaving loop;
                    exists = False

                if (time_diff > 600): # ckeck time limit of 10 Minutes; move on when time limit is over
                    exists = False
                    logging.warning("time exeeded")
                    overtime = True

            # extract comment data
            soup = BeautifulSoup(driver.page_source, 'lxml')
            comment_container = soup.find_all("div", {"class": re.compile("talk-stream-comment-wrapper talk-stream-comment-wrapper-level-0 Comment__root___3hQ_c Comment__rootLevel0___1rJSw(.*)")}) ##########################################################

            if not overtime: # only when time limit was not overstepped scrape extract comment data
                for container in comment_container:
                    parent = "toplevel"
                    extractComment(container, parent, 0, url, run)
            else:
                logging.warning("news article comment scraping exeeded time limit of 10 Minutes for one news article: ")
                logging.warning(url)

        else:
            # change article data
            logging.warning("problems finding buttons")

    else:
        logging.warning("page down so try again after 10 secs")
        time.sleep(10)
        spiegelCommentScraper(url, None)



# test links to check, if subprogram works: de-comment one of the urls and the last line, run 'python3 Comments_Spiegel.py' in the console (in directory of Comments_Spiegel.py file) -> data is saved in mongodb!!!
#url="https://www.spiegel.de/psychologie/mehr-kompetenz-fuer-die-liebe-konflikte-loesen-statt-streiten-so-geht-s-spiegel-coaching-podcast-a-9857a45f-eb3c-40f8-93aa-b5d9f5f073eb#ref=rss"
#spiegelCommentScraper(url, "test")
