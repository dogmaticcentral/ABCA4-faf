
"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import datetime
from faf00_settings import global_db_proxy
from peewee import (BooleanField, CharField, DateTimeField, FloatField,
                    ForeignKeyField, IntegerField, Model, TextField, Proxy)

"""
Database tables, aka 'models' defined using peewee (python ORM package).
See http://docs.peewee-orm.com/en/latest/index.html
"""

# creating db as a global var is the suggested use for pewee (ugh. why?)
# this breaks down parallelization
# db = db_connect()
# class BaseModel(Model):
#     class Meta:
#         database = db  # what is the purpose of this?


class BaseModel(Model):
    class Meta:
        database = global_db_proxy


class Case(BaseModel):
    class Meta:
        table_name = "cases"
    alias     = CharField(unique=True)
    onset_age = FloatField(null=True)
    haplotype_tested = BooleanField(default=False, null=False)
    is_control       = BooleanField(default=False, null=False)


class FafImage(BaseModel):
    class Meta:
        table_name = "faf_images"

    case_id = ForeignKeyField(Case, backref='faf_images')  # what is backref?
    eye     = CharField(max_length=2, null=False)  # Sqlite has no enum fields, so peewee does not support it either
    image_path   = CharField(unique=True)
    age_acquired = FloatField(null=True)
    width  = IntegerField(null=True)
    height = IntegerField(null=True)
    disc_x = IntegerField(null=True)
    disc_y = IntegerField(null=True)
    fovea_x = IntegerField(null=True)
    fovea_y = IntegerField(null=True)
    usable  = BooleanField(default=True, null=False)
    vasculature_detectable = BooleanField(default=True, null=False)
    clean_view = BooleanField(default=False, null=False)
    notes      = TextField(null=True)

    created_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)


class ImagePair(BaseModel):
    class Meta:
        table_name = "image_pairs"

    left_eye_image_id  = ForeignKeyField(FafImage, backref='image_pairs')
    right_eye_image_id = ForeignKeyField(FafImage, backref='image_pairs')
