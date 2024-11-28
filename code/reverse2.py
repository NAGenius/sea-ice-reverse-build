import os.path
from pathlib import Path

import numpy as np
from pyproj import CRS, Transformer
from scipy.spatial.distance import cdist

from utils.get_data import merge_data

# from utils.plot import plot_path
from utils.write_data import write_data

end_nc_dir = '../result/end/nc'
start_nc_dir = '../result/start/nc'
start_img_dir = '../result/start/img'


def reverse(path_x, path_y, days_motion, days_idle):
    global lat, lon, u, v, x, y, days, transformer, year, cnt, path_all
    if days_motion == 365:
        path_lat, path_lon = transformer.transform(path_x, path_y)
        cnt += 1
        nc_path = start_nc_dir + '/' + year + '/' + str(cnt) + '.nc'
        print(cnt)
        path_all.append(nc_path)
        write_data(path_lat, path_lon, [days], nc_path)
        return
    # if days_idle >= 30:
    #     print('超过30天处于无效值位置')
    #     return
    col, row = np.searchsorted(x, path_x[-1], side='left') - 1, np.searchsorted(y, path_y[-1], side='left') - 1
    # 以该网格点为中心，向外扩展出7*7的搜索范围（根据海冰的速度确定）
    u1 = (u[days_motion][row - 3: row + 4, col - 3: col + 4]).astype(float).reshape((7 * 7, 1))
    v1 = (v[days_motion][row - 3: row + 4, col - 3: col + 4]).astype(float).reshape((7 * 7, 1))
    x1 = np.tile(x[col - 3: col + 4], (7, 1)).reshape((7 * 7, 1))
    y1 = np.tile(y[row - 3: row + 4], (7, 1)).reshape((7 * 7, 1))
    pos = np.hstack((x1, y1))
    # 如果u1/v1数组中存在不是-9999（无效点）的点，则求其起点
    if np.any(u1 != fill_value):
        # 根据速度得到第i天7*7网格上每个点海冰漂移的位移（逆向位移取反），再计算 终点 = 起点 + 位移
        predict_x = (path_x[-1] - 864 * u1).reshape((7 * 7, 1))
        predict_y = (path_y[-1] - 864 * v1).reshape((7 * 7, 1))
        predict_pos = np.hstack((predict_x, predict_y))
        start_x, start_y = [], []
        # 计算每一个预测的起点与7*7网格中每一个点的欧式距离
        dist = cdist(predict_pos, pos, 'euclidean')
        # 判断该起点是否满足
        min_idx = np.argmin(dist, axis=1)
        flag = False
        for j in range(len(min_idx)):
            # 求出终点最接近的网格编号，判断是否由该点海冰漂移过来
            if dist[j][min_idx[j]] < 35355 and u1[min_idx[j]] == u1[j] and v1[min_idx[j]] == v1[j]:
                start_x.append(predict_x[j][0])
                start_y.append(predict_y[j][0])
                flag = True
        # 去重
        # start_x = list(set(start_x_tmp))
        # start_x.sort(key=start_x_tmp.index)
        # start_y = list(set(start_y_tmp))
        # start_y.sort(key=start_y_tmp.index)
        # print(start_x, start_y)
        # coordinates = list(zip(start_x, start_y))
        coordinates = list(set(list(zip(start_x, start_y))))
        # if len(coordinates) > 1:
        #     print('1111111111111111111111111')
        # 对于第i个点找到一个或多个起点，多起点则以第一个为起点继续逆向，或者递归每一个起点（以下为第一种方法）
        if flag:
            for j in range(len(coordinates)):
                path_x.append(coordinates[j][0])
                path_y.append(coordinates[j][1])
                reverse(path_x, path_y, days_motion + 1, days_idle)
                path_x.pop()
                path_y.pop()
        # 对于第i个点未找到其起点
        else:
            path_x.append(path_x[-1])
            path_y.append(path_y[-1])
            reverse(path_x, path_y, days_motion + 1, days_idle + 1)
    else:
        path_x.append(path_x[-1])
        path_y.append(path_y[-1])
        reverse(path_x, path_y, days_motion + 1, days_idle + 1)
    return


if __name__ == '__main__':
    folder_path = Path(end_nc_dir)
    resolution = 25000
    fill_value = -9999
    for item in folder_path.rglob('*.nc'):
        cnt = 0
        year = item.name[:4]
        if year != '1980':
            continue
        if int(year) > 2022 or int(year) < 1980:
            continue
        print(year + "----------------------------------------------")
        ends, lat, lon, u, v, x, y, crs_wkt, days = merge_data(item)
        u = u[::-1]
        v = v[::-1]
        x -= resolution / 2
        y -= resolution / 2
        source_crs = CRS.from_wkt(crs_wkt)
        target_crs = CRS.from_epsg(4326)
        transformer = Transformer.from_crs(source_crs, target_crs)
        transformer2 = Transformer.from_crs(target_crs, source_crs)

        if not os.path.exists(start_nc_dir + '/' + year):
            os.mkdir(start_nc_dir + '/' + year)
        if not os.path.exists(start_img_dir):
            os.mkdir(start_img_dir)

        path_all = []
        for end in ends:
            print(end)
            sx, sy = transformer2.transform(end[0], end[1])
            reverse([sx], [sy], 0, 0)
        from utils.plot import plot_path
        path_img = start_img_dir + '/' + year + '.png'
        plot_path(path_all, path_img)
