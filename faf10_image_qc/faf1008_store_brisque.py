#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from utils.db_utils import db_connect

from models.abca4_results  import Score
from faf05_image_qc.qc_utils.stat_utils import brisque_score

class BrisqueScore(FafAnalysis):

    def input_manager(self, faf_img_dict) -> Path:
        return Path(faf_img_dict["image_path"])

    @staticmethod
    def store_or_update(image_id, score):
        score_selected = Score.select().where(Score.faf_image_id == image_id)
        if score_selected.exists():
            update_fields = {'brisque_score': round(score,2)}
            Score.update(**update_fields).where(Score.faf_image_id == image_id).execute()
        else:
            score_info = {"faf_image_id": image_id, 'brisque_score': score}
            score_created = Score.create(**score_info)
            score_created.save()


    #######################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """ Inner content of the loop over faf image data - a convenience for parallelization
        :param faf_img_dict: bool
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        db = db_connect()
        original_image_path = self.input_manager(faf_img_dict)
        try:
            score = brisque_score(original_image_path)
            self.store_or_update(faf_img_dict["id"], score)
            return "ok"
        except Exception as e:
            return f"failed: {e}"
        finally:
            db.close()  # is this ever reached?


def is_brisque_in_score_table() -> bool:
    db = db_connect()
    ok = True
    if not Score.table_exists():
        print(f"table Score not found found in {db.database}")
        ok = False
    else:
        existing_columns = [col.name for col in db.get_columns('scores')]
        if 'brisque_score' not in existing_columns:
            print(f"table Score in {db.database} does not have 'brisque_score' column")
            ok = False
    db.close()
    return ok

def main():
    if not is_brisque_in_score_table(): exit(1)
    faf_analysis = BrisqueScore(name_stem="brisque_score")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
