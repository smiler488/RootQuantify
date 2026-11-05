# RootQuantify

[English](README.md) | 中文

[![CI](https://github.com/smiler488/RootQuantify/actions/workflows/test.yml/badge.svg)](https://github.com/smiler488/RootQuantify/actions/workflows/test.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) ![Python 3.9+](https://img.shields.io/badge/Python_3.9%2B-informational)
一个基于 OpenCV 的小工具，处理洗根后的根系扫描图。每张图的流程是：手动圈出根系范围 → 自动分割 → 用画笔修正掩膜 → 保存干净的二值图，并测量总根长、投影面积、平均直径和根尖数。

全自动阈值很容易把土粒、托盘边缘和标签连同根系一起识别进来。先圈定范围、最后再手动修一下掩膜，就能把这些杂物挡在测量结果之外。

## 安装

```bash
git clone https://github.com/smiler488/RootQuantify.git
cd RootQuantify
pip install -r requirements.txt
```

需要 Python 3.9 及以上，Windows、macOS、Linux 都可以用。

## 使用

```bash
python RootImager.py path/to/scans --dpi 600
```

不指定文件夹时会弹出文件夹选择框。之后出现两个窗口：左边是原图，右边是操作窗口。

**1. 圈选**：在右边窗口里依次点击，围出包住根系的多边形。
`c` 确认，`r` 重画，`s` 跳过这张图，`Esc` 结束整批处理。

**2. 自动分割**：先用灰度闭运算估计背景，再从原图中减去背景，把差值拉伸到 0–255 后做阈值分割，得到白底黑根的二值图。

**3. 手动修正**：`d` 画根，`e` 擦除，`+`/`-` 调画笔大小（绿色圆圈表示当前大小），`u` 撤销上一笔，`q` 完成。

**4. 保存与测量**：掩膜保存为 `output/processed-<文件名>`，性状追加一行到 `output/root_traits.csv`，原图移到 `processed_original/`，这样中途停下以后可以接着处理。如果不想移动原图，加 `--keep-originals`。

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--dpi` | 无 | 扫描分辨率；给定后性状以 mm / mm² 为单位输出，否则为像素 |
| `--kernel` | 50 | 背景估计的核大小（像素），要比最粗的根更宽 |
| `--threshold` | 30 | 归一化差值图上的阈值（0–255）；调低能保留更多细侧根，但噪声也更多 |
| `-o` | `<文件夹>/output` | 输出目录 |
| `--keep-originals` | 关 | 处理完不移动原图 |

## 性状

| 列名 | 计算方法 |
|---|---|
| `length` | 对掩膜提取骨架，按 Kimura et al. (1999) 公式计算：√(Nd² + (Nd + No/2)²) + No/2，其中 No、Nd 分别是直连和斜连的相邻像素对数 |
| `area` | 根像素数 |
| `mean_diameter` | 面积 / 根长 |
| `tips` | 骨架端点数 |
| `objects` | 连通的根段数（小于 20 像素的视为杂点去掉） |

在合成测试图上，直根、斜根和弯曲根的长度误差都在 2–4%。面积/根长得到的是整个根系的平均直径，细侧根多时会偏小。根系交叉的地方只会算一次，这是所有二维方法的共同局限，所以扫描前尽量把根在托盘里铺开。

## 本次修订

- 原 README 说会弹出文件夹选择框，代码里却写死了我笔记本上的路径。现在既有选择框，也支持命令行参数。
- 新增根系性状测量。之前的版本只输出二值图。
- 输出目录改到图片所在的文件夹，而不是当前工作目录。
- 屏幕尺寸改用 Tk 获取，不再依赖只有 Windows 才有的系统调用。
- 新增 `s` 跳过当前图、`Esc` 退出。
- requirements 不再锁定 2022 年的旧版本，那些版本没有 Python 3.12 的安装包。

## 引用

```bibtex
@software{deng_rootquantify,
  author = {Deng, Liangchao},
  title  = {RootQuantify: semi-automatic segmentation and measurement of root scans},
  year   = {2025},
  url    = {https://github.com/smiler488/RootQuantify}
}
```

Kimura, K., Kikuchi, S. & Yamasaki, S. (1999). Accurate root length measurement by image analysis. *Plant and Soil*, 216, 117–127.

## 许可证

MIT，见 [LICENSE](LICENSE)。邓良超（Liangchao Deng）。
