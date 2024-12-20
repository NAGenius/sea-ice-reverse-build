import os
from datetime import datetime
from pathlib import Path

import numpy as np

from utils import get_nearest_points
from utils.get_data import read_tif, coord2xy
from utils.write_data import write_data

base_date = datetime(1970, 1, 1)
extent_dir = '../extent/data'  # 数据所在目录
nc_dir = '../result/end/nc'

fram_strait = (80.0, -5.0)  # 弗拉姆海峡坐标: 北纬80度, 西经5度
fram_strait_lon_range = (-15.0, .0)  # 大致经度范围
fram_strait_lon_range2 = (.0, 15.0)  # 大致经度范围 30.0


def get_end(filename):
    data, geotransform, transformer = read_tif(filename)
    ice_indices = np.where(data == 1)  # 得到有海冰的坐标
    x_coords, y_coords = coord2xy(ice_indices, geotransform)
    lat, lon = transformer.transform(x_coords, y_coords)
    points = []
    # 1. 找到离弗拉姆海峡最近的点的纬度作为阈值, 得到这一纬度上的点
    lat_threshold = get_nearest_points(lat, lon, fram_strait, 1)[0][0][0]
    if lat_threshold < 78 or lat_threshold > 82:
        print("Can't find the right spot!!!")
        return

    for j in range(len(lat)):
        if abs(lat[j] - lat_threshold) < 0.15 and fram_strait_lon_range[0] <= lon[j] <= fram_strait_lon_range[1]:
            # 0.15
            points.append((lat[j], lon[j]))
    print(len(points))
    # 2. 找到靠近弗拉姆海峡的侧边海冰
    for row in range(data.shape[0]):
        cols = np.where(data[row] == 1)[0]
        if len(cols) > 0:
            x_coords, y_coords = coord2xy((row, cols[-1]), geotransform)
            lat, lon = transformer.transform(x_coords, y_coords)
            if lat_threshold < lat < 85 and fram_strait_lon_range2[0] <= lon <= fram_strait_lon_range2[1]:
                # flag = True
                # for p in points:
                #     if abs(lat - p[0]) < 0.1:  # 0.05
                #         flag = False
                #         break
                # if flag:
                #     points.append((lat, lon))
                points.append((lat, lon))
    print(len(points))
    return set(points)


if __name__ == '__main__':
    if not os.path.exists(nc_dir):
        os.mkdir(nc_dir)

    folder_path = Path(extent_dir)
    # 使用 rglob() 递归遍历文件夹中的所有文件
    for item in folder_path.rglob('*.tif'):
        # if item.name[2:6] != '1986':
        #     continue
        print(item.name[2:6] + '---------------------')
        end_coord = get_end(item)
        for point in end_coord:
            print(f"坐标: {point}")
        x = [point[0] for point in end_coord]  # 纬度
        y = [point[1] for point in end_coord]  # 经度
        time_data = [f'{item.name[2:6]}-{item.name[6:8]}-{item.name[8:10]}']
        days = []
        for i in time_data:
            days.append((datetime.strptime(i, '%Y-%m-%d') - base_date).days)
        nc_path = nc_dir + '/' + item.name[2:6] + '.nc'
        write_data(x, y, days, nc_path)
