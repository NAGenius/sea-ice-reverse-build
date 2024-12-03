import numpy as np
import pandas as pd

from utils.plot import init_map, plot_heatmap


def normalize(_data):
    _data = np.array(_data)
    min_val = np.min(_data)
    max_val = np.max(_data)
    return (_data - min_val) / (max_val - min_val)


if __name__ == '__main__':
    # 权重设置
    conc_weight = 0.4
    thickness_weight = 0.6
    alpha = 1.05
    years = list(range(1979, 2023))
    tmp = alpha ** np.arange(len(years))
    tmp = tmp / tmp.sum()
    year_weight = {str(year): weight for year, weight in zip(years, tmp)}
    print(year_weight)
    lats, lons, datas = [], [], []
    with pd.ExcelFile('../result/start/all.xlsx') as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            concentration = normalize(df['密集度(concentration/(percent))'].tolist())
            thickness = normalize(df['厚度(thickness/(m))'].tolist())
            score = year_weight[sheet_name] * (conc_weight * concentration + thickness_weight * thickness)
            lats.append(df['纬度(latitude/(°))'].tolist())
            lons.append(df['经度(longitude/(°))'].tolist())
            datas.append(score.tolist())
    lats = np.array([i for lat in lats for i in lat])
    lons = np.array([i for lon in lons for i in lon])
    datas = np.array([i for data in datas for i in data])
    m = init_map()
    plot_heatmap(m, 'Heatmap', lons, lats, datas)
