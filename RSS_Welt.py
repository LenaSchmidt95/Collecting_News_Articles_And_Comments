from bs4 import BeautifulSoup
from datetime import datetime
import logging
import pymongo
import requests
import time

def extract_WeltData(url):
    '''Method to extract Welt.de article data from a given url; return article data structure with extracted article data'''
    html = None
    # with a stable internet connection, the website with the article can be reached through the url, if not, the data scraping failed and nothing is returned
    try:
        r=requests.get(url)
        html =  r.content
    except Exception as e:
        print('failed Welt article scraping: ')
        print(e)
        return None

    soup = BeautifulSoup(html, 'lxml')

    # extraction of article title
    if soup.find('title'):
        title = soup.find('title').text
    else:
        title = None

    # extraction of article description
    if soup.find('meta', {'name':'description'}):
        desc_cont = soup.find('meta', {'name':'description'})
        desc = desc_cont['content']
    else:
        desc = None

    # extraction of articles' date of publication
    if soup.find('meta', {'name':'last-modified'}):
        pub_date_cont = soup.find('meta', {'name':'last-modified'})
        pub_date = datetime.fromisoformat(pub_date_cont['content'][:-1])
    else:
        pub_date = None

    # check if the article is premium content
    if "/plus" in url:
        is_premium = True
    else:
        is_premium = False

    # extraction of article text
    if soup.find("div", {"class":"c-article-text c-content-container __margin-bottom--is-0"}):
        article_fullText=soup.find("div", {"class":"c-article-text c-content-container __margin-bottom--is-0"})######################################
    else:
        article_fullText = None

    # check if the article is text or a video
    if article_fullText:
        article_text = article_fullText.find_all('p') #adjust for best container################################################
        text = ""
        for a in article_text:
            text =text + a.text + "\n"
    else:
        text = None

    # complete article data structure extracted from article html through article url
    link_article_welt = {
        "title":title,
        "url":url,
        "description":desc,
        "category":None,
        "publicated": pub_date,
        "premium_content": is_premium,
        "commentable": True,
        "html": html,
        "text": text,
        "do_date": datetime.now()
    }

    return link_article_welt



def welt_rss():
    '''Method to read the rss and convert rss data into rss_article dictionary; returns a list of rss_article dictionaries'''
    rss_article_list = []

    try:
        # Welt RSS feed adress: https://www.welt.de/feeds/latest.rss
        r = requests.get("https://www.welt.de/feeds/latest.rss")
        time.sleep(1)
        soup = BeautifulSoup(r.content, 'xml')
        articles = soup.find_all('item')

        # extract rss feed data and append the cleaned data to the rss_article_list
        for a in articles:
            title = a.find('title').text # title ectraction
            url = a.find('link').text # url extraction
            if a.find('description'): # description extraction
                desc = a.find('description').text
            else:
                desc = None
            category = a.find('category').text # category extraction
            # date extraction
            pub_date = a.find('pubDate').text
            rss_date_p1 = pub_date.split(",")
            rss_date_p2 = rss_date_p1[1]
            rss_date_p3 = rss_date_p2.split()
            rss_date_p4 = rss_date_p3[0] + "/" + rss_date_p3[1] + "/"  + rss_date_p3[2][2:] + " " + rss_date_p3[3]
            rss_date_pub = datetime.strptime(rss_date_p4, '%d/%b/%y %H:%M:%S')

            # article document with title, url, description, category and publication date extracted from the RSS feed
            rss_article = {
                "title":title,
                "url":url,
                "description":desc,
                "category":category,
                "publicated":rss_date_pub,
                "do_date": datetime.now(),
                "source":"direct"
            }

            # check if the content is premium content, if it is then ignore the article
            if a.find('welt:premium'):
                isPremium = a.find('welt:premium').text
                if not isPremium == 'true':
                    rss_article_list.append(rss_article)
            else:
                rss_article_list.append(rss_article)

        return rss_article_list

    except Exception as e:
        print('failed WELT RSS scraping: ')
        print(e)
        logging.warning("failed Welt RSS scraping: ")
        logging.warning(e)



def welt_html(url):
    '''method to return the html of a given url'''
    try:
        r=requests.get(url)
        time.sleep(1)
        return r.content
    except Exception as e:
        print('failed WELT article scraping: ')
        print(e)



def welt_text(html):
    '''Method to ectract the article text of a given Focus article html; returns article text string'''
    soup = BeautifulSoup(html, 'lxml')

    # rules find the right div
    if soup.find("div", {"class":"c-article-text c-content-container __margin-bottom--is-0"}):
        article_fullText = soup.find("div", {"class":"c-article-text c-content-container __margin-bottom--is-0"})
        article_text = article_fullText.find_all('p')
        article_textString = " "
        for a in article_text:
            article_textString = article_textString + a.text + "\n"
    else:
        article_textString = "not text"

    return article_textString



def premium_check_Welt(url):
    '''Method to check if a Focus article is premium content; returns true if it is premium content and false if not premium content'''
    if "/plus" in url:
        return True
    else:
        return False



def welt_scraping():
    '''Method to scrape Welt article data from the Welt RSS feed and save the scraped data in a database (momgodb local instance)'''

    # the scraping is logged for a better overview and error handling
    logging.basicConfig(filename='RSS_Scraping.log',level = logging.INFO)
    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info("begin Focus scraping")

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Welt = db["ArticleData_Welt"]

    #start scraping
    rss_article_list = welt_rss()
    #finished scraping

    # add data into database
    for a in rss_article_list:

        # check for existing url in database
        url_check = False
        url = a["url"]
        cursor = ArticleData_Welt.find({"url":url})
        for elem in cursor:
            if elem["url"] == url:
                url_check = True


        if not url_check:
            url = a.get('url')

            # with the help of the welt_html function, the article html text is extracted and added to the article data to have a extensive backup to extract data from the html
            html = welt_html(url)
            a.update({"html":html})

            # with the help of the premium_check_Welt function, it is checked whether the news article is premium content or not
            is_premium = premium_check_Welt(url)
            a.update({"premium_content": is_premium})
            a.update({"commentable": True})

            # with the help of the welt_text function, the article text is extracted from the html
            text = welt_text(html)
            a.update({"text":text})
            x=db.ArticleData_Welt.insert_one(a)
            print(x.inserted_id)
            print("Welt article added to database")
            logging.info(x.inserted_id)
            logging.info("Welt article added to database")

        else:
            print("Welt article already in database")
            logging.info("Welt article already in database")
