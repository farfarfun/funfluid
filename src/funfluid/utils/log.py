"""funfluid 统一日志入口，基于 farlog，不在 import 时配置全局 handler。"""

from farlog import getLogger

logger = getLogger("funfluid")
