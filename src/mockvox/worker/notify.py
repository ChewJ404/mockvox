from mockvox.engine.v4.inference import Inferencer
from mockvox.utils import i18n,notifier
import soundfile as sf
import torch
import gc
import os
import time
from pathlib import Path
from mockvox.config import OUT_PUT_PATH
from .worker import celeryApp
import asyncio


async def main(task_id:str , data:dict):
    notification_task = notifier.notify(
        task_id=task_id,
        payload=data
    )
    await notification_task

@celeryApp.task(name="notify",ignore_result=True,retry=False)
def notify_task(task_id:str , data:dict):
    asyncio.run(main(task_id, data))
