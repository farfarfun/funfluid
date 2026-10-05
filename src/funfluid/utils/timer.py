import time

from funfluid.utils.log import logger


# 定义一个函数用来统计传入函数的运行时间
def timer(func):  # 传入的参数是一个函数
    def deco(*args, **kwargs):  # 本应传入运行函数的各种参数
        logger.debug(f"\n函数:{func.__name__}开始运行:")
        start_time = time.time()  # 调用代运行的函数，并将各种原本的参数传入
        res = func(*args, **kwargs)
        end_time = time.time()
        # 返回值为函数的运行结果
        logger.debug(f"函数:{func.__name__}运行了 {end_time - start_time}秒")
        return res

    # 返回值为函数
    return deco
