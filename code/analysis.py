import numpy as np
from cftime import num2date
from netCDF4 import Dataset
from pyproj import Transformer

from utils.get_data import read_tif, coord2xy


def get_concentration(_filename, _lat, _lon):
    _data = read_tif(_filename)[0]
    # x_coords, y_coords = coord2xy((447, 303), geotransform)  # 第447行303列
    # print(x_coords, y_coords)
    for j in range(len(_lat)):
        x, y = transformer2.transform(_lat[j], _lon[j])
        # print(transformer.transform(x, y), _lat[j], _lon[j])
        col, row = np.searchsorted(x_coords, x, side='left') - 1, np.searchsorted(-y_coords, y, side='left') - 1
        if _data[row][col] in [2530, 2540]:
            for k in range(len(dx)):
                if 0 < _data[row + dy[k]][col + dx[k]] < 1000:
                    _data[row][col] = _data[row + dy[k]][col + dx[k]]
                    break
        concentrations.append(_data[row][col])


if __name__ == '__main__':
    dx = [0, 0, 1, -1]
    dy = [1, -1, 0, 0]
    data, geotransform, transformer = read_tif('../concentration/data/N_19800909_concentration_v3.0.tif')
    transformer2 = Transformer.from_crs(transformer.target_crs, transformer.source_crs)
    x_coords, _ = coord2xy((0, np.arange(304)), geotransform)
    _, y_coords = coord2xy((np.arange(448), 0), geotransform)
    # ice_indices = np.where((data > 0) & (data < 1000))  # 得到有海冰的坐标
    # x_coords, y_coords = coord2xy(ice_indices, geotransform)
    # lat, lon = transformer.transform(x_coords, y_coords)
    # print(max(lat), min(lat), max(lon), min(lon))  # 极点周围缺失值较多

    nc_obj = Dataset('../result/start/nc/all.nc', 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    time = np.array(nc_obj.variables['time'][:])
    dates = [date.strftime('%Y%m%d') for date in num2date(time, units=nc_obj.variables['time'].units)]
    concentrations = []
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
        if dates[i] != dates[i - 1] and i:
            filename = f'../concentration/data/N_{dates[i]}_concentration_v3.0.tif'
            get_concentration(filename, tmp_lat, tmp_lon)
            tmp_lat, tmp_lon = [], []
        tmp_lat.append(lat[i])
        tmp_lon.append(lon[i])

    filename = f'../concentration/data/N_{dates[-1]}_concentration_v3.0.tif'
    if len(tmp_lat):
        get_concentration(filename, tmp_lat, tmp_lon)
    print(set(concentrations))
