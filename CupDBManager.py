import sqlite3
import os
import sys
import logging

script_path = os.path.dirname(os.path.realpath(__file__))


class CupDBManager:

    def __init__(self, target=script_path + os.path.sep + "cup.db"):
        self.target = target
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.target)

    def close(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def create_database(self):
        try:
            c = self.conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS cup_question (
                question_id INTEGER PRIMARY KEY ON CONFLICT IGNORE,
                question_identifier TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                link TEXT,
                up_votes INTEGER,
                comment_count INTEGER,
                creation_date DATE,
                creation_time_in_db DATE,
                is_deleted INTEGER
                )''')

            c.execute('''CREATE TABLE IF NOT EXISTS cup_tag (
                name TEXT PRIMARY KEY,
                is_company INTEGER
                )''')

            c.execute('''CREATE TABLE IF NOT EXISTS cup_question_with_tag (
                question_id INTEGER,
                tag_name TEXT,
                PRIMARY KEY (question_id, tag_name)
                )''')

            self.conn.commit()
            logging.info('Database initialized.')

        except:
            logging.Exception(
                'Failed to create databse: ' + str(sys.exc_info()))
            raise

        finally:
            c.close()

    def drop_database(self):
        pass

    def insert_question(self, question):
        last_id = -1
        try:
            c = self.conn.cursor()
            c.execute('''INSERT OR IGNORE INTO cup_question VALUES(NULL, ?, ?, ?, ?, ?, ?, datetime('now'), 0 )''',
                      (question.question_id, question.question_content, question.link, question.up_votes, question.comment_count, question.creation_date))
            # self.conn.commit()
            last_id = c.lastrowid
        except:
            logging.Exception(
                'Failed to insert question: ' + str(sys.exc_info()))
            raise
        finally:
            c.close()

        return last_id

    def insert_tag(self, tag_name, is_company=0):
        try:
            c = self.conn.cursor()
            c.execute(
                '''INSERT OR IGNORE INTO cup_tag VALUES(?,?)''', (tag_name, is_company))
            # self.conn.commit()
        except:
            logging.Exception('Failed to insert tag: ' + str(sys.exc_info()))
            raise
        finally:
            c.close()

    def insert_question_with_tag(self, question_id, tag_name):
        try:
            c = self.conn.cursor()
            c.execute(
                '''INSERT OR IGNORE INTO cup_question_with_tag VALUES(?, ?)''', (question_id, tag_name))
            # self.conn.commit()
        except:
            logging.Exception(
                'Failed to insert question_with_tag: ' + str(sys.exc_info()))
            raise
        finally:
            c.close()
