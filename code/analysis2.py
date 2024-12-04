import numpy as np
from cftime import num2date
from netCDF4 import Dataset
from pyproj import Proj

from code import init, normalize
from utils.plot import plot_heatmap, init_map


def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def get_min(rows, cols, row, col):
    min_dist = float('inf')
    ans_r, ans_c = 0, 0
    for k in range(len(rows)):
        dist = manhattan_distance(rows[k], cols[k], row, col)
        if dist < min_dist:
            min_dist = dist
            ans_r, ans_c = rows[k], cols[k]
    return ans_r, ans_c


def get_concentration(year, lat, lon):
    data = concentration[year]
    x, y = to3411(lon, lat)
    col, row = int((x - pos[0][0]) / 25000), int((pos[0][1] - y) / 25000)
    if data[row][col] == 2510:  # 极点
        k = 0
        while True:
            k += 1
            if 0 < data[row - k][col] < 1000:
                return data[row - k][col] / 10
            if 0 < data[row + k][col] < 1000:
                return data[row + k][col] / 10

    if data[row][col] in [0, 2530, 2540, 2550]:  # 无效值
        rows, cols = [], []
        for r in range(row - 3, row + 4):
            for c in range(col - 3, col + 4):
                if 0 < data[row][col] < 1000:
                    rows.append(r)
                    cols.append(c)
        row, col = get_min(rows, cols, row, col)
    return data[row][col] / 10 if 0 < data[row][col] < 1000 else 0


def get_thickness(year, lat, lon):
    data = thickness[year]
    if int(year) < 2015:
        x, y = to3408(lon, lat)
        col, row = int((x - pos[1][0]) / 100000), int((y - pos[1][1]) / 100000)
    else:
        x, y = to3411(lon, lat)
        col, row = int((x - pos[0][0]) / 25000), int((pos[0][1] - y) / 25000)
    if data[row][col] in [-9999, np.nan]:
        rows, cols = [], []
        for r in range(row - 3, row + 4):
            for c in range(col - 3, col + 4):
                if data[row][col] not in [-9999, np.nan]:
                    rows.append(r)
                    cols.append(c)
        row, col = get_min(rows, cols, row, col)
    return data[row][col] if data[row][col] not in [-9999, np.nan] else 0


def get_weight(conc, thick, year):
    # for i in range(1979, 2022):
    #     conc[i] = normalize(conc[i])
    #     thick[i] = normalize(thick[i])
    # for i in range(len(conc[1979])):
    #     w = 0
    #     for j in range(1979, 2022):
    #         w += year_weight[str(j)] * (conc_weight * conc[j][i] + thick_weight * thick[j][i])
    #     weight.append(w)
    conc = normalize(conc)
    thick = normalize(thick)
    for i in range(len(conc)):
        w = year_weight[year] * (conc_weight * conc[i] + thick_weight * thick[i])
        # w = conc_weight * conc[i] + thick_weight * thick[i]
        weight.append(w)


if __name__ == '__main__':
    # x_coords = np.arange(-3850000.0, -3850000.0 + 25000 * 304, 25000)
    # y_coords = np.arange(5850000.0, 5850000.0 - 25000 * 448, -25000)
    # x_coords = np.arange(-4524654.440396539, -4524654.440396539 + 100000 * 91, 100000)
    # y_coords = np.arange(-4524654.440396539, -4524654.440396539 + 100000 * 91, 100000)
    to3411 = Proj('epsg:3411')
    to3408 = Proj('epsg:3408')
    pos = [(-3850000.0, 5850000.0), (-4524654.440396539, -4524654.440396539)]
    # 权重设置
    conc_weight = 0.4
    thick_weight = 0.6
    alpha = 1.03
    years = list(range(1979, 2022))
    tmp = alpha ** np.arange(0, len(years) + 1)
    # tmp = tmp / tmp.sum()
    year_weight = {str(year): weight for year, weight in zip(years, tmp)}
    concentration, thickness = init()
    print(year_weight)
    nc_obj = Dataset('../result/start/nc/all.nc', 'r')
    lats = np.array(nc_obj.variables['lat'][:])
    lons = np.array(nc_obj.variables['lon'][:])
    times = np.array(nc_obj.variables['time'][:])
    dates = [date.strftime('%Y%m%d') for date in num2date(times, units=nc_obj.variables['time'].units)]
    nc_obj.close()

    weight = []
    m = init_map()
    # tmp_conc, tmp_thick = {year: [] for year in range(1979, 2022)}, {year: [] for year in range(1979, 2022)}
    tmp_conc, tmp_thick = [], []
    for i in range(len(dates)):
        if dates[i] != dates[i - 1] and i != 0:
            print(dates[i - 1])
            get_weight(tmp_conc, tmp_thick, dates[i - 1][:4])
            # plot_heatmap(m, dates[i][:4], lons[i - len(tmp_conc):i], lats[i - len(tmp_conc):i],
            #              weight[i - len(tmp_conc):i], f'../result/heatmap/{dates[i][:4]}.png')
            # tmp_conc, tmp_thick = {year: [] for year in range(1979, 2022)}, {year: [] for year in range(1979, 2022)}
            tmp_conc, tmp_thick = [], []
        # for j in range(1979, 2022):
        #     tmp_conc[j].append(get_concentration(str(j), lats[i], lons[i]))
        #     tmp_thick[j].append(get_thickness(str(j), lats[i], lons[i]))
        tmp_conc.append(get_concentration(dates[i][:4], lats[i], lons[i]))
        tmp_thick.append(get_thickness(dates[i][:4], lats[i], lons[i]))
    print(dates[-1])
    get_weight(tmp_conc, tmp_thick, dates[-1][:4])
    # plot_heatmap(m, dates[-1][:4], lons[len(dates) - len(tmp_conc):-1], lats[len(dates) - len(tmp_conc):-1],
    #              weight[len(dates) - len(tmp_conc):-1], f'../result/heatmap/{dates[-1][:4]}.png')
    print(len(weight))
    print(max(weight), min(weight))
    # dataset = Dataset('all.nc', 'w', format='NETCDF4')
    dataset = Dataset('all2.nc', 'w', format='NETCDF4')
    dataset.createDimension('lat', len(lats))
    dataset.createDimension('lon', len(lons))
    dataset.createDimension('weight', len(weight))
    latitudes_var = dataset.createVariable('lat', 'f4', ('lat',))
    longitudes_var = dataset.createVariable('lon', 'f4', ('lon',))
    weight_var = dataset.createVariable('weight', 'f4', ('weight',))
    latitudes_var[:] = lats
    longitudes_var[:] = lons
    weight_var[:] = weight
    dataset.close()
    # plot_heatmap(m, 'Heatmap', lons, lats, weight)
