#!/usr/bin/env python
# -*- coding:utf-8 -*-

# start / loading from config file

import ConfigParser

config = ConfigParser.ConfigParser()
config.read("d2/config")
app_secret_key = config.get('app', 'app_secret_key')

memcached_cache_type = config.get('memcached', 'cache_type')
memcached_cache_default_timeout = config.get('memcached', 'cache_default_timeout')
memcached_cache_servers = config.get('memcached', 'cache_memcached_servers')

# end / loading from config file

from datetime import datetime
from flask import Flask, render_template, request, flash, url_for, redirect, make_response, current_app, g
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from flaskext.cache import Cache
from d2 import app

app = Flask(__name__)

# start / app&memcached config

memcached = Cache(app)

app.secret_key = app_secret_key
app.config.from_object(__name__)
app.config.update(DEBUG=True)

app.config['CACHE_TYPE'] = memcached_cache_type
app.config['CACHE_DEFAULT_TIMEOUT'] = memcached_cache_default_timeout
app.config['CACHE_MEMCACHED_SERVERS'] = memcached_cache_servers

# end / app&memcached config


# start / routing

@app.route('/')
@memcached.cached(timeout=60)
def index():
    context =  { 'site_info' : site_info(),
                'site_menu' : site_menu() }
    return render_template('index.html', **context)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = registration_form(request.form)
    context = { 'form' : form, 'site_info' : site_info(), 
                'site_menu' : site_menu() }
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
        return redirect(url_for('login'))
    context = { 'form': form, 'site_info': site_info(), 'site_menu': site_menu() }
    return render_template('register.html', **context)

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
    context = { 'form' : form, 'site_info': site_info(), 'site_menu': site_menu() }
    return render_template("login.html", **context)

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
    context = { 'form': form, 'site_info': site_info(), 'site_menu': site_menu() }
    return render_template("profile.html", **context) 

@app.route("/board/<board_name>/page/<int:page>/article/<int:article_number>")
def article_view(board_name, page, article_number):
    article_detail = session.query(Article).filter_by(id = article_number).first()
    board = session.query(Board).filter_by(board_id = article_detail.board_id).first()
    article_detail.hits = article_detail.hits + 1
    session.add(article_detail)
    try:
        session.commit()
    except:
        session.rollback()
    page_now = page
    page = page - 1
    next_page = page + 2
    board = session.query(Board).filter_by(board_name = board_name).first()
    lastest_article_number = int(session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_public==True).count())
    total_article_number = int(session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_public==True).count()) - (page * per_page)
    article_from = int(page) * int(per_page)
    article_to = (int(page) + 1) * int(per_page)
    article_list = session.query(Article).filter(Article.board_id==board.board_id).order_by(desc(Article.id)).filter(Article.is_public==True)[article_from:article_to]
    notice_list = session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_notice==True).order_by(desc(Article.id)).filter(Article.is_public==True).all()
    pagination = Pagination(page, per_page, lastest_article_number)
    context = { 'article_list': article_list, 'notice_list': notice_list, 
                'site_info': site_info, 'board' : board, 
                'board_name': board_name,
                'article_detail': article_detail,
                'max_title_string': max_title_string,
                'max_nick_name_string': max_nick_name_string,
                'page' : page, 'per_page': per_page, 'page_now': page_now,
                'pagination' : pagination, 'next_page': next_page, 
                'lastest_article_number': lastest_article_number,
                'total_article_number' : total_article_number,
                'site_info': site_info(), 'site_menu': site_menu() }
    return render_template("article.html", **context)


@app.route("/board/<board_name>")
@app.route("/board/<board_name>/")
def board(board_name, page=1):
    return redirect(url_for('board_view', board_name=board_name, page=page))
@app.route("/board/<board_name>/page/<int:page>")
@app.route("/board/<board_name>/page/<int:page>/")
def board_view(board_name,page):
    page_now = page
    page = page - 1
    next_page = page + 2
    board = session.query(Board).filter_by(board_name = board_name).first()
    lastest_article_number = int(session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_public==True).count())
    total_article_number = int(session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_public==True).count()) - (page * per_page)
    article_from = int(page) * int(per_page)
    article_to = (int(page) + 1) * int(per_page)
    article_list = session.query(Article).filter(Article.board_id==board.board_id).order_by(desc(Article.id)).filter(Article.is_public==True)[article_from:article_to]
    notice_list = session.query(Article).filter(Article.board_id==board.board_id).filter(Article.is_notice==True).order_by(desc(Article.id)).filter(Article.is_public==True).all()
    pagination = Pagination(page, per_page, lastest_article_number)
    context = { 'article_list': article_list, 'notice_list': notice_list, 
                'site_info': site_info, 'board' : board, 
                'board_name': board_name,
                'max_title_string': max_title_string,
                'max_nick_name_string': max_nick_name_string,
                'page' : page, 'per_page': per_page, 'page_now': page_now,
                'pagination' : pagination, 'next_page': next_page, 
                'lastest_article_number': lastest_article_number,
                'total_article_number' : total_article_number,
                'site_info': site_info(), 'site_menu': site_menu() }
    return render_template("board.html", **context)
#    return unicode(article_list[4].nick_name)

import json
import time
@app.route("/board/upload", methods=["POST"] )
def board_upload():
    if request.method != "POST":
        return "Error"
    file = request.files['file']
    if file and file.filename.endswith(".jpg"):
        secure_filename = str(int(time.time())) + ".jpg"
        file.save( os.path.join( file_upload_path , secure_filename ))
        url_path = "/" + str(os.path.basename( file_upload_path ))
        return json.dumps(
            { "filelink" : os.path.join ( url_path , secure_filename )})
    return json.dumps({})
    #file_upload_path

@app.route("/board/<board_name>/write", methods=["GET", "POST"], 
            defaults={'page_number': 1})
def board_write(board_name, page_number=1):
    form = write_article_form(request.form)
    board = session.query(Board).filter_by(board_name = board_name).first()
    board_id = board.board_id
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
        flash('article write')
        return redirect(url_for('board_view', board_name=board_name, page=1))
    context = { 'form' : form, 'site_info': site_info(), 'site_menu': site_menu(),
                'board_name': board_name }
    return render_template("write_article.html", **context)




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
    site_root = "http://rkrk.kr:5001/"
    siteinfo = SiteInfo(site_title, site_slogan, site_desc, site_root)
    session.add(siteinfo)
    try:
        session.commit()
    except:
        session.rollback()

    board_id = 1
    board_name = "신혼방"
    board_desc = "찌질거리는 이를 까지 말라"
    board = Board(board_id, board_name, board_desc)
    session.add(board)
    try:
        session.commit()
    except:
        session.rollback()

    menu_title = "신혼방"
    menu_link = "board/신혼방"
    menu = SiteMenu(menu_title, menu_link)
    session.add(menu)
    try:
        session.commit()
    except:
        session.rollback()

    for i in range(1,40000):
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
    return unicode("inserted")

# end / routing
