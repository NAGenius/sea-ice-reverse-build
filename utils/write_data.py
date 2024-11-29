import os
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset

base_date = datetime(1970, 1, 1)
end_dir = '../result/end/nc'
start_dir = '../result/start/nc'
if not os.path.exists(end_dir):
    os.makedirs(end_dir)

if not os.path.exists(start_dir):
    os.makedirs(start_dir)


def write_data(lat, lon, days, save_path='../result/end/nc/test.nc'):
    lat = np.array(lat)
    lon = np.array(lon)
    days = np.array(days).astype(float)
    dataset = Dataset(save_path, 'w', format='NETCDF4')
    # 定义维度 (纬度、经度和时间)
    dataset.createDimension('lat', len(lat))  # 纬度的维度大小
    dataset.createDimension('lon', len(lon))  # 经度的维度大小

    latitudes_var = dataset.createVariable('lat', 'f4', ('lat',))
    longitudes_var = dataset.createVariable('lon', 'f4', ('lon',))
    latitudes_var[:] = lat
    longitudes_var[:] = lon

    # 添加变量属性
    latitudes_var.units = 'degrees_north'
    longitudes_var.units = 'degrees_east'
    if len(days):
        dataset.createDimension('time', None)  # 时间维度可以是无限的
        time_var = dataset.createVariable('time', 'f8', ('time',))
        dates = [base_date + timedelta(days=i) for i in days]
        time_var[:] = np.array([(date - base_date).days for date in dates])
        time_var.units = 'days since 1970-01-01'

    # 关闭文件
    dataset.close()
    # print(f"NetCDF file saved to {save_path}")
