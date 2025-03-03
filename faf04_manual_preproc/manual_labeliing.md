
(ths md is work in progress)

Use overlays (produced earlier) and Inkscpae / Adobe Illustrator or similar
to label the locations of disc, fovea, usable region(s) and the background sampling region in each image.

To use the existing scripts, The optic disc should be labeled as a red circle (pure single channel colors), 
and fovea as a green circe, and saved together as a png image of the same same dimensions
as the original image. The file should be name *.disc_and_fovea.png, where * stands for the name stem of
the original image.

Similarly, the usable and sampling regions should be saved as blue areas and saved individually, in files
with the extensions *.usable_region.png and *.bg_sample.png in the same directory with the original image.
THe dimensions should again be the same  as in the original image.

The bg sampling region should be chosen from somewhere outside the inner and inside
the outer ellipse.

THe script `faf0901_disc_n_fovea_read_from_img.py` can be used to read off the pixel locations of 
the disc and fovea centers, and store the im the database, in the `faf_images table`.