import requests
import os
import re
from bs4 import BeautifulSoup
import lxml
from tqdm import tqdm


def get_pages():
    """获取版面链接"""
    print("Generating page links...")
    base = 'http://en.people.cn/'
    page_dict = {'opinion': '90780', 'politics': '90785', 'world': '90777', 'businss': 'business', 'society': '90882',
                 'culture': '90782', 'sci-tech': '202936', 'sports': '90779', 'latest': '102842'}

    page_list = [base + id for _, id in page_dict.items()]
    return page_list


def get_html(url):
    """获取url对应的HTML"""
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def get_article(url):
    """解析HTML网页，获取文章内容"""
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    try:
        # 获取文章标题
        title = soup.h1.text
        # 获取文章内容
        paragraphs = soup.find('div', attrs={'class': 'w860 d2txtCon cf'}).find_all('p')
        content = ''
        for p in paragraphs:
            if not p.find():
                content += p.text

        content = re.sub(r'\n', '', content)
        resp = title + '!!!!' + content + '\n'
        # print(resp)
        return resp

    except Exception as e:
        print('处理文章失败，错误信息: {}'.format(e))
        return ''


def get_links(page_link):
    """获取某一版面的所有文章链接列表"""
    html = get_html(page_link)
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find('ul', attrs={'class': 'foreign_list8 cf'}).find_all('li')

    article_links = []
    for article in articles:
        link = article.a['href']
        url = 'http://en.people.cn' + link
        article_links.append(url)
    return article_links


def save_articles():
    # 读取文章链接
    with open('china_daily_links.txt', 'r') as f:
        links_str = f.read()
        links = links_str.split('\n')

    with open('china_daily.txt', 'w') as f:
        for link in tqdm(links):
            f.write(get_article(link))


def save_page_links(num_page):
    pages = get_pages()
    page_links = []
    for page in pages:
        print(f"Getting page :{page}")
        for i in range(1, 1 + num_page):
            page_url = page + f'/index{i}.html'
            page_links.extend(get_links(page_url))

    page_links = list(set(page_links))  # 去重
    with open('china_daily_links.txt', 'w') as f:
        f.write('\n'.join(page_links))


if __name__ == "__main__":
    # save_page_links(50)
    save_articles()
    # article = get_article('http://en.people.cn/n3/2023/1009/c90000-20081178.html')
