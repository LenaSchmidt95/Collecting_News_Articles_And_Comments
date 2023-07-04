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
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager


def extractComment_Zeit(soup, toplevel, url, run):
    '''Method to extract data from a given comment container; method saves the data in mongodb (local instance) '''

    # open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Comments_Zeit_Direct = db["Comments_Zeit_Direct"]

    # extract comment data
    toplevel_commentNumber = toplevel['data-ct-row']

    # extraction of comment username data
    if toplevel.find("a", {"data-ct-label":"user_profile"}):
        username = toplevel.find("a", {"data-ct-label":"user_profile"}).text
    else:
        username = None

    # download date is RIGHT NOW
    date_ref = datetime.now()

    # extraction of the date the comment was made
    if toplevel.find("a", {"data-ct-label":"datum"}):
        art_comm_date_all = toplevel.find("a", {"data-ct-label":"datum"}).text
        if "Uhr" in art_comm_date_all:
            art_comm_date_info_p1 = art_comm_date_all.split()
            day = art_comm_date_info_p1[2][:-1]
            month = art_comm_date_info_p1[3]
            year = art_comm_date_info_p1[4][:-1]
            time = art_comm_date_info_p1[5]
            if month == "Januar":
                month_number = 1
            elif month == "Februar":
                month_number = 2
            elif month == "März":
                month_number = 3
            elif month == "April":
                month_number = 4
            elif month == "Mai":
                month_number = 5
            elif month == "Juni":
                month_number = 6
            elif month == "Juli":
                month_number = 7
            elif month == "August":
                month_number = 8
            elif month == "September":
                month_number = 9
            elif month == "Oktober":
                month_number = 10
            elif month == "November":
                month_number = 11
            elif month == "Dezember":
                month_number = 12
            else:
                month_number = 0
            time_sep = time.split(":")
            art_comm_date = datetime(int(year), month_number, int(day), int(time_sep[0]), int(time_sep[1]), 0 )
        else:
            art_comm_date_info_p1 = art_comm_date_all.split("vor")
            art_comm_date_info_p2 = art_comm_date_info_p1[1].split("\n")
            art_comm_date_info_p3 = art_comm_date_info_p2[0].split()
            if "Minute" in art_comm_date_info_p3[-1]:
                minute = timedelta(minutes = int(art_comm_date_info_p3[0]))
                art_comm_date = date_ref - minute
            elif "Stunde" in art_comm_date_info_p3[-1]:
                hour = timedelta(hours = int(art_comm_date_info_p3[0]))
                art_comm_date = date_ref - hour
            elif "Tag" in art_comm_date_info_p3[-1]:
                day = timedelta(days = int(art_comm_date_info_p3[0]))
                art_comm_date = date_ref - day
            elif "Woche" in art_comm_date_info_p3[-1]:
                week = timedelta(weeks = int(art_comm_date_info_p3[0]))
                art_comm_date = date_ref - week
            elif "Monat" in art_comm_date_info_p3[-1]:
                months = int(art_comm_date_info_p3[0])*(4*(timedelta(weeks = 1)))
                art_comm_date = date_ref - months
            elif "Jahr" in art_comm_date_info_p3[-1]:
                year = timedelta(weeks = 52)
                art_comm_date = date_ref - (int(art_comm_date_p1[1])*year)
            else:
                art_comm_date = None
    else:
        art_comm_date = None

    # extraction of comment text data
    if toplevel.find("div", {"class":"comment__body"}):
        comment = toplevel.find("div", {"class":"comment__body"}).text
        comment = comment[1:]
    else:
        comment = None

    # collection of extracted data in zeit_comment dictionary
    zeit_comment = {
        "source_comment": "direct",
        "source_article": url,
        "username": username,
        "art_parent":"toplevel", # toplevel comment has no parent
        "art_comm_date": art_comm_date,
        "art_comm_do_date": date_ref,
        "art_comm_text": comment,
        "direct_run": run
    }
    logging.info(zeit_comment)


    # save comment data structure in db when it isn't already in the db, return comment _id to link children to parent
    x=db.Comments_Zeit_Direct.insert_one(zeit_comment)
    logging.info(x.inserted_id)

    # information extraction of child comments
    if soup.find_all("article", {"data-ct-row":toplevel_commentNumber}):

        # extract child comments
        count_lower = 0
        children_of_toplevel = soup.find_all("article", {"data-ct-row":toplevel_commentNumber})
        for child in children_of_toplevel:
            lowerLevel_commentNumber = child['data-ct-row']
            if "comment--indented" in str(child['class']):
                count_lower = count_lower + 1
                # extraction of child username
                if child.find("a", {"data-ct-label":"user_profile"}):
                    username = child.find("a", {"data-ct-label":"user_profile"}).text
                else:
                    username = None

                # extraction of the date the child comment was made
                if child.find("a", {"data-ct-label":"datum"}):
                    art_comm_date_all = toplevel.find("a", {"data-ct-label":"datum"}).text
                    if "Uhr" in art_comm_date_all:
                        art_comm_date_info_p1 = art_comm_date_all.split()
                        day = art_comm_date_info_p1[2][:-1]
                        month = art_comm_date_info_p1[3]
                        year = art_comm_date_info_p1[4][:-1]
                        time = art_comm_date_info_p1[5]
                        if month == "Januar":
                            month_number = 1
                        elif month == "Februar":
                            month_number = 2
                        elif month == "März":
                            month_number = 3
                        elif month == "April":
                            month_number = 4
                        elif month == "Mai":
                            month_number = 5
                        elif month == "Juni":
                            month_number = 6
                        elif month == "Juli":
                            month_number = 7
                        elif month == "August":
                            month_number = 8
                        elif month == "September":
                            month_number = 9
                        elif month == "Oktober":
                            month_number = 10
                        elif month == "November":
                            month_number = 11
                        elif month == "Dezember":
                            month_number = 12
                        else:
                            month_number = 0
                        time_sep = time.split(":")
                        art_comm_date = datetime(int(year), month_number, int(day), int(time_sep[0]), int(time_sep[1]), 0 )
                    else:
                        art_comm_date_info_p1 = art_comm_date_all.split("vor")
                        art_comm_date_info_p2 = art_comm_date_info_p1[1].split("\n")
                        art_comm_date_info_p3 = art_comm_date_info_p2[0].split()
                        if "Stunde" in art_comm_date_info_p3[-1]:
                            hour = timedelta(hours = int(art_comm_date_info_p3[0]))
                            art_comm_date = date_ref - hour
                        elif "Tag" in art_comm_date_info_p3[-1]:
                            day = timedelta(days = int(art_comm_date_info_p3[0]))
                            art_comm_date = date_ref - day
                        elif "Woche" in art_comm_date_info_p3[-1]:
                            week = timedelta(weeks = int(art_comm_date_info_p3[0]))
                            art_comm_date = date_ref - week
                        elif "Monat" in art_comm_date_info_p3[-1]:
                            for i  in range(int(art_comm_date_info_p3[0])):
                                months = months + 4*(timedelta(weeks = 1))
                            art_comm_date = date_ref - months
                        elif "Jahr" in art_comm_date_info_p3[-1]:
                            year = timedelta(weeks = 52)
                            art_comm_date = date_ref - (int(art_comm_date_p1[1])*year)
                        else:
                            art_comm_date = None
                else:
                    art_comm_date = None

                # extraction od child comment text data
                if child.find("div", {"class":"comment__body"}):
                    comment = child.find("div", {"class":"comment__body"}).text
                    comment = comment[1:]
                else:
                    comment = None

                # collection of extracted data in zeit_comment_child dictionary
                zeit_comment_child = {
                    "source_comment": "direct",
                    "source_article": url,
                    "username": username,
                    "art_parent": x.inserted_id,
                    "art_comm_date": art_comm_date,
                    "art_comm_do_date": date_ref,
                    "art_comm_text": comment,
                    "direct_run": run
                    }
                logging.info(zeit_comment_child)

                # save comment data structure in db
                x_child=db.Comments_Zeit_Direct.insert_one(zeit_comment_child)
                logging.info(x_child.inserted_id)



def click_moreAnswers(driver, url, run):
    '''Method to click all "more answers" buttons to get to all the comments '''
    # click all relevant buttons to expand comments/replies
    exists = True
    try:
        driver.find_element(by=By.XPATH, value='//button[@class="comment-overlay js-load-comment-replies"]')

    except NoSuchElementException:
        exists = False
    except WebDriverException as e:
        logging.warning(e)
        logging.warning("page crashed")
        print(e)
        exists = False

    if exists: # continue only when page is running
        try:
            driver.find_element(by=By.XPATH, value='//button[@class="comment-overlay js-load-comment-replies"]')
        except NoSuchElementException: # no more weitere Antworten button to click
            exists = False
        if exists:
            button_allAnswers = driver.find_elements(by=By.XPATH, value='//button[@class="comment-overlay js-load-comment-replies"]')
            for button in button_allAnswers:
                driver.execute_script("arguments[0].click();",button) # click buttons
                time.sleep(0.5) # wait shortly after clicking buttons
            exists = False

    # all buttons are clicked, now all comment conatiners need their information extracted
    soup = BeautifulSoup(driver.page_source, 'lxml')
    level_0_comments = soup.find_all("article", {"class":re.compile("comment js-comment-toplevel(.*)")})
    for toplevel in level_0_comments:
        extractComment_Zeit(soup, toplevel, url, run) # extract and save comments



def zeitCommentScraper(url, run):
    '''Method to scrape comments from articles of the zeit news outlet '''
    # when calling the method, the measurement of time starts to avoid unnecessary long scraping stuck in while loops triggered by unusual behavior of the website (mistakes on the website)
    before = time.time()

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + "ZeitComments.log"
    logging.basicConfig(filename=filename_logfile,level = logging.INFO)
    logging.info(" ")
    logging.info(url)

    # initiation of scraping tool (selenium) with check of website availability
    # after calling a website a short (two seconds) waiting (sleeping) period is executed to not run into website access problems
    # potential problems are logged as warning
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    pagerun = True
    try: # the initiation of the webdriver can throw an exception, for a more stable execution of the program the exception is expected
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    except requests.exceptions.RequestException as e:
        logging.warning(e)
        print(e)
        time.sleep(5)
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
    try: # calling the website can throw an exception, if the site can't be reached the scraping process will not be executed
        driver.get(url)
        time.sleep(2)
        logging.info(url)
    except WebDriverException as site_down:
        logging.warning("page down")
        logging.warning(site_down)
        print(site_down)
        print("page down")
        pagerun = False
    except NoSuchWindowException as site_down:
        logging.warning("page down")
        logging.warning(site_down)
        print(site_down)
        print("page down")
        pagerun = False

    # when the website is actually running and could be reached with the access tool the scraping process starts
    if pagerun:
        # firstly, give ad consent for zeit.de
        try:
            driver.find_element(by=By.XPATH, value='//div[@class="option__accbtn box__accbtn"]')
        except NoSuchElementException:
            logging.info("no button_discussion: no such Element")
            print("no button_discussion: no such Element" )
            exists = False
        if driver.find_element(by=By.XPATH, value='//div[@class="option__accbtn box__accbtn"]'):
            consent_butt = driver.find_element(by=By.XPATH, value='//div[@class="option__accbtn box__accbtn"]')
            soup = BeautifulSoup(driver.page_source, 'lxml')
            consent_butt_text = soup.find("div", {"class":"option__accbtn box__accbtn"})
            iFrame_conatiner = consent_butt_text.find("iframe")
            iFrame_id = iFrame_conatiner["id"]
            driver.switch_to.frame(iFrame_id)
            consent_butt_toClick=driver.find_element(by=By.XPATH, value='//button[@title="I Agree"]')
            driver.execute_script("arguments[0].click();",consent_butt_toClick)
            time.sleep(2)
        # ad consent given

        # extraxt comments
        later = time.time() # for time management to not overstep 10 minutes time limit
        diff_time = later - before
        exists_moreCommentsButt = True
        count_commentpages = 0
        while exists_moreCommentsButt and (diff_time < 600): # time limit of 10 minutes
            # time management
            later = time.time()
            diff_time = later - before

            # collect comment of website
            click_moreAnswers(driver, url, run)

            # as long as there are more pages with comments, visit those websites and collect the comments
            try:
                driver.find_element(by=By.XPATH, value='//a[@class="pager__button pager__button--next"]')
            except NoSuchElementException:
                exists_moreCommentsButt = False
            if exists_moreCommentsButt:
                count_commentpages = count_commentpages +1
                more_comments_butt = driver.find_element(by=By.XPATH, value='//a[@class="pager__button pager__button--next"]')
                try:
                    driver.execute_script("arguments[0].click();",more_comments_butt)
                    time.sleep(0.5)
                except WebDriverException:
                    time.sleep(5)
                    logging.warning("page crashed")
                    exists_moreCommentsButt = False



# test links to check, if subprogram works: de-comment one of the urls and the last line, run 'python3 Comments_Zeit.py' in the console (in directory of Comments_Zeit.py file) -> data is saved in mongodb!!!
# url = "https://www.zeit.de/politik/ausland/2022-05/brexit-grossbritannien-nordirlandprotokoll-liz-truss"
# zeitCommentScraper(url, "test" )
