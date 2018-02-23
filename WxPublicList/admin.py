#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 后台系统

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine

# 手工创建数据库表
# CREATE DATABASE IF NOT EXISTS yourdbname DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
# 访问数据库表
engine = create_engine("mysql+pymysql://root:no_way@127.0.0.1:3306/wxpublic?charset=utf8", encoding='utf-8', max_overflow=5)

Base = declarative_base()

class WxPublicAccount(Base):
    """docstring for WxPublicAccount"""
    def __init__(self, **kwargs):
        super(WxPublicAccount, self).__init__()
        for key in kwargs:
            setattr(self, key, kwargs[key])

    __tablename__ = 'wx_public_account'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128))
    account_id = Column(String(64),unique=True)
    account_img = Column(String(640), nullable=False)
    account_desc = Column(String(2048))
    account_qr = Column(String(640))
    account_url = Column(String(640), nullable=False)
    #account_uptime = Column(Datetime())

    '''
    __table_args__ = (
    UniqueConstraint('id', 'name', 'account_id', 'account_img', 'account_desc', 'account_qr', 'account_url'),
        Index('ix_id_name', 'name', 'extra'),
    )
    '''

class WxArticle(Base):
    """docstring for WxArticle"""
    def __init__(self, **kwargs):
        super(WxArticle, self).__init__()
        for key in kwargs:
            setattr(self, key, kwargs[key])
    
    __tablename__ = 'wx_article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    article_title = Column(String(128), primary_key=True)
    article_desc = Column(String(2048))
    article_thumb = Column(String(640))
    article_url = Column(String(640), nullable=False)
    article_pubtime = Column(String(32), nullable=False)
    article_account_id = Column(String(16), ForeignKey('wx_public_account.account_id'))


#定义初始化数据库函数
def init_db():
    Base.metadata.create_all(engine)

#顶固删除数据库函数
def drop_db():
    Base.metadata.drop_all(engine)

# drop_db()
if __name__ == '__main__':

    init_db()
    #drop_db()
