import math
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import PIL
import scipy.special

from funfluid.utils.log import logger


class Shape:
    def __init__(
        self,
        name,
        position,
        control_pts,
        n_control_pts,
        n_sampling_pts,
        radius,
        edgy,
        output_dir="output",
    ):
        self.name = name
        self.position = position
        self.control_pts = control_pts
        self.n_control_pts = n_control_pts
        self.n_sampling_pts = n_sampling_pts
        self.curve_pts = np.array([])
        self.area = 0.0
        self.size_x = 0.0
        self.size_y = 0.0
        self.radius = radius
        self.edgy = edgy
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def reset(self):
        # 重置对象
        self.name = "shape"
        self.control_pts = np.array([])
        self.n_control_pts = 0
        self.n_sampling_pts = 0
        self.radius = np.array([])
        self.edgy = np.array([])
        self.curve_pts = np.array([])
        self.area = 0.0

    def build(self):
        # 将控制点集合中心化
        center = np.mean(self.control_pts, axis=0)
        self.control_pts -= center

        # 按逆时针方向排序控制点
        control_pts, radius, edgy = ccw_sort(self.control_pts, self.radius, self.edgy)

        local_curves = []
        delta = np.zeros([self.n_control_pts, 2])
        radii = np.zeros([self.n_control_pts, 2])
        delta_b = np.zeros([self.n_control_pts, 2])

        # 计算生成曲线所需的全部中间量
        for i in range(self.n_control_pts):
            # 取出前一个/当前/后一个控制点
            prv = i - 1
            crt = i
            nxt = (i + 1) % self.n_control_pts
            pt_m = control_pts[prv, :]
            pt_c = control_pts[crt, :]
            pt_p = control_pts[nxt, :]

            # 计算切线方向向量
            diff = pt_p - pt_m
            diff = diff / np.linalg.norm(diff)
            delta[crt, :] = diff

            # 计算“锐度”偏移向量
            delta_b[crt, :] = 0.5 * (pt_m + pt_p) - pt_c

            # 计算控制半径
            dist = compute_distance(pt_m, pt_c)
            radii[crt, 0] = 0.5 * dist * radius[crt]
            dist = compute_distance(pt_c, pt_p)
            radii[crt, 1] = 0.5 * dist * radius[crt]

        # 逐段生成曲线
        for i in range(self.n_control_pts):
            crt = i
            nxt = (i + 1) % self.n_control_pts
            pt_c = control_pts[crt, :]
            pt_p = control_pts[nxt, :]
            dist = compute_distance(pt_c, pt_p)
            smpl = math.ceil(self.n_sampling_pts * math.sqrt(dist))

            local_curve = generate_bezier_curve(
                pt_c,
                pt_p,
                delta[crt, :],
                delta[nxt, :],
                delta_b[crt, :],
                delta_b[nxt, :],
                radii[crt, 1],
                radii[nxt, 0],
                edgy[crt],
                edgy[nxt],
                smpl,
            )
            local_curves.append(local_curve)

        curve = np.concatenate([c for c in local_curves])
        x, y = curve.T
        z = np.zeros(x.size)
        self.curve_pts = np.column_stack((x, y, z))
        self.curve_pts = remove_duplicate_pts(self.curve_pts)

        # 将曲线点集合中心化
        center = np.mean(self.curve_pts, axis=0)
        self.curve_pts -= center
        self.control_pts[:, 0:2] -= center[0:2]

        # 平移回目标位置
        self.control_pts[:, 0:2] += self.position[0:2]
        self.curve_pts[:, 0:2] += self.position[0:2]

    def generate_image(self, *args, **kwargs):
        """
        绘制并保存形状预览图。
        支持的可选参数：xmin/xmax/ymin/ymax（绘图坐标范围）。
        """
        xmin = kwargs.get("xmin", -1.0)
        xmax = kwargs.get("xmax", 1.0)
        ymin = kwargs.get("ymin", -1.0)
        ymax = kwargs.get("ymax", 1.0)

        # 绘制形状
        plt.xlim([xmin, xmax])
        plt.ylim([ymin, ymax])
        plt.axis("off")
        plt.gca().set_aspect("equal", adjustable="box")
        plt.fill(
            [xmin, xmax, xmax, xmin],
            [ymin, ymin, ymax, ymax],
            color=(0.784, 0.773, 0.741),
            linewidth=2.5,
            zorder=0,
        )
        plt.fill(self.curve_pts[:, 0], self.curve_pts[:, 1], "black", linewidth=0, zorder=1)

        # 绘制控制点，每个点使用不同颜色
        colors = matplotlib.cm.ocean(np.linspace(0, 1, self.n_control_pts))
        plt.scatter(
            self.control_pts[:, 0],
            self.control_pts[:, 1],
            color=colors,
            s=16,
            zorder=2,
            alpha=0.5,
        )

        # 保存图像
        filename = self.output_dir + self.name + ".png"

        plt.savefig(filename, dpi=200)
        plt.close(plt.gcf())
        plt.cla()
        trim_white(filename)

    def write_csv(self):
        """
        保存为csv文件
        """
        filename = self.output_dir + self.name + ".csv"
        with open(filename, "w") as file:
            # 写入文件头（控制点数量、采样点数量）
            file.write(f"{self.n_control_pts} {self.n_sampling_pts}\n")

            # 写入各控制点坐标、半径与锐度
            for i in range(0, self.n_control_pts):
                file.write(
                    f"{self.control_pts[i, 0]} {self.control_pts[i, 1]} "
                    f"{self.radius[i]} {self.edgy[i]}\n"
                )

    def read_csv(self, filename, *args, **kwargs):
        """
        读取csv文件 并且初始化颗粒形状
        支持的可选参数：keep_numbering（是否保留文件名中的编号后缀）。
        """
        keep_numbering = kwargs.get("keep_numbering", False)

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"找不到形状控制点 csv 文件: {filename}")

        self.reset()
        sfile = filename.split(".")
        sfile = sfile[-2]
        sfile = sfile.split("/")
        name = sfile[-1]

        if keep_numbering:
            sname = name.split("_")
            name = sname[0]

        x = []
        y = []
        radius = []
        edgy = []

        with open(filename) as file:
            header = file.readline().split()
            n_control_pts = int(header[0])
            n_sampling_pts = int(header[1])

            for _ in range(n_control_pts):
                coords = file.readline().split()
                x.append(float(coords[0]))
                y.append(float(coords[1]))
                radius.append(float(coords[2]))
                edgy.append(float(coords[3]))
                control_pts = np.column_stack((x, y))

        self.__init__(name, control_pts, n_control_pts, n_sampling_pts, radius, edgy)

    def modify_shape_from_field(self, deformation, pts_list):
        # 根据形变场修改形状：逐点更新坐标与锐度
        for i in range(len(pts_list)):
            self.control_pts[pts_list[i], 0] = deformation[i, 0]
            self.control_pts[pts_list[i], 1] = deformation[i, 1]
            self.edgy[pts_list[i]] = deformation[i, 2]


def compute_distance(p1: np.ndarray, p2: np.ndarray) -> float:
    """
    计算两个点之间的距离
    """
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def remove_duplicate_pts(pts: np.ndarray) -> np.ndarray:
    """删除输入坐标数组中的重复点。

    注意：此例程按 O(n^2) 两两比较实现，仅适用于控制点数量较小的场景，
    不建议用于大规模点集。

    Args:
        pts: 待去重的坐标数组，形状为 ``(n, d)``。

    Returns:
        去重后的坐标数组。
    """
    to_remove = []

    for i in range(len(pts)):
        for j in range(len(pts)):
            # 跳过相同下标
            if i == j:
                continue

            # 跳过已经标记为删除的点
            if (i in to_remove) or (j in to_remove):
                continue

            # 计算两点间距离
            pi = pts[i, :]
            pj = pts[j, :]
            dist = compute_distance(pi, pj)

            # 距离过近则标记其中一个点待删除
            if dist < 1.0e-8:
                to_remove.append(j)

    # 按逆序排序待删除下标，避免删除时下标错位
    to_remove.sort(reverse=True)

    # 从点集中移除标记的点
    for pt in to_remove:
        pts = np.delete(pts, pt, 0)

    return pts


def ccw_sort(
    pts: np.ndarray, rad: np.ndarray, edg: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """按逆时针（counter clock-wise）方向对控制点排序。

    做法：取点集几何中心 -> 平移使几何中心位于原点 -> 计算各点相对原点的
    角度 -> 按角度升序排序。

    Args:
        pts: 控制点坐标，形状为 ``(n, 2)``。
        rad: 与 `pts` 一一对应的半径参数。
        edg: 与 `pts` 一一对应的锐度参数。

    Returns:
        按逆时针排序后的 `(pts, rad, edg)` 三元组。
    """
    geometric_center = np.mean(pts, axis=0)
    translated_pts = pts - geometric_center
    angles = np.arctan2(translated_pts[:, 1], translated_pts[:, 0])
    x = angles.argsort()
    pts2 = np.array(pts)
    rad2 = np.array(rad)
    edg2 = np.array(edg)

    return pts2[x, :], rad2[x], edg2[x]


def compute_bernstein(n: int, k: int, t: np.ndarray) -> np.ndarray:
    """
    计算 Bernstein 多项式值
    """
    k_choose_n = scipy.special.binom(n, k)

    return k_choose_n * (t**k) * ((1.0 - t) ** (n - k))


def sample_bezier_curve(control_pts: np.ndarray, n_sampling_pts: int) -> np.ndarray:
    """按给定控制点采样贝塞尔（Bezier）曲线。

    贝塞尔曲线以 ``t ∈ [0, 1]`` 参数化，由 n 个控制点 ``P_i`` 定义：
    ``B(t) = sum_{i=0,n} B_i^n(t) * P_i``。

    Args:
        control_pts: 控制点坐标，形状为 ``(n_control_pts, 2)``。
        n_sampling_pts: 采样点数量。

    Returns:
        采样得到的曲线点坐标，形状为 ``(n_sampling_pts, 2)``。
    """
    n_control_pts = len(control_pts)
    t = np.linspace(0, 1, n_sampling_pts)
    curve = np.zeros((n_sampling_pts, 2))

    for i in range(n_control_pts):
        curve += np.outer(compute_bernstein(n_control_pts - 1, i, t), control_pts[i])

    return curve


def trim_white(filename: str) -> None:
    """裁剪图像中的白色背景并原地保存。

    Args:
        filename: 待裁剪图像的文件路径。
    """
    im = PIL.Image.open(filename)
    bg = PIL.Image.new(im.mode, im.size, (255, 255, 255))
    diff = PIL.ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    cp = im.crop(bbox)
    cp.save(filename)


def generate_cylinder_pts(n_pts):
    """生成圆柱体点"""
    if n_pts < 4:
        raise ValueError(f"生成圆柱体控制点至少需要 4 个点，实际传入 n_pts={n_pts}")

    pts = np.zeros([n_pts, 2])
    ang = 2.0 * math.pi / n_pts
    for i in range(0, n_pts):
        pts[i, :] = [0.5 * math.cos(float(i) * ang), 0.5 * math.sin(float(i) * ang)]

    return pts


def generate_square_pts(n_pts):
    """生成正方形点"""
    if n_pts != 4:
        raise ValueError(f"生成正方形控制点要求 n_pts=4，实际传入 n_pts={n_pts}")

    pts = np.zeros([n_pts, 2])
    pts[0, :] = [1.0, 1.0]
    pts[1, :] = [-1.0, 1.0]
    pts[2, :] = [-1.0, -1.0]
    pts[3, :] = [1.0, -1.0]

    pts[:, :] *= 0.5

    return pts


def generate_bezier_curve(
    p1,
    p2,
    delta1,
    delta2,
    delta_b1,
    delta_b2,
    radius1,
    radius2,
    edgy1,
    edgy2,
    n_sampling_pts,
):
    """生成两点之间的三次贝塞尔（Bezier）曲线。

    Args:
        p1: 曲线起点坐标。
        p2: 曲线终点坐标。
        delta1: 起点处的切线方向向量。
        delta2: 终点处的切线方向向量。
        delta_b1: 起点处的“锐度”偏移向量。
        delta_b2: 终点处的“锐度”偏移向量。
        radius1: 起点处的控制半径。
        radius2: 终点处的控制半径。
        edgy1: 起点处的锐度系数（0 表示圆滑，1 表示尖锐）。
        edgy2: 终点处的锐度系数。
        n_sampling_pts: 采样点数量；为 0 时直接返回两点间的直线。

    Returns:
        曲线点坐标数组。
    """

    # n_sampling_pts 非 0 时按贝塞尔曲线采样
    if n_sampling_pts != 0:
        # 构造三次贝塞尔曲线的 4 个控制点：
        # 首尾两点已给定，中间两个控制点由边界点、切线方向、
        # 偏移向量、控制半径与锐度系数插值计算得到
        control_pts = np.zeros((4, 2))
        control_pts[0, :] = p1[:]
        control_pts[3, :] = p2[:]

        # 计算中间控制点 ctrl_p1、ctrl_p2 的基准值
        ctrl_p1_base = radius1 * delta1
        ctrl_p2_base = -radius2 * delta2

        ctrl_p1_edgy = radius1 * delta_b1
        ctrl_p2_edgy = radius2 * delta_b2

        control_pts[1, :] = p1 + edgy1 * ctrl_p1_base + (1.0 - edgy1) * ctrl_p1_edgy
        control_pts[2, :] = p2 + edgy2 * ctrl_p2_base + (1.0 - edgy2) * ctrl_p2_edgy

        # 在贝塞尔曲线上采样
        curve = sample_bezier_curve(control_pts, n_sampling_pts)

    # 否则直接返回两点间的直线
    else:
        curve = p1
        curve = np.vstack([curve, p2])

    return curve


def generate_shape(
    n_pts: int,
    position: list[float],
    shape_type: str,
    shape_size: float,
    shape_name: str,
    n_sampling_pts: int,
    output_dir: str,
) -> "Shape":
    """按给定形状类型生成障碍物形状，写出预览图与控制点 csv。

    Args:
        n_pts: 控制点数量。
        position: 形状中心位置 `[x, y]`。
        shape_type: 形状类型，取值 `"cylinder"` / `"square"` / `"random"`。
        shape_size: 形状尺寸（控制点坐标的缩放系数）。
        shape_name: 形状名称，同时作为输出文件名前缀。
        n_sampling_pts: 每段控制点之间的采样点数量。
        output_dir: 输出目录，预览图（`.png`）与控制点（`.csv`）写入此处。

    Returns:
        构建完成的 `Shape` 实例。

    Raises:
        ValueError: `shape_type` 不在支持的取值范围内。
    """
    # 校验输入参数
    if shape_type not in ["cylinder", "square", "random"]:
        raise ValueError(
            f'不支持的 shape_type: {shape_type!r}，仅支持 "cylinder"、"square"、"random"'
        )
    logger.debug(f"generate_shape: shape_type={shape_type}, n_pts={n_pts}")

    # 根据形状类型生成控制点
    if shape_type == "cylinder":
        radius = 0.5 * np.ones(n_pts)
        edgy = 1.0 * np.ones(n_pts)
        ctrl_pts = generate_cylinder_pts(n_pts)
        ctrl_pts[:, :] *= shape_size

    elif shape_type == "square":
        radius = np.zeros(n_pts)
        edgy = np.ones(n_pts)
        ctrl_pts = generate_square_pts(n_pts)
        ctrl_pts[:, :] *= shape_size

    else:  # shape_type == "random"
        radius = np.random.uniform(low=0.8, high=1.0, size=n_pts)
        edgy = np.random.uniform(low=0.45, high=0.55, size=n_pts)
        ctrl_pts = np.random.rand(n_pts, 2)
        ctrl_pts[:, :] *= shape_size

    # 初始化并构建形状
    shape = Shape(shape_name, position, ctrl_pts, n_pts, n_sampling_pts, radius, edgy, output_dir)

    shape.build()
    shape.generate_image(xmin=-shape_size, xmax=shape_size, ymin=-shape_size, ymax=shape_size)
    shape.write_csv()

    return shape
