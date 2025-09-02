import asyncio
from typing import  List, Optional

import aiohttp
from mockvox.utils import MockVoxLogger
from mockvox.config import get_config

cfg = get_config()

class AsyncNotifier:
    """
    一个使用指数退避策略发送异步HTTP通知的工具类。
    """

    def __init__(
        self,
        retry_delays: Optional[List[int]] = None,
        timeout: int = 3,
        notifier_url: str = cfg.NOTIFIER_URL
    ):
        """
        初始化 AsyncNotifier。

        Args:
            retry_delays (Optional[List[int]]): 
                重试的延迟时间列表（秒）。
                如果为 None，则使用默认值 [15, 15, 30, 60, 180]。
            timeout (int): 请求超时时间（秒）。
        """
        self.retry_delays = retry_delays or [15, 15, 30, 60, 180]
        self.timeout = timeout
        self.notifier_url = notifier_url

    async def _send_request(self, session: aiohttp.ClientSession, url: str, payload: dict) -> bool:
        """
        内部方法，用于发送单个HTTP POST请求。

        Args:
            session (aiohttp.ClientSession): aiohttp 客户端会话。
            url (str): 目标 URL。
            payload (dict): 要发送的 JSON 数据。

        Returns:
            bool: 如果请求成功则返回 True，否则返回 False。
        """
        try:
            async with session.post(url, json=payload, timeout=self.timeout, verify_ssl=False) as response:
                # 如果服务器返回非 2xx 的状态码，则抛出 ClientResponseError 异常
                response.raise_for_status()
                return True
        except aiohttp.ClientError as e:
            MockVoxLogger.error(f"请求失败: {str(e)}")
            return False
        except asyncio.TimeoutError:
            MockVoxLogger.error(f"请求超时: {str(url)}")
            return False

    async def send_notification_with_retry(self, task_id: str, callback_url: str, payload: dict):
        """
        使用指数退避策略异步发送回调通知的核心逻辑。

        Args:
            task_id (str): 任务 ID，用于日志记录。
            callback_url (str): 回调 URL。
            payload (dict): 要作为 JSON 发送的数据。
        """
        target_url = f"{callback_url}?task_id={task_id}"
        MockVoxLogger.info(f"任务 {task_id}: 准备为回调URL {target_url} 发送通知。")

        async with aiohttp.ClientSession() as session:
            for i, delay in enumerate(self.retry_delays):
                attempt = i + 1
                MockVoxLogger.info(f"任务 {task_id}: 正在发送通知 (尝试次数 {attempt}/{len(self.retry_delays)})...")
                
                success = await self._send_request(session, target_url, payload)
                if success:
                    MockVoxLogger.info(f"任务 {task_id}: 回调通知发送成功 (尝试次数 {attempt})。")
                    return  # 成功后立即退出

                MockVoxLogger.warning(f"任务 {task_id}: 回调通知发送失败 (尝试次数 {attempt}/{len(self.retry_delays)})。")

                if i < len(self.retry_delays) - 1:
                    MockVoxLogger.info(f"任务 {task_id}: 将在 {delay} 秒后重试...")
                    await asyncio.sleep(delay)

        MockVoxLogger.error(f"任务 {task_id}: 在所有重试后，回调通知最终发送失败。")

    def notify(self, task_id: str, payload: dict) -> asyncio.Task:
        """
        创建一个后台任务来发送通知，不会阻塞当前代码的执行。

        Args:
            task_id (str): 任务 ID。
            callback_url (str): 回调 URL。
            payload (dict): 要发送的数据。

        Returns:
            asyncio.Task: 创建的后台任务对象。
        """
        return asyncio.create_task(
            self.send_notification_with_retry(task_id, self.notifier_url, payload)
        )
    
notifier = AsyncNotifier(retry_delays=[2, 5, 15])


# --- 使用示例 ---
async def main():
    """
    一个演示如何使用 AsyncNotifier 的异步主函数。
    """
    # 模拟一个 Web 服务器，用于接收回调
    # 在实际使用中，这是一个独立的、一直在运行的服务
    async def mock_server(request):
        # 模拟前几次请求失败
        if mock_server.call_count < 2:
            mock_server.call_count += 1
            MockVoxLogger.info(f"[Mock Server] 收到请求，但返回 500 错误。")
            return aiohttp.web.Response(status=500, text="Internal Server Error")
        
        task_id = request.query.get('task_id', 'N/A')
        data = await request.json()
        MockVoxLogger.info(f"[Mock Server] 成功收到来自 task_id={task_id} 的回调, 数据: {data}")
        return aiohttp.web.Response(text="Callback received")

    mock_server.call_count = 0

    # 设置并运行模拟服务器
    app = aiohttp.web.Application()
    app.router.add_post("/callback", mock_server)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    MockVoxLogger.info("模拟回调服务器已在 http://localhost:8080/callback 启动")

    # ---- notifier 的使用 ----
    
    # 1. 创建 notifier 实例 (使用较短的重试间隔以方便演示)
    notifier = AsyncNotifier(retry_delays=[2, 4, 8])

    # 2. 模拟触发一个需要回调的事件
    task_id = "task-12345"
    callback_payload = {"status": "completed", "result": "some_data.zip"}
    
    # 3. 调用 notify 方法，它会立即返回一个 task 对象，并在后台执行发送逻辑
    MockVoxLogger.info("主程序: 调用 notifier.notify()，开始在后台发送通知。")
    notification_task = notifier.notify(
        task_id=task_id,
        payload=callback_payload
    )

    # 主程序可以继续执行其他任务...
    MockVoxLogger.info("主程序: 继续执行其他任务...")
    await asyncio.sleep(1) # 模拟其他工作
    MockVoxLogger.info("主程序: 其他任务完成。")

    # 等待后台通知任务完成 (可选，仅为演示目的)
    await notification_task
    MockVoxLogger.info("主程序: 演示结束。")

    # 清理服务器
    await runner.cleanup()


#if __name__ == "__main__":
    #try:
    #    asyncio.run(main())
    #except KeyboardInterrupt:
    #    MockVoxLogger.info("程序被用户中断。")