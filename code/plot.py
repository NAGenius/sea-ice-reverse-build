import os
from pathlib import Path

import numpy as np

from netCDF4 import Dataset

import utils.plot
from utils.plot import plot_coordinates, plot_path, init_map

end_dir = '../result/end'
start_dir = '../result/start'
kde_dir = '../result/kde'


def read_nc(file_path):
    nc_obj = Dataset(file_path, 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    return lon, lat


def plot_end(_map):
    nc_dir = end_dir + '/nc'
    img_dir = end_dir + '/img'
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    for item in Path(nc_dir).rglob('*.nc'):
        lon, lat = read_nc(item)
        img_path = img_dir + '/' + item.name[:4] + '.png'
        plot_coordinates(_map, item.name[:4], lon, lat, img_path)


def plot_start(_map):
    nc_dir = start_dir + '/nc'
    img_dir = start_dir + '/img'
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    for _, dirs, _ in os.walk(nc_dir):
        for directory in dirs:
            tmp = os.path.join(nc_dir, directory)
            for _, _, files in os.walk(tmp):
                files = [os.path.join(tmp, file) for file in files]
                print(len(files))
                img_path = img_dir + '/' + directory[:4] + '.png'
                plot_path(_map, directory[:4], files, img_path)


def plot_kde(_map):
    nc_dir = start_dir + '/nc'
    img_dir = kde_dir + '/img'
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    lon_all, lat_all = [], []
    for _, dirs, _ in os.walk(nc_dir):
        for directory in dirs:
            tmp = os.path.join(nc_dir, directory)
            for _, _, files in os.walk(tmp):
                for file in files:
                    lon, lat = read_nc(os.path.join(tmp, file))
                    lon_all.append(lon[-1])
                    lat_all.append(lat[-1])
    print(len(lon_all))
    img_path = img_dir + '/kde.png'
    utils.plot.plot_kde(_map, 'KDE', lon_all, lat_all, img_path)


if __name__ == '__main__':
    if not os.path.exists(end_dir):
        os.mkdir(end_dir)
    if not os.path.exists(start_dir):
        os.mkdir(start_dir)
    if not os.path.exists(kde_dir):
        os.mkdir(kde_dir)

    m = init_map()
    # plot_end(m)  # 画终点
    plot_start(m)  # 画起点
    # plot_kde(m)  # 画核密度
