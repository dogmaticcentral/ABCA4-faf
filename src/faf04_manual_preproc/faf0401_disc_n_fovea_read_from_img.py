#! /usr/bin/env python

from imagesize import imagesize

from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from utils.image_utils import read_single_channel
from utils.ndarray_utils import ndarray2pointlist
from utils.utils import  is_nonempty_file


def sanity_check(original_path, disc_and_macula_filepath):

    tiff_extension = ".tiff"
    if original_path[-len(tiff_extension):] != tiff_extension:
        print(f"I expected extension '{tiff_extension}' in the  original image path, got {original_path} instead.")
        return False
    if not is_nonempty_file(original_path):
        print(f"{original_path} is empty or does not exist")
        return False

    if not is_nonempty_file(disc_and_macula_filepath):
        print(f"{disc_and_macula_filepath} is empty or does not exist")
        return False

    if imagesize.get(disc_and_macula_filepath) != imagesize.get(original_path):
        print("the image sizes to not seem to match:")
        for path in [disc_and_macula_filepath, original_path]:
            print(f"\t {path}  {imagesize.get(path)}")
        return False

    return True


def find_center(list_of_coords) -> list[int]:
    if len(list_of_coords) == 0: return [0, 0]
    x_center = int(round(sum([x for (x, y) in list_of_coords])/len(list_of_coords), 0))
    y_center = int(round(sum([y for (x, y) in list_of_coords])/len(list_of_coords), 0))

    return [x_center, y_center]


def find_center_of_circle_img(path, channel) -> list[int]:
    circle  = read_single_channel(path, channel)
    vectors = ndarray2pointlist(circle)
    return find_center(vectors)


def store_centers(faf_img: FafImage, image_size, disc_center, fovea_center):

    center_info = {
        "width": image_size[0], "height": image_size[1],
        "disc_x": disc_center[0], "disc_y": disc_center[1],
        "fovea_x": fovea_center[0], "fovea_y": fovea_center[1]
    }
    FafImage.update(**center_info).where(FafImage.id == faf_img.id).execute()
    print(f"updated disc and fovea center for {faf_img}")


def process_disc_and_macula(faf_img: FafImage, expected_extension: str):

    disc_and_macula_filepath = str(faf_img.image_path).replace(".tiff", expected_extension)

    print(f"processing {faf_img.image_path}")
    if not sanity_check(faf_img.image_path, disc_and_macula_filepath):
        exit()

    image_size = imagesize.get(disc_and_macula_filepath)
    disc_center  = find_center_of_circle_img(disc_and_macula_filepath, "red")
    fovea_center = find_center_of_circle_img(disc_and_macula_filepath, "green")
    print(f"\t  image_size {image_size}   disc_center {disc_center}  macula_center {fovea_center} ")

    store_centers(faf_img, image_size, disc_center, fovea_center)


def disc_and_macula_locations_known(faf_img: FafImage):
    if faf_img.width is None: return False
    if faf_img.width is None: return False
    if faf_img.disc_y is None: return False
    if faf_img.fovea_x is None: return False
    if faf_img.fovea_y is None: return False
    return True


def main():
    expected_extension = ".disc_and_macula.png"

    db = db_connect()
    for faf_img in FafImage.select().where(FafImage.usable==1):
        if disc_and_macula_locations_known(faf_img): continue
        process_disc_and_macula(faf_img, expected_extension)
    db.close()


########################################
if __name__ == "__main__":
   main()
