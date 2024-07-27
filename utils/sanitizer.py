#!/usr/bin/env python
import os
import warnings

import MySQLdb
import sys
import sqlite3

#######
def search_db(cursor, qry, verbose=False):
    warnings.filterwarnings('ignore', category=MySQLdb.Warning)
    try:
        cursor.execute(qry)
    except MySQLdb.Error as e:
        if verbose:
            print("Error running cursor.execute() for  qry:\n%s\n%s" % (qry, e.args[1]))
        return [["Error"], e.args]
    except MySQLdb.Warning as e: # this does not work for me - therefore filterwarnings
        if verbose:
            print("Warning running cursor.execute() for  qry:\n%s\n%s" % (qry, e.args[1]))
        return [["Warning"], e.args]

    try:
        rows = cursor.fetchall()
    except MySQLdb.Error as e:
        if verbose:
            print("Error running cursor.fetchall() for  qry:\n%s\n%s" % (qry, e.args[1]))
        return [["Error"], e.args]

    if len(rows) == 0:
        if verbose:
            print("No return for query:\n%s" % qry)
        return False

    # since python3 fetchall returns bytes inst of str in some  random fashion
    # not clear what's going on
    # here is a rather useless issue page on github
    # https://github.com/PyMySQL/mysqlclient-python/issues/145#issuecomment-283936456
    rows_clean = []
    for row in rows:
        rows_clean.append([r.decode('utf-8') if type(r)==bytes else r for r in row])
    return rows_clean


########
def connect_to_mysql():
    try:
        mysql_conn_handle =  MySQLdb.connect(host="127.0.0.1", port=3308,
                     user="abca4",
                     passwd=os.environ.get("MARIADB_PASSWD"),
                     db="abca4_faf")

    except  MySQLdb.Error as e:
        print(("Error connecting to mysql (%s) " % (e.args[1])))
        sys.exit(1)
    return mysql_conn_handle

########
def switch_to_db(cursor, db_name):
    qry = "use %s" % db_name
    rows = search_db(cursor, qry, verbose=False)
    if rows:
        print(rows)
        return False
    return True



def mariadb_connect():

    db = connect_to_mysql()
    cursor = db.cursor()
    search_db(cursor, "set autocommit=1")
    db.set_character_set('utf8mb4')
    cursor.execute('SET NAMES utf8mb4')
    cursor.execute('SET CHARACTER SET utf8mb4')
    cursor.execute('SET character_set_connection=utf8mb4')
    switch_to_db(cursor, "abca4")

    return db, cursor


def check_cases(cursor_maria, cursor_sqlit):

    qry = "select * from cases"
    maria_dict = dict((ret[1], ret[2:]) for ret in search_db(cursor_maria, qry))
    sqlit_dict = dict((ret[1], ret[2:]) for ret in search_db(cursor_sqlit, qry))
    for k, v_maria in maria_dict.items():
        v_sqlit = sqlit_dict[k]
        for i in range(len(v_maria)):
            if v_maria[i] != v_sqlit[i]:
                print(f"{k} mismatch in cases table")
                print(f"maria {v_maria[i]}")
                print(f"sqlit {v_sqlit[i]}")
                exit()
    print("cases ok")


def check_images(cursor_maria, cursor_sqlit):
    qry = "select * from faf_images"
    maria_dict = dict((ret[3], [ret[2]] + ret[4:-2]) for ret in search_db(cursor_maria, qry))
    sqlit_dict = dict((ret[3], [ret[2]] + ret[4:-2]) for ret in search_db(cursor_sqlit, qry))
    for k, v_maria in maria_dict.items():
        v_sqlit = sqlit_dict[k]
        for i in range(len(v_maria)):
            if v_maria[i] != v_sqlit[i]:
                print(f"{k} mismatch in faf_images table")
                print(f"maria {v_maria[i]}")
                print(f"sqlit {v_sqlit[i]}")
                exit()
    print(f"images ok")


def check_scores(cursor_maria, cursor_sqlit, score_name):
    qry = f"select faf_image_id, {score_name} from scores"
    for img_id_maria, score_maria in search_db(cursor_maria, qry):
        qry = f"select image_path from faf_images where id={img_id_maria}"
        image_path = search_db(cursor_maria, qry)[0][0]

        qry = f"select id from faf_images where image_path='{image_path}'"
        image_id_sqlite = search_db(cursor_sqlit, qry)[0][0]

        qry = f"select {score_name} from scores where faf_image_id={image_id_sqlite}"
        score_sqlit = search_db(cursor_sqlit, qry)[0][0]
        if round(score_maria, 0) != round(score_sqlit, 0):
            print(f"{image_path},  {img_id_maria},   {image_id_sqlite},    {score_maria:.2f},   {score_sqlit:.2f}")
            exit()
    print("scores ok")


def main():
    db_maria, cursor_maria = mariadb_connect()
    switch_to_db(cursor_maria, "abca4_faf")

    db_sqlit = sqlite3.connect("../abca4_faf.sqlite")
    cursor_sqlit = db_sqlit.cursor()

    check_cases(cursor_maria, cursor_sqlit)
    check_images(cursor_maria, cursor_sqlit)
    check_scores(cursor_maria, cursor_sqlit, "pixel_score")

    cursor_sqlit.close()
    db_sqlit.close()

    cursor_maria.close()
    db_maria.close()


########################
if __name__ == "__main__":
    main()

