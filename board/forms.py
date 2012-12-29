#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wtforms import Form, BooleanField, TextField, PasswordField, TextAreaField, \
                    validators

class registration_form(Form):
    username = TextField('id', [validators.Length(min=2, max=20)])
    nickname = TextField('Nick name', [validators.Length(min=2, max=20)])
    email = TextField('Email address', [validators.Length(min=2, max=50)])
    password = PasswordField('password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('confirm Password')

class profile_form(Form):
    nickname = TextField('Nick name', [validators.Length(min=2, max=20)])
    email = TextField('Email address', [validators.Length(min=2, max=50)])

class login_form(Form):
    username = TextField('id', [validators.Length(min=2, max=50),
                                validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    remember = BooleanField('remember')

class write_article_form(Form):
    nick_name = TextField('nick name', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    title = TextField('title', [validators.Required()])
    redactor = TextAreaField('Text', [validators.Required()])

class write_reply_form(Form):
    nick_name = TextField('nick name', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    redactor = TextAreaField('Text', [validators.Required()])
