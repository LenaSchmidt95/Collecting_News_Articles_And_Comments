from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging
import os
import pymongo
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager


def extractComment_Welt(container, parent, url, run):
    '''Method to extract data from a given comment container; method saves the data in mongodb (local instance) '''

    # connection to (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Comments_Welt_Direct = db["Comments_Welt_Direct"]


    # extract username
    if container.find("a", {"name":"la_community_link_to_public_profile"}):
        user = container.find("a", {"name":"la_community_link_to_public_profile"})
        username = user.text
    else:
        username = None

    # download date is RIGHT NOW
    date_ref = datetime.now()

    # extract date comment
    if container.find("div", {"style":"margin-left: 45px; margin-bottom: 0.375rem;"}):
        date_container = container.find("div", {"style":"margin-left: 45px; margin-bottom: 0.375rem;"})
        date_calc = date_container.find("span").text
        art_comm_date_p1 = date_calc.split()
        if "Minute" in art_comm_date_p1[-1]:
            minute = timedelta(minutes = int(art_comm_date_p1[1]))
            art_comm_date = date_ref - minute
        elif "Stunde" in art_comm_date_p1[-1]:
            hour = timedelta(hours = int(art_comm_date_p1[1]))
            art_comm_date = date_ref - hour
        elif "Tag" in art_comm_date_p1[-1]:
            day = timedelta(days = int(art_comm_date_p1[1]))
            art_comm_date = date_ref - day
        elif "Woche" in art_comm_date_p1[-1]:
            week = timedelta(weeks = int(art_comm_date_p1[1]))
            art_comm_date = date_ref - week
        elif "Monat" in art_comm_date_p1[-1]:
            week = timedelta(weeks = 1)
            art_comm_date = date_ref - (int(art_comm_date_p1[1])*4*week)
        elif "Jahr" in art_comm_date_p1[-1]:
            year = timedelta(weeks = 52)
            art_comm_date = date_ref - (int(art_comm_date_p1[1])*year)
        else:
            art_comm_date = None
    else:
        date_calc = None

    # extract comment text data
    if container.find("div", {"style": "font-family: freight, Georgia, serif; font-size: 1.125rem; color: rgb(29, 29, 29); line-height: 1.875rem; overflow-wrap: break-word; white-space: pre-line; padding-right: 3.125rem; margin-left: 45px;"}):
        comment_container = container.find("div", {"style": "font-family: freight, Georgia, serif; font-size: 1.125rem; color: rgb(29, 29, 29); line-height: 1.875rem; overflow-wrap: break-word; white-space: pre-line; padding-right: 3.125rem; margin-left: 45px;"})
        if comment_container.find("span"):
            comment = comment_container.find("span").text
            comment = comment[1:]
        else:
            comment = None
    else:
        comment = None

    # collection of extracted data in welt_comment dictionary
    welt_comment={
        "source_comment": "direct",
        "source_article": url,
        "username": username,
        "art_parent":parent,
        "art_comm_date": art_comm_date,
        "art_comm_do_date": date_ref,
        "art_comm_text": comment,
        "direct_run": run
    }
    logging.info(welt_comment)

    # save comment in database
    x=db.Comments_Welt_Direct.insert_one(welt_comment)
    logging.info(x.inserted_id)

    # extract answers
    answers = container.find_all("div", {"data-qa":"Comment.Child"})
    for answer in answers:

        # extract user name of answer
        if answer.find("a", {"name":"la_community_link_to_public_profile"}):
            user_answer = answer.find("a", {"name":"la_community_link_to_public_profile"})
            username_answer = user_answer.text
        else:
            username_answer = None

        # extract answers' date
        if answer.find("div", {"style":"margin-left: 45px; margin-bottom: 0.375rem;"}):
            date_container_answer = answer.find("div", {"style":"margin-left: 45px; margin-bottom: 0.375rem;"})
            date_calc_answer = date_container_answer.find("span").text
            art_comm_date_p1 = date_calc.split()
            if "Minute" in art_comm_date_p1[-1]:
                minute = timedelta(minutes = int(art_comm_date_p1[1]))
                art_comm_date = date_ref - minute
            elif "Stunde" in art_comm_date_p1[-1]:
                hour = timedelta(hours = int(art_comm_date_p1[1]))
                art_comm_date = date_ref - hour
            elif "Tag" in art_comm_date_p1[-1]:
                day = timedelta(days = int(art_comm_date_p1[1]))
                art_comm_date = date_ref - day
            elif "Woche" in art_comm_date_p1[-1]:
                week = timedelta(weeks = int(art_comm_date_p1[1]))
                art_comm_date = date_ref - week
            elif "Monat" in art_comm_date_p1[-1]:
                week = timedelta(weeks = 1)
                art_comm_date = date_ref - (int(art_comm_date_p1[1])*4*week)
            elif "Jahr" in art_comm_date_p1[-1]:
                year = timedelta(weeks = 52)
                art_comm_date = date_ref - (int(art_comm_date_p1[1])*year)
            else:
                art_comm_date = None
        else:
            date_calc_answer = None

        if answer.find("div", {"style": "font-family: freight, Georgia, serif; font-size: 1.125rem; color: rgb(29, 29, 29); line-height: 1.875rem; overflow-wrap: break-word; white-space: pre-line; padding-right: 3.125rem; margin-left: 45px;"}):
            comment_container_answer = answer.find("div", {"style": "font-family: freight, Georgia, serif; font-size: 1.125rem; color: rgb(29, 29, 29); line-height: 1.875rem; overflow-wrap: break-word; white-space: pre-line; padding-right: 3.125rem; margin-left: 45px;"})
            comment_answer = comment_container_answer.find("span").text
        else:
            comment_answer = None

        # collection of extracted data in welt_comment_answer dictionary
        welt_comment_answer={
            "source_comment": "direct",
            "source_article": url,
            "username": username_answer,
            "art_parent":x.inserted_id,
            "art_comm_date": art_comm_date,
            "art_comm_do_date": date_ref,
            "art_comm_text": comment_answer[1:],
            "direct_run": run
        }
        logging.info(welt_comment_answer)
        # save comment in database
        x=db.Comments_Welt_Direct.insert_one(welt_comment_answer)
        logging.info(x.inserted_id)



def weltCommentScraper(url, run):
    '''Method to scrape comments from articles of the welt news outlet '''
    # when calling the method, the measurement of time starts to avoid unnecessary long scraping stuck in while loops triggered by unusual behavior of the website (mistakes on the website)
    before = time.time()
    # the scraping is logged for a better overview and error handling

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + "WeltComments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(" ")
    logging.info(url)

    # initiation of scraping tool (selenium) with check of website availability
    # after calling a website a short (two seconds) waiting (sleeping) period is executed to not run into website access problems
    # potential problems are logged as warning
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    pagerun = True
    try:
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    except requests.exceptions.RequestException as e:
        logging.warning(e)
        print(e)
        time.sleep(5)
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    try:  # calling the website can throw an exception, if the site can't be reached the scraping process will not be executed
        driver.get(url)
        time.sleep(2)
        logging.info(url)
        print(url)
    except WebDriverException as site_down:
        logging.warning("page down")
        logging.warning(site_down)
        print(site_down)
        print("page down")
        pagerun = False

    # when the website is actually running and could be reached with the access tool the scraping process starts
    if pagerun:
        # to access all comments, all buttons leading to more comments must be clicked
        exists = True # as long as there are buttons that access more comments of the discussion the buttons need to be clicked
        try:
            driver.find_element(by=By.XPATH, value='//div[@style="text-align: center; height: 44px; cursor: pointer;"]') # button to access discussion
        except NoSuchElementException:
            logging.info("no button_discussion: no such Element")
            print("no button_discussion: no such Element" )
            exists = False

        later = time.time()
        diff_time = later - before
        counter = 0
        while exists and (diff_time < 600):
            diff_time = later - before
            later = time.time()

            try:
                driver.find_element(by=By.XPATH, value='//div[@style="text-align: center; height: 44px; cursor: pointer;"]')
            except NoSuchElementException:
                exists = False
                print("no further discussion" )
                time.sleep(1)

            if exists:
                button_allAnswers = driver.find_element(by=By.XPATH, value='//div[@style="text-align: center; height: 44px; cursor: pointer;"]')
                driver.execute_script("arguments[0].click();",button_allAnswers) # buttons are clicked
                time.sleep(1)

        exists_more = True # as ling as there are buttons to load more ansers to comments, the buttons need to be clicked
        try:
            driver.find_element(by=By.XPATH, value='//div[@data-qa="Replies.BottomNav"]')
        except NoSuchElementException:
            exists_more = False

        later = time.time()
        diff_time = later - before
        while exists_more and (diff_time < 600):
            diff_time = later - before
            later = time.time()
            button_commentAnswers = driver.find_elements(by=By.XPATH, value='//div[@data-qa="Replies.BottomNav"]')
            for button in button_commentAnswers:
                driver.execute_script("arguments[0].click();",button) # click more buttons
                time.sleep(1)
            exists_more = False

        # after clicking all the buttons to access all comments, the comments can be extracted
        if diff_time < 600: # time management to not overstep time limit
            soup = BeautifulSoup(driver.page_source, 'lxml')
            containers = soup.find_all("div", {"style":"margin-top: 1.875rem;"}) # find all comment containers
            for container in containers:
                parent = "toplevel"
                extractComment_Welt(container, parent, url, run) # extract all comment information and save data in database
        else:
            logging.warning("exeeded 10 minute time limit")
            print("exeeded 10 minute time limit")

    else:
        logging.warning("page down")
        print("page down")



# test links to check, if subprogram works: de-comment one of the urls and the last line, run 'python3 Comments_Welt.py' in the console (in directory of Comments_Welt.py file) -> data is saved in mongodb!!!
#url = "https://www.welt.de/debatte/kommentare/article238653843/Russlands-Armee-Putin-fuehrt-Krieg-wie-vor-77-Jahren.html"
#weltCommentScraper(url, "test")
