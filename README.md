
## Choosing your db server

You don't have to choose one, just make sure not to delete the db.sqlitee file that
will appear in your work directory.


## Settings

Fill in the values in `faf00_settings.py`. You don't have to run this script, but if you do it will 
do some basic sanity checking for the settings you have provided.

## Creating and loading the database

The csv/tsc should have the following columns, in arbitrary order:
patient id, 

Note that you can export a tbels in csv format from any major spreadsheet application.
If you use tabe as the field separator, please give the file the extension ".tsv" because the separator is
guessed from the extension (',' for a csv, and '\t' for tsv file.)

## Labeling the faf images
* create a png image (e.g. using Inkscape) marking the optic disc and the center of the macula (putative fovea location)
* use that to create an svg image with the disc, macula and the two ellipses
* overlay the ellipses and create the png image containing disc, macula, usable and bg_sample region (red, green, blue purple)