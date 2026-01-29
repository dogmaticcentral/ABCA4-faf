
"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from faf00_settings import DATABASES, RECOGNIZED_ENGINES, global_db_proxy
from peewee import MySQLDatabase, PostgresqlDatabase, SqliteDatabase


def db_connect(test=False, initialize_global=True):
    for kwd in ["ENGINE", "DB_NAME"]:
        try:
            DATABASES["default"][kwd]
        except:
            raise Exception(f"{kwd} not defined in DATABASES dict")
    engine = DATABASES["default"]["ENGINE"]
    if engine not in RECOGNIZED_ENGINES:
        raise Exception(f"Engine {engine} not recognized.")

    if engine in set(RECOGNIZED_ENGINES).difference({"peewee.sqlite"}):
        for kwd in ["USER", "PASSWORD", "HOST", "PORT"]:
            try:
                DATABASES["default"][kwd]
            except:
                raise Exception(f"{kwd} not defined in DATABASES dict")

    db_name = DATABASES["default"]["DB_NAME"]

    connection = {
        "peewee.sqlite": SqliteDatabase,
        "peewee.mysql": MySQLDatabase,
        "peewee.postgres": PostgresqlDatabase
    }

    if engine == "peewee.sqlite":
        db_handle = SqliteDatabase(db_name)
    else:
        db_handle = connection[engine](
            db_name,
            user=DATABASES["default"]["USER"],
            password=DATABASES["default"]["PASSWORD"],
            host=DATABASES["default"]["HOST"],
            port=DATABASES["default"]["PORT"],
            autoconnect=False
        )

    if initialize_global:
        global_db_proxy.initialize(db_handle)
        if not test: db_handle.connect()

    return db_handle
