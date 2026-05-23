# core/metrics_db.py
import sqlite3
import asyncio
import uuid
from datetime import datetime


class MetricsDB:
    def __init__(self, db_path="core/jarvis_metrics.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. API 项目(密钥)表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')
            # 2. 消耗流水表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT,
                    session_id TEXT,
                    model TEXT,
                    prompt_len INTEGER,
                    completion_len INTEGER,
                    ttft_ms REAL,
                    total_latency_ms REAL,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
                )
            ''')

            cursor.execute("SELECT COUNT(*) FROM api_projects")
            if cursor.fetchone()[0] == 0:
                default_key = f"sk-jarvis-{uuid.uuid4().hex[:16]}"
                cursor.execute("INSERT INTO api_projects (name, api_key) VALUES (?, ?)", ("默认核心项目", default_key))
                print(f"🔑 [系统初始化] 已生成默认 API Key: {default_key}")

            conn.commit()

    async def create_project(self, name: str):
        def _write():
            new_key = f"sk-jarvis-{uuid.uuid4().hex[:16]}"
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("INSERT INTO api_projects (name, api_key) VALUES (?, ?)", (name, new_key))
                conn.commit()
            return {"name": name, "api_key": new_key}

        return await asyncio.to_thread(_write)

    async def delete_project(self, api_key: str):
        def _write():
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("DELETE FROM api_projects WHERE api_key = ?", (api_key,))
                conn.commit()

        await asyncio.to_thread(_write)

    async def list_projects(self):
        def _read():
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor().execute(
                    "SELECT id, name, api_key, created_at FROM api_projects ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]

        return await asyncio.to_thread(_read)

    async def verify_api_key(self, api_key: str) -> bool:
        def _read():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor().execute("SELECT 1 FROM api_projects WHERE api_key = ?", (api_key,))
                return cursor.fetchone() is not None

        return await asyncio.to_thread(_read)

    async def log_request(self, api_key: str, session_id: str, model: str, prompt_len: int, completion_len: int,
                          ttft_ms: float, total_latency_ms: float):
        def _write():
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute('''
                    INSERT INTO usage_logs (api_key, session_id, model, prompt_len, completion_len, ttft_ms, total_latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (api_key, session_id, model, prompt_len, completion_len, ttft_ms, total_latency_ms))
                conn.commit()

        await asyncio.to_thread(_write)

    async def get_dashboard_metrics(self, filter_api_key=None, target_month=None):
        """
        核心重构：支持月份筛选、返回多维账单（日/周/月/总）以及按天聚合的趋势图表数据
        """
        # 默认查询当月
        if not target_month:
            target_month = datetime.now().strftime('%Y-%m')

        def _read():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 动态 SQL 条件
                key_cond = "api_key = ?" if filter_api_key else "1=1"
                params_key = (filter_api_key,) if filter_api_key else ()

                # 辅助函数：根据时间条件聚合模型消耗
                def get_usage(time_cond, time_params):
                    query = f"SELECT model, SUM(prompt_len), SUM(completion_len) FROM usage_logs WHERE {key_cond} AND {time_cond} GROUP BY model"
                    cursor.execute(query, params_key + time_params)

                    ins_in = ins_out = exp_in = exp_out = 0
                    for row in cursor.fetchall():
                        m = row[0].lower()
                        if 'expert' in m:
                            exp_in += row[1] or 0
                            exp_out += row[2] or 0
                        else:
                            ins_in += row[1] or 0
                            ins_out += row[2] or 0
                    return {
                        "instant_prompt": ins_in, "instant_completion": ins_out,
                        "expert_prompt": exp_in, "expert_completion": exp_out
                    }

                # 1. 计算多维度算力账单
                # 全部累计
                total_usage = get_usage("1=1", ())
                # 指定月份
                month_usage = get_usage("strftime('%Y-%m', created_at) = ?", (target_month,))
                # 本周 (基于 SQLite strftime '%Y-%W')
                week_usage = get_usage("strftime('%Y-%W', created_at) = strftime('%Y-%W', 'now', 'localtime')", ())
                # 今日
                today_usage = get_usage("date(created_at) = date('now', 'localtime')", ())

                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 2. X轴按日期(日)聚合，服务于 Token吞吐量图 和 请求计数图
                cursor.execute(f'''
                    SELECT 
                        date(created_at) as dt, 
                        COUNT(id) as req_count, 
                        SUM(prompt_len) as prompt_len, 
                        SUM(completion_len) as completion_len,
                        AVG(ttft_ms) as avg_ttft_ms,
                        AVG(total_latency_ms) as avg_latency_ms
                    FROM usage_logs 
                    WHERE {key_cond} AND strftime('%Y-%m', created_at) = ?
                    GROUP BY dt 
                    ORDER BY dt ASC
                ''', params_key + (target_month,))
                daily_stats = [dict(row) for row in cursor.fetchall()]

                # 3. 指定月份的模型算力调用占比
                cursor.execute(f'''
                    SELECT model, COUNT(*) as count 
                    FROM usage_logs 
                    WHERE {key_cond} AND strftime('%Y-%m', created_at) = ? 
                    GROUP BY model
                ''', params_key + (target_month,))
                model_dist = [dict(row) for row in cursor.fetchall()]

                return {
                    "summary": {
                        "total": total_usage,
                        "month": month_usage,
                        "week": week_usage,
                        "today": today_usage
                    },
                    "daily_stats": daily_stats,
                    "distribution": model_dist,
                    "target_month": target_month
                }

        return await asyncio.to_thread(_read)

    async def clear_all_logs(self):
        def _write():
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().execute("DELETE FROM usage_logs")
                conn.cursor().execute("DELETE FROM sqlite_sequence WHERE name='usage_logs'")
                conn.commit()

        await asyncio.to_thread(_write)