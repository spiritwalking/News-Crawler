import xlrd
import xlwt
import time
import logging
import xlutils.copy
from time import sleep
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.DEBUG)


class crawler:
    """ 环球时报新闻爬取类

    类实现了爬取环球时报各个栏目下的一定数量的文章并将其存入excel文件中

    Auther: Gy

    Attributes:
        url : 爬取的页面的url
        column_dict : 爬取栏目字典（中文目前未使用）
        excel_file_name : 保存文档名
        crawl_page_num : 爬取栏目页面的几页（模拟用户点击MORE）
        deiver_wait_time : 隐式等待（浏览器加载项目最长等待时间）
        passage_wait_time : 进入页面后等待多久

    """

    def __init__(self, url, column_dict, crawl_page_num=10, deiver_wait_time=10, page_wait_time=1):
        """ 初始化 """
        self.url = url
        self.column_dict = column_dict
        self.crawl_page_num = crawl_page_num
        self.page_wait_time = page_wait_time
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(deiver_wait_time)
        self.article_links = []

    def crawl(self):
        """开始爬取"""
        logging.info('开始爬取')
        for column, column_name in self.column_dict.items():
            logging.info('爬取栏目 {}'.format(column))
            self.process_a_column(column)

        # try:
        #     for title, link in self.article_links:
        #         self.process_a_passage(title, link)
        # except Exception as e:
        #     logging.error('处理文章失败，错误信息： {}'.format(e))

        with open('links.txt', 'w') as f:
            f.write('\n'.join(self.article_links))

        self.browser.quit()
        logging.info('爬取完成')

    def process_a_column(self, column):
        """爬取一个栏目"""
        column_url = self.url + column + '/index.html'
        self.browser.get(column_url)
        sleep(self.page_wait_time)
        for times in range(self.crawl_page_num):
            # 点击MORE展开一页
            self.browser.find_element(By.CLASS_NAME, "show_more").click()
            sleep(self.page_wait_time)

        source = self.browser.page_source
        logging.info('开始解析栏目 {}'.format(column))
        try:
            html_tree = etree.HTML(source)
            passage_list = self.process_column_link(html_tree)
            self.article_links.extend(passage_list)
        except Exception as e:
            logging.error('解析栏目 {} 链接失败，错误信息： {}'.format(column, e))
        logging.info('栏目 {} 解析完成'.format(column))

        # try:
        #     for title, link in passage_list:
        #         self.process_a_passage(title, link, column)
        # except Exception as e:
        #     logging.error('处理文章失败，错误信息： {}'.format(e))

    def process_column_link(self, html_tree):
        """处理页面获取所有文章标题和连接

        Args:
            html : 栏目的树结构

        Returns:
            一个文章标题和链接元组构成的列表
        """
        ret_list = []
        passages_list = html_tree.xpath('//div[@class="level01_list"]//div[@class="list_info"]/a')
        if passages_list:
            for passage in passages_list:
                title = passage.xpath('./text()')[0]
                link = passage.xpath('./@href')[0]
                logging.debug('获取到当前文章 {} , url {}'.format(title, link))
                ret_list.append(link)
        return ret_list

    def process_a_passage(self, title, link):
        """处理文章信息

        Args:
            title : 文章标题
            link : 链接
            column : 栏目
        """
        logging.info('正在处理文章 {} 链接 {}'.format(title, link))
        row = []
        self.browser.get(link)
        sleep(self.page_wait_time)
        source = self.browser.page_source
        html_tree = etree.HTML(source)

        content_lst = html_tree.xpath(
            '//div[@class="article_page"]//div[@class="article"]//div[@class="article_content"]//div[@class="article_right"]/br')
        # 找不到文章内容直接退出
        if not content_lst:
            return

        # 获取文章内容
        content = ''
        for one_content in content_lst:
            if one_content.tail:
                content = content + '\n' + one_content.tail.strip()
        author_and_publictime_span = html_tree.xpath(
            '//div[@class="article_page"]//div[@class="article"]//div[@class="article_top"]//div[@class="author_share"]//div[@class="author_share_left"]/span')
        # 获取作者
        auther = author_and_publictime_span[0].text.replace('By ', '')
        # 获取发表时间
        public_time = author_and_publictime_span[1].text.replace('Published: ', '')

        row.append(title)
        row.append(auther)
        row.append(public_time)
        row.append(link)
        row.append(content)
        self.write_excel(row)
        logging.debug('爬取一条信息 : {} {} {} {} {} {}'.format(title, column, auther, public_time, link, content))
        logging.info('文章 {} 处理完成'.format(title))


if __name__ == '__main__':
    news_columns_dict = {
        'sport': '体育',
        'life': '生活',
        'world': '世界',
        'In-depth': '深度',
        'opinion': '观点',
        'source': '来源',
        'china': '中国'
    }

    globaltimes_crawler = crawler('https://www.globaltimes.cn/', news_columns_dict, 2)
    globaltimes_crawler.crawl()

