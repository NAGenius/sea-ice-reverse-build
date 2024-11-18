import os
from datetime import datetime
from pathlib import Path
from osgeo import gdal
import numpy as np
from pyproj import CRS, Transformer
from geopy.distance import geodesic

from utils.plot import plot_shadow
# from utils.plot import plot_coordinates
# from utils.write_data import write_data


base_date = datetime(1970, 1, 1)
extent_dir = '../extent/data'  # 数据所在目录
img_dir = '../result/end/img'
nc_dir = '../result/end/nc'
gdal.UseExceptions()  # 启用异常处理

fram_strait = (80.0, -5.0)  # 弗拉姆海峡坐标: 北纬80度, 西经5度
fram_strait_lon_range = (-15.0, .0)  # 大致经度范围
fram_strait_lon_range2 = (.0, 15.0)  # 大致经度范围


def coord2latlon(coords, geotransform, transformer):
    x_coords = geotransform[0] + coords[1] * geotransform[1] + coords[0] * geotransform[2]
    y_coords = geotransform[3] + coords[0] * geotransform[5] + coords[1] * geotransform[4]
    return transformer.transform(x_coords, y_coords)


def get_nearest_points(lat, lon, cnt=10):
    coordinates = list(zip(lat, lon))
    dist = [(coord, geodesic(coord, fram_strait).kilometers) for coord in coordinates]
    dist.sort(key=lambda tup: tup[1])
    return dist[:cnt]


def get_end(filename):
    """
    得到每年最小海冰范围的 `cnt` 个坐标
    :param filename:
    :return:
    """
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    # width, height = dataset.RasterXSize, dataset.RasterYSize  # 宽高 304 448
    # bands = dataset.RasterCount  # 波段数 1

    band = dataset.GetRasterBand(1)  # 只有一个波段
    # print(dataset.transform)  # 没有该属性
    ice_extent = band.ReadAsArray()
    # print(np.unique(ice_extent))  # [  0   1 253 254]
    # print(ice_extent.shape)  # 448 304
    ice_indices = np.where(ice_extent == 1)  # 得到有海冰的坐标

    # 转换为当前的坐标体系下的坐标 起点+像元宽/高度+旋转
    geotransform = dataset.GetGeoTransform()  # 获取地理变换参数 (-3850000.0, 25000.0, 0.0, 5850000.0, 0.0, -25000.0)
    # 进行投影
    projection = dataset.GetProjection()  # 获取投影信息, AUTHORITY["EPSG","3411"]
    source_crs = CRS.from_wkt(projection)
    target_crs = CRS.from_epsg(4326)  # 目标坐标系是WGS84（经纬度）
    transformer = Transformer.from_crs(source_crs, target_crs)  # 创建转换器

    lat, lon = coord2latlon(ice_indices, geotransform, transformer)
    plot_shadow(lon, lat)
    # 求出距离弗拉姆海峡最近的 cnt 个坐标
    # points = get_nearest_points(lat, lon, cnt=cnt)

    points = []
    # 1. 找到离弗拉姆海峡最近的点的纬度作为阈值, 得到这一纬度上的点
    lat_threshold = get_nearest_points(lat, lon, 1)[0][0][0]
    if lat_threshold < 78 or lat_threshold > 82:
        print("Can't find the right spot!!!")
        return

    for i in range(len(lat)):
        if abs(lat[i] - lat_threshold) < 0.1 and fram_strait_lon_range[0] <= lon[i] <= fram_strait_lon_range[1]:
            points.append((lat[i], lon[i]))
    print(len(points))
    # 2. 找到靠近弗拉姆海峡的侧边海冰
    for row in range(ice_extent.shape[0]):
        cols = np.where(ice_extent[row] == 1)[0]
        if len(cols) > 0:
            lat, lon = coord2latlon((row, cols[-1]), geotransform, transformer)
            if lat_threshold < lat < 85 and fram_strait_lon_range2[0] <= lon <= fram_strait_lon_range2[1]:
                flag = True
                for p in points:
                    if abs(lat - p[0]) < 0.1:
                        flag = False
                        break
                if flag:
                    points.append((lat, lon))

    print(len(points))
    return set(points)


if __name__ == '__main__':
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)
    if not os.path.exists(nc_dir):
        os.mkdir(nc_dir)

    folder_path = Path(extent_dir)
    # 使用 rglob() 递归遍历文件夹中的所有文件
    for item in folder_path.rglob('*.tif'):
        print(item.name[2:6] + '---------------------')
        if item.name[2:6] != '2021':
            continue
        end_coord = get_end(item)
        for point in end_coord:
            print(f"坐标: {point}")

        x = [point[0] for point in end_coord]  # 纬度
        y = [point[1] for point in end_coord]  # 经度
        time_data = [f'{item.name[2:6]}-{item.name[6:8]}-{item.name[8:10]}']
        days = []
        for i in time_data:
            days.append((datetime.strptime(i, '%Y-%m-%d') - base_date).days)
        img_path = img_dir + '/' + item.name[2:6] + '.png'
        nc_path = nc_dir + '/' + item.name[2:6] + '.nc'
        # plot_coordinates(y, x, img_path)
        # write_data(x, y, days, nc_path)
