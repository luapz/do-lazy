#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from forms import *

import bcrypt
import redis
import ConfigParser
import sys 
import dateutil.parser as parser

from redis import Redis, StrictRedis
from BeautifulSoup import BeautifulSoup

from flask import Flask, render_template, request, url_for, redirect
from flask.ext.login import LoginManager, current_user, login_required, \
                            login_user, logout_user, UserMixin, AnonymousUser, \
                            confirm_login, fresh_login_required
from sqlalchemy import desc, asc

reload(sys) 
sys.setdefaultencoding('utf-8') 

config = ConfigParser.ConfigParser()
config.read("/home/luapz/public_html/do-lazy/config")
db_id = config.get('db', 'db_id')
ARTICLE_PER_PAGE = config.get('board', 'article_per_page')

redis = Redis()
r_hits = StrictRedis(host='localhost', port=6379, db=1)

login_manager = LoginManager()
login_manager.setup_app(app)

@login_manager.user_loader
def load_user(userid):
    return db.session.query(User).filter_by(id=userid).first()
    if user:
        return User(userid)
    else:
        return None

def site_info():
    rv = db.session.query(SiteInfo).first()
    return rv

def last_article():
    rv = db.session.query(Article).filter_by(is_public=True).limit(5).all()
    return rv

def get_board_info(board_name):
    rv = db.session.query(Board).filter_by(name=board_name).first()
    return rv

def get_page_number(article_number,article_per_page):
    article_number = int(article_number)
    article_per_page = int(article_per_page)
    if (article_number % 2 == 1): 
        article_number += 1
    page_number = (article_number / (article_per_page+1)) 
    return page_number

# 글 작성시 타이틀 문자열에서 html 제거용
def remove_html_tag(string):
    soup = BeautifulSoup(''.join(unicode(string)))
    text_parts = soup.findAll(text=True)
    removed_text = unicode(''.join(text_parts))
    return removed_text

# 글 작정시 본문에서 자바스크립트 제거용
def remove_script_tag(string):
    soup = BeautifulSoup(''.join(unicode(string)))
    [s.extract() for s in soup('script')]
    removed_text = soup
    return removed_text

# 페이지 번호 생성용
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


@app.route('/')
def index():
    shinhonbang = db.session.query(Article).filter_by(id=1).filter_by(is_public=True).limit(5)
    minecraft = db.session.query(Article).filter_by(id=2).filter_by(is_public=True).limit(5)
    context = {'site_info':site_info(), 'last_article': last_article(),
                'shinhonbang':shinhonbang, 'minecraft':minecraft
    }
    return render_template('index.html', **context)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = registration_form(request.form)
    if request.method == 'POST' and form.validate():
        salt = bcrypt.gensalt()
        user = User(user_name = remove_html_tag(form.username.data), 
                    nick_name = remove_html_tag(form.nickname.data), 
                    email = remove_html_tag(form.email.data), 
                    password = bcrypt.hashpw(remove_html_tag(form.password.data), salt), 
                    confirmed_at = datetime.datetime.now(), 
                    last_login_at = datetime.datetime.now(),
                    current_login_at = datetime.datetime.now(),
                    last_login_ip = request.remote_addr,
                    current_login_ip = request.remote_addr,
                    login_count = "0",
                    active = True,
                    is_trust = False
                )
        db.session.add(user)
        db.session.commit()
        db.session.expunge_all()
        db.session.close()
        return redirect(url_for('login'))
    context = {'site_info':site_info(), 'form':form
    }
    return render_template('register_user.html', **context) 

@app.route("/login", methods=["GET", "POST"])
def login():
    form = login_form(request.form)
    if request.method == 'POST' and form.validate():
        user_info = User.query.filter_by(user_name=remove_html_tag(form.username.data)).first() 
        # form.username.data가 db에 없을 경우 
        if user_info is None:
            error_message = u"아이디나 암호가 틀립니다"
            context = { 'form' : form, 'error_message' : error_message, 'site_info': site_info() } 
            return render_template("login_user.html", **context )
        # active가 false 인 경우 비활성 계정임을 알림 
        if user_info.active is False:
            error_message = u"해당 계정은 사용이 정지되었습니다."
            context = { 'form' : form, 'error_message' : error_message, 'site_info': site_info() } 
            return render_template("login_user.html", **context )
        # form.password.data 해싱값이 디비의 해시와 같으면 로그인 
        if bcrypt.hashpw(remove_html_tag(form.password.data), user_info.password) == revemo_html_tag(user_info.password):
            user_info.last_login_at = datetime.datetime.now()
            user_info.current_login_at = datetime.datetime.now()
            user_info.last_login_ip = request.remote_addr
            user_info.current_login_ip = request.remote_addr
            user_info.login_count = int(user_info.login_count) + 1
            db.session.commit()
            login_user(user_info)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            error_message = "아이디나 암호가 틀립니다"
            context = { 'form' : form, 'error_message' : error_message } 
            return render_template("login_user.html", **context )
    context = { 'form' : form, 'site_info':site_info() } 
    return render_template("login_user.html", **context )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/<board>")
def board_view(board):
    # page 
    try:
        page = int(request.args.get('page'))
    except TypeError:
        page = int(1)
    finally:
        page = int(page) - 1
    board_info = get_board_info(board)
    article_list = db.session.query(Article).filter_by(is_public=True).\
                    filter_by(board_id=board_info.id).\
                    order_by(desc(Article.id)).limit(ARTICLE_PER_PAGE).\
                    offset(int(page)*int(ARTICLE_PER_PAGE)).all()

    # article list
    for article in article_list:
        article.views = r_hits.get(db_id+str(article.id))
        if (article.views == None):
            article.views = 0
        isoformat_date = (parser.parse(str(article.create_at)))
        isoformat_date = (isoformat_date.isoformat())
        article.create_at_ago = isoformat_date

    pagination = Pagination(page, ARTICLE_PER_PAGE, board_info.total_article_number)
    page = page + 1

    # act 
    try:
        act = unicode(request.args.get('act'))
    except TypeError:
        pass
    else:
        if act == "delete":
            return "delete"
        elif act == "update":
            return "update"

    # article 
    try:
        article = int(request.args.get('article'))
    except TypeError:
        pass
    else:
        article_detail = db.session.query(Article).filter_by(id=article).filter_by(is_public=True).first()
        r_hits.incr(db_id+str(article_detail.id))
        context = {'site_info':site_info(), 'article_list':article_list,
                   'board_info':board_info, 'pagination':pagination,
                   'page':page, 'article_detail':article_detail
        }
        return render_template('article.html', **context)


    context = {'site_info':site_info(), 'article_list':article_list,
               'board_info':board_info, 'pagination':pagination,
               'page':page }
    return render_template('article.html', **context)

@app.route("/write", methods=['GET', 'POST'])
def board_write():
    form = write_article_form(request.form)
    board_info = get_board_info(board_name)
    if request.method == 'POST' and form.validate():
        if (current_user.is_authenticated() is True):
            user_name = current_user.user_name
            nick_name = current_user.nick_name
            password = current_user.password
            is_anonymous = False
            user_id = current_user.get_id()
        else:
            user_name = "Anonymous"
            nick_name = remove_html_tag(form.nick_name.data)
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(remove_html_tag(form.password.data), salt)
            is_anonymous = True
            user_id = None
        board_id = board_info.id
        title = remove_html_tag(form.title.data)
        text = remove_script_tag(form.redactor.data)
        create_at = datetime.datetime.now()
        modified_at = create_at
        is_notice = False
        is_public = True
        is_best= False
        ip = request.remote_addr
        thumbs_up = 0
        thumbs_down = 0
        reply_number = 0
        article = Article(user_name=user_name,
                        nick_name=nick_name,
                        password=password,
                        is_anonymous=is_anonymous,
                        title=title,
                        text=text,
                        create_at=create_at,
                        modified_at=modified_at,
                        is_notice=is_notice,
                        is_public=is_public,
                        is_best=is_best,
                        ip=ip,
                        thumbs_up=thumbs_up,
                        thumbs_down=thumbs_down,
                        reply_number=reply_number,
                        user_id=user_id,
                        board_id=board_id
                    )
        db.session.add(article)
        db.session.commit()
        r_hits.set(db_id+str(article.id), 0)
        db.session.expunge_all()
        db.session.close()

        board_info = get_board_info(board_name)
        board_info.total_article_number = db.session.query(Article).filter_by(board_id=board_info.id).filter_by(is_public=True).count()
        db.session.commit()
        db.session.expunge_all()
        db.session.close()
        return redirect(url_for('board_view', BOARD_NAME=board_name, PAGE_NUMBER = 1))
    context = {'site_info':site_info(), 
                'form':form,
                'board_info':board_info}
    return render_template('article_write.html', **context)

@app.route('/init_db')
def init_db():
    db.create_all()
    context = { 
    }
    return "init_db"

@app.route('/drop_all')
def drop_all():
    db.drop_all()
    return "drop_all"
