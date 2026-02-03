
"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from peewee import FloatField, ForeignKeyField, Model
from faf00_settings import global_db_proxy
from models.abca4_faf_models import FafImage


class BaseModel(Model):
    class Meta:
        database = global_db_proxy  # what is the purpose of this?


class Score(BaseModel):
    class Meta:
        table_name = "scores"
    faf_image_id = ForeignKeyField(FafImage, backref='scores',  on_delete='CASCADE')  # what is backref?
    pixel_score = FloatField(null=True)
    pixel_score_auto = FloatField(null=True)
    pixel_score_denoised = FloatField(null=True)
    pixel_score_peripapillary = FloatField(null=True)
    brisque_score = FloatField(null=True)


class PlaygroundScore(BaseModel):
    class Meta:
        table_name = "playground_scores"
    faf_image_id = ForeignKeyField(FafImage, backref='playground_scores')  # what is backref?
    pixel_score_white = FloatField(null=True)
    pixel_score_black = FloatField(null=True)
    pixel_score_1 = FloatField(null=True)  # black pixel with the same weight as the white one
    pixel_score_5 = FloatField(null=True)  # black pixel with  5 times the weight of the white
    pixel_score_15 = FloatField(null=True)  # black pixel with 15 times the weight of the white

