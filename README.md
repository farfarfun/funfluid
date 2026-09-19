# funfluid

基于格子玻尔兹曼方法（LBM）的流体仿真工具库，同时提供显微视频中衣藻（chlamydomonas）粒子检测与轨迹分析的实验代码。

## 安装

```bash
pip install funfluid
```

视频/图像检测相关功能（依赖 opencv-python、tqdm、imageio）与 Tecplot 数据对接功能为可选依赖，按需安装：

```bash
pip install "funfluid[video]"     # 显微视频粒子检测
pip install "funfluid[tecplot]"   # Tecplot 数据读写
```

## 最小示例

构造一个 4x4 的小型格子并执行单步碰撞-流动-宏观量计算：

```python
from funfluid.lbm.core.lattice import Lattice

lattice = Lattice(nx=4, ny=4, tau_lbm=0.8)

lattice.equilibrium()
lattice.collision_stream()
lattice.macro()

print(lattice.u.shape)   # (2, 4, 4) 速度场
print(lattice.rho.shape)  # (4, 4) 密度场
```

更完整的圆柱绕流、Turek 基准等仿真示例见 `src/funfluid/lbm/example/`。

## 模块概览

- `funfluid.lbm`：LBM 求解器核心（`Lattice`、障碍物形状生成、观测量滑动平均等）
- `funfluid.simulate`：椭圆粒子仿真与 Tecplot 数据读取工具
- `funfluid.tecplot`：Tecplot 360 连接与模板工具（需安装 `funfluid[tecplot]`）
- `funfluid.experiment.chlamydomonas`：显微视频中衣藻粒子的检测、追踪与 MSD 分析（需安装 `funfluid[video]`）

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
