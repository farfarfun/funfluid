import tecplot as tp


def new_layout_connect(port: int = 7600) -> None:
    """连接 Tecplot 360 会话并新建布局。

    Args:
        port: Tecplot 360 PyTecplot 服务端口。

    Returns:
        无返回值。

    Raises:
        tecplot.exception.TecplotError: 连接或新建布局失败时由 PyTecplot 抛出。
    """
    tp.session.connect(port=port)
    tp.new_layout()
