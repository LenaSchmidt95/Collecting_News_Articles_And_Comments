from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
import logging
import os
import pymongo
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
import time
from webdriver_manager.chrome import ChromeDriverManager


def extractComment_Focus(container, parent, url, run):
    '''Method to extract data from a given comment container; method saves the data in mongodb (local instance) '''

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    Comments_Focus_Direct = db["Comments_Focus_Direct"]


    # extraction of comment username data
    if container.find("p", {"class":"user"}):
        user = container.find("p", {"class":"user"})
        if user.find("a"):
            username = user.find("a").text
        else:
            username = None
    else:
        username = None

    # extraction of the date the comment was made
    if user.find("span",{"class":"greydate"}):
        date_calc = user.find("span",{"class":"greydate"}).text
        art_comm_date_p1 = date_calc.split()
        art_comm_date_p2 = art_comm_date_p1[1].split(".")
        art_comm_date_p3 = art_comm_date_p2[0] + "/" + art_comm_date_p2[1] + "/" + art_comm_date_p2[2][2:]
        art_comm_date_p4 = art_comm_date_p3 + " " + art_comm_date_p1[-1]
        art_comm_date = datetime.strptime(art_comm_date_p4, '%d/%m/%y %H:%M')
    else:
        art_comm_date = None

    # download date is RIGHT NOW
    date_ref = datetime.now()

    # extraction of comment text data
    if container.find("p", {"class": "text"}):
        comment = container.find("p", {"class": "text"})
    else:
        comment = None

    # collection of extracted data in focus_comment dictionary
    focus_comment={
        "source_comment": "direct",
        "source_article": url,
        "username": username,
        "art_parent":"toplevel",
        "art_comm_date": art_comm_date,
        "art_comm_do_date": date_ref,
        "art_comm_text": comment.text[18:],
        "direct_run" : run
    }
    logging.info(focus_comment)

    #save comment in database, get id, set id as parent id for comment answers (children of toplevel comments)
    x=db.Comments_Focus_Direct.insert_one(focus_comment)
    logging.info(x.inserted_id)

    parent_id = x.inserted_id

    answers_show = container.find_all("ul", {"class":"answers clearfix"})
    for answer in answers_show: # only answers to comments possible

        # extraction of child username data
        if not answer.find("p", {"class":"user"}) is None:
            user = answer.find("p", {"class":"user"})
            if user.find("a"):
                username = user.find("a").text
            else:
                username = None
        else:
            username = None

        # extraction of the date the child comment was made
        if user.find("span",{"class":"greydate"}):
            date_calc = user.find("span",{"class":"greydate"}).text
            art_comm_date_p1 = date_calc.split()
            art_comm_date_p2 = art_comm_date_p1[1].split(".")
            art_comm_date_p3 = art_comm_date_p2[0] + "/" + art_comm_date_p2[1] + "/" + art_comm_date_p2[2][2:]
            art_comm_date_p4 = art_comm_date_p3 + " " + art_comm_date_p1[-1]
            art_comm_date = datetime.strptime(art_comm_date_p4, '%d/%m/%y %H:%M')
        else:
            art_comm_date = None

        # the download date is RIGHT NOW
        date_ref = datetime.now()

        # extraction of child comment text data
        if answer.find("p", {"class": "text"}):
            answer_text = answer.find("p", {"class": "text"})
        else:
            answer_text = None

        # collection of extracted data in focus_comment dictionary
        focus_comment={
            "source_comment": "direct",
            "source_article": url,
            "username": username,
            "art_parent":parent_id,
            "art_comm_date": art_comm_date,
            "art_comm_do_date": date_ref,
            "art_comm_text": answer_text.text[30:],
            "direct_run": run
        }
        logging.info(focus_comment)
        # save comment data structure in db
        x=db.Comments_Focus_Direct.insert_one(focus_comment)
        logging.info(x.inserted_id)



def focusCommentScraper(url, run):
    '''Method to scrape comments from articles of the focus news outlet '''
    # when calling the method, the measurement of time starts to avoid unnecessary long scraping stuck in while loops triggered by unusual behavior of the website (mistakes on the website)
    before = time.time()

    # the scraping is logged for a better overview and error handling
    date_today = datetime.now()
    filename_logfile = date_today.strftime("%Y%m%d") +"_" + "FocusComments.log"
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
        time.sleep(5) # after ten seconds try to install again, if it can't be installed the scraping process will not be executed
        s=Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options = chrome_options)
        pagerun = True
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

    # when the website is actually running and could be reached with the access tool the scraping process starts
    if pagerun:
        # check if there are buttons that give access to more comments
        # click all the "Weitere Kommentare" and "Weitere Antworten anzeigen" until there are no such buttons left, exposing all comments
        try:
            driver.find_element(by=By.XPATH, value='//a[@class="moreComments bluebutton"]')
            exists_more = True
        except NoSuchElementException:
            logging.info("NoSuchElementException button bluebutton")
            time.sleep(10)
            exists_more = False

        # time management to not run into infinite while loop becuase of unexpected behavior or mistakes on the website
        later = time.time()
        diff_time = later - before
        while exists_more and (diff_time < 600): # time limit is set to 600 seconds = 10 Minutes
            diff_time = later - before
            later = time.time()
            try: # clicking of "Weitere Kommentare"
                driver.find_element(by=By.XPATH, value='//a[@class="moreComments bluebutton"]')
                button_moreComments = driver.find_element(by=By.XPATH, value='//a[@class="moreCommentsAjx bluebutton"]')
                driver.execute_script("arguments[0].click();",button_moreComments) # CLICK ALL THE (relevant) BUTTONS
                time.sleep(1)
            except NoSuchElementException:
                exists_more = False
            try:
                driver.find_element(by=By.XPATH, value='//a[@class="moreCommentsAjx bluebutton"]')
                exists_more = True
            except NoSuchElementException:
                exists_more = False
            if exists_more == True:
                try: # clicking of "Weitere Kommentare"
                    button_moreComments = driver.find_element(by=By.XPATH, value='//a[@class="moreCommentsAjx bluebutton"]')
                    driver.execute_script("arguments[0].click();",button_moreComments) # CLICK MORE (relevant) BUTTONS
                    time.sleep(1)
                except StaleElementReferenceException:
                    logging.warning("StaleElementReferenceException")
                    print("StaleElementReferenceException")
                except NoSuchElementException:
                    exists_more = False

        exists = True
        diff_time = later - before
        while exists and (diff_time < 600):
            diff_time = later - before
            later = time.time()

            # click all the "Weiter Antworten Anzeigen" buttons as long as they exist
            try:
                driver.find_elements(by=By.XPATH, value='//a[@class="allAnswers bluebutton"]')
            except NoSuchElementException:
                exists = False

            if exists:
                button_allAnswers = driver.find_elements(by=By.XPATH, value='//a[@class="allAnswers bluebutton"]')
                for answers in button_allAnswers:
                    driver.execute_script("arguments[0].click();",answers) # CLICK EVEN MORE (relevant) BUTTONS
                    time.sleep(0.5)
            exists = False

        # button clicking to get to all the comments is completed, now the information in the comment containers needs to be extracted
        # all while minding the ten minute time limit
        soup = BeautifulSoup(driver.page_source, 'lxml')
        containers = soup.find_all("div", {"class":re.compile("comment clearfix open oid-(.*)")})
        if diff_time < 600:
            for container in containers:
                extractComment_Focus(container, "toplevel", url, run)
        else:
            logging.warning("over the time limit of 10 Minutes")
            print("over the time limit of 10 Minutes")



# test links to check, if subprogram works: de-comment one of the urls and the last line, run 'python3 Comments_Focus.py' in the console (in directory of Comments_Focus.py file) -> data is saved in mongodb!!!
# url = "https://www.focus.de/politik/ausland/ukraine-krise/krieg-in-der-ukraine-der-eiserne-general-beschert-russland-verluste-die-es-sich-nie-vorstellen-konnte_id_82122743.html"
# url = "https://www.focus.de/panorama/welt/16-jaehriger-verdaechtigt-sek-stuermt-wohnung-polizei-verhindert-amoklauf-an-essener-schule_id_97979252.html"
# focusCommentScraper(url, "test")
