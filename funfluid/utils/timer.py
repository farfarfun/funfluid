import time

from funfluid.utils.log import logger


# 定义一个函数用来统计传入函数的运行时间
def timer(func):  # 传入的参数是一个函数
    def deco(*args, **kwargs):  # 本应传入运行函数的各种参数
        logger.debug('\n函数:{_funcname_}开始运行:'.format(_funcname_=func.__name__))
        start_time = time.time()  # 调用代运行的函数，并将各种原本的参数传入
        res = func(*args, **kwargs)
        end_time = time.time()
        # 返回值为函数的运行结果
        logger.debug('函数:{_funcname_}运行了 {_time_}秒'.format(_funcname_=func.__name__, _time_=(end_time - start_time)))
        return res

    # 返回值为函数
    return deco
