import os
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

from utils.get_data import read_tif
import utils.plot
from utils.plot import plot_coordinates, plot_shadow, plot_path, init_map

end_dir = '../result/end'
start_dir = '../result/start'
kde_dir = '../result/kde'
extent_dir = '../extent'
shadow_dir = '../result/shadow'


def read_nc(file_path):
    nc_obj = Dataset(file_path, 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    return lon, lat


def plot_extent(_map=None):
    folder_path = Path(os.path.join(extent_dir, 'data'))
    for item in folder_path.rglob('*.tif'):
        _, _, _, lat, lon = read_tif(item)
        img_path = shadow_dir + '/' + item.name[2:6] + '.png'
        plot_shadow(_map, item.name[2:6], lon, lat, img_path)


def plot_end(_map=None):
    nc_dir = end_dir + '/nc'
    img_dir = end_dir + '/img'
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    for item in Path(nc_dir).rglob('*.nc'):
        # if item.name[:4] != '1984':
        #     continue
        lon, lat = read_nc(item)
        dic[item.name[:4]] = len(lon)
        img_path = img_dir + '/' + item.name[:4] + '.png'
        plot_coordinates(_map, item.name[:4], lon, lat, img_path)
    # print(json.dumps(dic, indent=4))


def plot_start(_map=None):
    nc_dir = start_dir + '/nc'
    img_dir = start_dir + '/img'
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    for _, dirs, _ in os.walk(nc_dir):
        for directory in dirs:
            # if directory[:4] != '1984':
            #     continue
            tmp = os.path.join(nc_dir, directory)
            for _, _, files in os.walk(tmp):
                files = [os.path.join(tmp, file) for file in files]
                # dic[directory[:4]] = {'end': dic[directory[:4]], 'start': len(files)}
                img_path = img_dir + '/' + directory[:4] + '.png'
                plot_path(_map, directory[:4], files, img_path)
    # print(json.dumps(dic, indent=4))


def plot_kde(_map=None):
    nc_dir = start_dir + '/nc'
    lon, lat = read_nc(os.path.join(nc_dir, 'all.nc'))
    print(len(lon))
    img_path = kde_dir + '/kde.png'
    utils.plot.plot_kde(_map, 'KDE', lon, lat, img_path)


if __name__ == '__main__':
    if not os.path.exists(kde_dir):
        os.mkdir(kde_dir)
    if not os.path.exists(shadow_dir):
        os.mkdir(shadow_dir)
    dic = {}
    m = init_map()
    # m = None
    # plot_extent(m)  # 画海冰范围阴影图
    plot_end(m)  # 画终点
    plot_start(m)  # 画起点
    plot_kde(m)  # 画核密度
    # print(json.dumps(dic, indent=4))
