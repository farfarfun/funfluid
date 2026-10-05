import numba as nb
from numba import jit


@jit(nopython=True, parallel=True, cache=True)
def nb_equilibrium(u, c, w, rho, g_eq):
    """计算 D2Q9 平衡态分布函数，就地写入 `g_eq`。"""
    v = 1.5 * (u[0, :, :] ** 2 + u[1, :, :] ** 2)

    # 计算平衡态
    for q in nb.prange(9):
        t = 3.0 * (u[0, :, :] * c[q, 0] + u[1, :, :] * c[q, 1])
        g_eq[q, :, :] = 1.0 + t + 0.5 * t**2 - v
        g_eq[q, :, :] *= rho[:, :] * w[q]


@jit(nopython=True, parallel=True, cache=True)
def nb_col_str(g, g_eq, g_up, om_p, om_m, c, ns, nx, ny, lx, ly):
    """执行一步 TRT 碰撞与迁移，就地更新 `g`。"""
    # 先处理 q=0 方向
    g_up[0, :, :] = g[0, :, :] - om_p * (g[0, :, :] - g_eq[0, :, :])
    g[0, :, :] = g_up[0, :, :]

    # 再处理其余方向的碰撞
    for q in nb.prange(1, 9):
        qb = ns[q]

        g_up[q, :, :] = (
            g[q, :, :]
            - om_p * 0.5 * (g[q, :, :] + g[qb, :, :] - g_eq[q, :, :] - g_eq[qb, :, :])
            - om_m * 0.5 * (g[q, :, :] - g[qb, :, :] - g_eq[q, :, :] + g_eq[qb, :, :])
        )

    # 迁移
    g[1, 1:nx, :] = g_up[1, 0:lx, :]
    g[2, 0:lx, :] = g_up[2, 1:nx, :]
    g[3, :, 1:ny] = g_up[3, :, 0:ly]
    g[4, :, 0:ly] = g_up[4, :, 1:ny]
    g[5, 1:nx, 1:ny] = g_up[5, 0:lx, 0:ly]
    g[6, 0:lx, 0:ly] = g_up[6, 1:nx, 1:ny]
    g[7, 0:lx, 1:ny] = g_up[7, 1:nx, 0:ly]
    g[8, 1:nx, 0:ly] = g_up[8, 0:lx, 1:ny]


@jit(nopython=True, parallel=True, cache=True)
def nb_drag_lift(boundary, ns, c, g_up, g, R_ref, U_ref, L_ref):
    """累加障碍物边界上的动量交换，返回无量纲阻力/升力系数。"""
    # 初始化
    fx = 0.0
    fy = 0.0

    # 遍历障碍物边界点
    for k in nb.prange(len(boundary)):
        i = boundary[k, 0]
        j = boundary[k, 1]
        q = boundary[k, 2]
        qb = ns[q]
        cx = c[q, 0]
        cy = c[q, 1]
        g0 = g_up[q, i, j] + g[qb, i, j]

        fx += g0 * cx
        fy += g0 * cy

    # 归一化为无量纲系数
    Cx = -2.0 * fx / (R_ref * L_ref * U_ref**2)
    Cy = -2.0 * fy / (R_ref * L_ref * U_ref**2)

    return Cx, Cy


@jit(nopython=True, parallel=True, cache=True)
def nb_bounce_back_obstacle(IBB, boundary, ns, sc, obs_ibb, g_up, g, u, lattice):
    """障碍物半程反弹无滑移边界条件（`IBB` 为真时使用插值反弹）。"""
    # 插值反弹（IBB）
    if IBB:
        for k in nb.prange(len(boundary)):
            i = boundary[k, 0]
            j = boundary[k, 1]
            q = boundary[k, 2]
            qb = ns[q]
            cb = sc[qb, :]
            im = i + cb[0]
            jm = j + cb[1]
            imm = i + 2 * cb[0]
            jmm = j + 2 * cb[1]

            p = obs_ibb[k]
            pp = 2.0 * p
            if p < 0.5:
                g[qb, i, j] = (
                    p * (pp + 1.0) * g_up[q, i, j]
                    + (1.0 + pp) * (1.0 - pp) * g_up[q, im, jm]
                    - p * (1.0 - pp) * g_up[q, imm, jmm]
                )
            else:
                g[qb, i, j] = (
                    (1.0 / (p * (pp + 1.0))) * g_up[q, i, j]
                    + ((pp - 1.0) / p) * g_up[qb, i, j]
                    + ((1.0 - pp) / (1.0 + pp)) * g_up[qb, im, jm]
                )

    # 标准半程反弹
    if not IBB:
        for k in nb.prange(len(boundary)):
            i = boundary[k, 0]
            j = boundary[k, 1]
            q = boundary[k, 2]
            qb = ns[q]

            g[qb, i, j] = g_up[q, i, j]


@jit(nopython=True, cache=True)
def nb_zou_he_left_wall_velocity(lx, ly, u, u_left, rho, g):
    """Zou-He 左侧壁面速度边界条件。"""
    cst1 = 2.0 / 3.0
    cst2 = 1.0 / 6.0
    cst3 = 1.0 / 2.0

    u[0, 0, :] = u_left[0, :]
    u[1, 0, :] = u_left[1, :]

    rho[0, :] = (
        g[0, 0, :]
        + g[3, 0, :]
        + g[4, 0, :]
        + 2.0 * g[2, 0, :]
        + 2.0 * g[6, 0, :]
        + 2.0 * g[7, 0, :]
    ) / (1.0 - u[0, 0, :])

    g[1, 0, :] = g[2, 0, :] + cst1 * rho[0, :] * u[0, 0, :]

    g[5, 0, :] = (
        g[6, 0, :]
        - cst3 * (g[3, 0, :] - g[4, 0, :])
        + cst2 * rho[0, :] * u[0, 0, :]
        + cst3 * rho[0, :] * u[1, 0, :]
    )

    g[8, 0, :] = (
        g[7, 0, :]
        + cst3 * (g[3, 0, :] - g[4, 0, :])
        + cst2 * rho[0, :] * u[0, 0, :]
        - cst3 * rho[0, :] * u[1, 0, :]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_right_wall_velocity(lx, ly, u, u_right, rho, g):
    """Zou-He 右侧壁面速度边界条件。"""
    cst1 = 2.0 / 3.0
    cst2 = 1.0 / 6.0
    cst3 = 1.0 / 2.0

    u[0, lx, :] = u_right[0, :]
    u[1, lx, :] = u_right[1, :]

    rho[lx, :] = (
        g[0, lx, :]
        + g[3, lx, :]
        + g[4, lx, :]
        + 2.0 * g[1, lx, :]
        + 2.0 * g[5, lx, :]
        + 2.0 * g[8, lx, :]
    ) / (1.0 + u[0, lx, :])

    g[2, lx, :] = g[1, lx, :] - cst1 * rho[lx, :] * u[0, lx, :]

    g[6, lx, :] = (
        g[5, lx, :]
        + cst3 * (g[3, lx, :] - g[4, lx, :])
        - cst2 * rho[lx, :] * u[0, lx, :]
        - cst3 * rho[lx, :] * u[1, lx, :]
    )

    g[7, lx, :] = (
        g[8, lx, :]
        - cst3 * (g[3, lx, :] - g[4, lx, :])
        - cst2 * rho[lx, :] * u[0, lx, :]
        + cst3 * rho[lx, :] * u[1, lx, :]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_right_wall_pressure(lx, ly, u, rho_right, u_right, rho, g):
    """Zou-He 右侧壁面压力（密度）边界条件。"""
    cst1 = 2.0 / 3.0
    cst2 = 1.0 / 6.0
    cst3 = 1.0 / 2.0

    rho[lx, :] = rho_right[:]
    u[1, lx, :] = u_right[1, :]

    u[0, lx, :] = (
        g[0, lx, :]
        + g[3, lx, :]
        + g[4, lx, :]
        + 2.0 * g[1, lx, :]
        + 2.0 * g[5, lx, :]
        + 2.0 * g[8, lx, :]
    ) / rho[lx, :] - 1.0

    g[2, lx, :] = g[1, lx, :] - cst1 * rho[lx, :] * u[0, lx, :]

    g[6, lx, :] = (
        g[5, lx, :]
        + cst3 * (g[3, lx, :] - g[4, lx, :])
        - cst2 * rho[lx, :] * u[0, lx, :]
        - cst3 * rho[lx, :] * u[1, lx, :]
    )

    g[7, lx, :] = (
        g[8, lx, :]
        - cst3 * (g[3, lx, :] - g[4, lx, :])
        - cst2 * rho[lx, :] * u[0, lx, :]
        + cst3 * rho[lx, :] * u[1, lx, :]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_top_wall_velocity(lx, ly, u, u_top, rho, g):
    """Zou-He 顶部无滑移壁面速度边界条件。"""
    cst1 = 2.0 / 3.0
    cst2 = 1.0 / 6.0
    cst3 = 1.0 / 2.0

    u[0, :, ly] = u_top[0, :]
    u[1, :, ly] = u_top[1, :]

    # 顶壁位于 j = ly，这里的密度与各分布函数都必须取 ly 行；
    # 取 0 行会把顶壁密度写到底壁上，同时让下面用到的 rho[:, ly] 保持陈旧值。
    rho[:, ly] = (
        g[0, :, ly]
        + g[1, :, ly]
        + g[2, :, ly]
        + 2.0 * g[3, :, ly]
        + 2.0 * g[5, :, ly]
        + 2.0 * g[7, :, ly]
    ) / (1.0 + u[1, :, ly])

    g[4, :, ly] = g[3, :, ly] - cst1 * rho[:, ly] * u[1, :, ly]

    g[8, :, ly] = (
        g[7, :, ly]
        - cst3 * (g[1, :, ly] - g[2, :, ly])
        + cst3 * rho[:, ly] * u[0, :, ly]
        - cst2 * rho[:, ly] * u[1, :, ly]
    )

    g[6, :, ly] = (
        g[5, :, ly]
        + cst3 * (g[1, :, ly] - g[2, :, ly])
        - cst3 * rho[:, ly] * u[0, :, ly]
        - cst2 * rho[:, ly] * u[1, :, ly]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_bottom_wall_velocity(lx, ly, u, u_bot, rho, g):
    """Zou-He 底部无滑移壁面速度边界条件。"""
    cst1 = 2.0 / 3.0
    cst2 = 1.0 / 6.0
    cst3 = 1.0 / 2.0

    u[0, :, 0] = u_bot[0, :]
    u[1, :, 0] = u_bot[1, :]

    rho[:, 0] = (
        g[0, :, 0]
        + g[1, :, 0]
        + g[2, :, 0]
        + 2.0 * g[4, :, 0]
        + 2.0 * g[6, :, 0]
        + 2.0 * g[8, :, 0]
    ) / (1.0 - u[1, :, 0])

    g[3, :, 0] = g[4, :, 0] + cst1 * rho[:, 0] * u[1, :, 0]

    g[5, :, 0] = (
        g[6, :, 0]
        - cst3 * (g[1, :, 0] - g[2, :, 0])
        + cst3 * rho[:, 0] * u[0, :, 0]
        + cst2 * rho[:, 0] * u[1, :, 0]
    )

    g[7, :, 0] = (
        g[8, :, 0]
        + cst3 * (g[1, :, 0] - g[2, :, 0])
        - cst3 * rho[:, 0] * u[0, :, 0]
        + cst2 * rho[:, 0] * u[1, :, 0]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_bottom_left_corner_velocity(lx, ly, u, rho, g):
    """Zou-He 左下角无滑移速度边界条件。"""
    u[0, 0, 0] = u[0, 1, 0]
    u[1, 0, 0] = u[1, 1, 0]

    rho[0, 0] = rho[1, 0]

    g[1, 0, 0] = g[2, 0, 0] + (2.0 / 3.0) * rho[0, 0] * u[0, 0, 0]

    g[3, 0, 0] = g[4, 0, 0] + (2.0 / 3.0) * rho[0, 0] * u[1, 0, 0]

    g[5, 0, 0] = (
        g[6, 0, 0] + (1.0 / 6.0) * rho[0, 0] * u[0, 0, 0] + (1.0 / 6.0) * rho[0, 0] * u[1, 0, 0]
    )

    g[7, 0, 0] = 0.0
    g[8, 0, 0] = 0.0

    g[0, 0, 0] = (
        rho[0, 0]
        - g[1, 0, 0]
        - g[2, 0, 0]
        - g[3, 0, 0]
        - g[4, 0, 0]
        - g[5, 0, 0]
        - g[6, 0, 0]
        - g[7, 0, 0]
        - g[8, 0, 0]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_top_left_corner_velocity(lx, ly, u, rho, g):
    """Zou-He 左上角无滑移速度边界条件。"""
    u[0, 0, ly] = u[0, 1, ly]
    u[1, 0, ly] = u[1, 1, ly]

    rho[0, ly] = rho[1, ly]

    g[1, 0, ly] = g[2, 0, ly] + (2.0 / 3.0) * rho[0, ly] * u[0, 0, ly]

    g[4, 0, ly] = g[3, 0, ly] - (2.0 / 3.0) * rho[0, ly] * u[1, 0, ly]

    g[8, 0, ly] = (
        g[7, 0, ly]
        + (1.0 / 6.0) * rho[0, ly] * u[0, 0, ly]
        - (1.0 / 6.0) * rho[0, ly] * u[1, 0, ly]
    )

    g[5, 0, ly] = 0.0
    g[6, 0, ly] = 0.0

    g[0, 0, ly] = (
        rho[0, ly]
        - g[1, 0, ly]
        - g[2, 0, ly]
        - g[3, 0, ly]
        - g[4, 0, ly]
        - g[5, 0, ly]
        - g[6, 0, ly]
        - g[7, 0, ly]
        - g[8, 0, ly]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_top_right_corner_velocity(lx, ly, u, rho, g):
    """Zou-He 右上角无滑移速度边界条件。"""
    u[0, lx, ly] = u[0, lx - 1, ly]
    u[1, lx, ly] = u[1, lx - 1, ly]

    rho[lx, ly] = rho[lx - 1, ly]

    g[2, lx, ly] = g[1, lx, ly] - (2.0 / 3.0) * rho[lx, ly] * u[0, lx, ly]

    g[4, lx, ly] = g[3, lx, ly] - (2.0 / 3.0) * rho[lx, ly] * u[1, lx, ly]

    g[6, lx, ly] = (
        g[5, lx, ly]
        - (1.0 / 6.0) * rho[lx, ly] * u[0, lx, ly]
        - (1.0 / 6.0) * rho[lx, ly] * u[1, lx, ly]
    )

    g[7, lx, ly] = 0.0
    g[8, lx, ly] = 0.0

    g[0, lx, ly] = (
        rho[lx, ly]
        - g[1, lx, ly]
        - g[2, lx, ly]
        - g[3, lx, ly]
        - g[4, lx, ly]
        - g[5, lx, ly]
        - g[6, lx, ly]
        - g[7, lx, ly]
        - g[8, lx, ly]
    )


@jit(nopython=True, cache=True)
def nb_zou_he_bottom_right_corner_velocity(lx, ly, u, rho, g):
    """Zou-He 右下角无滑移速度边界条件。"""
    u[0, lx, 0] = u[0, lx - 1, 0]
    u[1, lx, 0] = u[1, lx - 1, 0]

    rho[lx, 0] = rho[lx - 1, 0]

    g[2, lx, 0] = g[1, lx, 0] - (2.0 / 3.0) * rho[lx, 0] * u[0, lx, 0]
    g[3, lx, 0] = g[4, lx, 0] + (2.0 / 3.0) * rho[lx, 0] * u[1, lx, 0]
    g[7, lx, 0] = (
        g[8, lx, 0]
        - (1.0 / 6.0) * rho[lx, 0] * u[0, lx, 0]
        + (1.0 / 6.0) * rho[lx, 0] * u[1, lx, 0]
    )

    g[5, lx, 0] = 0.0
    g[6, lx, 0] = 0.0

    g[0, lx, 0] = (
        rho[lx, 0]
        - g[1, lx, 0]
        - g[2, lx, 0]
        - g[3, lx, 0]
        - g[4, lx, 0]
        - g[5, lx, 0]
        - g[6, lx, 0]
        - g[7, lx, 0]
        - g[8, lx, 0]
    )
