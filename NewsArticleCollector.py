from datetime import date
from datetime import datetime
from datetime import timedelta

from RSS_Focus import focus_scraping
from RSS_Spiegel import spiegel_scraping
from RSS_Welt import welt_scraping
from RSS_Zeit import zeit_scraping

# from Reddit_Scraper import reddit_scraper_article
# from Twitter_Scraper import twitter_scraper_article

#print(date.today())
now = datetime.now()
print(now.strftime("%d/%m/%Y %H:%M:%S"))
print("start RSS scraping")
# rss news article scraping
focus_scraping()
spiegel_scraping()
welt_scraping()
zeit_scraping()
print("RSS scraping complete")

#######################################################################################
# # continuous program block
#if now.strftime("%H") == "00": # only once a day and not every hour like RSS scraping

    # dayly reddit (article) scraping
    # url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=relevance"
    # reddit_scraper_article(url, "ArticleData_Zeit")
    # url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=top"
    # reddit_scraper_article(url, "ArticleData_Zeit")
    # url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=comments"
    # reddit_scraper_article(url, "ArticleData_Zeit")
    # url = "https://www.reddit.com/search/?q=site%3Azeit.de&t=day&sort=new"
    # reddit_scraper_article(url, "ArticleData_Zeit")
    #
    # url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=relevance"
    # reddit_scraper_article(url, "ArticleData_Welt")
    # url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=top"
    # reddit_scraper_article(url, "ArticleData_Welt")
    # url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=comments"
    # reddit_scraper_article(url, "ArticleData_Welt")
    # url = "https://www.reddit.com/search/?q=site%3Awelt.de&t=day&sort=new"
    # reddit_scraper_article(url, "ArticleData_Welt")
    #
    # url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=relevance"
    # reddit_scraper_article(url, "ArticleData_Spiegel")
    # url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=top"
    # reddit_scraper_article(url, "ArticleData_Spiegel")
    # url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=comments"
    # reddit_scraper_article(url, "ArticleData_Spiegel")
    # url = "https://www.reddit.com/search/?q=site%3Aspiegel.de&t=day&sort=new"
    # reddit_scraper_article(url, "ArticleData_Spiegel")
    #
    # url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=relevance"
    # reddit_scraper_article(url, "ArticleData_Focus")
    # url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=top"
    # reddit_scraper_article(url, "ArticleData_Focus")
    # url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=comments"
    # reddit_scraper_article(url, "ArticleData_Focus")
    # url = "https://www.reddit.com/search/?q=site%3Afocus.de&t=day&sort=new"
    # reddit_scraper_article(url, "ArticleData_Focus")


    # twitter (article) scraping
    # yesterday = now - timedelta(days=1)
    # until_date = now.strftime("%Y-%m-%d")
    # since_date = yesterday.strftime("%Y-%m-%d")

    # url = "https://twitter.com/search?q=focus.de%20until%3A" + until_date + "%20since%3A" + since_date + "%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
    # twitter_scraper_article(url, "ArticleData_Focus")
    # url = "https://twitter.com/search?q=spiegel.de%20until%3A" + until_date + "%20since%3A" + since_date + "%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
    # twitter_scraper_article(url, "ArticleData_Spiegel")
    # url = "https://twitter.com/search?q=welt.de%20until%3A" + until_date + "%20since%3A" + since_date + "%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
    # twitter_scraper_article(url, "ArticleData_Welt")
    # url = "https://twitter.com/search?q=zeit.de%20until%3A" + until_date + "%20since%3A" + since_date + "%20filter%3Alinks%20-filter%3Areplies&src=typed_query&f=top"
    # twitter_scraper_article(url, "ArticleData_Zeit")

#######################################################################################
