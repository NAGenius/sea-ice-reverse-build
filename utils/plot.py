import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
from matplotlib.patches import Patch
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import seaborn as sns
# from scipy.stats import gaussian_kde


# import matplotlib
# matplotlib.use('Agg')
rcParams['font.family'] = 'Times New Roman, SimHei'
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
land_patch = Patch(color='lemonchiffon', label='陆地')
ocean_patch = Patch(color='lightskyblue', label='海洋')


def init_map():
    # 创建地图
    # m = Basemap(llcrnrlon=-45.0, llcrnrlat=75.0, urcrnrlon=135.0, urcrnrlat=75.0,
    #             resolution='h', epsg=3408)
    # m.drawparallels(np.arange(80., 91., 10.), labels=[False, False, False, False])  # 纬度
    # m.drawmeridians(np.arange(0., 359., 45.), labels=[True, False, False, False])  # 经度
    # m.drawmapboundary(fill_color='lightskyblue')  # 边界
    # m.fillcontinents(color='lemonchiffon', lake_color='lightskyblue')  # 大陆内部填充颜色
    # m.drawcoastlines(linewidth=0.3)  # 海岸线
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
    sc = plt.scatter(x, y, s=1, marker='.', color='red', zorder=2, label='终点')
    plt.title(title)
    plt.legend(handles=[land_patch, ocean_patch, sc], loc='upper right', fontsize=8, framealpha=1.0,
               handleheight=0.8, handlelength=1.2, borderpad=0.5, handletextpad=1.5)
    plt.savefig(save_path, dpi=1000)
    sc.remove()
    print(f"Img saved to {save_path}")


def plot_shadow(m, title, lon, lat, save_path='../result/extent/test.png'):
    x, y = m(lon, lat)
    sc = plt.scatter(x, y, s=1, marker='.', c='grey', zorder=1, alpha=0.5, label='海冰范围')
    plt.legend(handles=[land_patch, ocean_patch, sc], loc='upper right', fontsize=8, framealpha=1.0,
               handleheight=0.8, handlelength=1.2, borderpad=0.5, handletextpad=1.5)
    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    sc.remove()
    print(f"Img saved to {save_path}")


def plot_path(m, title, path_all, save_path='../result/start/img/test.png'):
    objs = []
    sc, sc2, line = None, None, None
    for path in path_all:
        dataset = Dataset(path)
        lat, lon = np.array(dataset.variables['lat'][:]), np.array(dataset.variables['lon'][:])
        x, y = m(lon, lat)
        sc = m.scatter(x[0], y[0], s=1, marker='.', color='red', zorder=2, label='终点')
        sc2 = m.scatter(x[-1], y[-1], s=1, marker='.', c='green', zorder=2, label='起点')
        line = m.plot(x[0:-1], y[0:-1], '-', color='blue', linewidth=0.5, zorder=1, label='路径')[0]
        objs.append(sc)
        objs.append(sc2)
        objs.append(line)

    plt.title(title)
    plt.legend(handles=[land_patch, ocean_patch, sc, sc2, line], loc='upper right', fontsize=8, framealpha=1.0,
               handleheight=0.8, handlelength=1.2, borderpad=0.5, handletextpad=1.5)
    plt.savefig(save_path, dpi=1000)
    for obj in objs:
        obj.remove()
    print(f"Img saved to {save_path}")


def plot_kde(m, title, lon, lat, save_path='../result/start/kde/test.png'):
    x, y = m(lon, lat)
    sns.kdeplot(x=x, y=y, cmap="Reds", fill=True, bw_method=0.15, cbar=True)
    plt.legend(handles=[land_patch, ocean_patch], loc='upper right', fontsize=8, framealpha=1.0,
               handleheight=0.8, handlelength=1.2, borderpad=0.5, handletextpad=1.5)
    plt.title(title)
    plt.savefig(save_path, dpi=1000)
    print(f"Img saved to {save_path}")


def plot_heatmap(m, title, lon, lat, data, save_path='../result/start/heatmap.png'):
    x, y = m(lon, lat)
    scatter = m.scatter(x, y, c=data, s=10, marker='.', cmap='hot_r')
    plt.colorbar(scatter)
    # hb = m.hexbin(x, y, C=data, gridsize=50, cmap='hot_r', mincnt=1)
    # m.colorbar(hb)
    plt.title(title)
    plt.legend(handles=[land_patch, ocean_patch], loc='upper right', fontsize=8, framealpha=1.0,
               handleheight=0.8, handlelength=1.2, borderpad=0.5, handletextpad=1.5)
    plt.savefig(save_path, dpi=1000)
    print(f"Img saved to {save_path}")
