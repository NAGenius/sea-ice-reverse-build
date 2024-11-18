import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset

# 创建地图
m = Basemap(llcrnrlon=-45.0, llcrnrlat=60.0, urcrnrlon=135.0, urcrnrlat=60.0,
            resolution='h', epsg=3408)
m.drawparallels(np.arange(50., 81., 10.), labels=[False, False, False, False])  # 纬度
m.drawmeridians(np.arange(0., 359., 45.), labels=[True, False, False, False])  # 经度
m.drawmapboundary(fill_color='lightskyblue')  # 边界
m.fillcontinents(color='lemonchiffon', lake_color='lightskyblue')  # 大陆内部填充颜色
m.drawcoastlines(linewidth=0.3)  # 海岸线


def plot_coordinates(x, y, save_path='../result/end/img/test.png'):
    x, y = m(x, y)
    print(len(x), len(y))
    scatter = m.scatter(x, y, s=1, marker='.', color='red', zorder=2)
    plt.savefig(save_path, dpi=1000)
    scatter.remove()
    print(f"Img saved to {save_path}")


def plot_shadow(x, y, save_path='../result/extent/test.png'):
    x, y = m(x, y)
    scatter = m.scatter(x, y, s=1, marker='.', c='grey', zorder=1, alpha=0.5)
    plt.savefig(save_path, dpi=1000)
    scatter.remove()
    print(f"Img saved to {save_path}")


def plot_path(path_all, save_path='../result/start/img/test.png'):
    objs = []
    for path in path_all:
        dataset = Dataset(path)
        lat, lon = np.array(dataset.variables['lat'][:]), np.array(dataset.variables['lon'][:])
        x, y = m(lon, lat)
        objs.append(m.scatter(x[0], y[0], s=1, marker='.', color='red', zorder=2))
        if len(x) < 366:
            objs.append(m.plot(x[0:-1], y[0:-1], '-', color='gray', linewidth=0.5)[0])
            objs.append(m.scatter(x[-1], y[-1], s=1, marker='x', color='red', zorder=2))
        else:
            objs.append(m.plot(x[0:-1], y[0:-1], '-', color='blue', linewidth=0.5)[0])
            objs.append(m.scatter(x[-1], y[-1], s=1, marker='.', c='red', zorder=2))

    plt.savefig(save_path, dpi=1000)
    for obj in objs:
        obj.remove()
    print(f"Img saved to {save_path}")
