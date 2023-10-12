import logging
import re
from time import sleep

import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm


def create_logger(log_path):
    """将日志输出到日志文件和控制台"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 创建一个handler，用于写入日志文件
    file_handler = logging.FileHandler(filename=log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger


class Crawler:
    def __init__(self, url, column_list, crawl_page_num=10, deiver_wait_time=10, page_wait_time=1):
        """初始化函数
        :param url: 爬取的页面的url
        :param column_list: 爬取栏目的列表
        :param crawl_page_num: 爬取栏目页面的几页（模拟用户点击MORE）
        :param deiver_wait_time: 隐式等待时间（浏览器加载项目最长等待时间）
        :param page_wait_time: 进入页面后等待多久（防止被封ip）
        """
        self.url = url
        self.column_list = column_list
        self.crawl_page_num = crawl_page_num
        self.page_wait_time = page_wait_time
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(deiver_wait_time)
        self.article_links = []
        self.logger = create_logger('logs/crawler.log')

    def crawl(self):
        """爬虫主程序"""
        self.logger.info('开始爬取')
        for column in self.column_list:
            self.logger.info('爬取栏目 {}...'.format(column))
            self.process_column(column)

        # 将所有文章链接存储到文件中
        with open('data/global_times_links.txt', 'w') as f:
            f.write('\n'.join(self.article_links))

        self.browser.quit()
        self.logger.info('爬取完成')

    def process_column(self, column):
        """爬取一个栏目中所有文章链接"""
        column_url = self.url + column + '/index.html'
        self.browser.get(column_url)
        sleep(self.page_wait_time)
        for times in range(self.crawl_page_num):
            # 点击MORE展开一页
            self.browser.find_element(By.CLASS_NAME, "show_more").click()
            sleep(self.page_wait_time)

        source = self.browser.page_source
        self.logger.info('解析栏目 {}...'.format(column))
        try:
            html_tree = etree.HTML(source)
            passage_list = self.process_column_link(html_tree)
            self.article_links.extend(passage_list)  # 存储文章链接
        except Exception as e:
            self.logger.error('解析栏目{} 失败，错误信息: {}'.format(column, e))
        self.logger.info('栏目{} 解析完成'.format(column))

    def process_column_link(self, html_tree):
        """处理页面获取所有文章链接"""
        ret_list = []
        passages_list = html_tree.xpath('//div[@class="level01_list"]//div[@class="list_info"]/a')
        if passages_list:
            for passage in passages_list:
                link = passage.xpath('./@href')[0]
                ret_list.append(link)
        return ret_list


def download_articles():
    # 读取文章链接
    with open('data/global_times_links.txt', 'r') as f:
        links_str = f.read()
        links = links_str.split('\n')

    with open('data/global_times.txt', 'w') as f:
        try:
            for link in tqdm(links):
                f.write(process_passage(link))
        except Exception as e:
            print('处理文章失败，错误信息: {}'.format(e))


def process_passage(link):
    """爬取文章内容"""
    # sleep(1)
    r = requests.get(link)
    html_tree = etree.HTML(r.text)

    content_lst = html_tree.xpath(
        '//div[@class="article_page"]//div[@class="article"]//div[@class="article_content"]//div[@class="article_right"]//br')
    # 找不到文章内容直接退出
    if not content_lst:
        return ''

    # 获取文章内容
    content = ''
    for one_content in content_lst:
        if one_content.tail:
            content = content + one_content.tail.strip()

    content = re.sub(r'\n', '', content)
    # print(content)
    return content + '\n'


if __name__ == '__main__':
    # column_list = ['sport', 'life', 'world', 'In-depth', 'opinion', 'source', 'china']
    #
    # globaltimes_crawler = Crawler('https://www.globaltimes.cn/', column_list, 10)
    # globaltimes_crawler.crawl()
    download_articles()
