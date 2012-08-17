#!/usr/bin/env python
# -*- coding:utf-8 -*-

import redis
from datetime import datetime
redis = redis.StrictRedis(host='localhost', port=6379, db="oneline")


creat_date = str(datetime.now())[:19]
redis.set(creat_date, "0")
print creat_date
