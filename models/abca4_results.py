
"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from peewee import FloatField, ForeignKeyField, Model

from models.abca4_faf_models import FafImage, global_db_proxy


class BaseModel(Model):
    class Meta:
        database = global_db_proxy  # what is the purpose of this?


class Score(BaseModel):
    class Meta:
        table_name = "scores"
    faf_image_id = ForeignKeyField(FafImage, backref='scores')  # what is backref?
    pixel_score = FloatField(null=True)
    pixel_score_auto = FloatField(null=True)
    pixel_score_peripapillary = FloatField(null=True)

