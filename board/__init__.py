#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
from flask import Flask

config = ConfigParser.ConfigParser()
config.read("/home/luapz/public_html/do-lazy/config")
db_id = config.get('db', 'db_id')
ARTICLE_PER_PAGE = config.get('board', 'article_per_page')
secret_key = config.get('app', 'secret_key')

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

import views
import models
import forms
