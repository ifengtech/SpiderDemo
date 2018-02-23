#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 数据库连接

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from admin import WxPublicAccount
from admin import WxArticle

#数据库配置
host='127.0.0.1'
port=3306
user='root'
passwd='no_way'
dbname='wxpublic'

engine = create_engine("mysql+pymysql://%s:%s@%s:%d/%s?charset=utf8" % (user,passwd,host,port,dbname), encoding='utf-8', max_overflow=5)
Session = sessionmaker(bind=engine)

dbsession = Session()
