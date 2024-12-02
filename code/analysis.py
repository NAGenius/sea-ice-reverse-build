import os.path

import numpy as np
import pandas as pd
from cftime import num2date
from netCDF4 import Dataset
from pyproj import Transformer, Proj

from utils.get_data import read_tif, coord2xy


def get_concentration(year, _lat, _lon):
    _data = read_tif(f'../concentration/data/N_{year}_concentration_v3.0.tif')[0]
    # x_coords, y_coords = coord2xy((447, 303), geotransform)  # 第447行303列
    for j in range(len(_lat)):
        x, y = transformer2.transform(_lat[j], _lon[j])
        col, row = int((x - x_coords[0]) / 25000), int((y_coords[0] - y) / 25000)
        if _data[row][col] in [0, 2530, 2540, 2550]:
            for k in range(len(dx)):
                if 0 < _data[row + dy[k]][col + dx[k]] < 1000:
                    _data[row][col] = _data[row + dy[k]][col + dx[k]]
                    break
        concentrations.append(_data[row][col])


def get_thickness(year, _lat, _lon):
    _nc_obj = Dataset(f'../thickness/data/{year}09.nc', 'r')  # epsg:3411
    if int(year) > 2014:
        _data = np.array(_nc_obj.variables['sea_ice_thickness'][:])
        x, y = to3411(_lon, _lat)
        for j in range(len(x)):
            col, row = int((x[j] - x_coords2[0][0]) / 25000), int((y_coords2[0][0] - y[j]) / 25000)
            if _data[row][col] == -9999:
                for k in range(len(dx)):
                    if _data[row + dy[k]][col + dx[k]] != -9999:
                        _data[row][col] = _data[row + dy[k]][col + dx[k]]
                        break
            thickness.append(_data[row][col])
    else:
        _data = np.array(_nc_obj.variables['thickness'][:])
        x, y = to3408(_lon, _lat)
        for j in range(len(x)):
            col, row = int((x[j] - x_coords3[0][0]) / 100000), int((y[j] - y_coords3[0][0]) / 100000)
            if _data[row][col] == np.nan:
                for k in range(len(dx)):
                    if _data[row + dy[k]][col + dx[k]] != np.nan:
                        _data[row][col] = _data[row + dy[k]][col + dx[k]]
                        break
            thickness.append(_data[row][col])


if __name__ == '__main__':
    dx = [0, 0, 1, -1, -1, -1, 1, 1]
    dy = [1, -1, 0, 0, -1, 1, -1, 1]
    data, geotransform, transformer = read_tif('../concentration/data/N_19800909_concentration_v3.0.tif')
    transformer2 = Transformer.from_crs(transformer.target_crs, transformer.source_crs)
    x_coords, _ = coord2xy((0, np.arange(304)), geotransform)
    _, y_coords = coord2xy((np.arange(448), 0), geotransform)

    nc_obj = Dataset('../thickness/data/201509.nc', 'r')  # epsg:3411
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    nc_obj.close()
    to3411 = Proj('epsg:3411')
    x_coords2, y_coords2 = to3411(lon, lat)
    x_coords2 -= 25000 / 2
    y_coords2 += 25000 / 2

    nc_obj = Dataset('../motion/data/icemotion_daily_nh_25km_19790101_19791231_v4.1.nc', 'r')
    crs_wkt = nc_obj.variables['crs'].crs_wkt
    nc_obj.close()
    nc_obj = Dataset('../thickness/data/197909.nc', 'r')  # epsg:3408'
    lat = np.array(nc_obj.variables['latitude'][:])
    lon = np.array(nc_obj.variables['longitude'][:])
    nc_obj.close()
    to3408 = Proj(crs_wkt)
    x_coords3, y_coords3 = to3408(lon, lat)
    concentrations, thickness = [], []

    # print(x_coords[0], y_coords[0], x_coords[-1], y_coords[-1], len(y_coords))
    # print(x_coords2[0][0], y_coords2[0][0], x_coords2[0][-1], y_coords2[-1][0], y_coords2.shape)
    # get_concentration(20160913, [88.42886], [-110.83542])
    # get_thickness(2016, [88.42886], [-110.83542])
    # print(concentrations)
    # print(thickness)

    nc_obj = Dataset('../result/start/nc/all.nc', 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    time = np.array(nc_obj.variables['time'][:])
    dates = [date.strftime('%Y%m%d') for date in num2date(time, units=nc_obj.variables['time'].units)]
    nc_obj.close()

    missing = {
        "1980": "19790905",
        "1981": "19800909",
        "1982": "19810912",
        "1983": "19820907",
        "1984": "19830916",
        "1985": "19840908",
        "1986": "19850905",
    }
    tmp_lat, tmp_lon = [], []
    for i in range(len(lat)):
        if str(int(dates[i][:4]) + 1) in missing:
            dates[i] = missing[str(int(dates[i][:4]) + 1)]
        if dates[i] != dates[i - 1] and i != 0:
            print(dates[i])
            get_concentration(dates[i - 1], tmp_lat, tmp_lon)
            get_thickness(dates[i - 1][:4], tmp_lat, tmp_lon)
            tmp_lat, tmp_lon = [], []
        tmp_lat.append(lat[i])
        tmp_lon.append(lon[i])

    if len(tmp_lat):
        get_concentration(dates[-1], tmp_lat, tmp_lon)
        get_thickness(dates[-1][:4], tmp_lat, tmp_lon)

    cnt = 0
    for i in range(len(thickness)):
        if thickness[i] == -9999:
            cnt += 1
    print(cnt, len(thickness))
    cnt = 0
    for i in range(len(concentrations)):
        if concentrations[i] in [0, 2530, 2540, 2550]:
            cnt += 1
    print(cnt, len(concentrations))
    data = {
        '纬度(latitude)': lat,
        '经度(longitude)': lon,
        '密集度(concentration)': concentrations,
        '厚度(thickness)': thickness,
        '时间': dates
    }
    if not os.path.exists('../result/start'):
        os.mkdir('../result/start')
    pd.DataFrame(data).to_csv('../result/start/all.csv', index=False)
