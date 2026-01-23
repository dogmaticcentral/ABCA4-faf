
"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from peewee import FloatField, ForeignKeyField, Model, CharField, IntegerField

from models.abca4_faf_models import FafImage, global_db_proxy


class BaseModel(Model):
    class Meta:
        database = global_db_proxy  # what is the purpose of this?


class OptosLocation(BaseModel):
    class Meta:
        table_name = "optos_locations"
    faf_image_id = ForeignKeyField(FafImage, backref='optos_locations')  # what is backref?
    fovea_algorithm = CharField(null=True)
    fovea_location_x = IntegerField(null=False)
    fovea_location_y = IntegerField(null=False)
    fovea_confidence = FloatField(null=False)
    disc_location_x  = IntegerField(null=False)
    disc_location_y  = IntegerField(null=False)
    disc_confidence = FloatField(null=False)


class FAF123Label(BaseModel):
    class Meta:
        table_name = "faf123_labels"
    faf_image_id = ForeignKeyField(FafImage, backref='faf123_labels')  # what is backref?
    label = IntegerField(null=False)
    curator = CharField(null=True)
