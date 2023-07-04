from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
from datetime import timedelta
import pymongo
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time
from webdriver_manager.chrome import ChromeDriverManager


def extractComment_Reddit(comment):
    '''Method to extract reddit comment information; returns data dictionary with comment information '''
    # datetime reference to timestamp the exact time the comment data was extracted
    date_ref = datetime.now()

    # check if container is actually a comment conatiner or not
    not_container = False
    if "continueThread" in comment['id']:
        not_container = True

    if not not_container: # not not actually checks for comment container

        # extract the username
        if comment.find("a", {"data-testid":"comment_author_link"}):
            username = comment.find("a", {"data-testid":"comment_author_link"}).text
        else:
            username = None

        # extract reddit comment id
        reddit_id = comment["id"]

        # find comment parent
        reddit_parent_grabber = comment.find_all("div", {"class":re.compile("_36AIN2ppxy_z-XSDxTvYj5 (.*)")})
        if reddit_parent_grabber:
            if len(reddit_parent_grabber) <= 1:
                reddit_parent = "Toplevel"
            elif len(reddit_parent_grabber) > 1:
                reddit_parent_last = reddit_parent_grabber[-2]
                reddit_parent_parts = reddit_parent_last['class']
                reddit_parent = reddit_parent_parts[-1]
            else:
                reddit_parent = None
        else:
            reddit_parent = None

        # extract comment date
        if comment.find("a", {"data-testid":"comment_timestamp"}):
            date_calc = comment.find("a", {"data-testid":"comment_timestamp"}).text
            art_comm_date_p1 = date_calc.split()
            if "now"in art_comm_date_p1[1]:
                reddit_comm_date = date_ref
            elif "min" in art_comm_date_p1[1]:
                minute = timedelta(minutes = int(art_comm_date_p1[0]))
                reddit_comm_date = date_ref - minute
            elif "hr" in art_comm_date_p1[1]:
                hour = timedelta(hours = int(art_comm_date_p1[0]))
                reddit_comm_date = date_ref - hour
            elif "day" in art_comm_date_p1[1]:
                day = timedelta(days = int(art_comm_date_p1[0]))
                reddit_comm_date = date_ref - day
            elif "week" in art_comm_date_p1[1]:
                week = timedelta(weeks = int(art_comm_date_p1[0]))
                reddit_comm_date = date_ref - week
            elif "month" in art_comm_date_p1[1]:
                week = timedelta(weeks = 1)
                reddit_comm_date = date_ref - (int(art_comm_date_p1[0])*4*week)
            elif "year" in art_comm_date_p1[1]:
                week = timedelta(weeks = 1)
                reddit_comm_date = date_ref - (int(art_comm_date_p1[0])*52*week)
            else:
                reddit_comm_date = None
        else:
            reddit_comm_date = None

        # extract comment text
        if comment.find("div", {"data-testid":"comment"}):
            comment_allText = comment.find("div", {"data-testid":"comment"})
            comment_Text = comment_allText.find_all("p")
            comment = ""
            for comment_text in comment_Text:
                comment = comment + comment_text.text + "\n "
        else:
            comment = None

        # reddit comment dictionary with extracted information
        reddit_comment = {
            "source_comment":"reddit",
            "username": username,
            "reddit_comm_id": reddit_id,
            "reddit_parent": reddit_parent,
            "reddit_comm_date" : reddit_comm_date,
            "reddit_comm_do_date": datetime.now(),
            "reddit_comm_text": comment
        }

        return reddit_comment

def reddit_comment_scraper(url, run):
    '''Method to scrape comment from a given reddit post; returns list of comment data dictionaries '''
    print("reddit comment scraping: " + url)

    # website access tool
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s, options = chrome_options)
    driver.get(url)
    time.sleep(5)

    # click all the "more comments" buttons until the page does not change
    button_morereplies_exists = True
    try:
        driver.find_element(by=By.XPATH, value='//div[starts-with (@id, "moreComments")]')

    except NoSuchElementException:
        button_morereplies_exists = False

    while button_morereplies_exists:
        pagelength_beginning = driver.execute_script("return document.body.scrollHeight")

        # click all the "more replies" buttons to get all the comments
        buttonsMoreReplies = driver.find_elements(by=By.XPATH, value='//div[starts-with (@id, "moreComments")]//p')
        for button in buttonsMoreReplies:
            try:
                driver.execute_script("arguments[0].click();",button)
                time.sleep(0.5)
            except StaleElementReferenceException:
                print("Stale Element")

        time.sleep(3)
        pagelength_afterClicks = driver.execute_script("return document.body.scrollHeight")
        try:
            driver.find_element(by=By.XPATH, value='//div[starts-with (@id, "moreComments")]')
        except NoSuchElementException:
            print("")

        if button_morereplies_exists:
            if pagelength_beginning == pagelength_afterClicks:
                button_morereplies_exists = False


    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.close()

    # find all container with comment information
    comments = soup.find_all("div", {"class":"_3sf33-9rVAO_v4y0pIW_CH"})

    # extract comment information
    comments_output = []
    comment_counter = 0
    for comment in comments:
        save_comment = extractComment_Reddit(comment)
        if save_comment and ('username' in save_comment.keys()):
            save_comment.update({"reddit_url":url})
            save_comment.update({"reddit_run":run})
            comment_counter = comment_counter + 1

        comments_output.append(save_comment)

    return comments_output

# test url:
# url = "https://www.reddit.com/r/de/comments/vf3mue/rückkehr_zur_schuldenbremse_lindner_will/"
# comments = reddit_comment_scraper(url, None)
#
# count = 0
# for comment in comments:
#     if comment:
#         print(comment)
#         count = count + 1
#         print(count)
