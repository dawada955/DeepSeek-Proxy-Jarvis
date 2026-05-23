# api/routes.py
import time
import json
import httpx
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from core.config import config
from core.ds_engine import DeepSeekEngine
from core.gc_manager import GCManager
from core.metrics_db import MetricsDB
from api.utils import decode_st_squashed_payload

router = APIRouter()

# 单例缓存池
_ds_engine = None
gc_manager = None
metrics_db = None


def get_engine_and_gc():
    global _ds_engine, gc_manager, metrics_db
    if _ds_engine is None:
        _ds_engine = DeepSeekEngine()
        gc_manager = GCManager(_ds_engine)
        metrics_db = MetricsDB()
    return _ds_engine, gc_manager, metrics_db


# ==========================================
# 🔑 核心组件：数据库动态鉴权拦截器
# ==========================================
async def verify_request_auth(request: Request, db: MetricsDB) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    api_key = auth_header.split("Bearer ")[1].strip()

    # 动态查询 SQLite 校验密钥有效性
    is_valid = await db.verify_api_key(api_key)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid API Key. Please create one in Jarvis Dashboard.")

    return api_key


@router.get("/v1/models")
async def list_models(request: Request):
    _, _, db = get_engine_and_gc()

    # 获取并校验多租户密钥 (无需获取具体值，只要合法即可放行)
    await verify_request_auth(request, db)

    # 🌟 完美的矩阵大扩容：支持新一代 V4 与 V4 Pro 的全功能排列
    models = [
        "deepseek-instant",  # 基础极速版 (V4)
        "deepseek-instant-think",  # 极速版 + 深度思考
        "deepseek-expert",  # 专家高级版 (V4 Pro)
        "deepseek-expert-think"  # 专家高级版 + 深度思考 (V4 Pro + R1)
    ]
    return {
        "object": "list",
        "data": [{"id": m, "object": "model", "created": int(time.time()), "owned_by": "jarvis-proxy"} for m in models]
    }


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    engine, gc, db = get_engine_and_gc()

    # 1. 🔑 租户鉴权拦截，并提取合法客户端的 API Key
    client_api_key = await verify_request_auth(request, db)

    raw_messages = body.get("messages", [])
    if not raw_messages:
        raise HTTPException(status_code=400, detail="Empty messages")

    # 2. 动态清洗压缩载荷
    messages = decode_st_squashed_payload(body, raw_messages)
    is_stream = body.get("stream", False)

    # 🧠 全火力算力路由解析
    requested_model = body.get("model", "deepseek-instant")
    is_expert = "expert" in requested_model
    is_thinking = "think" in requested_model
    is_search = "search" in requested_model

    print(
        f"\n🚀 [算力路由] 租户: {client_api_key[:12]}... | 分配模型: {'Expert(V4 Pro)' if is_expert else 'Instant(V4)'} | 深度思考: {'ON' if is_thinking else 'OFF'} | 模式: {'Stream' if is_stream else 'Block'}")

    try:
        combat_headers = engine.get_combat_headers()

        # 3. 建立纯管道无状态频段
        session_id = engine.create_new_chat_session()
        actual_prompt = "\n".join([f"{m.get('role', 'none')}: {m.get('content', '')}" for m in messages])

        payload = {
            "chat_session_id": session_id,
            "parent_message_id": None,
            "prompt": actual_prompt,
            "model_type": "expert" if is_expert else "default",
            "thinking_enabled": is_thinking,
            "search_enabled": is_search,
            "ref_file_ids": []
        }

        # ⏱️ 埋点 1：记录起点时间戳与输入长度
        start_time = time.time()
        prompt_length = len(actual_prompt)

        # 4. 跨周期异步垃圾池与性能落盘钩子
        async def drop_into_trash_hook(final_completion_length, ttft_time):
            # 计算延迟指标
            total_latency = (time.time() - start_time) * 1000
            ttft_ms = (ttft_time - start_time) * 1000 if ttft_time else total_latency

            try:
                # 📊 将监控数据推送到 SQLite (高度解耦，绑定对应的 API Key)
                await db.log_request(
                    api_key=client_api_key,  # 👈 核心修复：注入多租户 Key
                    session_id=session_id,
                    model=requested_model,
                    prompt_len=prompt_length,
                    completion_len=final_completion_length,
                    ttft_ms=round(ttft_ms, 2),
                    total_latency_ms=round(total_latency, 2)
                )

                # 🏷️ 覆盖官方会话标题 (标题带有租户特征段，方便从官网抓包排查)
                full_datetime = time.strftime('%Y-%m-%d %H:%M:%S')
                model_label = "Exp" if is_expert else "Ins"
                think_label = "-R1" if is_thinking else ""
                custom_title = f"🤖 [{client_api_key[10:14]}] {model_label}{think_label} {full_datetime}"
                await asyncio.to_thread(engine.update_session_title, session_id, custom_title)
            except Exception as e:
                print(f"⚠️ [钩子执行异常] {e}")

            # 无论如何，推入销毁队列
            await gc.mark_for_deletion(session_id)

        # ==========================================
        # 通道 A: 极速流式链路 (原生标准 reasoning_content 分流转发)
        # ==========================================
        if is_stream:
            async def real_event_generator():
                state_machine = {"current_type": "RESPONSE"}  # 独占状态机
                first_token_time = None  # ⏱️ 埋点 2：首字时间戳
                total_completion_len = 0  # 统计输出长度

                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", f"{config.DS_API_BASE}/completion", headers=combat_headers,
                                             json=payload, timeout=120.0) as response:
                        if response.status_code != 200:
                            yield f"data: {json.dumps({'error': f'API Error: {response.status_code}'})}\n\n"
                            return

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    yield "data: [DONE]\n\n"
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    if not isinstance(chunk, dict): continue

                                    token_content = ""

                                    # 🔍 阶段一：截获首包状态声明
                                    if "v" in chunk and isinstance(chunk["v"], dict) and "response" in chunk["v"]:
                                        fragments = chunk["v"]["response"].get("fragments", [])
                                        if fragments:
                                            frag_type = fragments[0].get("type", "RESPONSE")
                                            state_machine["current_type"] = frag_type
                                            token_content = fragments[0].get("content", "")

                                    # 🔍 阶段二：截获思维跃迁锚点
                                    elif chunk.get("p") == "response/fragments" and chunk.get("o") == "APPEND":
                                        new_frags = chunk.get("v", [])
                                        if new_frags:
                                            frag_type = new_frags[0].get("type", "RESPONSE")
                                            token_content = new_frags[0].get("content", "")
                                            state_machine["current_type"] = frag_type

                                    # 🔍 阶段三：提取流式持续输出
                                    elif "v" in chunk and isinstance(chunk["v"], str):
                                        p_val = chunk.get("p")
                                        if p_val is None or "content" in str(p_val):
                                            token_content = chunk["v"]

                                    # 📤 完美封装：尊重原生标准协议
                                    if token_content:
                                        # ⏱️ 记录首字到达时间
                                        if first_token_time is None:
                                            first_token_time = time.time()

                                        total_completion_len += len(token_content)

                                        delta_payload = {}
                                        if state_machine["current_type"] == "THINK":
                                            delta_payload["reasoning_content"] = token_content
                                        else:
                                            delta_payload["content"] = token_content

                                        openai_chunk = {
                                            "id": f"chatcmpl-{int(time.time())}",
                                            "object": "chat.completion.chunk",
                                            "choices": [{"delta": delta_payload}]
                                        }
                                        yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"

                                        # 本地控制台高亮辅助 (灰色代表正在思考，绿色/默认代表正式输出)
                                        if state_machine["current_type"] == "THINK":
                                            print(f"\033[90m{token_content}\033[0m", end="", flush=True)
                                        else:
                                            print(token_content, end="", flush=True)

                                except json.JSONDecodeError:
                                    pass

                # 触发后台异步清理和数据落盘
                asyncio.create_task(drop_into_trash_hook(total_completion_len, first_token_time))
                print("\n✅ [网关转发] 流传输结束。")

            return StreamingResponse(real_event_generator(), media_type="text/event-stream")


        # ==========================================
        # 通道 B: 阻塞全量打包 (标准无状态分池双蓄水)
        # ==========================================
        else:
            full_content = ""
            reasoning_content = ""  # 🧠 独立的思维链蓄水池
            state_machine = {"current_type": "RESPONSE"}

            print("⏳ [网关转发] ST 前端要求全量数据，正在后台静默蓄水...")
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{config.DS_API_BASE}/completion", headers=combat_headers,
                                         json=payload, timeout=120.0) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail="DeepSeek 接口报错")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]": break
                            try:
                                chunk = json.loads(data_str)
                                if not isinstance(chunk, dict): continue
                                token_content = ""

                                if "v" in chunk and isinstance(chunk["v"], dict) and "response" in chunk["v"]:
                                    fragments = chunk["v"]["response"].get("fragments", [])
                                    if fragments:
                                        frag_type = fragments[0].get("type", "RESPONSE")
                                        state_machine["current_type"] = frag_type
                                        token_content = fragments[0].get("content", "")

                                elif chunk.get("p") == "response/fragments" and chunk.get("o") == "APPEND":
                                    new_frags = chunk.get("v", [])
                                    if new_frags:
                                        frag_type = new_frags[0].get("type", "RESPONSE")
                                        token_content = new_frags[0].get("content", "")
                                        state_machine["current_type"] = frag_type

                                elif "v" in chunk and isinstance(chunk["v"], str):
                                    p_val = chunk.get("p")
                                    if p_val is None or "content" in str(p_val):
                                        token_content = chunk["v"]

                                # 📥 按状态打入专属池子
                                if token_content:
                                    if state_machine["current_type"] == "THINK":
                                        reasoning_content += token_content
                                    else:
                                        full_content += token_content
                                    print(".", end="", flush=True)

                            except json.JSONDecodeError:
                                pass

            print(f"\n✅ [网关转发] 蓄水完成，正文: {len(full_content)} 字，思维链: {len(reasoning_content)} 字！")

            # 计算总长度，执行阻塞模式落盘清理
            total_len = len(full_content) + len(reasoning_content)
            await drop_into_trash_hook(final_completion_length=total_len, ttft_time=None)

            # 组装尊贵、标准的带 reasoning_content 非流式实体
            message_dict = {"role": "assistant", "content": full_content}
            if reasoning_content:
                message_dict["reasoning_content"] = reasoning_content

            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": requested_model,
                "choices": [{
                    "index": 0,
                    "message": message_dict,
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    except Exception as e:
        print(f"\n❌ [网关转发报错] {e}")
        raise HTTPException(status_code=500, detail=str(e))