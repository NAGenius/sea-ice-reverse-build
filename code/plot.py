import os
from pathlib import Path

import os
from pathlib import Path

import numpy as np
from netCDF4 import Dataset
from pyproj import Proj, Transformer

import utils.plot
from utils.get_data import read_tif
from utils.plot import plot_shadow

end_dir = '../result/end'
start_dir = '../result/start'
kde_dir = '../result/kde'
extent_dir = '../extent'
shadow_dir = '../result/shadow'


def read_nc(file_path):
    nc_obj = Dataset(file_path, 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    nc_obj.close()
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
        # plot_coordinates(_map, item.name[:4], lon, lat, img_path)
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
                dic[directory[:4]] = len(files)
                img_path = img_dir + '/' + directory[:4] + '.png'
                # plot_path(_map, directory[:4], files, img_path)
    # print(json.dumps(dic, indent=4))


def plot_kde(_map=None):
    nc_dir = start_dir + '/nc'
    lon, lat = read_nc(os.path.join(nc_dir, 'all.nc'))
    print(len(lon))
    img_path = kde_dir + '/kde.png'
    utils.plot.plot_kde(_map, 'KDE', lon, lat, img_path)


def plot_heatmap(_map=None):
    # nc_obj = Dataset('../code/all.nc', 'r')
    nc_obj = Dataset('../code/all2.nc', 'r')
    lats = np.array(nc_obj.variables['lat'][:])
    lons = np.array(nc_obj.variables['lon'][:])
    weights = np.array(nc_obj.variables['weight'][:])
    nc_obj.close()
    pos = (-4524654.440396539, -4524654.440396539)
    resolution = 50000
    to3408 = Proj('epsg:3408')
    transformer = Transformer.from_crs("epsg:3408", "epsg:4326")
    x, y = to3408(lons, lats)
    w, cnt = {}, {}
    lon, lat, weight = [], [], []
    for i in range(len(x)):
        col, row = int((x[i] - pos[0]) / resolution), int((y[i] - pos[1]) / resolution)
        w[(row, col)] = w.get((row, col), 0) + weights[i]
        cnt[(row, col)] = cnt.get((row, col), 0) + 1
    for key in w.keys():
        weight.append(w[key] / cnt[key])
        tmp_lat, tmp_lon = transformer.transform(pos[0] + resolution * (key[1]), pos[1] + resolution * (key[0]))
        lon.append(tmp_lon)
        lat.append(tmp_lat)
    lon = np.array(lon)
    lat = np.array(lat)
    weight = np.array(weight)
    sorted_indices = np.argsort(weight)[::-1]
    idx = sorted_indices[9:30]
    print(list(zip(lon[idx], lat[idx], weight[idx])))
    print(len(lat))
    # utils.plot.plot_heatmap(_map, 'Heatmap', lon, lat, weight)


if __name__ == '__main__':
    if not os.path.exists(kde_dir):
        os.mkdir(kde_dir)
    if not os.path.exists(shadow_dir):
        os.mkdir(shadow_dir)
    dic = {}
    # m = init_map()
    m = None
    # plot_extent(m)  # 画海冰范围阴影图
    # plot_end(m)  # 画终点
    # plot_start(m)  # 画起点
    # plot_kde(m)  # 画核密度
    plot_heatmap(m)
    # print(json.dumps(dic, indent=4))
