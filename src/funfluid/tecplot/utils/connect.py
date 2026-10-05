import tecplot as tp


def new_layout_connect(port=7600):
    tp.session.connect(port=port)
    tp.new_layout()
