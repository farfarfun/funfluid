"""LBM 求解器默认参数计算与 Lattice 构建。

此前该模块在 import 时直接执行仿真参数计算、打印日志并创建
`./results/` 目录，属于不应有的导入期副作用。现收敛到
`build_default_lattice()`，仅在需要时显式调用；作为脚本直接运行时
（`python -m funfluid.lbm.params`）才会执行并打印参数、创建输出目录。
"""

import datetime
import math
import os

from funfluid.lbm.core.lattice import Lattice
from funfluid.utils.log import logger


def build_default_lattice(results_dir: str = "./results/") -> Lattice:
    """按内置的一组默认物理/数值参数构建 LBM `Lattice`。

    Args:
        results_dir: 仿真输出根目录，函数内部会在其下按时间戳创建子目录，
            目录不存在时会被创建（调用方需自行承担该副作用）。

    Returns:
        已按默认参数初始化完成的 `Lattice` 实例。
    """
    ###############################################
    # LBM solver
    ###############################################

    # Domain
    x_min = 0.0
    x_max = 1.0
    y_min = 0.0
    y_max = 1.0

    # Fixed parameters
    # u_lbm < 0.05 maintains low Mach condition
    tau_lbm = 0.8
    dx_lbm = 1.0
    dt_lbm = 1.0
    Cs = 1.0 / math.sqrt(3.0)

    # Free parameters
    Re = 400.0
    rho = 1.0
    L = x_max - x_min
    nx = 600
    nu = 1.0e-3

    # nu_lbm     = u_lbm*nx/Re
    nu_lbm = 0.0001
    u_lbm = Re * nu_lbm / nx
    # nx         = math.floor(Re*nu_lbm/u_lbm)

    # Deduce u, dx and dt
    u = nu * Re / L
    ny = math.floor(nx * (y_max - y_min) / (x_max - x_min))
    dx = (x_max - x_min) / nx
    dt = dx * (u_lbm / u)

    # Set parameters conversions
    # Conversions are assumed s.t. a = Ca * a_lbm
    Cx = dx
    Ct = dt
    Cu = Cx / Ct
    Cn = Cx**2 / Ct
    Cr = 1.0
    Cf = Cr * Cx**2 / Ct

    # Deduce remaining parameters
    L_lbm = L / Cx
    # nu_lbm     = nu/Cn
    rho_lbm = rho / Cr
    Re_lbm = u_lbm * L_lbm / nu_lbm
    tau_lbm = 0.5 + nu_lbm / (Cs**2)
    # dt         = ((tau_lbm - 0.5)*Cs**2*dx**2)/nu

    # TRT parameters
    tau_p_lbm = tau_lbm
    lambda_trt = 1.0 / 4.0  # Constant TRT parameter
    tau_m_lbm = lambda_trt / (tau_p_lbm - 0.5) + 0.5

    # Output parameters
    output_freq = 500
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    output_dir = results_dir + str(time) + "/"

    # Other parameters
    lattice_name = "lattice"
    t_max = 30.0
    it_max = math.floor(t_max / dt) + 1
    dpi = 200

    logger.info("### LBM solver ###")
    logger.info(f"# u          = {u}")
    logger.info(f"# u_lbm      = {u_lbm}")
    logger.info(f"# tau_p_lbm  = {tau_p_lbm}")
    logger.info(f"# tau_m_lbm  = {tau_m_lbm}")
    logger.info(f"# Re         = {Re}")
    logger.info(f"# Re_lbm     = {Re_lbm}")
    logger.info(f"# nx         = {nx}")
    logger.info(f"# ny         = {ny}")
    logger.info(f"# dx         = {dx}")
    logger.info(f"# dt         = {dt}")
    logger.info(f"# dx/dt      = {dx / dt}")
    logger.info(f"# nu         = {nu}")
    logger.info(f"# nu_lbm     = {nu_lbm}")
    logger.info(f"# it         = {it_max}")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Initialize lattice
    return Lattice(
        lattice_name,
        x_min,
        x_max,
        y_min,
        y_max,
        nx,
        ny,
        tau_p_lbm,
        tau_m_lbm,
        Cx,
        Ct,
        Cs,
        Cr,
        Cu,
        Cf,
        dx,
        dt,
        output_dir,
        dpi,
    )


if __name__ == "__main__":
    build_default_lattice()
