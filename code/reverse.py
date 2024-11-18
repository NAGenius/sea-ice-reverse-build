import os.path
from pathlib import Path

import numpy as np
from pyproj import CRS, Transformer

from utils.get_data import merge_data
from utils.plot import plot_path
from utils.write_data import write_data

end_nc_dir = '../result/end/nc'
start_nc_dir = '../result/start/nc'
start_img_dir = '../result/start/img'


def is_equal(a, b, epsilon=1e-4):
    return abs(a - b) < epsilon


def reverse(_data, _year):
    resolution = 25000
    fill_value = 9999
    inf = 1e18
    ends, lat, lon, u, v, x, y, crs_wkt, days = _data
    source_crs = CRS.from_wkt(crs_wkt)
    target_crs = CRS.from_epsg(4326)  # 目标坐标系是WGS84（经纬度）
    transformer = Transformer.from_crs(source_crs, target_crs)  # 创建转换器
    transformer2 = Transformer.from_crs(target_crs, source_crs)  # 创建转换器
    # print(ends)
    u = -u[::-1]
    v = -v[::-1]
    x -= resolution / 2
    y -= resolution / 2
    path_all = []
    for index, end in enumerate(ends):
        sx, sy = transformer2.transform(end[0], end[1])
        path_x, path_y = [sx], [sy]
        j, i = np.searchsorted(x, sx, side='left') - 1, np.searchsorted(y, sy, side='left') - 1
        for t in range(len(u)):
            print(f'{t}---------------------')
            total_time = 24 * 3600
            print(j, i, u[t][i][j], v[t][i][j])
            while total_time > 0:
                t1, t2 = inf, inf
                v1, v2 = u[t][i][j], v[t][i][j]
                if is_equal(v1, fill_value) or is_equal(v2, fill_value):
                    print(f"第{t}天, 剩余时间: {total_time}, 位置: {transformer.transform(sx, sy)}, 海冰速度无效, 保持不动")
                    break
                if is_equal(v1, 0) and is_equal(v1, 0):
                    print(f"第{t}天, 速度为 0, 保持不动!")
                    break
                v1 /= 100
                v2 /= 100
                # 速度 u
                if v1 > 0:
                    t1 = (x[j + 1] - sx) / v1
                elif v1 < 0:
                    t1 = (sx - x[j]) / -v1
                # 速度 v
                if v2 > 0:
                    t2 = (y[i + 1] - sy) / v2
                elif v2 < 0:
                    t2 = (sy - y[i]) / -v2

                if is_equal(t1, 0) and is_equal(t2, 0):
                    break
                if is_equal(t1, 0):
                    t1 = inf
                if is_equal(t2, 0):
                    t2 = inf
                cost_time = min(total_time, t1, t2)
                total_time -= cost_time
                sx += cost_time * v1
                sy += cost_time * v2
                if cost_time == t1:
                    if v1 > 0:
                        j += 1
                    elif v1 < 0:
                        j -= 1
                if cost_time == t2:
                    if v2 > 0:
                        i += 1
                    elif v2 < 0:
                        i -= 1

            path_x.append(sx)
            path_y.append(sy)
        path_lat, path_lon = transformer.transform(path_x, path_y)
        print(len(path_lat), len(path_lon))
        nc_path = start_nc_dir + '/' + _year + '/' + str(index + 1) + '.nc'
        write_data(path_lat, path_lon, [days], nc_path)
        path_all.append(nc_path)

    return path_all


if __name__ == '__main__':
    folder_path = Path(end_nc_dir)
    for item in folder_path.rglob('*.nc'):
        year = item.name[:4]
        # if year != '1982':
        #     continue
        data = merge_data(item)
        if not os.path.exists(start_nc_dir + '/' + year):
            os.mkdir(start_nc_dir + '/' + year)
        if not os.path.exists(start_img_dir):
            os.mkdir(start_img_dir)

        path = reverse(data, year)
        path_img = start_img_dir + '/' + year + '.png'
        plot_path(path, path_img)
