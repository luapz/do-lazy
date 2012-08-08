#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


import ConfigParser

config = ConfigParser.ConfigParser()
config.read("d2/config")
db_id = config.get('db', 'db_id')
db_password = config.get('db', 'db_password')
db_name = config.get('db', 'db_name')
app_secret_key = config.get('app', 'app_secret_key')
debug_mode = config.get('app', 'debug_mode')
per_page = config.get('app', 'per_page')
port = config.get('app', 'port')

import hashlib
from datetime import datetime
from flask import Flask, render_template, request, flash, url_for, redirect, make_response, current_app
from wtforms import Form, BooleanField, TextField, PasswordField, TextAreaField, validators
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)

app = Flask(__name__, template_folder=template_dir)
app.secret_key = app_secret_key
app.config.from_object(__name__)

class Anonymous(AnonymousUser):
    nick_name = u"anonymous"

login_manager = LoginManager()

login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"
login_manager.setup_app(app)

@login_manager.user_loader
def load_user(userid):
    return session.query(User).filter_by(id=userid).first()
    if user:
        return User(userid)
    else:
        return None

from sqlalchemy import create_engine, MetaData, Column, Integer, String, UnicodeText, ForeignKey, desc, func
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, sessionmaker, relationship, backref
from sqlalchemy.types import DateTime, Boolean

engine = create_engine('mysql://%s:%s@localhost/%s?charset=utf8' %  (db_id, db_password, db_name))

Base = declarative_base()
sql_datetime = DateTime


class SiteInfo(Base):
    __tablename__ = "site-info"
    id = Column(Integer, primary_key=True)
    site_title = Column(String(length=50), nullable = False)
    site_slogan = Column(String(length=200), nullable = False)
    site_desc = Column(String(length=200), nullable = False)
    site_root = Column(String(length=50), nullable = False)

    def __init__(self, site_title, site_slogan, site_desc, site_root):
        self.site_title = site_title
        self.site_slogan = site_slogan
        self.site_desc = site_desc
        self.site_root = site_root

class SiteMenu(Base):
    __tablename__ = "site-menu"
    id = Column(Integer, primary_key=True)
    menu_title = Column(String(length=50), nullable = False)
    menu_link = Column(String(length=50), nullable = False)

    def __init__(self, menu_title, menu_link):
        self.menu_title = menu_title
        self.menu_link = menu_link

class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    user_name = Column(String(length=20), nullable = False)
    nick_name = Column(String(length=20), nullable = False)
    email = Column(String(length=50), nullable = False)
    password = Column(String(length=64), nullable = False)
    creat_date = Column(DateTime)
    login_date = Column(DateTime)
    access_date = Column(DateTime)
    signature = Column(String(length=1000), nullable = True)
    icon_url = Column(String(length=256), nullable = True)
    trophy = Column(String(length=200), nullable = True)

    def __init__(self, user_name, nick_name, email, password, 
                creat_date=None, login_date=None, access_date=None, 
                signature=None, icon_url=None, trophy=None):
        self.user_name = user_name
        self.nick_name = nick_name
        self.email = email
        self.password = password
        if creat_date is None:
            creat_date = sql_datetime()
        self.creat_date = creat_date
        if login_date is None:
            login_date = sql_datetime()
        self.login_date = login_date
        if access_date is None:
            access_date = sql_datetime()
        self.access_date = access_date
        self.signature = signature
        self.icon_url = icon_url
        self.trophy = trophy

class Board(Base):
    __tablename__ = 'board'
    id = Column(Integer, primary_key=True)
    board_id = Column(String(length=20), nullable = False)
    board_name = Column(String(length=20), nullable = False)
    board_desc = Column(String(length=80), nullable = False)
    public_article_number = Column(Integer)

    def __init__(self, board_id, board_name, board_desc, public_article_number):
        self.board_id = board_id
        self.board_name = board_name
        self.board_desc = board_desc
        self.public_article_number = public_article_number

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    board_id = Column(String(length=2), nullable = False)
    user_name = Column(String(length=20), nullable = True)
    nick_name = Column(String(length=20), nullable = True)
    password = Column(String(length=64), nullable = True)
    title = Column(UnicodeText, nullable=False)
    text = Column(UnicodeText, nullable=False)
    creat_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    is_notice = Column(Boolean, nullable=True)
    is_public = Column(Boolean, nullable=True)
    is_mobile = Column(Boolean, nullable=True)
    anonymity = Column(Boolean, nullable=False)
    remote_addr = Column(String(length=16), nullable = False)
    thumbs_up = Column(String(length=5), nullable = True)
    thumbs_down = Column(String(length=5), nullable = True)
    hits = Column(Integer)

    def __init__(self, board_id, user_name, nick_name, password, 
                title, text, creat_date, modified_date, is_notice, 
                is_public, is_mobile, anonymity, remote_addr, 
                thumbs_up=0, thumbs_down=0, hits=0):
        self.board_id = board_id
        self.user_name = user_name
        self.nick_name = nick_name
        self.password = password
        self.title = title
        self.text = text
        if creat_date is None:
            creat_date = sql_datetime()
        self.creat_date = creat_date
        if modified_date is None:
            modified_date = sql_datetime()
        self.modified_date = modified_date
        self.is_notice = is_notice
        self.is_public = is_public
        self.is_mobile = is_mobile
        self.anonymity = anonymity
#        if remote_addr is None and has_request_context():
#            remote_addr = request.remote_addr
        self.remote_addr = remote_addr
        self.thumbs_up = thumbs_up
        self.thumbs_down = thumbs_down
        self.hits = hits

class SpamFilter(Base):
    __tablename__= "filter-spam"
    id = Column(Integer, primary_key=True)
    spam_word = Column(String(length=20), nullable = False)
    count = Column(Integer, nullable = True)

    def __init__(spam_word, count):
        self.spam_word = spam_word
        self.count = count

class DenyFilter(Base):
    __tablename__= "filter-deny"
    id = Column(Integer, primary_key=True)
    spam_word = Column(String(length=20), nullable = False)
    count = Column(Integer, nullable = True)

    def __init__(spam_word, count):
        self.spam_word = spam_word
        self.count = count

class IpFilter(Base):
    __tablename__= "filter-ip"
    id = Column(Integer, primary_key=True)
    spam_ip = Column(String(length=20), nullable = False)
    count = Column(Integer, nullable = True)

    def __init__(spam_word, count):
        self.spam_ip = spam_ip
        self.count = count

Session = sessionmaker(bind=engine)
session=Session()
session.begin_nested()

Base.metadata.create_all(engine) 

def encode_md5(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()

def encode_sha256(content):
    sha256 = hashlib.sha256()
    sha256.update(content)
    return sha256.hexdigest()

def mobile_check(request):
    if request.user_agent.platform in ['iphone', 'android']:
        return True
    else:
        return False

from math import ceil

class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))
    @property
    def has_prev(self):
        return self.page > 1
    @property
    def has_next(self):
        return self.page < self.pages
    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


class registration_form(Form):
    user_name = TextField('id', [validators.Length(min=4, max=20)])
    nick_name = TextField('Nick name', [validators.Length(min=4, max=20)])
    email = TextField('Email address', [validators.Length(min=4, max=50)])
    password = PasswordField('password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('confirm Password')

class login_form(Form):
    user_name = TextField('id', [validators.Length(min=4, max=50), 
                                validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    remember = BooleanField('remember')

class profile_form(Form):
#    user_name = current_user.user_name
#    user = session.query(User).filter_by(user_name = user_name).first()
    user_name = TextField('id')

class write_article_form(Form):
    nick_name = TextField('nick name', [validators.Length(max=50), 
                                        validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    title = TextField('title', [validators.Length(max=200), 
                                validators.Required()])
    redactor = TextAreaField('Text', default="")

site_info = session.query(SiteInfo).first()

@app.route('/')
def index():
    site_info = session.query(SiteInfo).first()
    site_menu = session.query(SiteMenu).all()
    return render_template('index.html', site_info = site_info, 
                            site_menu=site_menu)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = registration_form(request.form)
    return render_template('register.html', form=form)

@app.route('/register/add', methods=['GET', 'POST'])
def register():
    form = registration_form(request.form)
    if request.method == 'POST' and form.validate():
        creat_date = datetime.now()
        password = encode_sha256(encode_md5(form.password.data+form.user_name.data))
        user = User(form.user_name.data, form.nick_name.data, form.email.data,
                    password, creat_date)
        session.add(user)
        try:
            session.commit()
        except:
            session.rollback() 
        flash('Thanks for registering')
        return redirect(url_for('index'))
    return render_template('register.html', form=form, site_info=site_info)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = login_form(request.form)
    if request.method == "POST" and form.validate():
        user = session.query(User).filter_by(user_name = form.user_name.data).first()
        if user is None:
            return "no id"
        else:
            input_password = encode_sha256(encode_md5(form.password.data+form.user_name.data))
            if user.password == input_password:
                user.login_date = datetime.now()                
                try:
                    session.commit()
                except:
                    session.rollback()
                login_user(user)
                return redirect(url_for('index'))
            else:
                return "wrong password"
    return render_template("login.html", form=form, site_info=site_info)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/profile/<user_name>")
@login_required
def profile(user_name):
    form = profile_form(request.form)
    user_name = current_user.user_name
    user = session.query(User).filter_by(user_name = user_name).first()
    return unicode(user)
#    return render_template("profile.html", form=form, site_info=site_info) 

@app.route("/article/<int:article_number>")
def article_view(article_number):
    article_detail = session.query(Article).filter_by(id = article_number).first()
    article_detail.hits = article_detail.hits + 1
    session.add(article_detail)
    try:
        session.commit()
    except:
        session.rollback()
    return render_template("article.html", article_detail=article_detail, 
                            site_info=site_info)

@app.route("/article/write", methods=["GET", "POST"])
def write_article():
    form = write_article_form(request.form)
    if request.method == 'POST':
        if current_user.nick_name == "anonymous":
            user_name = Anonymous.nick_name
            nick_name = form.nick_name.data
            password = encode_sha256(encode_md5(form.password.data+user_name))
        else:
            user_name = current_user.user_name
            nick_name = current_user.nick_name
            password = current_user.password
        text = form.redactor.data
        creat_date = datetime.now()
        modified_date = datetime.now()
        is_public = True
        remote_addr = request.remote_addr
        article = Article(user_name, nick_name, password, text, creat_date, 
                            modified_date, is_public, remote_addr)
        session.add(article)
        try:
            session.commit()
        except:
            session.rollback()
        flash('article write')
        return redirect(url_for('index'))
    return render_template("write_article.html", form=form, site_info=site_info) 

@app.route("/board/<board_name>")
@app.route("/board/<board_name>/")
@app.route("/board/<board_name>/page/<int:page>", defaults={'page': 1})
@app.route("/board/<board_name>/page/<int:page>/", defaults={'page': 1})
def board_view(board_name, page=1):
    board = session.query(Board).filter_by(board_name = board_name).first()
    article_list = session.query(Article).filter_by(board_id=board.board_id).order_by(desc(Article.id)).limit(per_page)
    whole_article_number = board.public_article_number
    pagination = Pagination(page, per_page, whole_article_number)
    number_list = board.public_article_number
    return render_template("board.html", article_list=article_list, 
                            site_info=site_info, board=board, 
                            number_list=number_list, pagination=pagination, 
                            page=page, per_page=per_page, 
                            whole_article_number=whole_article_number )

@app.route("/board/<board_name>/write", methods=["GET", "POST"], 
            defaults={'page_number': 1})
def board_write(board_name, page_number=1):
    form = write_article_form(request.form)
    board = session.query(Board).filter_by(board_name = board_name).first()
    board_id = board.board_id
    b_name = board.board_name
    if request.method == 'POST':
        if current_user.nick_name == "anonymous":
            user_name = Anonymous.nick_name
            nick_name = form.nick_name.data
            password = encode_sha256(encode_md5(form.password.data+user_name))
            anonymity = True 
        else:
            user_name = current_user.user_name
            nick_name = current_user.nick_name
            password = current_user.password
            anonymity = False
        title = form.title.data
        text = form.redactor.data
        creat_date = datetime.now()
        modified_date = datetime.now()
        is_notice = False
        is_public = True
        is_mobile = mobile_check(request)
        remote_addr = request.remote_addr
        article = Article(board_id, user_name, nick_name, password, 
                            title, text, creat_date, modified_date, 
                            is_notice, is_public, is_mobile, anonymity, 
                            remote_addr)
        session.add(article)
        try:
            session.commit()
        except:
            session.rollback()
        # update public article count number
        public_article_count = session.query(Article).filter(Article.is_public.like(True)).count() 
        board.article_number = public_article_count
        session.add(board)
        try:
            session.commit()
        except:
            session.rollback()
        flash('article write')
        b = "/board/%s" % (b_name)
        return redirect(url_for('board_view', board_name=b_name, page_number=1))
    return render_template("write_article.html", form=form, 
                            site_info=site_info, board_name=board_name) 




@app.route("/rss/article")
def rss_view():
    last_article = session.query(Article).order_by(desc(Article.id)).first()
    article_list = session.query(Article).order_by(Article.id).limit(10)
    return render_template("rss.xml", last_article=last_article, 
                            article_list=article_list, site_info=site_info) 

@app.route("/i")
def write_article():
    site_title = "dolazy"
    site_slogan = "아스카와 나의 신혼방"
    site_desc = "힘겨운 삶의 진통제"
    site_root = "http://dolazy.com/d2"
    siteinfo = SiteInfo(site_title, site_slogan, site_desc, site_root)
    session.add(siteinfo)
    try:
        session.commit()
    except:
        session.rollback()

    board_id = 1
    board_name = "신혼방"
    board_desc = "찌질거리는 이를 까지 말라"
    public_article_number = 0
    board = Board(board_id, board_name, board_desc, public_article_number)
    session.add(board)
    try:
        session.commit()
    except:
        session.rollback()

    for i in range(1,40):
        b_name = 1
        board_id = 1
        i = str(i)
        user_name = "user_name" + i
        nick_name = "nick_name" + i
        password = "password" + i
        anonymity = False
        title = "title " + i
        text = "text" + i
        creat_date = datetime.now()
        modified_date = datetime.now()
        is_notice = False
        is_public = True
        is_mobile = mobile_check(request)
        remote_addr = request.remote_addr
        article = Article(board_id, user_name, nick_name, password, 
                            title, text, creat_date, modified_date, 
                            is_notice, is_public, is_mobile, anonymity, 
                            remote_addr)
        session.add(article)
        try:
            session.commit()
        except:
            session.rollback()
        # update public article count number
        public_article_count = session.query(Article).filter(Article.is_public.like(True)).count() 
        board.article_number = public_article_count
        session.add(board)
        try:
            session.commit()
        except:
            session.rollback()
    return unicode("inserted")
