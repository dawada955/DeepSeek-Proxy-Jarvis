# core/gc_manager.py
import os
import json
import asyncio
import time


class GCManager:
    def __init__(self, engine, trash_file="core/trash_bin.json"):
        self.engine = engine
        self.trash_file = trash_file
        self.is_running = False
        self._lock = asyncio.Lock()  # 确保多协程文件写入安全
        self._ensure_trash_file()

    def _ensure_trash_file(self):
        """确保本地垃圾箱文件存在"""
        if not os.path.exists(self.trash_file):
            with open(self.trash_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    async def mark_for_deletion(self, session_id: str):
        """[对外接口] 将废弃会话 ID 异步追加并持久化落盘，防止断电丢失"""
        async with self._lock:
            try:
                # 采用阻塞式文件读写，配合 to_thread 防止完全卡死事件循环
                def _write():
                    with open(self.trash_file, "r+", encoding="utf-8") as f:
                        data = json.load(f)
                        if session_id not in data:
                            data.append(session_id)
                            f.seek(0)
                            f.truncate()
                            json.dump(data, f, ensure_ascii=False, indent=4)

                await asyncio.to_thread(_write)
                print(f"📌 [本地垃圾箱] 成功将废弃会话 {session_id[:8]}... 铭刻至磁盘")
            except Exception as e:
                print(f"❌ [本地垃圾箱] 持久化写入异常: {e}")

    async def start_patrol(self, interval_seconds=300):
        """[生命周期绑定] 后台异步定时巡逻协程"""
        self.is_running = True
        print(f"🧹 [系统守护] 异步清道夫已上线，巡逻周期: {interval_seconds}秒/次")

        while self.is_running:
            await asyncio.sleep(interval_seconds)

            async with self._lock:
                try:
                    with open(self.trash_file, "r", encoding="utf-8") as f:
                        trash_list = json.load(f)

                    if not trash_list:
                        continue

                    print(f"\n🗑️ [清道夫巡逻] 发现本地残留 {len(trash_list)} 个废弃会话，启动战术核平...")

                    success_deleted = []
                    for sid in trash_list:
                        try:
                            # 转换为线程去调用 engine 的同步 requests 阻断删除
                            await asyncio.to_thread(self.engine.delete_chat_session, sid)
                            success_deleted.append(sid)
                            await asyncio.sleep(0.5)  # 顺滑降频，防触发风控
                        except Exception as e:
                            print(f"❌ [清道夫巡逻] 销毁会话 {sid[:8]} 失败: {e}")

                    # 清理成功的部分，更新本地文件
                    remaining = [sid for sid in trash_list if sid not in success_deleted]
                    with open(self.trash_file, "w", encoding="utf-8") as f:
                        json.dump(remaining, f, ensure_ascii=False, indent=4)

                    print(f"✅ [清道夫巡逻] 本轮批量清理完毕，成功销毁 {len(success_deleted)} 个废弃会话。\n")

                except Exception as e:
                    print(f"❌ [清道夫巡逻] 巡逻执行期间发生故障: {e}")