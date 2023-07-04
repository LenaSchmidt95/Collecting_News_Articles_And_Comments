import requests
from bs4 import BeautifulSoup
import pymongo
import time
from datetime import datetime
import logging


def extract_SpiegelData(url):
    '''Method to extract Spiegel.de article data from a given url; return article data structure with extracted article data'''

    html = None
    # with a stable internet connection, the website with the article can be reached through the url, if not, the data scraping failed and nothing is returned
    try:
        r=requests.get(url)
        html =  r.content
    except Exception as e:
        print('failed SPIEGEL article scraping: ')
        print(e)

    soup = BeautifulSoup(html, 'lxml')

    # extraction of article title
    if soup.find('meta', {'property':'og:title'}):
        title_cont = soup.find('meta', {'property':'og:title'})
        title = title_cont['content']
    elif soup.find('title'):
        title = soup.find('title').text
    else:
        title = None

    # extraction of article description
    if soup.find('meta', {'property':'og:description'}):
        desc_cont = soup.find('meta', {'property':'og:description'})
        desc = desc_cont['content']
    else:
        desc = None

    if soup.find('meta', {'property':'og:type'}):
        category_cont = soup.find('meta', {'property':'og:type'})
        category = category_cont['content']
    else:
        category = None

    # extraction of articles' date of publication
    if soup.find('meta', {'name':'last-modified'}):
        pub_date_cont = soup.find('meta', {'name':'last-modified'})
        pub_date = datetime.fromisoformat(pub_date_cont['content'])
    elif soup.find('time'):
        pub_date_cont = soup.find('time')
        try:
            pub_date = datetime.strptime(pub_date_cont['datetime'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pub_date = None
    else:
        pub_date = None

    # check if article is premium content
    if soup.find('meta', {'property': 'og:title'}):
        content_cont = soup.find('meta', {'property': 'og:title'})
        content = content_cont['content']
    else:
        content = None

    if content:
        if "(S+)" in content:
            is_premium =  True
        else:
            is_premium = False
    else:
        if soup.find('span', {'class':'text-white font-bold mt-4 mr-8 leading-normal'}):
            s_plus = soup.find('span', {'class':'text-white font-bold mt-4 mr-8 leading-normal'})
            if s_plus.text == "Weiterlesen mit ":
                is_premium =  True
            else:
                is_premium =  False
        else:
            is_premium = None

    # check if article is commentable
    commentable_cont = soup.find_all("span", {"class":"relative bottom-px"})
    is_commentable = False
    for possible_commentable in commentable_cont:
        if possible_commentable.text == "Diskutieren Sie mit":
            is_commentable = True

    # extraction of article text
    if soup.find("div", {"class":"relative", "data-article-el":"body" }):
        article_fullText = soup.find("div", {"class":"relative", "data-article-el":"body" })
        article_text = article_fullText.find_all('p') #adjust for best container
        text = ""
        for a in article_text:
            text = text + a.text + "\n"
    else:
        text = None

    # complete article data structure extracted from article html through article url
    link_article = {
        "title":title,
        "url":url,
        "description":desc,
        "category":category,
        "publicated": pub_date,
        "premium_content": is_premium,
        "commentable": is_commentable,
        "html": html,
        "text": text,
        "do_date": datetime.now()
    }

    return link_article



def spiegel_rss():
    '''Method to read the rss and convert rss data into rss_article dictionary; returns a list of rss_article dictionaries'''
    rss_article_list = []

    try:
        # Spiegel RSS feed adress: https://www.spiegel.de/schlagzeilen/index.rss
        r=requests.get('https://www.spiegel.de/schlagzeilen/index.rss') # SPIEGEL.de komplett – RSS-Feed mit allen Artikeln
        time.sleep(1)
        soup = BeautifulSoup(r.content, 'xml')
        articles = soup.find_all('item')

        # extract rss feed data and append the cleaned data to the rss_article_list
        for a in articles:
            title = a.find('title').text # title ectraction
            url = a.find('link').text # url extraction
            desc = a.find('description').text # description extraction
            category = a.find('category').text # category extraction
            #date extraction
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
        print('failed SPIEGEL RSS scraping: ')
        print(e)
        logging.warning("failed Spiegel RSS scraping: ")
        logging.warning(e)



def spiegel_html(url):
    '''method to return the html of a given url'''
    try:
        r=requests.get(url)
        time.sleep(1)
        return r.content
    except Exception as e:
        print('failed SPIEGEL article scraping: ')
        print(e)



# method to ectract the article text of a given html, assuming the news outlet is spiegel online
def spiegel_text(html):
    '''Method to ectract the article text of a given Focus article html; returns article text string'''
    soup = BeautifulSoup(html, 'lxml')

    # rule to find the right div
    article_fullText=soup.find("div", {"class":"relative", "data-article-el":"body" })
    article_text = article_fullText.find_all('p')
    article_textString = " "
    for a in article_text:
        article_textString = article_textString + a.text + "\n"

    return article_textString



def commentable_check(html):
    '''Method to check if a Spiegel article is commentable; returns true if it is commentable and false if not commentable'''
    soup = BeautifulSoup(html, 'lxml')
    commentable_cont = soup.find_all("span", {"class":"relative bottom-px"})
    is_commentable = False
    for possible_commentable in commentable_cont:
        if possible_commentable.text == "Diskutieren Sie mit":
            is_commentable = True
    return is_commentable



def premium_check(html):
    '''Method to check if a Spiegel article is premium content; returns true if it is premium content and false if not premium content'''
    soup = BeautifulSoup(html, 'lxml')
    content_cont = soup.find('meta', {'property': 'og:title'})
    content = content_cont['content']
    if "(S+)" in content:
        return True
    else:
        return False


def spiegel_scraping():
    '''Method to scrape Spiegel article data from the Spiegel RSS feed and save the scraped data in a database (momgodb local instance)'''

    # the scraping is logged for a better overview and error handling
    logging.basicConfig(filename='RSS_Scraping.log',level = logging.INFO)
    logging.info(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logging.info("begin Focus scraping")

    #open (local) database
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["NewsAndComments_prov"]
    ArticleData_Spiegel = db["ArticleData_Spiegel"]

    #start scraping
    rss_article_list = spiegel_rss()
    #finished scraping

    # add data into database
    for a in rss_article_list:

        # check for existing url in database
        url_check = False
        url = a["url"]
        cursor = ArticleData_Spiegel.find({"url":url})
        for elem in cursor:
            if elem["url"] == url:
                url_check = True

        # only when the article title is not in the database the data is added
        if not url_check:
            url = a.get('url')

            # with the help of the spiegel_html function, the article html text is extracted and added to the article data to have a extensive backup to extract data from the html
            html = spiegel_html(url)

            # with the help of the premium_check_Spiegel function, it is checked whether the news article is premium content or not
            is_premium = premium_check(html)
            a.update({"premium_content": is_premium})

            # with the help of the commentable_check_Spiegel function, it is checked whether the news article is commentable or not
            is_commentable = commentable_check(html)
            a.update({"commentable": is_commentable})

            # with the help of the spiegel_text function, the article text is extracted from the html
            a.update({"html":html})
            text = spiegel_text(html)
            a.update({"text":text})
            x=db.ArticleData_Spiegel.insert_one(a)
            print(x.inserted_id)
            print("Spiegel article added to database")
            logging.info(x.inserted_id)
            logging.info("Spiegel article added to database")

        else:
            print("Spiegel article already in database")
            logging.info("Spiegel article already in database")
