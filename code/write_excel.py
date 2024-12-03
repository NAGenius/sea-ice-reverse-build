from datetime import datetime

import numpy as np
from cftime import num2date
from netCDF4 import Dataset
from pyproj import Transformer, Proj

from utils.get_data import read_tif, coord2xy


def get_concentration(_year, _lat, _lon):
    _data = read_tif(f'../concentration/data/N_{_year}_concentration_v3.0.tif')[0]
    # x_coords, y_coords = coord2xy((447, 303), geotransform)  # 第447行303列
    ans = []
    for j in range(len(_lat)):
        x, y = transformer2.transform(_lat[j], _lon[j])
        col, row = int((x - x_coords[0]) / 25000), int((y_coords[0] - y) / 25000)
        _col, _row = col, row
        if _data[row][col] == 2510:  # 极点
            k = 1
            while True:
                if 0 < _data[row - k][col] < 1000:
                    _row, _col = row - k, col
                    break
                if 0 < _data[row + k][col] < 1000:
                    _row, _col = row + k, col
                    break
                k += 1
        if _data[row][col] in [0, 2530, 2540, 2550]:  # 无效值
            rows, cols = [], []
            for r in range(row - 3, row + 4):
                for c in range(col - 3, col + 4):
                    if 0 < _data[r][c] < 1000:
                        rows.append(r)
                        cols.append(c)
            min_dist = float('inf')
            for k in range(len(rows)):
                r, c = rows[k], cols[k]
                dist = (x_coords[c] - x_coords[col]) ** 2 + (y_coords[r] - y_coords[row]) ** 2
                if dist < min_dist:
                    min_dist = dist
                    _row, _col = r, c
        ans.append(_data[_row][_col] / 10)
    return ans


def get_thickness(_year, _lat, _lon):
    _nc_obj = Dataset(f'../thickness/data/{_year}09.nc', 'r')  # epsg:3411
    ans = []
    if int(_year) > 2014:
        _data = np.array(_nc_obj.variables['sea_ice_thickness'][:])
        x, y = to3411(_lon, _lat)
        for j in range(len(x)):
            col, row = int((x[j] - x_coords2[0][0]) / 25000), int((y_coords2[0][0] - y[j]) / 25000)
            _col, _row = col, row
            if _data[row][col] == -9999:
                rows, cols = [], []
                for r in range(row - 5, row + 6):
                    for c in range(col - 5, col + 6):
                        if _data[r][c] != -9999:
                            rows.append(r)
                            cols.append(c)
                min_dist = float('inf')
                for k in range(len(rows)):
                    r, c = rows[k], cols[k]
                    dist = (x_coords2[0][c] - x_coords2[0][col]) ** 2 + (y_coords2[r][0] - y_coords2[row][0]) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        _row, _col = r, c
            ans.append(_data[_row][_col])
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
            ans.append(_data[row][col])
    return ans


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

    nc_obj = Dataset('../result/start/nc/all.nc', 'r')
    lat = np.array(nc_obj.variables['lat'][:])
    lon = np.array(nc_obj.variables['lon'][:])
    time = np.array(nc_obj.variables['time'][:])
    date = [date.strftime('%Y%m%d') for date in num2date(time, units=nc_obj.variables['time'].units)]
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
    dates, lats, lons, concentrations, thicknesses = [], [], [], [], []
    tmp_date, tmp_lat, tmp_lon = [], [], []
    for i in range(len(lat)):
        if str(int(date[i][:4]) + 1) in missing:
            date[i] = missing[str(int(date[i][:4]) + 1)]
        if date[i] != date[i - 1] and i != 0:
            print(date[i])
            concentrations.append(get_concentration(date[i - 1], tmp_lat, tmp_lon))
            thicknesses.append(get_thickness(date[i - 1][:4], tmp_lat, tmp_lon))
            lats.append(tmp_lat)
            lons.append(tmp_lon)
            dates.append(tmp_date)
            tmp_date, tmp_lat, tmp_lon = [], [], []
        tmp_date.append(datetime.strptime(date[i], '%Y%m%d').strftime('%Y-%m-%d'))
        tmp_lat.append(lat[i])
        tmp_lon.append(lon[i])

    if len(tmp_lat):
        concentrations.append(get_concentration(date[-1], tmp_lat, tmp_lon))
        thicknesses.append(get_thickness(date[-1][:4], tmp_lat, tmp_lon))
        lats.append(tmp_lat)
        lons.append(tmp_lon)
        dates.append(tmp_date)
    # with pd.ExcelWriter('../result/start/all.xlsx') as writer:
    #     for date, lat, lon, conc, thick in zip(dates, lats, lons, concentrations, thicknesses):
    #         df = pd.DataFrame({
    #             '日期(date)': date,
    #             '纬度(latitude/(°))': lat,
    #             '经度(longitude/(°))': lon,
    #             '密集度(concentration/(percent))': conc,
    #             '厚度(thickness/(m))': thick,
    #         })
    #         # 将DataFrame写入对应年份的工作表
    #         df.to_excel(writer, sheet_name=str(int(date[0][:4]) + 1), index=False)
