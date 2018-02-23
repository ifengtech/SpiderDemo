# coding: utf-8
# 这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from urllib import quote
from pyquery import PyQuery as pq
from selenium import webdriver

from dataconn import dbsession
from admin import WxPublicAccount
from admin import WxArticle

import requests
import time
import re
import json
import os

class wx_spider:
    def __init__(self):
        
        #搜狗引擎链接url
        self.sogou_search_url_f = 'http://weixin.sogou.com/weixin?type=1&query=%s&ie=utf8&s_from=input&_sug_=n&_sug_type_='

        # 爬虫伪装头部设置
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}

        # 超时时长
        self.timeout = 5

        # 爬虫模拟在一个request.session中完成
        self.session = requests.Session()

        # excel 第一行数据
        #self.excel_headData = [u'发布时间', u'文章标题', u'文章链接', u'文章简介']

    def log(self, msg):
        '''
        日志函数
        :param msg: 日志信息
        :return:
        '''
        print u'%s: %s' % (time.strftime('%Y-%m-%d %H-%M-%S'), msg)

    def composeSearchUrl(self,keyword = ''):
        return self.sogou_search_url_f % quote(keyword)

    def run(self):

        '''
        构造函数，借助搜狗微信搜索引擎，根据微信公众号获取微信公众号对应的文章的，发布时间、文章标题, 文章链接, 文章简介等信息
        :param Wechat_PublicID: 微信公众号
        '''
        publicId = 'Fin2050'

        wxaccount = WxPublicAccount(account_id=publicId)
        # 第一步 ：GET请求到搜狗微信引擎，以微信公众号英文名称作为查询关键字
        self.log(u'开始获取，微信公众号英文名为：%s' % wxaccount.account_id)
        self.log(u'开始调用sougou搜索引擎')

        searchurl = self.composeSearchUrl(wxaccount.account_id)
        self.log(u'搜索地址为：%s' % searchurl)
        sougou_search_html = self.session.get(searchurl, headers=self.headers, timeout=self.timeout).content

        # 第二步：从搜索结果页中解析出公众号主页链接
        doc = pq(sougou_search_html)
        
        # 通过pyquery的方式处理网页内容，类似用beautifulsoup，但是pyquery和jQuery的方法类似，找到公众号主页地址
        wxaccount.name = doc('div[class=txt-box]')('p[class=tit]')('a').text().strip()
        wxaccount.account_url = doc('div[class=txt-box]')('p[class=tit]')('a').attr('href')
        wxaccount.account_img = doc('div[class=img-box]')('a')('img').attr('src')
        wxaccount.account_desc = doc('ul[class=news-list2]')('li').eq(0)('dl').eq(0)('dd').text().strip()
        wxaccount.account_qr = doc('div[class=ew-pop]')('span')('img').attr('src')
        #wxaccount.account_uptime

        if wxaccount.name == '':
            self.log(u'获取公众号信息失败，%s' % wxaccount.account_id)
            return

        # 公众号信息获取成功，并写入数据库
        self.log(u'获取wx_url成功，%s' % wxaccount.account_url)
        #wxaccount.account_uptime = datetime.now()
        
        if dbsession.query(WxPublicAccount).filter(WxPublicAccount.account_id==wxaccount.account_id).first() != '':
            # 记录已经存在则更新
            self.log(u'执行到这里....1')
            dbsession.merge(wxaccount)
        else:
            self.log(u'执行到这里....2')
            dbsession.add(wxaccount)

        dbsession.flush()
        

        # 第三步：Selenium+PhantomJs获取js异步加载渲染后的html
        self.log(u'开始调用selenium渲染html')
        browser = webdriver.PhantomJS()
        browser.get(wxaccount.account_url)
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

            wx_article_list = []

            articles_list = doc('div[class="weui_media_box appmsg"]')
            articlesLength = len(articles_list)
            self.log(u'抓取到微信文章%d篇' % articlesLength)

            # Step 6: 把微信文章数据封装成字典的list
            self.log(u'开始整合微信文章数据为字典')

            # 遍历找到的文章，解析里面的内容
            if articles_list:
                index = 0
                article_index = WxArticle(article_account_id=wxaccount.account_id)

                # 以当前时间为名字建表
                '''
                excel_sheet_name = time.strftime('%Y-%m-%d')
                excel_content = self.excle_Workbook.add_sheet(excel_sheet_name)
                colindex = 0
                columnsLength = len(self.excel_headData)
                for data in self.excel_headData:
                    excel_content.write(0, colindex, data)
                    colindex += 1
                '''
                for article in articles_list.items():
                    self.log(' ' )
                    self.log(u'开始整合(%d/%d)' % (index, articlesLength))
                    index += 1
                    article_index = WxArticle(article_account_id=wxaccount.account_id)

                    # 处理单个文章
                    # 获取标题
                    article_index.article_title = article('h4[class="weui_media_title"]').text().strip()
                    self.log(u'标题是： %s' % article_index.article_title)
                    
                    # 获取概要内容
                    # summary = article('.weui_media_desc').text()
                    article_index.article_desc = article('p[class="weui_media_desc"]').text()
                    self.log(u'文章简述： %s' % article_index.article_desc)
                    

                    # 获取文章缩略图
                    # 这里需要拆分css的style属性
                    pic = article('.weui_media_hd').attr('style')
                    p = re.compile(r'background-image:url(.+)')
                    rs = p.findall(pic)
                    if len(rs) > 0:
                        p = rs[0].replace('(', '')
                        p = p.replace(')', '')
                        article_index.article_thumb = p
                        self.log(u'封面图片是：%s ' % p)

                    # 获取标题对应的地址
                    article_index.article_url = 'http://mp.weixin.qq.com' + article('h4[class="weui_media_title"]').attr('hrefs')
                    self.log(u'地址为： %s' % article_index.article_url)

                    # 获取文章发表时间
                    # date = article('.weui_media_extra_info').text().strip()
                    article_index.article_pubtime = article('p[class="weui_media_extra_info"]').text().strip()
                    self.log(u'发表时间为： %s' % article_index.article_pubtime)
                    
                    wx_article_list.append(article_index)
                    
                # 保存下载好的微信文章
                dbsession.add_all(wx_article_list)
                dbsession.flush()

                # 提交服务器
                dbsession.commit()

            self.log(u'保存完成，程序结束')

if __name__ == '__main__':

    wx_spider().run()

