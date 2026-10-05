"""
轻量冒烟测试（smoke tests），非详尽单元测试。

目标：验证 funfluid 包的顶层/常用子模块可以正常导入，核心公开类/函数
在不依赖真实网络、数据库、云凭据、GPU 或长时间仿真的情况下可以被构造/调用。

已知问题（发现但未修复，超出本次冒烟测试范围）：
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
import tempfile

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
        "funfluid.experiment.chlamydomonas.plot.core",
        "funfluid.experiment.chlamydomonas.plot.property",
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


def test_video_split_parse_path_collects_all_split_segments(tmp_path, monkeypatch):
    """回归测试：分段录制的视频（`*.split1.avi`、`*.split2.avi`...）
    应从首段聚合出全部存在的分段文件。"""
    from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit

    monkeypatch.chdir(tmp_path)
    base = tmp_path / "sample"
    (tmp_path / f"{base.name}.split1.avi").write_bytes(b"")
    (tmp_path / f"{base.name}.split2.avi").write_bytes(b"")

    vs = VideoSplit()
    ok = vs.parse_path(str(base) + ".split1.avi")
    assert ok is True
    assert vs.video_name == base.name
    assert vs.video_paths == [
        str(base) + ".split1.avi",
        str(base) + ".split2.avi",
    ]


def test_video_split_parse_path_rejects_non_first_segment():
    """边界场景：传入非首段分段文件（如 `*.split2.avi`）应返回 False，
    调用方需要始终从 split1 开始解析整组分段。"""
    from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit

    vs = VideoSplit()
    ok = vs.parse_path("/data/videos/sample.split2.avi")
    assert ok is False


def test_video_split_to_json_round_trip():
    from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit

    vs = VideoSplit()
    vs.parse_path("/data/videos/sample.mp4")
    vs.parse_other()

    data = vs.to_json()
    assert data["video_name"] == "sample"
    assert data["video_path"] == "/data/videos/sample.mp4"
    assert data["cache_dir"] == "/data/videos/sample"


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
# 4b. funfluid.experiment.chlamydomonas.plot（此前 import 即崩溃，现已修复）
# ---------------------------------------------------------------------------


def test_plot_core_plot_particle_csv_reads_file(tmp_path):
    """回归测试：此前 `plot.core` 在 import 时直接读取写死的本机路径并
    print，import 本身不应有任何副作用；读取逻辑现收敛到
    `plot_particle_csv(csv_path)` 函数中，显式传参才会执行 I/O。"""
    from funfluid.experiment.chlamydomonas.plot.core import plot_particle_csv

    csv_path = tmp_path / "particle.csv"
    csv_path.write_text("x,y\n1,2\n3,4\n")

    df = plot_particle_csv(str(csv_path))

    assert list(df.columns) == ["x", "y"]
    assert len(df) == 2


def test_plot_core_plot_particle_csv_missing_file_raises():
    """失败路径：传入不存在的 csv 路径应抛出 FileNotFoundError。"""
    from funfluid.experiment.chlamydomonas.plot.core import plot_particle_csv

    with pytest.raises(FileNotFoundError):
        plot_particle_csv("/tmp/funfluid-does-not-exist/particle.csv")


def test_plot_property_analyse_property_not_implemented():
    """回归测试：此前 `plot.property` 在 import 时直接调用未定义的
    `analyse(...)`，import 即 NameError；现收敛为显式的
    `analyse_property(video_path)` 函数，未实现时抛出
    NotImplementedError 而不是让 import 崩溃。"""
    from funfluid.experiment.chlamydomonas.plot.property import analyse_property

    with pytest.raises(NotImplementedError):
        analyse_property("/tmp/does-not-matter.avi")


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
    tecplot_file.write_text('VARIABLES = "x", "y"\nZONE N=3, F=POINT\n0.0 0.0\n1.0 0.0\n0.0 1.0\n')

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


# ---------------------------------------------------------------------------
# 11. 本轮审计修复的回归测试（farfarfun/todo-list#833）
# ---------------------------------------------------------------------------


def _build_small_lattice(tmp_path, **kwargs):
    """构造一个小尺寸 Lattice，输出目录落在 tmp_path 下，避免污染工作区。"""
    from funfluid.lbm.core.lattice import Lattice

    params = {"nx": 6, "ny": 6, "results_dir": f"{tmp_path}/results/"}
    params.update(kwargs)
    return Lattice(**params)


def test_lattice_compute_flag_starts_true_and_check_stop_turns_it_off(tmp_path):
    """compute 表示「继续迭代」，初值必须为 True，达到 it_max 后才变 False。

    此前初值为 False 且 check_stop 在结束时置 True，方向写反，
    导致所有 `while lat.compute:` 主循环一次都进不去。
    """
    lattice = _build_small_lattice(tmp_path, stop="it", it_max=3)

    assert lattice.compute is True

    # check_stop 先判断 it > it_max 再自增，因此前 it_max + 1 次都应继续
    for _ in range(4):
        assert lattice.check_stop() is True
    # it 递增到超过 it_max 后应停止
    assert lattice.check_stop() is False
    assert lattice.compute is False


def test_lattice_results_dir_is_configurable(tmp_path):
    """results_dir 应可通过关键字覆盖，而不是硬编码 ./results/。"""
    lattice = _build_small_lattice(tmp_path)

    assert lattice.results_dir == f"{tmp_path}/results/"
    assert os.path.isdir(lattice.output_dir)
    assert os.path.isdir(lattice.png_dir)


def test_zou_he_top_wall_writes_density_on_top_row():
    """顶壁边界条件必须把密度写在 j=ly 行，而不是 j=0 行。"""
    import numpy as np

    from funfluid.lbm.core.speed_nb import nb_zou_he_top_wall_velocity

    nx, ny = 5, 4
    ly = ny - 1
    u = np.zeros((2, nx, ny))
    u_top = np.zeros((2, nx))
    rho = np.full((nx, ny), -1.0)  # 哨兵值，便于区分哪一行被写过
    g = np.zeros((9, nx, ny))
    # 只在顶行放置非零分布函数；底行保持全 0
    g[:, :, ly] = 1.0

    nb_zou_he_top_wall_velocity(nx - 1, ly, u, u_top, rho, g)

    # 顶壁速度为 0 时，rho[:, ly] = g0 + g1 + g2 + 2*(g3+g5+g7) = 1*3 + 2*3 = 9
    assert np.allclose(rho[:, ly], 9.0)
    # 底行不应被顶壁边界条件改写
    assert np.allclose(rho[:, 0], -1.0)


def test_build_default_lattice_applies_computed_parameters(tmp_path):
    """build_default_lattice 必须真的把推导出的参数传进 Lattice。

    此前用 19 个位置参数调用 `Lattice(*args, **kwargs)`，而 BaseDefine
    只读 kwargs，位置参数被整体丢弃，返回的是全默认参数的 Lattice。
    """
    from funfluid.lbm.params import build_default_lattice

    lattice = build_default_lattice(results_dir=f"{tmp_path}/results/")

    # 默认值是 nx=100 / dpi=100 / Re_lbm=100.0；推导值与之不同
    assert lattice.nx == 600
    assert lattice.ny == 600
    assert lattice.dpi == 200
    assert lattice.name == "lattice"
    assert lattice.results_dir == f"{tmp_path}/results/"
    assert lattice.Re_lbm != 100.0


def test_background_nearest_returns_minimum_score_background():
    """process_background_nearest 应返回 score 最小的背景，而不是最后一个。"""
    import numpy as np

    pytest.importorskip(
        "cv2",
        reason="funfluid.experiment.chlamydomonas.detect 依赖 funfluid[video] extra",
    )
    from funfluid.experiment.chlamydomonas.base.base import VideoBase
    from funfluid.experiment.chlamydomonas.detect.background import (
        BackGround,
        BackGroundDetect,
    )

    class _FakeConfig:
        cache_dir = "."
        video_width = 4
        video_height = 4

    detect = BackGroundDetect.__new__(BackGroundDetect)
    detect.filepath = "unused.pkl"
    detect.config = _FakeConfig()
    assert VideoBase is not None

    image = np.zeros((4, 4, 3), dtype=np.uint8)
    near = BackGround(4, 4, uid="near")
    near.back_image = np.zeros((4, 4, 3), dtype=np.uint8)
    far = BackGround(4, 4, uid="far")
    far.back_image = np.full((4, 4, 3), 255, dtype=np.uint8)

    # near 排在前面，倒序遍历时最后访问到的是 near；若实现正确应始终返回 near
    detect.background_list = [near, far]
    assert detect.process_background_nearest(image).uid == "near"
    detect.background_list = [far, near]
    assert detect.process_background_nearest(image).uid == "near"
    # 空列表应返回 None 而不是抛异常
    detect.background_list = []
    assert detect.process_background_nearest(image) is None


def test_ellipse_plot_module_import_has_no_side_effects():
    """simulate.ellipse.plot 导入时不得读取 data.txt 或绘图。"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import matplotlib; matplotlib.use('Agg');"
            " import funfluid.simulate.ellipse.plot as m; print(len(m.ELLIPSE_COLUMNS))",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=tempfile.gettempdir(),
    )
    assert result.returncode == 0, result.stderr
    assert "19" in result.stdout


def test_load_ellipse_frames_normal_and_failure_paths(tmp_path):
    import matplotlib

    matplotlib.use("Agg")
    from funfluid.simulate.ellipse.plot import ELLIPSE_COLUMNS, load_ellipse_frames

    good = tmp_path / "data.txt"
    row = " ".join(str(float(i)) for i in range(len(ELLIPSE_COLUMNS)))
    good.write_text(f"{row}\n{row}\n", encoding="utf-8")

    df = load_ellipse_frames(good)
    assert list(df.columns) == ELLIPSE_COLUMNS
    assert len(df) == 2

    empty = tmp_path / "empty.txt"
    empty.write_text("\n  \n", encoding="utf-8")
    with pytest.raises(ValueError, match="内容为空"):
        load_ellipse_frames(empty)

    bad = tmp_path / "bad.txt"
    bad.write_text("1.0 2.0 3.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="列数不匹配"):
        load_ellipse_frames(bad)

    with pytest.raises(FileNotFoundError):
        load_ellipse_frames(tmp_path / "missing.txt")


def test_split_all_extensions():
    from funfluid.temp.temp1 import split_all_extensions

    assert split_all_extensions("/a/b/c.tar.gz") == ("/a/b/c", [".tar", ".gz"])
    assert split_all_extensions("/a/b/c.txt") == ("/a/b/c", [".txt"])
    assert split_all_extensions("/a/b/c") == ("/a/b/c", [])


def test_back_contain_default_center_is_not_shared():
    """BackContain 的 center 默认值不能是共享的可变 numpy 数组。"""
    pytest.importorskip(
        "cv2",
        reason="funfluid.experiment.chlamydomonas.detect 依赖 funfluid[video] extra",
    )
    from funfluid.experiment.chlamydomonas.detect.contain import BackContain

    a = BackContain()
    b = BackContain()
    a.center[0] = 99
    assert b.center[0] == 0


def test_base_cache_read_accepts_extra_positional_args(tmp_path):
    """overwrite 已改为仅限关键字参数，透传的 *args 不应与它冲突。"""
    from funfluid.common.base.cache import BaseCache

    class _Cache(BaseCache):
        def __init__(self, filepath):
            super().__init__(filepath=filepath)
            self.calls = []

        def execute(self, *args, **kwargs):
            self.calls.append(("execute", args, kwargs))

        def _read(self, *args, **kwargs):
            return ("read", args, kwargs)

        def _save(self, *args, **kwargs):
            self.calls.append(("save", args, kwargs))

    cache = _Cache(str(tmp_path / "nonexistent.bin"))
    assert cache.read("extra", flag=1) == ("read", ("extra",), {"flag": 1})
    assert ("execute", ("extra",), {"flag": 1}) in cache.calls


def test_add_obstacle_ibb_length_matches_boundary(tmp_path):
    """启用 IBB 时 obs.ibb 必须与 obs.boundary 等长且逐项对应。

    此前 ibb 以 `np.empty(1)` 起始，首元素是未初始化的脏数据，
    导致 nb_bounce_back_obstacle 中 obs_ibb[k] 与 boundary[k] 整体错位一位。
    """
    import numpy as np

    lattice = _build_small_lattice(tmp_path, nx=21, ny=21, IBB=True)
    square = np.array([[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]])
    lattice.add_obstacle(square, 1)

    obs = lattice.obstacles[0]
    assert len(obs.boundary) > 0
    assert len(obs.ibb) == len(obs.boundary)
    assert np.all(np.isfinite(obs.ibb))
