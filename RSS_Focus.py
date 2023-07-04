import requests
from bs4 import BeautifulSoup
import pymongo
import time
from datetime import datetime
import logging


def extract_FocusData(url):
    '''Method to extract Focus.de article data from a given url; return article data structure with extracted article data'''
    html = None
    # with a stable internet connection, the website with the article can be reached through the url, if not, the data scraping failed and nothing is returned
    try:
        r=requests.get(url)
        html = r.content
    except Exception as e:
        print('failed Focus article scraping: ')
        print(e)
        return None

    soup = BeautifulSoup(html, 'lxml')

    # extraction of article title
    title = soup.find("title").text

    # extraction of article description
    if soup.find('meta', {'name':'description'}):
        desc_cont = soup.find('meta', {'name':'description'})
        desc = desc_cont['content']
    else:
        desc = None

    # extraction of articles' date of publication
    if soup.find('meta', {'name':'date'}):
        pub_date_cont = soup.find('meta', {'name':'date'})
        pub_date = datetime.fromisoformat(pub_date_cont['content'])
    else:
        pub_date = None

    # extraction of article text
    if soup.find("div", {"class":"articleContent landscape ps-tracking-position ps-trackingposition_ArticleContent" }):
        article_fullText = soup.find("div", {"class":"articleContent landscape ps-tracking-position ps-trackingposition_ArticleContent" })
    elif soup.find("div", {"class":"articleContent small ps-tracking-position ps-trackingposition_ArticleContent" }) :
        article_fullText = soup.find("div", {"class":"articleContent small ps-tracking-position ps-trackingposition_ArticleContent" })
    else:
        print("could not find text container")
        article_fullText = None
    if article_fullText:
        article_text = article_fullText.find_all('p')
        text = ""
        for a in article_text:
            text = text + a.text + "\n"
    else:
        text = None

    # extraction of article commentability information
    commentable_cont = soup.find("span", {"class": "communityWriteCommentAs"})
    if commentable_cont:
        is_commentable = True
    else:
        is_commentable = False

    # complete article data structure extracted from article html through article url
    link_article_focus = {
        "title":title,
        "url":url,
        "description":desc,
        "category":None,
        "publicated": pub_date,
        "premium_content": False,
        "commentable": is_commentable,
        "html": html,
        "text": text,
        "do_date": datetime.now()
    }

    return link_article_focus



def focus_rss():
    '''Method to read the rss and convert rss data into rss_article dictionary; returns a list of rss_article dictionaries'''
    rss_article_list = []

    try:
        # Focus RSS feed adress: http://rss.focus.de/fol/XML/rss_folnews.xml
        r = requests.get("http://rss.focus.de/fol/XML/rss_folnews.xml")
        time.sleep(1)
        soup = BeautifulSoup(r.content, 'xml')
        articles = soup.find_all('item')

        # extract rss feed data and append the cleaned data to the rss_article_list
        for a in articles:
            title = a.find('title').text # title ectraction
            url = a.find('link').text # url extraction
            desc = a.find('description').text # description extraction
            category = a.find('category').text # category extraction
            #to clean up the data a little leading '\n' and '\t' are deleted
            while (desc.startswith('\n') or desc.startswith('\t')):
                desc = desc[2:]
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
            rss_article_list.append(rss_article)

        return rss_article_list

    except Exception as e:
        print('failed FOCUS RSS scraping: ')
        print(e)
        logging.warning("failed FOCUS RSS scraping: ")
        logging.warning(e)



def focus_html(url):
    '''method to return the html of a given url'''
    try:
        r=requests.get(url)
        time.sleep(1)
        return r.content
    except Exception as e:
        print('failed FOCUS article scraping: ')
        print(e)



def focus_text(html):
    '''Method to ectract the article text of a given Focus article html; returns article text string'''
    soup = BeautifulSoup(html, 'lxml')

    # rule to find the right div: the article text is in either of two containers
    if soup.find("div", {"class":"articleContent landscape ps-tracking-position ps-trackingposition_ArticleContent" }):
        article_fullText = soup.find("div", {"class":"articleContent landscape ps-tracking-position ps-trackingposition_ArticleContent" })
    elif soup.find("div", {"class":"articleContent small ps-tracking-position ps-trackingposition_ArticleContent" }) :
        article_fullText = soup.find("div", {"class":"articleContent small ps-tracking-position ps-trackingposition_ArticleContent" })
    else:
        #print("could not find text container")
        logging.info("could not find text container")

    # the article text can be narrowed down to the p containers in the previously extracted article_fullText container
    article_text = article_fullText.find_all('p')
    article_textString = ""

    # the text elements only need to be concatenated to build the complete article text string
    for a in article_text:
        article_textString = article_textString + a.text + " \n"

    return article_textString



def commentable_check_Focus(html):
    '''Method to check if a Focus article is commentable; returns true if commentable and false if not commentable'''
    soup = BeautifulSoup(html, 'lxml')
    commentable_cont = soup.find("span", {"class": "communityWriteCommentAs"})
    if commentable_cont:
        return True
    else:
        return False



def focus_scraping():
    '''Method to scrape Focus article data from the Focus RSS feed and save the scraped data in a database (momgodb local instance)'''
    # the scraping is logged for a better overview and error handling
    logging.basicConfig(filename='RSS_Scraping.log',level = logging.INFO)
    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info("begin Focus scraping")

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Focus = db["ArticleData_Focus"]

    #start scraping article data with the focus_rss method
    rss_article_list = focus_rss()
    #finished scraping

    # add data into database (local mongodb database localhost:27017)
    for a in rss_article_list:

        # check for existing url in database
        url = a["url"]
        cursor = ArticleData_Focus.find({"url":url})
        url_check = False
        for elem in cursor:
            if elem["url"] == url: #if url is already in the database article data already exists and is not added again
                url_check = True

        if not url_check:
            url = a.get('url')

            # with the help of the focus_html function, the article html text is extracted and added to the article data to have a extensive backup to extract data from the html
            html = focus_html(url)
            a.update({"html":html})

            # the Focus RSS feed does not have premium content
            a.update({"premium_content":False})

            # with the help of the commentable_check_Focus function, it is checked whether the news article is commentable or not
            is_commentable = commentable_check_Focus(html)
            a.update({"commentable": is_commentable})

            # with the help of the focus_text function, the article text is extracted from the html
            text = focus_text(html)
            a.update({"text":text})

            # the complete article data structure is saved in the database
            x=db.ArticleData_Focus.insert_one(a)
            print(x.inserted_id)
            print("Focus article added to database")
            logging.info(x.inserted_id)
            logging.info("Focus article added to database")

        else:
            print("Focus article already in database")
            logging.info("Focus article already in database")
