#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import telegram
import praw
import os
import logging
import html
import sys

from time import sleep
from datetime import datetime


if 'TOKEN' not in os.environ:
    raise RuntimeError("Put bot token in TOKEN env var")

if 'SUBREDDIT' not in os.environ:
    raise RuntimeError("Put subreddit name in SUBREDDIT env var")

if 'CHANNEL' not in os.environ:
    raise RuntimeError("Put channel name in CHANNEL env var")


log = logging.getLogger('telegram_poster')
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

TOKEN = os.environ['TOKEN']
SUBREDDIT = os.environ['SUBREDDIT']
CHANNEL = os.environ['CHANNEL']
MAINTAINER = os.environ['MAINTAINER']
START_TIME = datetime.utcnow().timestamp()

# Read the file with latest submissions
def read_last_submissions_id():
    try:
        with open('last_submissions.id', 'r') as f:
            content = f.readlines()
            return [line.strip() for line in content]
    except:
        log.info('File not found, creating a new one.')
        with open('last_submissions.id', 'w') as f:
            f.close()

# Write post id to file after sending to channel
def write_last_submissions_id(submission_id):
    try:
        with open('last_submissions.id', 'a') as f:
            f.write(submission_id + "\n")
            f.close()
    except:
        log.exception("--- ERROR writing submission ID")

# Clear submissions file after two days
def clear_last_submissions():
    pass

def notify_maintainer(e):
    bot.sendMessage(chat_id=MAINTAINER, text=str(e))

def rest():
    log.info("--- Finished 'hot' list, rechecking in one hour")
    sleep(3600)

r = praw.Reddit(user_agent='Reddit-to-Telegram', site_name="default")
r.read_only = True
bot = telegram.Bot(token=TOKEN)

while datetime.now().minute != 0:
    log.info('Waiting for next hour.')
    sleep(1)

while True:
    subreddit = r.subreddit(SUBREDDIT).hot(limit=25)
    last_submissions_id = read_last_submissions_id()

    try:
        for submission in subreddit:
            link = 'https://redd.it/{id}'.format(id=submission.id)
            if submission.id in last_submissions_id:  # Repeat until you find a new entry
                log.info(f'Not posting \"{submission.title}\", repeated entry.')
                continue

            flair = html.escape(submission.link_flair_text or '')
            title = html.escape(submission.title or '')
            message_template = f'<a href=\'{link}\'>{title}</a>'

            log.info(f'Posting \"{link}\"')
            bot.sendMessage(chat_id=CHANNEL, parse_mode=telegram.ParseMode.HTML, text=message_template)
            # bot.sendMessage(chat_id=MAINTAINER, parse_mode=telegram.ParseMode.HTML, text=message_template)  # DEBUG
            write_last_submissions_id(submission.id)
            rest()
    except Exception as e:
        log.exception("--- ERROR parsing {}".format(link))
        notify_maintainer(e)
