import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from cftime import num2date
from netCDF4 import Dataset
from tqdm import tqdm


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

    pos = 'N'

    month_mapping = {
        1: "01_Jan", 2: "02_Feb", 3: "03_Mar", 4: "04_Apr",
        5: "05_May", 6: "06_Jun", 7: "07_Jul", 8: "08_Aug",
        9: "09_Sep", 10: "10_Oct", 11: "11_Nov", 12: "12_Dec"
    }

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


def validate_motion_data(start=1979, end=2023):
    motion_dir = '../motion/data'
    for i in range(start, end):
        motion_file_name = f'icemotion_daily_nh_25km_{i}0101_{i}1231_v4.1.nc'
        nc_obj = Dataset(os.path.join(motion_dir, motion_file_name), 'r')
        u = np.array(nc_obj.variables['u'][:])
        nc_obj.close()
        cnt = 0
        for j in range(len(u)):
            if np.sum(u[j] == -9999) == 361 ** 2:
                cnt += 1
                print(j, end=' ')
        print(f'\n第{i}年, 数据缺失天数: {cnt}')


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


# if __name__ == '__main__':
    # get_extent_data()
    # get_motion_data()
    # validate_motion_data()

# 第1979年, 数据缺失天数: 0
# 210 211 212 213
# 第1980年, 数据缺失天数: 4
# 第1981年, 数据缺失天数: 0
# 193 194 195 196 209 210 211 212 213 214 215 216 217 218 219 220 225 226 227 228
# 第1982年, 数据缺失天数: 20
# 第1983年, 数据缺失天数: 0
# 223 224 225 226 227 228 229 230 231 232 233 234 235 236
# 第1984年, 数据缺失天数: 14
# 363 364
# 第1985年, 数据缺失天数: 2
# 340 341 342 343 348 349 350 351
# 第1986年, 数据缺失天数: 8
# 365
# 第2020年, 数据缺失天数: 1
# 364
# 第2021年, 数据缺失天数: 1
