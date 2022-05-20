# s2_download
The code containing in this folder is to deploy a custom analytic for Alteia's platform. All steps are here  https://alteia.helpjuice.com/en_US/sdk-and-cli/custom-analytics

In this project, there are all files to create a custom analytic. 

This custom analytic allows to download a S2 tuile and crop it with a given AOI.

The search of S2 data is in 2 dates. For the moment we can only download one tuile.

So check it before on https://peps.cnes.fr/rocket/#/search?maxRecords=50&page=1

This script use peps_download script written by Olivier Hagolle (https://github.com/olivierhagolle/peps_download)

Inputs are:
- AOI, polygon of area of interest;
- peps credentials in a txt file uploaded on the project (format: mail password)

The parameters are:
- Tuile of S2 (if not set, get the centroid of the AOI)
- Start date
- End date

Outpus are:
- Reflectance_map_B_G_R_RE705_RE740_NIR: S2 reflectance map
- Reflectance_map_B_G_R_RE705_RE740_NIR_crop: S2 reflectance map cropped by AOI

