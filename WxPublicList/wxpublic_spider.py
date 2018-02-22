# coding: utf-8
# 这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from urllib import quote
from pyquery import PyQuery as pq
from selenium import webdriver
from pyExcelerator import *  # 导入excel相关包

import requests
import time
import re
import json
import os

class wx_spider:
    def __init__(self,Wechat_PublicID):
        '''
        构造函数，借助搜狗微信搜索引擎，根据微信公众号获取微信公众号对应的文章的，发布时间、文章标题, 文章链接, 文章简介等信息
        :param Wechat_PublicID: 微信公众号
        '''
        self.Wechat_PublicID = Wechat_PublicID
        #搜狗引擎链接url
        self.sogou_search_url = 'http://weixin.sogou.com/weixin?type=1&query=%s&ie=utf8&s_from=input&_sug_=n&_sug_type_=' % quote(Wechat_PublicID)

        # 爬虫伪装头部设置
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}

        # 超时时长
        self.timeout = 5

        # 爬虫模拟在一个request.session中完成
        self.session = requests.Session()

        # excel 第一行数据
        self.excel_headData = [u'发布时间', u'文章标题', u'文章链接', u'文章简介']

        # 定义excel操作句柄
        self.excle_Workbook = Workbook()

    def log(self, msg):
        '''
        日志函数
        :param msg: 日志信息
        :return:
        '''
        print u'%s: %s' % (time.strftime('%Y-%m-%d %H-%M-%S'), msg)

    def run(self):

        #Step 0 ：  创建公众号命名的文件夹
        if not os.path.exists(self.Wechat_PublicID):
            os.makedirs(self.Wechat_PublicID)

        # 第一步 ：GET请求到搜狗微信引擎，以微信公众号英文名称作为查询关键字
        self.log(u'开始获取，微信公众号英文名为：%s' % self.Wechat_PublicID)
        self.log(u'开始调用sougou搜索引擎')

        self.log(u'搜索地址为：%s' % self.sogou_search_url)
        sougou_search_html = self.session.get(self.sogou_search_url, headers=self.headers, timeout=self.timeout).content

        # 第二步：从搜索结果页中解析出公众号主页链接
        doc = pq(sougou_search_html)
        # 通过pyquery的方式处理网页内容，类似用beautifulsoup，但是pyquery和jQuery的方法类似，找到公众号主页地址
        wx_url = doc('div[class=txt-box]')('p[class=tit]')('a').attr('href')
        self.log(u'获取wx_url成功，%s' % wx_url)

        # 第三步：Selenium+PhantomJs获取js异步加载渲染后的html
        self.log(u'开始调用selenium渲染html')
        browser = webdriver.PhantomJS()
        browser.get(wx_url)
        time.sleep(3)
        # 执行js得到整个页面内容
        selenium_html = browser.execute_script("return document.documentElement.outerHTML")
        browser.close()


        # 第四步: 检测目标网站是否进行了封锁
        ' 有时候对方会封锁ip，这里做一下判断，检测html中是否包含id=verify_change的标签，有的话，代表被重定向了，提醒过一阵子重试 '
        if pq(selenium_html)('#verify_change').text() != '':
            self.log(u'爬虫被目标网站封锁，请稍后再试')
        else:
            # 第五步: 使用PyQuery，从第三步获取的html中解析出公众号文章列表的数据
            self.log(u'调用selenium渲染html完成，开始解析公众号文章')
            doc = pq(selenium_html)

            articles_list = doc('div[class="weui_media_box appmsg"]')
            articlesLength = len(articles_list)
            self.log(u'抓取到微信文章%d篇' % articlesLength)

            # Step 6: 把微信文章数据封装成字典的list
            self.log(u'开始整合微信文章数据为字典')

            # 遍历找到的文章，解析里面的内容
            if articles_list:
                index = 0

                # 以当前时间为名字建表
                excel_sheet_name = time.strftime('%Y-%m-%d')
                excel_content = self.excle_Workbook.add_sheet(excel_sheet_name)
                colindex = 0
                columnsLength = len(self.excel_headData)
                for data in self.excel_headData:
                    excel_content.write(0, colindex, data)
                    colindex += 1
                for article in articles_list.items():
                    self.log(' ' )
                    self.log(u'开始整合(%d/%d)' % (index, articlesLength))
                    index += 1
                    # 处理单个文章
                    # 获取标题
                    title = article('h4[class="weui_media_title"]').text().strip()
                    self.log(u'标题是： %s' % title)
                    # 获取标题对应的地址
                    url = 'http://mp.weixin.qq.com' + article('h4[class="weui_media_title"]').attr('hrefs')
                    self.log(u'地址为： %s' % url)
                    # 获取概要内容
                    # summary = article('.weui_media_desc').text()
                    summary = article('p[class="weui_media_desc"]').text()
                    self.log(u'文章简述： %s' % summary)
                    # 获取文章发表时间
                    # date = article('.weui_media_extra_info').text().strip()
                    date = article('p[class="weui_media_extra_info"]').text().strip()
                    self.log(u'发表时间为： %s' % date)
                    # # 获取封面图片
                    # pic = article('.weui_media_hd').attr('style')
                    #
                    # p = re.compile(r'background-image:url(.+)')
                    # rs = p.findall(pic)
                    # if len(rs) > 0:
                    #     p = rs[0].replace('(', '')
                    #     p = p.replace(')', '')
                    #     self.log(u'封面图片是：%s ' % p)
                    tempContent = [date, title, url, summary]
                    for j in range(columnsLength):
                        excel_content.write(index, j, tempContent[j])

                self.excle_Workbook.save(self.Wechat_PublicID + '/' + self.Wechat_PublicID + '.xls')

            self.log(u'保存完成，程序结束')

if __name__ == '__main__':

    wx_spider("Fin2050").run()