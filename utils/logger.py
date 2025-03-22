import coloredlogs
import logging


def setup_logger():
    """配置并返回日志记录器"""
    coloredlogs.install(
        level='DEBUG',
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        level_styles={
            'debug': {'color': 'green'},
            'info': {'color': 'cyan'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'red', 'bold': True},
        }
    )
    return logging.getLogger(__name__)


# 创建全局日志记录器实例
logger = setup_logger()
