import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from cftime import num2date
from netCDF4 import Dataset
from osgeo import gdal
from pyproj import CRS, Transformer
from tqdm import tqdm

gdal.UseExceptions()  # 启用异常处理
pos = 'N'
month_mapping = {
    1: "01_Jan", 2: "02_Feb", 3: "03_Mar", 4: "04_Apr",
    5: "05_May", 6: "06_Jun", 7: "07_Jul", 8: "08_Aug",
    9: "09_Sep", 10: "10_Oct", 11: "11_Nov", 12: "12_Dec"
}


def download_file(url, filename):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/129.0.0.0 Safari/537.36',
               'Cookie': '_hjSessionUser_3253376=eyJpZCI6IjgzMWQ0ODc2LTcyOWMtNWQxMS1hZGU1LWMzOGFiNDdmNDZmOCIsIm'
                         'NyZWF0ZWQiOjE3MjgzNTU3MDAxMzIsImV4aXN0aW5nIjp0cnVlfQ==; '
                         'nsidc=50cf247c-0f36-4d42-a290-df67e24b6718; _gid=GA1.2.21322404.1728894951;'
                         ' _ga=GA1.2.695005719.1728355700; _ga_7LML12VZ6P=GS1.1.1728894951.7.1.1728894968.0.0.0'}
    response = requests.get(url, headers=headers, stream=True)
    chunk_size = 1024  # 每次读取 1024 字节

    # 如果没有 content-length，我们就不知道总大小，因此无法设置 total 参数
    total_size = response.headers.get('content-length')
    # 打开文件用于写入
    with open(filename, 'wb') as file:
        # 如果 total_size 存在，使用它，否则只显示手动进度
        if total_size is None:
            # 没有 content-length，手动进度条
            with tqdm(unit='B', unit_scale=True, desc=filename) as progress_bar:
                for chunk in response.iter_content(chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))
        else:
            # 有 content-length，显示完整进度条
            total_size = int(total_size)
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as progress_bar:
                for chunk in response.iter_content(chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))


def get_extent_data(start=1979, end=2022):
    file_path = '../extent/daily/N_seaice_extent_daily_v3.0.csv'
    data = pd.read_csv(file_path)

    # 去掉首行描述行
    data = data.iloc[1:]

    # 去掉列名多余的空白字符
    data.columns = data.columns.str.strip()

    # 转换数据类型
    data['Year'] = data['Year'].astype(int)
    data['Month'] = data['Month'].astype(int)
    data['Day'] = data['Day'].astype(int)
    data['Extent'] = data['Extent'].astype(float)

    # 找到每一年海冰范围最小的那一天
    min_extent_per_year = data.loc[data.groupby('Year')['Extent'].idxmin()]

    # 打印每一年最小海冰范围的日期和当前月份, 并下载相应数据
    base_url = 'https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/geotiff'

    save_dir = '../extent/data'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for _, row in min_extent_per_year.iterrows():
        year = row['Year']
        if year < start or year > end:
            continue
        month = row['Month']
        day = row['Day']
        day = f'{pos}_{year}{month:02d}{day:02d}'
        url = f'{base_url}/{year}/{month_mapping[month]}/{day}_extent_v3.0.tif'
        file_path = os.path.join(save_dir, os.path.basename(url))
        if not os.path.exists(file_path):
            download_file(url, file_path)

    print('Success!!!')


def get_motion_data(start=1979, end=2023):
    base_url = 'https://daacdata.apps.nsidc.org/pub/DATASETS/nsidc0116_icemotion_vectors_v4/north/daily'
    save_dir = '../motion/data'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    for i in range(start, end):
        url = f'{base_url}/icemotion_daily_nh_25km_{i}0101_{i}1231_v4.1.nc'
        print(url)
        file_path = os.path.join(save_dir, os.path.basename(url))
        if not os.path.exists(file_path):
            download_file(url, file_path)

    print('Success!!!')


def get_concentration_data(date_range, start=1980, end=2022):
    # 打印每一年最小海冰范围的日期和当前月份, 并下载相应数据
    base_url = 'https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/geotiff'
    save_dir = '../concentration/data'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # date_range = json.loads(date_range)
    for year in range(start, end + 1):
        if date_range:
            _, month, day = date_range[str(year)].split(' ')[0].split('-')
            year -= 1
            day = f'{pos}_{year}{month}{day}'
            url = f'{base_url}/{year}/{month_mapping[int(month)]}/{day}_concentration_v3.0.tif'
            file_path = os.path.join(save_dir, os.path.basename(url))
            if not os.path.exists(file_path):
                download_file(url, file_path)

    print('Success!!!')


def get_thickness_data(start=2015, end=2022):
    pass


def coord2xy(coords, geotransform):
    x_coords = geotransform[0] + coords[1] * geotransform[1] + coords[0] * geotransform[2]
    y_coords = geotransform[3] + coords[1] * geotransform[4] + coords[0] * geotransform[5]
    return x_coords, y_coords


def read_tif(filename):
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    # 转换为当前的坐标体系下的坐标 起点+像元宽/高度+旋转
    geotransform = dataset.GetGeoTransform()
    # 进行投影
    projection = dataset.GetProjection()
    source_crs = CRS.from_wkt(projection)
    target_crs = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(source_crs, target_crs)

    return data, geotransform, transformer


def validate_motion_data(start=1979, end=2023):
    motion_dir = '../motion/data'
    dic = {}
    for i in range(start, end):
        motion_file_name = f'icemotion_daily_nh_25km_{i}0101_{i}1231_v4.1.nc'
        nc_obj = Dataset(os.path.join(motion_dir, motion_file_name), 'r')
        u = np.array(nc_obj.variables['u'][:])
        nc_obj.close()
        missing = []
        for j in range(len(u)):
            if np.sum(u[j] == -9999) == 361 ** 2:
                missing.append(j)
        dic[str(i)] = {'缺失天数': len(missing), '缺失': missing}
    return json.dumps(dic, ensure_ascii=False)


def merge_data(file_path, days=365):
    motion_dir = '../motion/data'
    nc_obj = Dataset(file_path, 'r')
    time_var = nc_obj.variables['time'][:]
    lat = nc_obj.variables['lat'][:]
    lon = nc_obj.variables['lon'][:]
    ends = list(zip(lat, lon))
    dates = num2date(time_var, units=nc_obj.variables['time'].units)
    nc_obj.close()

    date_str = dates[0].strftime('%Y-%m-%d')
    end_date = datetime.strptime(date_str, '%Y-%m-%d')
    start_date = end_date - timedelta(days=days)

    start_year = start_date.year
    end_year = end_date.year
    start_day_of_year = start_date.timetuple().tm_yday
    end_day_of_year = end_date.timetuple().tm_yday
    # 先获取当年的数据
    motion_file_name = f'icemotion_daily_nh_25km_{end_year}0101_{end_year}1231_v4.1.nc'
    nc_obj = Dataset(os.path.join(motion_dir, motion_file_name), 'r')
    crs_wkt = nc_obj.variables['crs'].crs_wkt
    lat = np.array(nc_obj.variables['latitude'][:end_day_of_year])
    lon = np.array(nc_obj.variables['longitude'][:end_day_of_year])
    u = np.array(nc_obj.variables['u'][:end_day_of_year])
    v = np.array(nc_obj.variables['v'][:end_day_of_year])
    x = np.array(nc_obj.variables['x'][:])
    y = np.array(nc_obj.variables['y'][:])
    nc_obj.close()

    if start_year != end_year and end_year != 1979:
        # 再获取前一年的数据
        motion_file_name = f'icemotion_daily_nh_25km_{start_year}0101_{start_year}1231_v4.1.nc'
        nc_obj = Dataset(os.path.join(motion_dir, motion_file_name), 'r')
        lat2 = np.array(nc_obj.variables['latitude'][start_day_of_year:])
        lon2 = np.array(nc_obj.variables['longitude'][start_day_of_year:])
        u2 = np.array(nc_obj.variables['u'][start_day_of_year:])
        v2 = np.array(nc_obj.variables['v'][start_day_of_year:])
        nc_obj.close()
        lat = np.concatenate([lat2, lat])
        lon = np.concatenate([lon2, lon])
        u = np.concatenate([u2, u])
        v = np.concatenate([v2, v])
    return ends, lat, lon, u, v, x, y, crs_wkt, int(time_var[0])


def get_time_info(days=365):
    nc_dir = '../result/end/nc'
    dic = {}
    for item in Path(nc_dir).rglob('*.nc'):
        if 1980 <= int(item.name[:4]) <= 2022:
            nc_obj = Dataset(item, 'r')
            time_var = nc_obj.variables['time'][:]
            dates = num2date(time_var, units=nc_obj.variables['time'].units)
            nc_obj.close()
            end_date = datetime.strptime(dates[0].strftime('%Y-%m-%d'), '%Y-%m-%d')
            start_date = end_date - timedelta(days=days)
            dic[item.name[:4]] = start_date.strftime('%Y-%m-%d') + ' ' + end_date.strftime('%Y-%m-%d')

    return json.dumps(dic, indent=4)


if __name__ == '__main__':
    # get_extent_data()
    # get_motion_data()
    ice_extent = read_tif('../concentration/data/N_20040920_concentration_v3.0.tif')[0]
    print(np.unique(ice_extent))
    # print(validate_motion_data())
    time = {
        "1980": "1979-09-05 1980-09-05",
        "1981": "1980-09-09 1981-09-10",
        "1982": "1981-09-12 1982-09-13",
        "1983": "1982-09-07 1983-09-08",
        "1984": "1983-09-16 1984-09-16",
        "1985": "1984-09-08 1985-09-09",
        "1986": "1985-09-05 1986-09-06",
        "1987": "1986-09-02 1987-09-02",
        "1988": "1987-09-12 1988-09-11",
        "1989": "1988-09-22 1989-09-22",
        "1990": "1989-09-21 1990-09-21",
        "1991": "1990-09-16 1991-09-16",
        "1992": "1991-09-08 1992-09-07",
        "1993": "1992-09-13 1993-09-13",
        "1994": "1993-09-05 1994-09-05",
        "1995": "1994-09-04 1995-09-04",
        "1996": "1995-09-11 1996-09-10",
        "1997": "1996-09-03 1997-09-03",
        "1998": "1997-09-17 1998-09-17",
        "1999": "1998-09-12 1999-09-12",
        "2000": "1999-09-12 2000-09-11",
        "2001": "2000-09-19 2001-09-19",
        "2002": "2001-09-18 2002-09-18",
        "2003": "2002-09-17 2003-09-17",
        "2004": "2003-09-19 2004-09-18",
        "2005": "2004-09-20 2005-09-20",
        "2006": "2005-09-14 2006-09-14",
        "2007": "2006-09-14 2007-09-14",
        "2008": "2007-09-19 2008-09-18",
        "2009": "2008-09-12 2009-09-12",
        "2010": "2009-09-19 2010-09-19",
        "2011": "2010-09-08 2011-09-08",
        "2012": "2011-09-17 2012-09-16",
        "2013": "2012-09-13 2013-09-13",
        "2014": "2013-09-16 2014-09-16",
        "2015": "2014-09-08 2015-09-08",
        "2016": "2015-09-08 2016-09-07",
        "2017": "2016-09-13 2017-09-13",
        "2018": "2017-09-21 2018-09-21",
        "2019": "2018-09-18 2019-09-18",
        "2020": "2019-09-14 2020-09-13",
        "2021": "2020-09-14 2021-09-14",
        "2022": "2021-09-15 2022-09-15",
    }
    get_concentration_data(time)
    # print(get_time_info())
