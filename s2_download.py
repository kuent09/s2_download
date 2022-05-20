"""
Download S2 reflectance map from AOI
"""

import json
import logging
import os, glob
from pathlib import Path
import shutil
import sys
from dl_S2_from_aoi import dl_S2_from_aoi

LOG_FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=LOG_FORMAT)


def load_inputs(input_path):
    inputs_desc = json.load(open(input_path))
    inputs = inputs_desc.get('inputs')
    parameters = inputs_desc.get('parameters')
    return inputs, parameters


def main():
    WORKING_DIR = os.getenv('DELAIRSTACK_PROCESS_WORKDIR')
    if not WORKING_DIR:
        raise KeyError('DELAIRSTACK_PROCESS_WORKDIR environment variable must be defined')
    WORKING_DIR = Path(WORKING_DIR).resolve()

    logging.debug('Extracting inputs and parameters...')

    # Retrieve inputs and parameters from inputs.json
    inputs, parameters = load_inputs(WORKING_DIR / 'inputs.json')

    # Get info for the inputs
    config = inputs.get('config_file')
    config_path = inputs['config_file']['components'][0]['path']
    logging.info('Config_file dataset: {name!r} (id: {id!r}) in {config_path!r}'.format(
        name=config['name'],
        id=config['_id'],
        config_path=config_path))

    polygon = inputs.get('input_aoi')
    polygon_path = inputs['input_aoi']['components'][0]['path']
    logging.info('AOI dataset: {name!r} (id: {id!r} in {polygon_path!r})'.format(
        name=polygon['name'],
        id=polygon['_id'],
        polygon_path=polygon_path))

    tuile = parameters.get('tuile')
    logging.info('Tuile is: {name!r} '.format(
        name=tuile))    
    
    start_date = parameters.get('start_date')
    logging.info('Start date is: {name!r} '.format(
        name=start_date))

    end_date = parameters.get('end_date')
    logging.info('End date is: {name!r} '.format(
        name=end_date))

    # Create the output directory
    logging.debug('Creating the output directory')
    outpath = WORKING_DIR

    # Simulate computation
    logging.info('Computing download S2 and crop by location...')
    dl_S2_from_aoi(config_path,
                    polygon_path,
                    tuile,
                    start_date,
                    end_date,
                    str(outpath))

    # Create the outputs file path
    out_names = {}
    lst_output = glob.glob(str(outpath)+'/*.tif')
    logging.info(f'Number of outputs: {len(lst_output)}')
    for file in lst_output:
        if file.endswith('R.tif'):
            outfilename = os.path.basename(file)
            out_names.update({"reflectance_map" : [outfilename, file]})
        elif file.endswith('crop.tif'):
            outfile_crop = os.path.basename(file)
            out_names.update({"reflectance_map_crop" : [outfile_crop, file]})
    
    logging.info(f'Output file on: {out_names["reflectance_map"][1]}')
    logging.info(f'Output file crop on: {out_names["reflectance_map_crop"][1]}')

    # Create the outputs.json to describe the deliverables and its path
    logging.debug('Creating the outputs.json')
    outputs = {
        "outputs": {
            "reflectance_map": {  # Must match the name of deliverable in yaml
                "type": "raster",
                "format": "tif",
                "name": out_names["reflectance_map"][0],
                "bands":[{'name':'blue'},
                        {'name':'green'},
                        {'name':'red'},
                        {'name':'red_edge_705'},
                        {'name':'red_edge_740'},
                        {'name':'nir'}],
                "categories":['reflectances'],
                "components": [
                    {
                        "name": "raster",
                        "path": out_names["reflectance_map"][1]
                    }
                ]
            },
            "reflectance_map_crop": {  # Must match the name of deliverable in yaml
                "type": "raster",
                "format": "tif",
                "name": out_names["reflectance_map_crop"][0],
                "bands":[{'name':'blue'},
                        {'name':'green'},
                        {'name':'red'},
                        {'name':'red_edge_705'},
                        {'name':'red_edge_740'},
                        {'name':'nir'}],
                "categories":['reflectances'],
                "components": [
                    {
                        "name": "raster",
                        "path": out_names["reflectance_map_crop"][1]
                    }
                ]
            }
        },
        "version": "0.1"
    }
    with open(WORKING_DIR / 'outputs.json', 'w+') as f:
        json.dump(outputs, f, indent = 4)

    logging.info('End of processing.')


if __name__ == '__main__':
    main()
