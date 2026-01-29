#!/usr/bin/env python

"""
    © 2024-2026 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pathlib import Path

import svgwrite

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, GEOMETRY, DEBUG
from utils.conventions import construct_workfile_path
from utils.fundus_geometry import disc_fovea_distance, fovea_disc_angle
from utils.image_utils import svg2png
from utils.utils import is_nonempty_file, scream


class FafOverlay(FafAnalysis):

    def __init__(self, internal_kwargs: dict|None=None, name_stem: str = "overlay"):
        super().__init__(internal_kwargs=internal_kwargs, name_stem=name_stem)
        description = "Create overlay images - transparent background, fovea and disc centers, ellipses."
        description += f"\nThis comes handy when manually determining the background (reference) region."
        self.description = description

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        pass

    def write_svg_overlay(self, faf_img_dict, skip_if_exists=False) -> str:

        """
        Write an svg file containing the locations and approx size of optic disc and fovea,as well as
        the inner and outer ellipse to be used as a guide for tha mask creation.
        https://svgwrite.readthedocs.io/en/latest/index.html
        https://pythonfix.com/code/svgwrite-code-examples/
        https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-width
        """

        for important_data in ['width', 'height', 'disc_x', 'disc_y', 'fovea_x', 'fovea_y']:
            if faf_img_dict.get(important_data) is None:
                scream(f"{important_data} not found for {faf_img_dict['image_path']}")
                return "failed"

        image_size   = (faf_img_dict['width'], faf_img_dict['height'])
        disc_center  = (faf_img_dict['disc_x'], faf_img_dict['disc_y'])
        fovea_center = (faf_img_dict['fovea_x'], faf_img_dict['fovea_y'])

        svg_filepath = construct_workfile_path(WORK_DIR, faf_img_dict['image_path'], faf_img_dict['case_id']['alias'],
                                                eye=faf_img_dict['eye'], purpose='overlay',  filetype='svg')
        if skip_if_exists and is_nonempty_file(svg_filepath):
            if DEBUG: print(f"found {svg_filepath}")
            return str(svg_filepath)

        # Create a new SVG drawing with specified width and height
        dwg = svgwrite.Drawing(str(svg_filepath), size=image_size)
        dist = disc_fovea_distance(disc_center, fovea_center)

        # Draw a red circle around disc center
        dwg.add(dwg.circle(center=disc_center, r=int(round(dist*GEOMETRY["disc_radius"])), fill='red'))

        # ... and a green one around fovea
        dwg.add(dwg.circle(center=fovea_center, r=int(round(dist*GEOMETRY["fovea_radius"])), fill='green'))

        # the inner ellipse
        radii = tuple(i*dist for i in GEOMETRY["ellipse_radii"])
        (x, y) = fovea_center
        angle = fovea_disc_angle(fovea_center, disc_center)
        extra_args = {"stroke": "red", "fill": "none", "stroke-width": int(round(dist/12)),
                      "transform": f"rotate({angle} {x} {y})"}
        dwg.add(dwg.ellipse(center=fovea_center, r=radii,  **extra_args))

        # the outer ellipse
        radii = tuple(i*dist for i in GEOMETRY["outer_ellipse_radii"])
        dwg.add(dwg.ellipse(center=fovea_center, r=radii,  **extra_args))

        # Save the SVG file
        dwg.save()
        if DEBUG: print(f"wrote {svg_filepath}")
        return str(svg_filepath)

    def write_png_overlay(self, svg_filepath, faf_img_dict, skip_if_exists=False):
        # Convert the SVG file to PNG
        # (For some reason, inkscape does not interpret the svg coordinated correctly, and they
        #  end up shifted wrt to the original tff image. N.B. gimp does not have this problem,
        #  However, if we convert to png, then the geometry works as intended.)
        png_filepath  = construct_workfile_path(WORK_DIR, faf_img_dict['image_path'], faf_img_dict['case_id']['alias'],
                                                eye=faf_img_dict['eye'], purpose='overlay',  filetype='png')
        if skip_if_exists and is_nonempty_file(png_filepath):
            if DEBUG: print(f"found {png_filepath}")
            return str(png_filepath)

        svg2png(svg_filepath, png_filepath)
        if DEBUG: print(f"wrote {png_filepath}")
        if is_nonempty_file(png_filepath):
            print(f"wrote {png_filepath}")
            return str(png_filepath)
        else:
            return f"{png_filepath} failed"

    def single_image_job(self, faf_img_dict: dict, skip_if_exists):

        if DEBUG: print(faf_img_dict['image_path'])

        svg_filepath = self.write_svg_overlay(faf_img_dict, skip_if_exists)
        if "failed" in svg_filepath:
            return f"failed creating svg for {faf_img_dict['image_path']}"
        return self.write_png_overlay(svg_filepath, faf_img_dict, skip_if_exists)


def main():
    faf_analysis = FafOverlay()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
