#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

"""
Settings sanity (existence, accessibility) checks.
"""
import os

from peewee import InterfaceError, ImproperlyConfigured, OperationalError

from faf00_settings import WORK_DIR, DATABASES, RECOGNIZED_ENGINES
from utils.db_utils import db_connect
from utils.utils import scream, comfort, is_nonempty_file, shrug


def workdir_check() -> bool:
    if not WORK_DIR.exists():
        scream(f"Work dir {WORK_DIR} not found")
        return False
    if not WORK_DIR.is_dir():
        scream(f"Work dir {WORK_DIR} does not seem to be a directory.")
        return False
    # interestingly enough, pathlib does not seem to have
    # a native way of checking if a dir is writable
    if not os.access(WORK_DIR, os.W_OK):
        scream(f"Work dir {WORK_DIR} is not writeable by the current user.")
        return False
    comfort(f"Work dir {WORK_DIR} OK.")
    return True


def db_engine_recognized() -> bool:
    if "default" not in DATABASES:
        scream(f"default DB not declared in settings.py.")
        return False

    if "ENGINE" not in DATABASES["default"]:
        scream(f'default DB engine  not declared in DATABASES["default"] dict.')
        return False

    engine = DATABASES["default"]["ENGINE"]

    if engine not in RECOGNIZED_ENGINES:
        scream(f"DB engine {engine} not recognized.")
        return False
    print(f"We'll be using {engine} DB engine")
    return True


def db_pass_defined() -> bool:
    passw = DATABASES["default"]["PASSWORD"]
    if (passw is None) or (passw == ""):
        scream(f"DB password not provided. (As an env variable?)")
        return False
    comfort("DB password defined.")
    return True


def db_connection_check() -> bool:
    conn = db_connect(test=True)
    try:
        conn.connect()
    except ImproperlyConfigured as e:
        scream(str(e))
        return False
    except OperationalError as e:
        scream(f"DB server problem: {e}")
        if "Unknown database" in str(e):
            db = DATABASES["default"]["DB_NAME"]
            user = DATABASES["default"]["USER"]
            scream(f"    The database {db} must exist, and the user {user} have all privileges therein.")
        return False
    except InterfaceError as e:
        scream(str(e))
        scream(f"   In particular the database name passed to the connector cannot be 'None'.")
        return False

    comfort(f"DB connection OK.")
    return True


def postgres_check_schema_privilege(conn, schema, privilege):
    sql = """
    SELECT 
      has_schema_privilege(%s, %s) AS has_privilege
    """

    with conn.connection_context():
        result = conn.execute_sql(sql, [schema, privilege])

        for row in result.fetchall():
            return row[0]


def user_can_create_tables() -> bool:
    conn = db_connect(test=True)
    conn.connect()
    can_create = True
    if DATABASES["default"]["ENGINE"] == 'peewee.postgres':
        can_create = postgres_check_schema_privilege(conn, 'public', 'CREATE')

    # TODO: the same check for mysql - though setting perms is less tricky here
    elif DATABASES["default"]["ENGINE"] == 'peewee.mysql':
        shrug(f"'permission to create tables' check not implemented for the mysql case")
        can_create = True

    db = DATABASES["default"]["DB_NAME"]
    user = DATABASES["default"]["USER"]
    if not can_create:
        scream(f"User '{user}' has no permission to create tables in '{db}' database.")
    else:
        comfort(f"User '{user}' can create tables in '{db}' database.")
    return can_create


def main():
    """Sanity checking for the project settings"""

    print("Settings sanity check:")
    failed = 0
    for test in [workdir_check]:
        if not test():
            failed += 1

    if "sqlite" in DATABASES["default"]["ENGINE"]:
        dbname = DATABASES["default"]["DB_NAME"]
        if is_nonempty_file(dbname):
            pass
        else:
            scream(f"{dbname} does not exists or is empty")
            failed += 1
    else:
        for test in [db_pass_defined, db_connection_check, user_can_create_tables]:
            if not test():
                failed += 1

    if not failed:
        print(f"All sanity checks OK.")
    else:
        print(f"{failed} test{'s' if failed>1 else ''} failed.")


###########################
if __name__ == "__main__":
    main()
