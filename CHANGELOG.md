# CHANGELOG

## [未发布]

### 修复

- `funfluid.experiment.chlamydomonas.plot.core` / `plot.property` 此前在 import 时
  直接读取写死的本机路径（`/Volumes/ChenDisk/...`）、执行 `print`，`plot.property`
  还调用了未定义的 `analyse(...)`，import 即报错；现收敛为带类型标注/中文 docstring
  的函数（`plot_particle_csv`、`analyse_property`），import 不再有副作用，脚本逻辑
  置于 `if __name__ == "__main__":` 下
- `.gitignore` 补充 `*.db`、`*.rar`、`.run/`、`logs/`、`.vscode/`（SPEC.md §10 要求的最低覆盖范围）

### 变更

- `funfluid.lbm.core.lattice`（`Obstacle`、`BaseDefine.__init__`、`macro`、
  `equilibrium`、`collision_stream`）与
  `funfluid.experiment.chlamydomonas.base.globalconfig`（`VideoSplit`、
  `GlobalConfig` 及其公开方法）补齐类型标注与中文 docstring
- `funfluid.lbm.core.lattice`、`funfluid.lbm.core.shape` 中的英文注释/英文
  一行 docstring 统一翻译为中文，保留 Zou-He/TRT/IBB 等领域术语与代码标识符

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
