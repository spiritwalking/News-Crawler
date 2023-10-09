import requests
import os
import time
import datetime
import re
from bs4 import BeautifulSoup


def get_html(url):
    """
    获取url对应的HTML
    """
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def get_page_links(year, month, day):
    """
    获取指定日期报纸的各版面的链接列表
    """
    url = 'http://paper.people.com.cn/rmrb/html/' + year + '-' + month + '/' + day + '/nbs.D110000renmrb_01.htm'
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    pages = soup.find('div', attrs={'class': 'swiper-container'}).find_all('div', attrs={'class': 'swiper-slide'})

    page_links = []
    for page in pages:
        link = page.a["href"]
        url = 'http://paper.people.com.cn/rmrb/html/' + year + '-' + month + '/' + day + '/' + link
        page_links.append(url)

    return page_links


def get_article_links(year, month, day, page_link):
    """
    获取指定日期报纸某一版面的所有文章链接列表
    """
    html = get_html(page_link)
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find('ul', attrs={'class': 'news-list'}).find_all('li')

    article_links = []
    for article in articles:
        link = article.a['href']
        url = 'http://paper.people.com.cn/rmrb/html/' + year + '-' + month + '/' + day + '/' + link
        article_links.append(url)
    return article_links


def get_article(html):
    """
    解析HTML网页，获取新闻的文章内容
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 获取文章标题
    title = soup.h3.text + '\n' + soup.h1.text + '\n' + soup.h2.text + '\n'

    # 获取文章内容
    paragraphs = soup.find('div', attrs={'id': 'ozoom'}).find_all('p')
    content = ''
    for p in paragraphs:
        content += p.text + '\n'

    resp = title + '!!!!' + content
    return resp


def get_daily_article(year, month, day, destdir):
    """
    爬取人民日报指定日期的新闻内容，并保存在指定目录下
    """
    articles = ""
    page_links = get_page_links(year, month, day)
    for page in page_links:
        article_links = get_article_links(year, month, day, page)
        for url in article_links:
            # 获取新闻文章内容
            html = get_html(url)
            article = get_article(html)
            cleaned_article = clean_article(article)
            articles += cleaned_article
    return articles


def clean_article(article):
    if len(article) < 30:
        return ''
    else:
        article = re.sub(r'\s+', '', article)  # 去除空格、换行符等
        return article+'\n'


def gen_dates(base_date, days):
    day = datetime.timedelta(days=1)
    for i in range(days):
        yield base_date + day * i


def get_date_list(begin_date, end_date):
    """
    生成日期列表
    """
    start = datetime.datetime.strptime(begin_date, "%Y%m%d")
    end = datetime.datetime.strptime(end_date, "%Y%m%d")

    days = []
    for d in gen_dates(start, (end - start).days):
        days.append(d)

    return days


if __name__ == '__main__':
    beginDate = '20200701'
    endDate = '20231001'
    data = get_date_list(beginDate, endDate)

    destdir = "rmrb.txt"
    with open(destdir, 'w', encoding='utf-8') as f:
        for d in data:
            year = str(d.year)
            month = str(d.month) if d.month >= 10 else '0' + str(d.month)
            day = str(d.day) if d.day >= 10 else '0' + str(d.day)

            daily_article = get_daily_article(year, month, day, destdir)
            f.write(daily_article)
            print("爬取完成：" + year + month + day)
            time.sleep(2)
