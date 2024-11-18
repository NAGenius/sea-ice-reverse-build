from datetime import datetime, timedelta
import os

import numpy as np
from netCDF4 import Dataset, date2num


base_date = datetime(1970, 1, 1)
end_dir = '../result/end/nc'
start_dir = '../result/start/nc'
if not os.path.exists(end_dir):
    os.makedirs(end_dir)

if not os.path.exists(start_dir):
    os.makedirs(start_dir)


def write_data(latitudes, longitudes, days, save_path='../result/end/nc/test.nc'):
    latitudes = np.array(latitudes)
    longitudes = np.array(longitudes)
    # 创建一个新的 NetCDF 文件
    dataset = Dataset(save_path, 'w', format='NETCDF4')

    # 定义维度 (纬度、经度和时间)
    dataset.createDimension('lat', len(latitudes))  # 纬度的维度大小
    dataset.createDimension('lon', len(longitudes))  # 经度的维度大小
    dataset.createDimension('time', None)  # 时间维度可以是无限的
    # print(f'有{365 - len(np.unique(latitudes))}天保持不动')
    # 创建变量（纬度、经度和时间）
    time_var = dataset.createVariable('time', 'f8', ('time',))
    latitudes_var = dataset.createVariable('lat', 'f4', ('lat',))
    longitudes_var = dataset.createVariable('lon', 'f4', ('lon',))

    # 添加变量属性
    latitudes_var.units = 'degrees_north'
    longitudes_var.units = 'degrees_east'
    time_var.units = 'days since 1970-01-01'

    start_date = base_date
    time_data = np.array([date2num(start_date + timedelta(days=i), units=time_var.units) for i in days])
    # 将数据写入变量
    latitudes_var[:] = latitudes
    longitudes_var[:] = longitudes
    time_var[:] = time_data

    # 关闭文件
    dataset.close()
    print(f"NetCDF file saved to {save_path}")
