# -*- coding: utf-8 -*-

import logging
import subprocess
import sys
import geopandas as gpd
from shapely.geometry import Polygon, box
import pandas as pd
from datetime import datetime as dt
import os, glob
import zipfile
import copy
import numpy as np
import rasterio
import rasterio.features
import rasterio.mask
import rasterio.warp
import rasterio.plot
import rasterio.crs
import shapely.geometry

class RasterFragment:
    """
    """

    def __init__(
        self, polygon: shapely.geometry.Polygon, raster: rasterio.io.DatasetReader,
    ) -> None:

        self.raster = raster

        # Get data only inside polygon(s) 
        image, self.transform = rasterio.mask.mask(
            dataset=raster,
            shapes=[shapely.geometry.mapping(polygon)],
            crop=True,
            nodata=0,
            filled=False,
            all_touched=True,
            pad=False,
        )

        # Be aware of a squeezable dimension
        self.masked_image = rasterio.plot.reshape_as_image(image)

    def save(self, path: str, crs: int, dtype, nodata) -> None:
        """
        """
        # Load CRS
        crs_object = rasterio.crs.CRS.from_epsg(crs)

        # Cast
        masked_image = self.masked_image.astype(dtype)

        # Get dimensions
        raster_width = masked_image.shape[1]
        raster_height = masked_image.shape[0]

        # Get contoured part bounds
        bounds = rasterio.transform.array_bounds(raster_height, raster_width, self.transform)

        # Get transform in specific CRS
        transform, width, height = rasterio.warp.calculate_default_transform(
            self.raster.crs,
            crs_object,
            self.raster.width,
            self.raster.height,
            *bounds,
        )

        # Get raster profile
        profile = copy.deepcopy(self.raster.profile)

        # Update it with fresh info
        profile.update(
            crs = crs_object,
            dtype=dtype,
            height=height,
            width=width,
            nodata=nodata,
            transform=transform,
            compress="lzw",
        )

        # Unmask array
        image = masked_image.filled(nodata)

        # Welcome in shape hell
        image = rasterio.plot.reshape_as_raster(image)

        # Write
        with rasterio.open(path, "w", **profile) as output_raster:
            output_raster.write(image)

LOG_FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=LOG_FORMAT)


def handle_end_of_command_execution(proc) -> None:
    """
    Updates the task status based on the return code of the command
    """

    if proc.returncode != 0:
        print("Error happened during process, code {}".format(
            proc.returncode))
        sys.exit(1)
    return


def follow_command_execution(proc):
    """
    Follows the command execution, updates the task progression
    and logs the outputs
    """
    while proc.poll() is None:
        line = proc.stdout.readline()
        if line:
            print(line)

    handle_end_of_command_execution(proc)


def run_a_command(command):
    """
    Run the specified command, and returns the process object
    """
    proc = subprocess.Popen(command,
                            bufsize=1,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            shell=False
                            )
    return proc


def dl_S2_from_aoi(config_path, input_aoi, tuile, start_date, end_date, out_folder):

    satellite = 'S2ST'

    ### Extract BBOX of project to get the AOI
    gpf_aoi = gpd.read_file(input_aoi)

    satellite = 'S2ST'

    ### Download S2 image
    logging.debug('Launch S2 download')
    script = '/opt/task/peps_download.py'
    if tuile is not None:
        logging.debug(f'Launch S2 download on the tuile: {tuile}')
        cmd = [
            'python3',
            script,
            '-c', f'{satellite}',
            '-t', f'{tuile}',
            '-a', f'{config_path}',
            '-d', f'{start_date}', 
            '-f', f'{end_date}', 
            '-w', f'{out_folder}'
            ]
    else:
        x = gpf_aoi.centroid.x[0]
        y = gpf_aoi.centroid.y[0]
        logging.debug(f'Launch S2 download on the centroid of aoi on X: {x} and Y: {y}')
        cmd = [
            'python3',
            script,
            '-c', f'{satellite}',
            '--lon', f'{x}',
            '--lat', f'{y}',
            '-a', f'{config_path}',
            '-d', f'{start_date}', 
            '-f', f'{end_date}', 
            '-w', f'{out_folder}'
            ] 

    print('Command to execute: {}'.format(' '.join(cmd)))
    proc = run_a_command(cmd)
    follow_command_execution(proc)

    ### Unzip the S2 data
    logging.debug('Unzip downloaded files')
    lst_files = glob.glob(os.path.join(out_folder,'*.zip'))

    for file in lst_files:
        with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(out_folder)

    lst_folder = os.listdir(out_folder)

    for folder in lst_folder:
        if folder.endswith('SAFE'):
            folder_split = folder.split('_')
            out_name_file = folder_split[0]+'_'+folder_split[1]+'_'+folder_split[5]+'_'+folder_split[6][:-12]+\
                '_B_G_R_RE705_RE740_RE783_NIR.tif'
            suffixe_jp2 = folder_split[5]+'_'+folder_split[2]+'_'

            ### Search the S2 bands of interest
            lst_jp2 = []
            for root, dirs, files in os.walk(out_folder):
                    for file in files:
                        if file.endswith(suffixe_jp2+"B02.jp2") or file.endswith(suffixe_jp2+"B03.jp2") or file.endswith(suffixe_jp2+"B04.jp2") \
                        or file.endswith(suffixe_jp2+"B05.jp2") or file.endswith(suffixe_jp2+"B06.jp2") or file.endswith(suffixe_jp2+"B07.jp2") \
                        or file.endswith(suffixe_jp2+"B08.jp2"):
                            path_file = os.path.join(root,file)
                            lst_jp2.append(path_file)
        
            logging.debug(f'Get reflectance band, number of bands is {len(lst_jp2)}')
            lst_jp2_sorted = sorted(lst_jp2)
            ### Write the S2 reflectance map
            out_path_file = os.path.join(out_folder, out_name_file) 
            logging.debug(f'Write reflectance map: {out_name_file}')

            f = rasterio.open(lst_jp2_sorted[0])
            bounds = f.bounds
            crs = int(f.crs.to_string().split(':')[1])
            with rasterio.open(f) as dataset:
                
                pixel_per_meter = float(10)
                ratio = dataset.transform[0]/ float(pixel_per_meter)
                print(ratio)
                
                data = dataset.read(
                        out_shape=(dataset.count, int(dataset.height * ratio ), int(dataset.width *ratio )),
                        resampling=Resampling.gauss
                    )
                
                # scale image transform
                transf = dataset.transform * dataset.transform.scale(
                    (dataset.width / data.shape[-1]),
                    (dataset.height / data.shape[-2])
                )
                out_meta = dataset.meta.copy()
                out_meta.update({'driver': 'GTiff',
                                'dtype': data.dtype,
                                'count': len(lst_jp2_sorted),
                                'compress': 'lzw',
                                'BIGTIFF': 'YES',
                                'width': data.shape[2],
                                'height': data.shape[1],
                                'crs': dataset.crs,
                                'nodata': dataset.nodata,
                                'transform': transf})
            

            gpf_aoi_utm = gpf_aoi.to_crs(crs)
            df_raster = gpd.GeoDataFrame({"id":1,"geometry":[box(*bounds)]}, crs = crs)
            
            logging.debug(f'Check if aoi overlap reflectance map')
            if len(gpd.sjoin(gpf_aoi_utm, df_raster, predicate='intersects')) != 0:
                with rasterio.open(
                        out_path_file,
                        'w',
                        ** out_meta
                        ) as dst:
                            for band_nr, src in enumerate(lst_jp2_sorted, start=1):
                                with rasterio.open(src) as src1:
                                        dst.write(src1.read(1), band_nr)

                ### Crop reflectance map
                out_name_file_crop = out_name_file[:-4]+'_crop.tif'
                logging.debug(f'Crop reflectance map: {out_name_file} in {out_name_file_crop}')
                # Outputs
                output_path = os.path.join(out_folder, out_name_file_crop)
                output_crs = crs
                output_dtype = np.float32
                output_nodata = -10000

                # Load inputs
                gpf_aoi_utm['geometry'] = gpf_aoi_utm.geometry.buffer(150)
                raster = rasterio.open(out_path_file)
                #output_crs = raster.crs

                # Merge contours
                polygon = gpf_aoi_utm.unary_union

                # Create raster fragment
                fragment = RasterFragment(raster = raster, polygon = polygon)

                # Save and project
                logging.debug('Save reflectance map')
                fragment.save(path = output_path, crs = output_crs, dtype = output_dtype, nodata = output_nodata)
            else:
                logging.debug("Polygon doesn't overlap reflectance map")
                sys.exit()
