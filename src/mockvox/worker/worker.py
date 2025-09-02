from celery import Celery
from mockvox.config import celery_config
import os
import torch
from mockvox.utils import MockVoxLogger

os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")


device_info = {
    "PyTorch 版本": torch.__version__,
    "CUDA 可用": torch.cuda.is_available(),
    "CUDA 设备数": 0,
    "当前设备": "无可用CUDA设备"
}
if device_info["CUDA 可用"]:
    MockVoxLogger.info(
        f"print PyTorch and CUDA info PyTorch 版本: {torch.__version__}, CUDA 可用: {torch.cuda.is_available()}, CUDA 设备数: {torch.cuda.device_count()}, 当前设备: {torch.cuda.get_device_name(0)}",
        extra={
            "PyTorch 版本": torch.__version__,
            "CUDA 可用": torch.cuda.is_available(),
            "CUDA 设备数": torch.cuda.device_count(),
            "当前设备": torch.cuda.get_device_name(0)
        }
    )
else:
    MockVoxLogger.warning(
        "当前无可用CUDA设备，推理和训练速度可能较慢。",
        extra=device_info
    )
celeryApp = Celery("worker")
celeryApp.config_from_object(celery_config)
celeryApp.conf.update(worker_hijack_root_logger=False)

celeryApp.autodiscover_tasks()