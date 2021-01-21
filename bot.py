import sys
import praw
import sqlite3
import os
import prawcore
import time
from configparser import ConfigParser

class Bot:

    def __init__(self, site):

        conf = ConfigParser()
        conf.read('/home/hacky/betterthanautomod/praw.ini')
        config = conf['meodp2']

        self.reddit = praw.Reddit('meopd2')
        self.subreddit = self.reddit.subreddit(reddit.config.custom['subreddit'])
        
        # Does not need to exit
        self.file = '/path/to/database/file.db'

        self.conn = sqlite3.connect(self.file)
        self.cursor = self.conn.cursor()

        # Create table
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, approved INTEGER, pending INTEGER, prior INTEGER)")
        self.cursor.execute("SELECT * FROM users")
        self.data = self.cursor.fetchall()

        # Me trying to be clever.
        changed = False

        for item in self.subreddit.new(limit=None):
            if str(item.author) not in [i[0] for i in self.data]:
                self.cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (str(item.author), 0, 0, 1))
                changed = True
        for item in self.subreddit.comments(limit=None):
            if str(item.author) not in [i[0] for i in self.data]:
                self.cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (str(item.author), 0, 0, 1))
                changed = True

        # It wasn't clever.
        if changed:
            self.conn.commit()

        self.cursor.execute("SELECT * FROM users")
        self.data = self.cursor.fetchall()


    def start(self):

        # DIY Stream Loop
        while True:
            self.stream()
            time.sleep(1)


    def stream(self):

        for item in self.subreddit.mod.modqueue(limit=None):
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (str(item.author),))
            data = self.cursor.fetchone()

            if not data:
                self.cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (str(item.author), 0, 1, 0))
                self.conn.commit()
                self.message(item.author, prior=0)
            elif data[1]:
                item.mod.approve()
            elif not data[2]:
                self.cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (str(item.author), 0, 1, data[3]))
                self.conn.commit()
                self.message(item.author, prior=data[3])

        for item in self.reddit.inbox.all(limit=None):
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (str(item.author),))
            data = self.cursor.fetchone()
            if not data:
                continue
            elif data[2] and 'yes' in item.body.lower() and item.new:
                self.cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (str(item.author), 1, 0, data[3]))
                self.conn.commit()
                item.mark_read()

        self.cursor.execute("SELECT * FROM users")
        self.data = self.cursor.fetchall()


    def message(self, user, *, prior):

        if prior:
            msg = """We would like to remind you to please make sure you've fulfilled the reading requirements over at our [wiki](https://new.reddit.com/r/AskAnAntinatalist/wiki/index?utm_source=reddit&utm_medium=usertext&utm_name=AskAnAntinatalist&utm_content=t5_287k4n) before participating. This is to ensure as much as possible that quality and original discussion takes place on /r/AskAnAntinatalist. 

Please confirm if you have read both the FAQ and The Ultimate Antinatalism Argument Guide Document.

[Confirm](https://www.reddit.com/message/compose/?to=AlphaMaleThrowAway2&subject=hi&message=yes) (Don't forget to hit "send" after clicking `Confirm`)"""
        
        else:
            msg = """We've detected that you're about to make your first post/comment on /r/AskAnAntinatalist. We would like to remind you to please make sure you've fulfilled the reading requirements over at our [wiki](https://new.reddit.com/r/AskAnAntinatalist/wiki/index?utm_source=reddit&utm_medium=usertext&utm_name=AskAnAntinatalist&utm_content=t5_287k4n) before participating. This is to ensure as much as possible that quality and original discussion takes place on our sub. 

Please confirm if you have read both the FAQ and The Ultimate Antinatalism Argument Guide Document.

[Confirm](https://www.reddit.com/message/compose/?to=AlphaMaleThrowAway2&subject=hi&message=yes) (Don't forget to hit "send" after clicking `Confirm`)"""

        try:
            user.message('Hold Your Horses!', msg)
        except praw.exceptions.RedditAPIException:
            pass


def main():
    while True:
        bot = Bot('meodp2')
        try:
            bot.start()
        except prawcore.exceptions.ServerError:
            pass


if __name__ == '__main__':
    main()


