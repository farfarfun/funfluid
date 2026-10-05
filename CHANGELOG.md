# CHANGELOG

## [未发布]

### 修复

- `funfluid.experiment.chlamydomonas.plot.core` / `plot.property` 此前在 import 时
  直接读取写死的本机路径（`/Volumes/ChenDisk/...`）、执行 `print`，`plot.property`
  还调用了未定义的 `analyse(...)`，import 即报错；现收敛为带类型标注/中文 docstring
  的函数（`plot_particle_csv`、`analyse_property`），import 不再有副作用，脚本逻辑
  置于 `if __name__ == "__main__":` 下
- `.gitignore` 补充 `*.db`、`*.rar`、`.run/`、`logs/`、`.vscode/`（SPEC.md §10 要求的最低覆盖范围）
- `Lattice.compute` 初值由 `False` 改为 `True`：该标志表示「仍需继续迭代」，
  初值为 `False` 会让 `while lat.compute` 形式的主循环一次都进不去
- `funfluid.lbm.core.speed_nb.nb_zou_he_top_wall_velocity` 修复顶壁密度行号：
  原先把 `rho[:, 0]` 当作顶壁密度写入并读取，既污染了底壁密度，又让顶壁分布函数
  使用了陈旧值；现统一改为 `rho[:, ly]`
- `funfluid.lbm.params.build_default_lattice` 修复参数传递：原先以 19 个位置参数
  调用 `Lattice(...)`，而 `BaseDefine` 只从 `**kwargs` 取值，所有计算出来的物理参数
  被静默丢弃，返回的是一个全默认参数的 `Lattice`；现逐项以关键字传入
- `funfluid.experiment.chlamydomonas.detect.background.BackGroundDetect.process_background_nearest`
  修复循环变量与结果变量同名的问题：原先返回的是最后遍历到的背景而非 score 最小的背景
- `funfluid.experiment.chlamydomonas.detect.contain.BackContain` 的 `center` 默认值
  改为 `None` 哨兵：原先直接写 `np.array([0, 0])`，所有未显式传参的实例共享同一个可变数组
- `funfluid.common.base.cache.BaseCache.read/save` 的 `overwrite` 改为关键字参数：
  原先位于 `*args` 之前，任何额外位置参数都会被误当成 `overwrite`
- `funfluid.lbm.example.example_obstacle` / `example_turek` 补回缺失的
  `numpy`、`Lattice`、`generate_shape` 导入，两个示例此前直接 `NameError`
- `funfluid.simulate.ellipse.project.track.plot` 的动画函数返回 `FuncAnimation` 对象，
  避免对象被 GC 回收导致动画不播放
- `funfluid.simulate.ellipse.plot`、`funfluid.temp.temp1` 移除 import 时的文件读取与
  `print` 副作用，收敛为带类型标注/中文 docstring 的函数 + `__main__` 守卫
- `funfluid.lbm.core.lattice.Lattice.add_obstacle` 修复 IBB 距离数组的越界起点：
  原先以 `np.empty(1)` 起始，首元素为未初始化脏数据，使 `obs_ibb[k]` 与
  `boundary[k]` 整体错位一位，启用插值反弹（IBB）时边界条件读到错误距离
- `funfluid.simulate.ellipse.project.project` 修复 `sep="\s+"` 的无效转义（W605），
  并把遮蔽内置名的参数 `type` 改名为 `angle_unit`

### 变更

- `funfluid.lbm.core.lattice`（`Obstacle`、`BaseDefine.__init__`、`macro`、
  `equilibrium`、`collision_stream`）与
  `funfluid.experiment.chlamydomonas.base.globalconfig`（`VideoSplit`、
  `GlobalConfig` 及其公开方法）补齐类型标注与中文 docstring
- `funfluid.lbm.core.lattice`、`funfluid.lbm.core.shape` 中的英文注释/英文
  一行 docstring 统一翻译为中文，保留 Zou-He/TRT/IBB 等领域术语与代码标识符
- `funfluid.lbm.core.speed_nb` 全部 13 个 numba 内核的英文 docstring 与注释翻译为中文
- 消除全部 `from ... import *` 通配导入（`lattice.py`、`obs_array.py`、
  `example_cavity1.py`、`tecplot/templates/templates1.py`、`tecplot/utils/connect.py`），
  改为显式导入；各 `__init__.py` 补齐 `__all__`
- `Lattice` 输出目录改为可配置的 `results_dir` 参数，不再写死 `./results/`
- `pyproject.toml` 新增 ruff 配置（`select = ["E","F","I","W","UP","B"]`、
  `line-length = 100`、`target-version = "py310"`，`ignore = ["PLE1205"]` 用于
  farlog 的 `{}` 占位符日志）、`[dependency-groups] dev` 与 `[tool.pytest.ini_options]`；
  移除构建后端为 hatchling 时无效的 `[tool.setuptools]` 配置；全仓 ruff 检查清零
- README 补充环境要求（Python >= 3.10、核心与可选依赖、Tecplot 360 license 前提）与开发验证命令
- `tests/test_smoke.py` 新增本轮修复对应的 10 个回归测试

## [1.0.6] - 2026-09-19

### 新增

- README 补充一句话简介、安装命令、最小可运行示例与模块概览
- README 末尾附组织统一的「关于 farfarfun」区块
- 新增 CHANGELOG.md
- `pyproject.toml` 新增 `video`（opencv-python/tqdm/imageio）与 `tecplot`（pytecplot）两个 extras，补齐此前未声明的运行时依赖

### 修复

- `funfluid.lbm.core.buff.Buff.mv_avg` 修复滑动平均增长率计算的越界判断：原先按 `add()` 调用次数（`self.it`）判断是否已有 5 个历史观测值，但 `avg3_buff` 实际按 `mv_avg()` 调用次数增长，两者不同步时会触发 `IndexError`；现改为按 `avg3_buff` 自身长度判断

### 变更

- `pyproject.toml` 声明 `license = "MIT"` 并收录 `LICENSE` 到打包产物
- 日志统一改用 `farlog`：移除 `funfluid.utils.log` 中的 `logging.basicConfig` 全局配置与裸 `logging` 用法
- 移除库代码中的 `print` 诊断输出（`funfluid.lbm.core.lattice`、`funfluid.lbm.core.shape`），改为 `farlog` 日志
- `funfluid.lbm.params` 不再在 import 时执行仿真计算、打印参数与创建 `./results/` 目录，相关逻辑收敛到 `build_default_lattice()` 函数，仅在作为脚本直接运行时执行
- 异常处理收敛为领域相关类型：`funfluid.common.base.cache.BaseCache` 的抽象方法改为 `NotImplementedError`；`ContainDetect.find_contain` 改为 `LookupError` 并保留原始上下文；`VideoProgress.execute` 捕获异常后改为 `logger.exception` 记录上下文并重新抛出，不再吞掉异常
- `funfluid.experiment.chlamydomonas.detect.particle` 移除 `from typing import List`，改用内置 `list[...]` 泛型写法
- 为 `funfluid.simulate.utils.tecplot.read_tecplot_point`、`funfluid.lbm.core.shape.generate_shape` 补充类型标注与中文 docstring
- `generate_shape` 遇到非法 `shape_type` 时改为 `raise ValueError`，不再 `print` 后 `exit()`

### 废弃

- 无
