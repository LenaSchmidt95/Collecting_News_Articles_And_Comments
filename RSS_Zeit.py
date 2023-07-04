from bs4 import BeautifulSoup
from datetime import datetime
import logging
import pymongo
import requests
import time

def extract_ZeitData(url):
    '''Method to extract Zeit.de article data from a given url; return article data structure with extracted article data'''
    # with a stable internet connection, the website with the article can be reached through the url, if not, the data scraping failed and nothing is returned
    try:
        r=requests.get(url)
        html =  r.content
    except Exception as e:
        print('failed Zeit article scraping: ')
        print(e)

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
        pub_date = datetime.fromisoformat(pub_date_cont['content'])
    else:
        pub_date = None

    # check if article is premium content
    if soup.find("meta", {"property":"outbrain:article_access_status"}):
        is_premium_cont = soup.find("meta", {"property":"outbrain:article_access_status"})
        is_premium_cont_con = is_premium_cont['content']
    else:
        is_premium_cont_con = None

    if is_premium_cont_con == "abo":
        is_premium = True
    elif is_premium_cont_con == "free":
        is_premium = False
    else:
        is_premium = None

    # check if article is commentable
    if soup.find("div", {"class":"comment-section__body"}):
        is_commentable_cont = soup.find("div", {"class":"comment-section__body"})
    else:
        is_commentable_cont = None

    if is_commentable_cont:
        is_commentable = True
    else:
        is_commentable = False

    # extraction of article text
    if soup.find("div", {"class":"article-body article-body--article"}):
        text = ""
        article_fullText=soup.find("div", {"class":"article-body article-body--article"})
        if article_fullText:
            article_paywall = soup.find("div", {"class":"paragraph--faded article__item"})
            article_liveblog = soup.find("div", {"class":"tik3-ticker tik3-sportstype-news tik3-ticker--style-tik3 tik3-ticker--locale-de tik3-ticker-wide"})
            if not (article_paywall or article_liveblog):
                article_text = article_fullText.find_all('p') #adjust for best container
                for a in article_text:
                    text = text + a.text + "\n"
            else:
                text= None
        else:
            text = None
    else:
        text = None

    # complete article data structure extracted from article html through article url
    link_article_zeit = {
        "title":title,
        "url":url,
        "description":desc,
        "category":None,
        "publicated": pub_date,
        "premium_content": is_premium,
        "commentable": is_commentable,
        "html": html,
        "text": text,
        "do_date": datetime.now()
    }

    return link_article_zeit



def zeit_rss():
    '''Method to read the rss and convert rss data into rss_article dictionary; returns a list of rss_article dictionaries'''
    rss_article_list = []
    #error handling in try: except:
    try:
        # Zeit RSS feed adress: https://newsfeed.zeit.de/index
        r = requests.get("https://newsfeed.zeit.de/index")
        time.sleep(1)
        soup = BeautifulSoup(r.content, 'xml')
        articles = soup.find_all('item')

        # extract rss feed data and append the cleaned data to the rss_article_list
        for a in articles:
            title = a.find('title').text # title ectraction
            url = a.find('link').text # url extraction
            desc = a.find('description').text # description extraction
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
            rss_article_list.append(rss_article)

        return rss_article_list

    except Exception as e:
        print('failed ZEIT RSS scraping: ')
        print(e)



def zeit_html(url):
    '''method to return the html of a given url'''
    try:
        r=requests.get(url)
        time.sleep(1)
        return r.content

    except Exception as e:
        print('failed ZEIT article scraping: ')
        print(e)


# method to ectract the article text of a given html, assuming the news outlet is spiegel online
def zeit_text(html):
    '''Method to ectract the article text of a given Focus article html; returns article text string'''

    article_textString=" "
    soup = BeautifulSoup(html, 'lxml')
    # the article texts can be found in the <div class = "article-body article-body--article">
    article_fullText=soup.find("div", {"class":"article-body article-body--article"})
    if article_fullText:
        article_paywall = soup.find("div", {"class":"paragraph--faded article__item"})
        article_liveblog = soup.find("div", {"class":"tik3-ticker tik3-sportstype-news tik3-ticker--style-tik3 tik3-ticker--locale-de tik3-ticker-wide"})
        if not (article_paywall or article_liveblog):
            article_text = article_fullText.find_all('p')
            for a in article_text:
                article_textString = article_textString + a.text + "\n"
        else:
            article_textString = "paywall or ticker"
            logging.info("paywall")
    else:
        article_textString = "not text"

    return article_textString



def premium_check_Zeit(html):
    '''Method to check if a Focus article is premium content; returns true if it is premium content and false if not premium content'''
    soup = BeautifulSoup(html, 'lxml')
    is_premium_cont = soup.find("meta", {"property":"outbrain:article_access_status"})
    is_premium_cont_con = is_premium_cont['content']
    if is_premium_cont_con == "abo":
        return True
    elif is_premium_cont_con == "free":
        return False
    else:
        return None



def commentable_check_Zeit(html):
    '''Method to check if a Focus article is commentable; returns true if commentable and false if not commentable'''
    soup = BeautifulSoup(html, 'lxml')
    is_commentable = soup.find("div", {"class":"comment-section__body"})
    if is_commentable:
        return True
    else:
        return False



def zeit_scraping():
    '''Method to scrape Zeit article data from the Zeit RSS feed and save the scraped data in a database (momgodb local instance)'''
    print("begin zeit scraping")

    # the scraping is logged for a better overview and error handling
    logging.basicConfig(filename='RSS_Scraping.log',level = logging.INFO)
    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info("begin Zeit scraping")

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"] # privisional data collection
    ArticleData_Zeit = db["ArticleData_Zeit"]

    #start scraping
    rss_article_list = zeit_rss()
    #finished scraping

    # add data into database
    for a in rss_article_list:
        url_check = False
        # check for existing url in database
        url = a["url"]
        cursor = ArticleData_Zeit.find({"url":url})
        for elem in cursor:
            if elem["url"] == url:
                url_check = True

        if not url_check:
            url = a.get('url')

            # with the help of the zeit_html function, the article html text is extracted and added to the article data to have a extensive backup to extract data from the html
            html = zeit_html(url)
            a.update({"html":html})

            # with the help of the zeit_text function, the article text is extracted from the html
            text = zeit_text(html)

            if ((text == "paywall or ticker") or (text == " ") or (text == "not text")):
                print("Article behind paywall or is a news ticker")
            else:
                # with the help of the premium_check_Zeit function, it is checked whether the news article is premium content or not
                is_premium = premium_check_Zeit(html)
                a.update({"premium_content": is_premium})

                # with the help of the commentable_check_Zeit function, it is checked whether the news article is commentable or not
                is_commentable = commentable_check_Zeit(html)
                a.update({"commentable": is_commentable})

                a.update({"text":text})
                x=db.ArticleData_Zeit.insert_one(a)
                print(x.inserted_id)
                print("Zeit article added to database")
                logging.info(x.inserted_id)
                logging.info("Zeit article added to database")

        else:
            print("Zeit article already in database")
            logging.info("Zeit article already in database")
