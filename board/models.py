#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import datetime
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask.ext.login import UserMixin
from board import app

config = ConfigParser.ConfigParser()
config.read("/home/luapz/public_html/do-lazy/config")
db_id = config.get('db', 'db_id')
db_password = config.get('db', 'db_password')
db_name = config.get('db', 'db_name')

app.config['SQLALCHEMY_DATABASE_URI'] = ('mysql://%s:%s@localhost/%s?charset=utf8' % (db_id, db_password, db_name))
db = SQLAlchemy(app)
db.echo=True

class SiteInfo(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.Unicode(255))
    slogan = db.Column(db.Unicode(255))
    description = db.Column(db.Unicode(255))

class Board(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode(255))
    slogan = db.Column(db.Unicode(255))
    description = db.Column(db.Unicode(255))
    total_article_number = db.Column(db.Integer())
    
class Article(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_name = db.Column(db.Unicode(100))
    nick_name = db.Column(db.Unicode(100))
    password = db.Column(db.Unicode(64))
    title = db.Column(db.Unicode(255))
    text = db.Column(db.Text())
    create_at = db.Column(db.DateTime())
    modified_at = db.Column(db.DateTime())
    is_notice = db.Column(db.Boolean())
    is_public = db.Column(db.Boolean())
    is_best = db.Column(db.Boolean())
    is_anonymous = db.Column(db.Boolean())
    ip = db.Column(db.Unicode(16))
    thumbs_up = db.Column(db.Integer())
    thumbs_down = db.Column(db.Integer())
    views = db.Column(db.Integer())
    reply_number = db.Column(db.Integer())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
        backref=db.backref('articles', lazy='dynamic'))
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))
    board = db.relationship('Board',
        backref=db.backref('articles', lazy='dynamic'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Unicode(80), unique=True)
    nick_name = db.Column(db.Unicode(80), unique=True)
    email = db.Column(db.Unicode(255), unique=True)
    password = db.Column(db.Unicode(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    # trust = True는 스팸 필터 미적용
    # login시 조건(글 작성 갯수, 리플 작성 갯수 등)에 맞으면 True로 update
    is_trust = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
