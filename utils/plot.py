import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import seaborn as sns
# from scipy.stats import gaussian_kde


# import matplotlib
# matplotlib.use('Agg')
plt.rc('font', family='Times New Roman')


def init_map():
    # 创建地图
    m = Basemap(llcrnrlon=-45.0, llcrnrlat=60.0, urcrnrlon=135.0, urcrnrlat=60.0,
                resolution='h', epsg=3408)
    m.drawparallels(np.arange(50., 81., 10.), labels=[False, False, False, False])  # 纬度
    m.drawmeridians(np.arange(0., 359., 45.), labels=[True, False, False, False])  # 经度
    m.drawmapboundary(fill_color='lightskyblue')  # 边界
    m.fillcontinents(color='lemonchiffon', lake_color='lightskyblue')  # 大陆内部填充颜色
    m.drawcoastlines(linewidth=0.3)  # 海岸线
    return m


def plot_coordinates(m, title, lon, lat, save_path='../result/end/img/test.png'):
    x, y = m(lon, lat)
    sc = plt.scatter(x, y, s=1, marker='.', color='red', zorder=2)
    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    sc.remove()
    print(f"Img saved to {save_path}")


def plot_shadow(m, title, lon, lat, save_path='../result/extent/test.png'):
    x, y = m(lon, lat)
    sc = plt.scatter(x, y, s=1, marker='.', c='grey', zorder=1, alpha=0.5)
    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    sc.remove()
    print(f"Img saved to {save_path}")


def plot_path(m, title, path_all, save_path='../result/start/img/test.png'):
    objs = []
    for path in path_all:
        dataset = Dataset(path)
        lat, lon = np.array(dataset.variables['lat'][:]), np.array(dataset.variables['lon'][:])
        x, y = m(lon, lat)
        objs.append(m.scatter(x[0], y[0], s=1, marker='.', color='red', zorder=2))
        objs.append(m.plot(x[0:-1], y[0:-1], '-', color='blue', linewidth=0.5, zorder=1)[0])
        objs.append(m.scatter(x[-1], y[-1], s=1, marker='.', c='green', zorder=2))

    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    for obj in objs:
        obj.remove()
    print(f"Img saved to {save_path}")


def plot_kde(m, title, lon, lat, save_path='../result/start/kde/test.png'):
    x, y = m(lon, lat)
    sns.kdeplot(x=x, y=y, cmap="Reds", fill=True, bw=.15, cbar=True)
    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    print(f"Img saved to {save_path}")
