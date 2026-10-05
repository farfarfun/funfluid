import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from funfluid.lbm.core.buff import Buff
from funfluid.lbm.core.speed_nb import (
    nb_bounce_back_obstacle,
    nb_col_str,
    nb_drag_lift,
    nb_equilibrium,
    nb_zou_he_bottom_left_corner_velocity,
    nb_zou_he_bottom_right_corner_velocity,
    nb_zou_he_bottom_wall_velocity,
    nb_zou_he_left_wall_velocity,
    nb_zou_he_right_wall_pressure,
    nb_zou_he_right_wall_velocity,
    nb_zou_he_top_left_corner_velocity,
    nb_zou_he_top_right_corner_velocity,
    nb_zou_he_top_wall_velocity,
)
from funfluid.utils.log import logger


class Obstacle:
    """
    障碍物
    """

    def __init__(
        self,
        polygon: np.ndarray,
        area: float,
        boundary: np.ndarray,
        ibb: np.ndarray,
        tag: int,
    ) -> None:
        """
        Args:
            polygon: 障碍物外轮廓的控制点坐标，形状为 ``(n, 2)``。
            area: 障碍物在网格中占据的物理面积。
            boundary: 障碍物边界上流体第一层网格点及其反弹方向，
                形状为 ``(m, 3)``（格点 i、格点 j、反弹方向索引）。
            ibb: 启用插值反弹（IBB）时，边界点到障碍物轮廓的归一化距离。
            tag: 该障碍物在网格 `lattice` 数组中对应的标记值。
        """
        self.polygon = polygon
        self.area = area
        self.boundary = boundary
        self.ibb = ibb
        self.tag = tag


class BaseDefine:
    """LBM 求解器的网格、物理参数与运行时状态定义。

    根据传入的关键字参数初始化网格尺寸、物理/无量纲参数、TRT 松弛参数、
    D2Q9 离散速度与权重、各类物理场数组，并创建输出目录。
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Args:
            *args: 预留参数，当前未使用。
            **kwargs: 网格与物理参数，支持的键见各属性赋值处的默认值，
                例如 ``nx``/``ny``（网格分辨率）、``tau_lbm``（松弛时间）、
                ``u_lbm``/``Re_lbm``（特征速度/雷诺数）、``stop``/``it_max``
                （停止条件）等；未传入时使用各自的默认值。
        """
        self.name = kwargs.get("name", "lattice")
        self.x_min = kwargs.get("x_min", 0.0)
        self.x_max = kwargs.get("x_max", 1.0)
        self.y_min = kwargs.get("y_min", 0.0)
        self.y_max = kwargs.get("y_max", 1.0)
        self.nx = kwargs.get("nx", 100)
        self.ny = kwargs.get("ny", self.nx)
        self.tau_lbm = kwargs.get("tau_lbm", 1.0)
        self.dx = kwargs.get("dx", 1.0)
        self.dt = kwargs.get("dt", 1.0)
        self.Cx = kwargs.get("Cx", self.dx)
        self.Ct = kwargs.get("Ct", self.dt)
        self.Cr = kwargs.get("Cr", 1.0)
        self.Cn = kwargs.get("Cn", self.Cx**2 / self.Ct)
        self.Cu = kwargs.get("Cu", self.Cx / self.Ct)
        self.Cf = kwargs.get("Cf", self.Cr * self.Cx**2 / self.Ct)
        self.dpi = kwargs.get("dpi", 100)
        self.u_lbm = kwargs.get("u_lbm", 0.05)
        self.L_lbm = kwargs.get("L_lbm", 100.0)
        self.nu_lbm = kwargs.get("nu_lbm", 0.01)
        self.Re_lbm = kwargs.get("Re_lbm", 100.0)
        self.rho_lbm = kwargs.get("rho_lbm", 1.0)
        self.IBB = kwargs.get("IBB", False)
        self.stop = kwargs.get("stop", "it")
        self.t_max = kwargs.get("t_max", 1.0)
        self.it_max = kwargs.get("it_max", 1000)
        self.obs_cv_ct = kwargs.get("obs_cv_ct", 1.0e-1)
        self.obs_cv_nb = kwargs.get("obs_cv_nb", 500)

        # 其他参数
        self.output_it = 0
        self.lx = self.nx - 1
        self.ly = self.ny - 1
        self.q = 9
        self.Cs = 1.0 / math.sqrt(3.0)

        # 输出目录
        time = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        self.results_dir = kwargs.get("results_dir", "./results/")
        self.output_dir = self.results_dir + str(time) + "/"
        self.png_dir = self.output_dir + "./png/"

        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if not os.path.exists(self.png_dir):
            os.makedirs(self.png_dir)

        # TRT（双松弛时间）参数
        self.tau_p_lbm = self.tau_lbm
        self.lambda_trt = 1.0 / 4.0  # 取该值时数值最稳定
        self.tau_m_lbm = self.lambda_trt / (self.tau_p_lbm - 0.5) + 0.5
        self.om_p_lbm = 1.0 / self.tau_p_lbm
        self.om_m_lbm = 1.0 / self.tau_m_lbm
        self.om_lbm = 1.0 / self.tau_lbm

        # D2Q9 离散速度方向
        self.c = np.array(
            [
                [0, 0],
                [1, 0],
                [-1, 0],
                [0, 1],
                [0, -1],
                [1, 1],
                [-1, -1],
                [-1, 1],
                [1, -1],
            ]
        )

        # 权重
        # 先是正交方向值，再是对角方向值，最后是中心值
        idx_card = [np.linalg.norm(ci) < 1.1 for ci in self.c]
        idx_extra_card = [np.linalg.norm(ci) > 1.1 for ci in self.c]

        self.w = np.ones(self.q)
        self.w[np.asarray(idx_card)] = 1.0 / 9.0
        self.w[np.asarray(idx_extra_card)] = 1.0 / 36.0
        self.w[0] = 4.0 / 9.0

        # 反弹边界条件用的方向映射数组
        self.ns = np.array([0, 2, 1, 4, 3, 6, 5, 8, 7])

        # 密度分布函数数组
        self.g = np.zeros((self.q, self.nx, self.ny))
        self.g_eq = np.zeros((self.q, self.nx, self.ny))
        self.g_up = np.zeros((self.q, self.nx, self.ny))

        # 边界条件
        self.u_left = np.zeros((2, self.ny))
        self.u_right = np.zeros((2, self.ny))
        self.u_top = np.zeros((2, self.nx))
        self.u_bot = np.zeros((2, self.nx))
        self.rho_right = np.zeros(self.ny)

        # 网格数组方向约定：
        # +x     = 从左到右
        # +y     = 从下到上
        # origin = 左下角
        self.lattice = np.zeros((self.nx, self.ny))

        # 物理场
        self.rho = np.ones((self.nx, self.ny))
        self.u = np.zeros((2, self.nx, self.ny))

        # 障碍物
        self.obstacles = []

        # 迭代与停止条件
        # compute 表示「仍需继续迭代」，初值必须为 True，否则 `while lat.compute`
        # 形式的主循环一次都不会进入。
        self.it = 0
        self.compute = True
        self.drag_buff = Buff("drag", self.dt, self.obs_cv_ct, self.obs_cv_nb, self.output_dir)
        self.lift_buff = Buff("lift", self.dt, self.obs_cv_ct, self.obs_cv_nb, self.output_dir)

        # 日志输出
        logger.info("")

        info = f"""
####################################
### LBM solver ###
####################################
##### Computation parameters')
### u_lbm      = {self.u_lbm:f}
### L_lbm      = {self.L_lbm:f}
### nu_lbm     = {self.nu_lbm:f}
### Re_lbm     = {self.Re_lbm:f}
### tau_p_lbm  = {self.tau_p_lbm:f}
### tau_m_lbm  = {self.tau_m_lbm:f}
### dt         = {self.dt:f}
### dx         = {self.dx:f}
### nx         = {self.nx}
### ny         = {self.ny}
### IBB        = {self.IBB}
####################################
            """
        logger.info(info)

    def macro(self) -> None:
        """根据当前密度分布函数 `g` 计算宏观场。

        就地更新 `self.rho`（密度场）与 `self.u`（速度场），无返回值。
        """
        self.rho[:, :] = np.sum(self.g[:, :, :], axis=0)

        # 计算速度
        self.u[0, :, :] = np.tensordot(self.c[:, 0], self.g[:, :, :], axes=(0, 0)) / self.rho[:, :]
        self.u[1, :, :] = np.tensordot(self.c[:, 1], self.g[:, :, :], axes=(0, 0)) / self.rho[:, :]

    def equilibrium(self) -> None:
        """计算 D2Q9 平衡态分布函数。

        根据当前的速度场 `self.u`、密度场 `self.rho` 计算平衡态分布，
        就地写入 `self.g_eq`，无返回值。
        """
        nb_equilibrium(self.u, self.c, self.w, self.rho, self.g_eq)

    def collision_stream(self) -> None:
        """执行一步 TRT 碰撞与迁移（collision and streaming）。

        就地更新 `self.g`，无返回值。
        """
        nb_col_str(
            self.g,
            self.g_eq,
            self.g_up,
            self.om_p_lbm,
            self.om_m_lbm,
            self.c,
            self.ns,
            self.nx,
            self.ny,
            self.lx,
            self.ly,
        )


class Condition(BaseDefine):
    """在 `BaseDefine` 之上提供 Zou-He 系列壁面/角点边界条件。

    所有方法都就地修改 `self.g`、`self.u`、`self.rho`，没有返回值。
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Args:
            *args: 透传给 `BaseDefine.__init__`。
            **kwargs: 透传给 `BaseDefine.__init__` 的网格与物理参数。
        """
        super().__init__(*args, **kwargs)

    def zou_he_right_wall_pressure(self) -> None:
        """施加 Zou-He 右侧壁面压力（密度）边界条件。"""
        nb_zou_he_right_wall_pressure(
            self.lx, self.ly, self.u, self.rho_right, self.u_right, self.rho, self.g
        )

    def zou_he_wall_velocity(self) -> None:
        """依次施加上下左右四个壁面的 Zou-He 速度边界条件。"""
        self.zou_he_bottom_wall_velocity()
        self.zou_he_left_wall_velocity()
        self.zou_he_right_wall_velocity()
        self.zou_he_top_wall_velocity()

    def zou_he_corner_velocity(self) -> None:
        """依次施加四个角点的 Zou-He 速度边界条件。"""
        self.zou_he_bottom_left_corner()
        self.zou_he_top_left_corner()
        self.zou_he_top_right_corner()
        self.zou_he_bottom_right_corner()

    def zou_he_left_wall_velocity(self) -> None:
        """施加 Zou-He 左侧壁面速度边界条件。"""
        nb_zou_he_left_wall_velocity(self.lx, self.ly, self.u, self.u_left, self.rho, self.g)

    def zou_he_right_wall_velocity(self) -> None:
        """施加 Zou-He 右侧壁面速度边界条件。"""
        nb_zou_he_right_wall_velocity(self.lx, self.ly, self.u, self.u_right, self.rho, self.g)

    def zou_he_top_wall_velocity(self) -> None:
        """施加 Zou-He 顶部无滑移壁面速度边界条件。"""
        nb_zou_he_top_wall_velocity(self.lx, self.ly, self.u, self.u_top, self.rho, self.g)

    def zou_he_bottom_wall_velocity(self) -> None:
        """施加 Zou-He 底部无滑移壁面速度边界条件。"""
        nb_zou_he_bottom_wall_velocity(self.lx, self.ly, self.u, self.u_bot, self.rho, self.g)

    def zou_he_bottom_left_corner(self) -> None:
        """施加 Zou-He 左下角边界条件。"""
        nb_zou_he_bottom_left_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_top_left_corner(self) -> None:
        """施加 Zou-He 左上角边界条件。"""
        nb_zou_he_top_left_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_top_right_corner(self) -> None:
        """施加 Zou-He 右上角边界条件。"""
        nb_zou_he_top_right_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)

    def zou_he_bottom_right_corner(self) -> None:
        """施加 Zou-He 右下角边界条件。"""
        nb_zou_he_bottom_right_corner_velocity(self.lx, self.ly, self.u, self.rho, self.g)


class Lattice(Condition):
    """完整的 LBM 求解器：在边界条件之上提供障碍物、受力统计与输出能力。"""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Args:
            *args: 透传给 `Condition.__init__`。
            **kwargs: 透传给 `Condition.__init__` 的网格与物理参数。
        """
        super().__init__(*args, **kwargs)

    def drag_lift(self, obs: int, R_ref: float, U_ref: float, L_ref: float) -> tuple[float, float]:
        """计算指定障碍物上的无量纲阻力系数与升力系数。

        Args:
            obs: 障碍物在 `self.obstacles` 中的下标。
            R_ref: 参考密度。
            U_ref: 参考速度。
            L_ref: 参考长度。

        Returns:
            二元组 `(Cx, Cy)`，分别为阻力系数与升力系数。
        """
        Cx, Cy = nb_drag_lift(
            self.obstacles[obs].boundary,
            self.ns,
            self.c,
            self.g_up,
            self.g,
            R_ref,
            U_ref,
            L_ref,
        )

        return Cx, Cy

    def add_buff(self, Cx: float, Cy: float, it: int) -> None:
        """将本次阻力/升力写入缓冲区、更新滑动平均并落盘。

        Args:
            Cx: 本步阻力系数。
            Cy: 本步升力系数。
            it: 当前迭代步号，用于换算成物理时间写入 `drag_lift` 文件。
        """
        self.drag_buff.add(Cx)
        self.lift_buff.add(Cy)

        avg_Cx, dcx = self.drag_buff.mv_avg()
        avg_Cy, dcy = self.lift_buff.mv_avg()

        # 写入文件
        filename = self.output_dir + "drag_lift"
        with open(filename, "a") as f:
            f.write(f"{it * self.dt} {Cx} {Cy} {avg_Cx} {avg_Cy} {dcx} {dcy}\n")

    def bounce_back_obstacle(self, obs: int) -> None:
        """对指定障碍物施加半程反弹（halfway bounce-back）无滑移边界条件。

        `self.IBB` 为 `True` 时使用插值反弹（IBB），否则使用标准反弹。
        结果就地写入 `self.g`。

        Args:
            obs: 障碍物在 `self.obstacles` 中的下标。
        """
        nb_bounce_back_obstacle(
            self.IBB,
            self.obstacles[obs].boundary,
            self.ns,
            self.c,
            self.obstacles[obs].ibb,
            self.g_up,
            self.g,
            self.u,
            self.lattice,
        )

    def output_fields(self, it, freq, *args, **kwargs):
        """输出 2D 流场速度幅值/等值线/流线图像。"""
        # 处理可选参数
        u_norm = kwargs.get("u_norm", True)
        u_ctr = kwargs.get("u_ctr", False)
        u_stream = kwargs.get("u_stream", True)

        # 未到输出频率则直接返回
        if it % freq != 0:
            return

        # 计算速度范数
        v = np.sqrt(self.u[0, :, :] ** 2 + self.u[1, :, :] ** 2)

        # 遮罩障碍物区域
        v[np.where(self.lattice > 0.0)] = -1.0
        vm = np.ma.masked_where((v < 0.0), v)
        vm = np.rot90(vm)

        # 绘制速度范数
        if u_norm:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            plt.imshow(
                vm,
                cmap="RdBu_r",
                vmin=0,
                vmax=1.5 * self.u_lbm,
                interpolation="spline16",
            )

            filename = self.png_dir + "u_norm_" + str(self.output_it) + ".png"
            plt.axis("off")
            plt.savefig(filename, dpi=self.dpi)
            plt.close()

        # 绘制速度等值线
        if u_ctr:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            x = np.linspace(0, 1, self.nx)
            y = np.linspace(0, 1, self.ny)
            ux = self.u[0, :, :].copy()
            uy = self.u[1, :, :].copy()
            uy = np.rot90(uy)
            ux = np.rot90(ux)
            uy = np.flipud(uy)
            ux = np.flipud(ux)
            vm = np.sqrt(ux**2 + uy**2)
            plt.contour(x, y, vm, cmap="RdBu_r", vmin=0.0, vmax=1.5 * self.u_lbm)
            filename = self.png_dir + "u_ctr_" + str(self.output_it) + ".png"
            plt.axis("off")
            plt.savefig(filename, dpi=self.dpi)
            plt.close()

        # 绘制流线
        # 输出的流线图是经过旋转和翻转的……
        if u_stream:
            plt.clf()
            fig, ax = plt.subplots(figsize=plt.figaspect(vm))
            fig.subplots_adjust(0, 0, 1, 1)
            ux = self.u[0, :, :].copy()
            uy = self.u[1, :, :].copy()
            uy = np.rot90(uy)
            ux = np.rot90(ux)
            uy = np.flipud(uy)
            ux = np.flipud(ux)
            vm = np.sqrt(ux**2 + uy**2)
            vm = np.rot90(vm)
            x = np.linspace(0, 1, self.nx)
            y = np.linspace(0, 1, self.ny)
            u = np.linspace(0, 1, 100)
            g = np.meshgrid(u, u)
            str_pts = list(zip(*(gi.flat for gi in g), strict=True))
            plt.streamplot(
                x,
                y,
                ux,
                uy,
                linewidth=1.5,
                color=uy,
                cmap="RdBu_r",
                arrowstyle="-",
                start_points=str_pts,
                density=3,
            )

            filename = self.output_dir + "u_stream.png"
            plt.axis("off")
            plt.savefig(filename, dpi=self.dpi)
            plt.close()

        # 更新计数器
        self.output_it += 1

    def add_obstacle(self, polygon, tag):
        """添加障碍物并计算其边界与面积。"""
        logger.info(f"### Obstacle {tag}")

        # 计算多边形边界范围
        poly_bnds = np.zeros(4)
        poly_bnds[0] = np.amin(polygon[:, 0])
        poly_bnds[1] = np.amax(polygon[:, 0])
        poly_bnds[2] = np.amin(polygon[:, 1])
        poly_bnds[3] = np.amax(polygon[:, 1])

        # 声明网格数组
        obstacle = np.empty((0, 2), dtype=int)
        boundary = np.empty((0, 3), dtype=int)
        ibb = np.empty(1, dtype=float)

        # 填充网格
        for i in range(self.nx):
            for j in range(self.ny):
                pt = self.lattice_coords(i, j)

                # 检查该点是否在多边形包围盒内
                if (
                    (pt[0] > poly_bnds[0])
                    and (pt[0] < poly_bnds[1])
                    and (pt[1] > poly_bnds[2])
                    and (pt[1] < poly_bnds[3])
                ):
                    if self.is_inside(polygon, pt):
                        self.lattice[i, j] = tag
                        obstacle = np.append(obstacle, np.array([[i, j]]), axis=0)

        logger.info(f"# {obstacle.shape[0]} locations in obstacle")

        # 构建障碍物边界，即流体第一层
        for k in range(len(obstacle)):
            i = obstacle[k, 0]
            j = obstacle[k, 1]

            for q in range(1, 9):
                qb = self.ns[q]
                cx = self.c[q, 0]
                cy = self.c[q, 1]
                ii = i + cx
                jj = j + cy

                if not self.lattice[ii, jj]:
                    boundary = np.append(boundary, np.array([[ii, jj, qb]]), axis=0)

        # 部分格点被重复计数，去重并排序
        boundary = np.unique(boundary, axis=0)

        logger.info(f"# {boundary.shape[0]} locations on boundary")

        # IBB 为 True 时计算网格到边界的距离
        if self.IBB:
            for k in range(len(boundary)):
                i = boundary[k, 0]
                j = boundary[k, 1]
                q = boundary[k, 2]
                pt = self.lattice_coords(i, j)
                x = polygon[:, 0] - pt[0]
                y = polygon[:, 1] - pt[1]
                dist = np.sqrt(np.square(x) + np.square(y))
                mpt = np.argmin(dist)
                mdst = dist[mpt] / (self.dx * np.linalg.norm(self.c[q]))
                ibb = np.append(ibb, mdst)

        # 计算障碍物面积
        area = 0.0
        for i in range(self.nx):
            for j in range(self.ny):
                if self.lattice[i, j] == tag:
                    area += self.dx**2

        logger.info(f"# Area = {area:f}")

        # 添加障碍物
        obs = Obstacle(polygon, area, boundary, ibb, tag)
        self.obstacles.append(obs)

    def lattice_coords(self, i, j):
        """将整数网格索引 (i, j) 转换为物理坐标。"""
        # 计算并返回格点 (i,j) 的坐标
        dx = (self.x_max - self.x_min) / (self.nx - 1)
        dy = (self.y_max - self.y_min) / (self.ny - 1)
        x = self.x_min + i * dx
        y = self.y_min + j * dy

        return [x, y]

    def is_inside(self, poly, pt):
        """判断点 pt 是否在闭合多边形 poly 内部（射线法，支持非凸多边形）。"""
        # 初始化
        j = len(poly) - 1
        odd_nodes = False

        # 判断点在多边形内部还是外部
        # 该算法对任意非凸多边形均有效
        for i in range(len(poly)):
            if ((poly[i, 1] < pt[1] <= poly[j, 1]) or (poly[j, 1] < pt[1] <= poly[i, 1])) and (
                poly[i, 0] < pt[0] or poly[j, 0] < pt[0]
            ):
                # 计算斜率
                slope = (poly[j, 0] - poly[i, 0]) / (poly[j, 1] - poly[i, 1])

                # 判断所在侧
                if (poly[i, 0] + (pt[1] - poly[i, 1]) * slope) < pt[0]:
                    odd_nodes = not odd_nodes

            # 递增
            j = i

        return odd_nodes

    def generate_image(self):
        """生成并保存当前网格（含障碍物边界）的图像。"""
        # 添加障碍物边界
        lat = self.lattice.copy()
        lat = lat.astype(float)

        for obs in range(len(self.obstacles)):
            for k in range(len(self.obstacles[obs].boundary)):
                i = self.obstacles[obs].boundary[k, 0]
                j = self.obstacles[obs].boundary[k, 1]
                lat[i, j] = -1.0

        # 绘制并保存网格图像
        filename = self.output_dir + self.name + ".png"

        plt.imsave(filename, np.rot90(lat), vmin=-1.0, vmax=1.0)

    def set_inlet_poiseuille(self, u_lbm, rho_lbm, it, sigma):
        """设置入口泊肃叶（Poiseuille）流场边界条件。"""
        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0
        self.rho_right[:] = rho_lbm

        for j in range(self.ny):
            pt = self.lattice_coords(0, j)
            self.u_left[:, j] = u_lbm * self.poiseuille(pt, it, sigma)

    def set_full_poiseuille(self, u_lbm, rho_lbm):
        """设置全域泊肃叶（Poiseuille）流场边界条件。"""
        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0
        self.rho_right[:] = rho_lbm

        for j in range(self.ny):
            for i in range(self.nx):
                pt = self.lattice_coords(i, j)
                u = u_lbm * self.poiseuille(pt, 1, 1.0e-10)
                self.u_left[:, j] = u
                self.u[:, i, j] = u

    def set_cavity(self, ut, ub=0.0, ul=0.0, ur=0.0):
        """设置顶盖驱动方腔（driven cavity）流场边界条件。"""
        lx = self.lx
        ly = self.ly

        self.u_left[:] = 0.0
        self.u_right[:] = 0.0
        self.u_top[:] = 0.0
        self.u_bot[:] = 0.0

        self.u_top[0, :] = ut
        self.u_bot[0, :] = ub
        self.u_left[1, :] = ul
        self.u_right[1, :] = ur

        self.u[0, :, ly] = self.u_top[0, :]
        self.u[1, :, ly] = self.u_top[1, :]
        self.u[0, :, 0] = self.u_bot[0, :]
        self.u[1, :, 0] = self.u_bot[1, :]
        self.u[0, 0, :] = self.u_left[0, :]
        self.u[1, 0, :] = self.u_left[1, :]
        self.u[0, lx, :] = self.u_right[0, :]
        self.u[1, lx, :] = self.u_right[1, :]

    def poiseuille(self, pt, it, sigma):
        """计算泊肃叶（Poiseuille）流速度剖面。"""
        y = pt[1]
        H = self.y_max - self.y_min
        u = np.zeros(2)
        u[0] = 4.0 * (self.y_max - y) * (y - self.y_min) / H**2

        val = it
        ret = 1.0 - math.exp(-(val**2) / (2.0 * sigma**2))
        u *= ret

        return u

    def poiseuille_error(self, u_lbm):
        """计算计算域中线处泊肃叶流的数值误差并写入文件。"""
        u_error = np.zeros((2, self.ny))
        nx = math.floor(self.nx / 2)

        for j in range(self.ny):
            pt = self.lattice_coords(nx, j)
            u_ex = self.poiseuille(pt, 1.0e10, 1)
            u = self.u[:, nx, j]

            u_error[0, j] = u[0] / u_lbm
            u_error[1, j] = u_ex[0]

        # 写入文件
        filename = self.output_dir + "poiseuille"
        with open(filename, "w") as f:
            for j in range(self.ny):
                f.write(f"{j * self.dx} {u_error[0, j]} {u_error[1, j]}\n")

    def cavity_error(self, u_lbm):
        """计算计算域中线处方腔流的数值误差并写入文件。"""
        ux_error = np.zeros(self.nx)
        uy_error = np.zeros(self.ny)
        nx = math.floor(self.nx / 2)
        ny = math.floor(self.ny / 2)

        for i in range(self.nx):
            uy_error[i] = self.u[1, i, ny] / u_lbm

        for j in range(self.ny):
            ux_error[j] = self.u[0, nx, j] / u_lbm

        # 写入文件
        filename = self.output_dir + "cavity_uy"
        with open(filename, "w") as f:
            for i in range(self.nx):
                f.write(f"{i * self.dx} {uy_error[i]}\n")
        filename = self.output_dir + "cavity_ux"
        with open(filename, "w") as f:
            for j in range(self.ny):
                f.write(f"{j * self.dx} {ux_error[j]}\n")

    def check_stop(self) -> bool:
        """检查停止条件（达到最大迭代步数或阻力/升力收敛）。

        Returns:
            是否还需要继续迭代：`True` 表示继续，`False` 表示已满足停止条件。
        """
        if self.stop == "it" and self.it > self.it_max:
            self.compute = False
            logger.info("# 计算结束：迭代步数超过 it_max")

        if self.stop == "obs" and self.drag_buff.obs_cv and self.lift_buff.obs_cv:
            self.compute = False
            logger.info("# 计算结束：阻力/升力已收敛")

        self.it += 1
        return self.compute

    def it_printings(self):
        """输出当前迭代步的进度日志。"""
        if self.stop == "it":
            logger.info(f"# it = {self.it} / {self.it_max}")
        if self.stop == "obs":
            str_d = f"{self.drag_buff.obs:10.6f}"
            str_l = f"{self.lift_buff.obs:10.6f}"
            logger.info(f"# it = {self.it}, avg drag ={str_d}, avg lift ={str_l}")
