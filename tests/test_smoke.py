"""
轻量冒烟测试（smoke tests），非详尽单元测试。

目标：验证 funfluid 包的顶层/常用子模块可以正常导入，核心公开类/函数
在不依赖真实网络、数据库、云凭据、GPU 或长时间仿真的情况下可以被构造/调用。

已知问题（发现但未修复，超出本次冒烟测试范围）：
- `funfluid.experiment.chlamydomonas.plot.core` / `plot.property` 属于
  写死本地路径（`/Volumes/ChenDisk/...`）的一次性脚本，`plot.property`
  中还调用了未定义的 `analyse(...)`，import 即报错，因此不纳入测试。
- `funfluid.experiment.chlamydomonas.*`（base.base / detect.* /
  progress.video_progress / analyse.analyse / run）依赖 `cv2`
  (opencv-python)、`tqdm`、`imageio`。这些依赖已在 pyproject.toml 的
  `[project.optional-dependencies].video` extra 中声明（`pip install
  funfluid[video]`），但属于较重的图像处理依赖，不在本次“轻量冒烟测试”
  范围内新增安装，相关测试以 pytest.importorskip 方式跳过。
- `funfluid.tecplot.utils.connect` 依赖专有软件 Tecplot 360 的 Python
  binding（PyPI 包名 `pytecplot`，import 名 `tecplot`），已在
  `[project.optional-dependencies].tecplot` extra 中声明，但需要真实的
  Tecplot 360 安装与许可证，无法在普通 CPU 环境冒烟测试，使用
  pytest.importorskip 跳过。
- `funfluid.lbm.obs_array` 是一个可直接运行的示例脚本（阵列障碍物绕流），
  import 时会直接执行完整仿真循环，耗时且非本包的公开 API，因此不纳入
  导入测试范围（`src/funfluid/lbm/example/*.py` 同理）。
"""

import os
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# 1. 顶层 & 常用子模块导入
# ---------------------------------------------------------------------------


def test_import_top_level_package():
    import funfluid  # noqa: F401


@pytest.mark.parametrize(
    "module_name",
    [
        "funfluid.utils.log",
        "funfluid.utils.timer",
        "funfluid.common",
        "funfluid.common.base",
        "funfluid.common.base.cache",
        "funfluid.common.particle",
        "funfluid.common.flow",
        "funfluid.lbm",
        "funfluid.lbm.core",
        "funfluid.lbm.core.buff",
        "funfluid.lbm.core.shape",
        "funfluid.lbm.core.lattice",
        "funfluid.lbm.params",
        "funfluid.simulate",
        "funfluid.simulate.utils",
        "funfluid.simulate.utils.tecplot",
        "funfluid.tecplot",
        "funfluid.tecplot.utils",
        "funfluid.tecplot.templates",
        "funfluid.temp",
        "funfluid.experiment",
        "funfluid.experiment.chlamydomonas",
        "funfluid.experiment.chlamydomonas.base",
        "funfluid.experiment.chlamydomonas.base.globalconfig",
    ],
)
def test_import_public_submodules(module_name):
    __import__(module_name)


def test_chlamydomonas_cv_stack_not_in_scope():
    """
    funfluid.experiment.chlamydomonas 下大部分模块 (base.base / detect.* /
    progress.video_progress / analyse.analyse / run) 依赖 cv2 / tqdm /
    imageio，这些依赖已声明为 `funfluid[video]` extra。这里不强行安装重量级的
    opencv 等依赖，改为跳过并说明原因。
    """
    pytest.importorskip(
        "cv2",
        reason=(
            "funfluid.experiment.chlamydomonas 的视频/图像检测模块依赖 "
            "opencv-python(cv2)/tqdm/imageio，已声明为 funfluid[video] extra，"
            "超出本次轻量冒烟测试范围，跳过。"
        ),
    )


def test_tecplot_utils_connect_needs_real_tecplot_license():
    """
    funfluid.tecplot.utils.connect 依赖专有软件 Tecplot 360 的 Python
    binding（`funfluid[tecplot]` extra，PyPI 包名 pytecplot），需要真实安装
    与许可证才能使用，无法在普通 CPU 环境中冒烟测试。
    """
    pytest.importorskip(
        "tecplot",
        reason="需要真实安装的 Tecplot 360 及许可证，跳过",
    )


# ---------------------------------------------------------------------------
# 2. funfluid.utils
# ---------------------------------------------------------------------------


def test_timer_decorator_wraps_and_returns_value():
    from funfluid.utils.timer import timer

    @timer
    def add(a, b):
        return a + b

    assert add(1, 2) == 3


# ---------------------------------------------------------------------------
# 3. funfluid.common.base.cache
# ---------------------------------------------------------------------------


def test_csv_dataframe_cache_round_trip(tmp_path):
    import pandas as pd

    from funfluid.common.base.cache import CSVDataFrameCache

    filepath = tmp_path / "data.csv"
    cache = CSVDataFrameCache(filepath=str(filepath))
    assert not cache.exists()

    cache.df = pd.DataFrame({"a": [1, 2, 3]})
    cache.save()
    assert cache.exists()

    result = cache.read()
    assert list(result["a"]) == [1, 2, 3]


def test_pickle_dataframe_cache_round_trip(tmp_path):
    import pandas as pd

    from funfluid.common.base.cache import PickleDataFrameCache

    filepath = tmp_path / "data.pkl"
    cache = PickleDataFrameCache(filepath=str(filepath))
    cache.df = pd.DataFrame({"b": [4, 5]})
    cache.save()

    result = cache.read()
    assert list(result["b"]) == [4, 5]


def test_base_cache_unimplemented_methods_raise_not_implemented_error():
    """抽象方法未实现时应抛出 NotImplementedError（领域相关类型），而不是裸 Exception。"""
    from funfluid.common.base.cache import BaseCache

    cache = BaseCache(filepath="/tmp/does-not-matter.bin")
    with pytest.raises(NotImplementedError):
        cache.execute()
    with pytest.raises(NotImplementedError):
        cache._read()
    with pytest.raises(NotImplementedError):
        cache._save()


# ---------------------------------------------------------------------------
# 4. funfluid.experiment.chlamydomonas.base.globalconfig (纯 Python，无重依赖)
# ---------------------------------------------------------------------------


def test_video_split_parse_path():
    from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit

    vs = VideoSplit()
    ok = vs.parse_path("/data/videos/sample.mp4")
    assert ok is True
    assert vs.video_name == "sample"
    assert vs.video_paths == ["/data/videos/sample.mp4"]


def test_global_config_get_result_path():
    from funfluid.experiment.chlamydomonas.base.globalconfig import GlobalConfig

    gc = GlobalConfig("/data/root")
    result = gc.get_result_path("/data/root/videos/sample.mp4")
    assert result is not None
    assert result.cache_dir == "/data/root/results/sample"


def test_contain_detect_find_contain_missing_raises_lookup_error():
    """
    ContainDetect.find_contain 在找不到对应 uid 时应抛出带上下文的
    LookupError，而不是裸 `raise Exception(...)`。
    """
    cv2 = pytest.importorskip(
        "cv2",
        reason="ContainDetect 所在模块顶层导入 cv2，为 funfluid[video] extra，跳过",
    )
    del cv2

    from funfluid.experiment.chlamydomonas.detect.contain import ContainDetect

    class _FakeConfig:
        cache_dir = "/tmp/funfluid-contain-detect-test"

    detect = ContainDetect(config=_FakeConfig())
    with pytest.raises(LookupError, match="missing-uid"):
        detect.find_contain("missing-uid")


# ---------------------------------------------------------------------------
# 5. funfluid.lbm.core.shape
# ---------------------------------------------------------------------------


def test_shape_pure_geometry_helpers():
    from funfluid.lbm.core.shape import compute_distance, generate_square_pts

    assert compute_distance([0, 0], [3, 4]) == pytest.approx(5.0)

    pts = generate_square_pts(4)
    assert pts.shape == (4, 2)


def test_generate_shape_square(tmp_path):
    import matplotlib

    matplotlib.use("Agg")  # 避免在无显示环境下尝试打开窗口

    from funfluid.lbm.core.shape import generate_shape

    output_dir = str(tmp_path) + os.sep
    shape = generate_shape(
        n_pts=4,
        position=[0, 0],
        shape_type="square",
        shape_size=0.5,
        shape_name="smoke_square",
        n_sampling_pts=10,
        output_dir=output_dir,
    )

    assert shape.curve_pts.shape[1] == 3
    assert os.path.exists(os.path.join(output_dir, "smoke_square.png"))
    assert os.path.exists(os.path.join(output_dir, "smoke_square.csv"))


def test_generate_shape_invalid_type_raises_value_error(tmp_path):
    """非法 shape_type 应抛出 ValueError，而不是 print + exit() 终止解释器。"""
    from funfluid.lbm.core.shape import generate_shape

    with pytest.raises(ValueError, match="shape_type"):
        generate_shape(
            n_pts=4,
            position=[0, 0],
            shape_type="triangle",
            shape_size=0.5,
            shape_name="bad",
            n_sampling_pts=10,
            output_dir=str(tmp_path) + os.sep,
        )


def test_generate_cylinder_pts_requires_at_least_four_points():
    from funfluid.lbm.core.shape import generate_cylinder_pts

    with pytest.raises(ValueError):
        generate_cylinder_pts(2)


def test_generate_square_pts_requires_exactly_four_points():
    from funfluid.lbm.core.shape import generate_square_pts

    with pytest.raises(ValueError):
        generate_square_pts(5)


# ---------------------------------------------------------------------------
# 6. funfluid.lbm.core.buff.Buff
# ---------------------------------------------------------------------------


def test_buff_add_and_mv_avg():
    from funfluid.lbm.core.buff import Buff

    buff = Buff(name="drag", dt=1.0, obs_cv_ct=1e-2, obs_cv_nb=5, output_dir="./")
    for value in (1.0, 2.0, 3.0):
        buff.add(value)

    obs, growth = buff.mv_avg()
    assert isinstance(obs, float)
    assert growth == 0.0


def test_buff_mv_avg_does_not_crash_when_add_outpaces_mv_avg():
    """
    回归测试：此前 `mv_avg()` 按 `self.it`（add() 调用次数）判断是否已有
    5 个历史观测值，但实际用来取值的 `avg3_buff` 是按 mv_avg() 调用次数
    增长的。当 add() 被调用的次数多于 mv_avg() 时，两者不同步，会触发
    `IndexError: index -5 is out of bounds`。现改为直接判断 avg3_buff
    自身长度，此处验证同样的调用模式不再崩溃。
    """
    from funfluid.lbm.core.buff import Buff

    buff = Buff(name="drag", dt=1.0, obs_cv_ct=1e-2, obs_cv_nb=5, output_dir="./")

    # 模拟 add() 调用次数（self.it）远多于 mv_avg() 调用次数的场景：
    # 十次迭代里，每次都 add()，但只在偶数步调用一次 mv_avg()。
    for step in range(10):
        buff.add(float(step))
        if step % 2 == 0:
            obs, growth = buff.mv_avg()
            assert isinstance(obs, float)
            assert isinstance(growth, float)

    assert buff.it == 10
    # mv_avg 被调用 5 次（step=0,2,4,6,8），avg3_buff 初始长度 2，
    # 故此时长度为 7，触发过一次 growth 计算而不会抛出 IndexError。
    assert len(buff.avg3_buff) == 7


# ---------------------------------------------------------------------------
# 7. funfluid.lbm.core.lattice.Lattice（微型网格，仅验证可构造与单步不报错）
# ---------------------------------------------------------------------------


def test_lattice_construct_and_single_step(tmp_path, monkeypatch):
    import matplotlib

    matplotlib.use("Agg")

    # Lattice/BaseDefine 会在当前工作目录下创建 ./results/<timestamp>/ 目录，
    # 切到临时目录避免污染仓库工作区。
    monkeypatch.chdir(tmp_path)

    from funfluid.lbm.core.lattice import Lattice

    lattice = Lattice(nx=4, ny=4, tau_lbm=0.8)
    assert lattice.u.shape == (2, 4, 4)
    assert lattice.rho.shape == (4, 4)

    # 跑最小的一步，确认 numba 编译的核心函数可以正常工作，
    # 而不是运行完整仿真。
    lattice.equilibrium()
    lattice.collision_stream()
    lattice.macro()

    assert lattice.u.shape == (2, 4, 4)


# ---------------------------------------------------------------------------
# 8. funfluid.lbm.params（此前在 import 时就有副作用，现收敛到函数里）
# ---------------------------------------------------------------------------


def test_import_lbm_params_has_no_side_effects(tmp_path, monkeypatch):
    """
    回归测试：此前 `funfluid.lbm.params` 在 import 时会直接计算仿真参数、
    打印日志并创建 `./results/` 目录。现在这些逻辑被收敛到
    `build_default_lattice()` 函数中，import 本身不应产生任何文件系统副作用。
    """
    monkeypatch.chdir(tmp_path)

    import importlib

    import funfluid.lbm.params as params_module

    importlib.reload(params_module)

    assert not os.path.exists(tmp_path / "results")
    assert hasattr(params_module, "build_default_lattice")


def test_build_default_lattice_returns_lattice(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    from funfluid.lbm.core.lattice import Lattice
    from funfluid.lbm.params import build_default_lattice

    lattice = build_default_lattice(results_dir=str(tmp_path / "results") + "/")

    assert isinstance(lattice, Lattice)
    assert os.path.exists(tmp_path / "results")


# ---------------------------------------------------------------------------
# 9. funfluid.simulate.utils.tecplot
# ---------------------------------------------------------------------------


def test_read_tecplot_point_parses_minimal_point_file(tmp_path):
    from funfluid.simulate.utils.tecplot import read_tecplot_point

    tecplot_file = tmp_path / "sample.dat"
    tecplot_file.write_text(
        'VARIABLES = "x", "y"\n'
        "ZONE N=3, F=POINT\n"
        "0.0 0.0\n"
        "1.0 0.0\n"
        "0.0 1.0\n"
    )

    df = read_tecplot_point(str(tecplot_file))

    # 注意：列名解析不会去除变量名两侧的引号/空格（VARIABLES 行原样切分），
    # 这是既有行为，此处按实际行为断言，不在本次修复范围内改变解析逻辑。
    assert list(df.columns) == ['"x"', ' "y"']
    assert len(df) == 3
    assert df['"x"'].tolist() == [0.0, 1.0, 0.0]


# ---------------------------------------------------------------------------
# 10. CLI 入口
# ---------------------------------------------------------------------------


def test_no_cli_entry_points_declared():
    """
    pyproject.toml 中没有 [project.scripts]，因此没有可测试的命令行入口。
    保留此测试作为文档记录：一旦未来添加 CLI 入口，应在此补充
    `--help` 的冒烟测试。
    """
    import tomllib

    pyproject_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyproject.toml"
    )
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    assert data.get("project", {}).get("scripts", {}) == {}


def test_python_executable_can_import_funfluid_as_subprocess():
    """作为最后一道防线：以子进程方式确认包在全新解释器中也能正常导入。"""
    result = subprocess.run(
        [sys.executable, "-c", "import funfluid; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "ok" in result.stdout
