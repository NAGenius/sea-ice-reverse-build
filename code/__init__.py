import os

import numpy as np
from netCDF4 import Dataset

from utils.get_data import read_tif


def normalize(data):
    data = np.array(data)
    min_val = np.min(data)
    max_val = np.max(data)
    return (data - min_val) / (max_val - min_val)


def init():
    conc, thick = {}, {}
    for _, _, files in os.walk('../concentration/data'):
        for file in files:
            data = read_tif(os.path.join('../concentration/data', file))[0]
            conc[file[2:6]] = data
    for _, _, files in os.walk('../thickness/data'):
        for file in files:
            data = Dataset(os.path.join('../thickness/data', file), 'r')  # epsg:3411
            if int(file[:4]) < 2015:
                thick[file[:4]] = np.array(data.variables['thickness'][:])
            else:
                thick[file[:4]] = np.array(data.variables['sea_ice_thickness'][:])
    return conc, thick
