# api/dashboard.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from core.metrics_db import MetricsDB

router = APIRouter()
db = MetricsDB()


class ProjectCreate(BaseModel):
    name: str


@router.get("/api/metrics")
async def get_metrics(api_key: str = None, target_month: str = None):
    data = await db.get_dashboard_metrics(filter_api_key=api_key, target_month=target_month)
    return {"status": "success", "data": data}


@router.delete("/api/metrics")
async def clear_metrics():
    await db.clear_all_logs()
    return {"status": "success"}


@router.get("/api/projects")
async def list_projects():
    projects = await db.list_projects()
    return {"status": "success", "data": projects}


@router.post("/api/projects")
async def create_project(req: ProjectCreate):
    proj = await db.create_project(req.name)
    return {"status": "success", "data": proj}


@router.delete("/api/projects/{api_key}")
async def delete_project(api_key: str):
    await db.delete_project(api_key)
    return {"status": "success"}


@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Jarvis 企业级算力总署</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
        <style>
            :root {
                --bg-color: #f0f2f5; --card-bg: #ffffff; --text-main: #1f1f1f; --text-muted: #8c8c8c;
                --primary: #1677ff; --success: #52c41a; --warning: #faad14; --danger: #ff4d4f;
                --expert-color: #722ed1; --instant-color: #13c2c2;
                --border-radius: 8px; --shadow: 0 2px 8px rgba(0,0,0,0.06);
            }
            body { 
                background: var(--bg-color); color: var(--text-main); 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                margin: 0; padding: 16px; box-sizing: border-box;
                height: 100vh; overflow: hidden; /* PC端默认锁死全屏 */
                display: flex; flex-direction: column; gap: 16px;
            }

            .header-bar { 
                flex: 0 0 auto; display: flex; justify-content: space-between; align-items: center; 
                background: var(--card-bg); padding: 12px 20px; border-radius: var(--border-radius); box-shadow: var(--shadow); 
            }
            h1 { margin: 0; font-size: 20px; font-weight: 700; color: var(--primary); }
            .selectors { display: flex; align-items: center; gap: 12px; font-size: 14px;}
            select, button, input { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; outline: none; transition: 0.3s; }
            select:focus, input:focus { border-color: var(--primary); }
            button { background: var(--primary); color: white; border: none; cursor: pointer; font-weight: 500; }
            button:hover { opacity: 0.8; }
            button.danger { background: transparent; color: var(--danger); border: 1px solid var(--danger); }
            button.danger:hover { background: var(--danger); color: white; }

            .billing-panel {
                flex: 0 0 auto; display: flex; gap: 16px;
            }
            .price-editor {
                flex: 0 0 320px; background: var(--card-bg); padding: 30px 20px; border-radius: var(--border-radius); box-shadow: var(--shadow);
                display: flex; flex-direction: column; justify-content: space-between;
            }
            .price-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; margin-bottom: 12px;}
            .price-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; align-items: center;}
            .price-input { width: 45px; padding: 2px 4px; text-align: right; background: #f5f5f5; border: 1px solid transparent; font-weight: bold; color: var(--primary);}
            .price-input:disabled { background: transparent; color: var(--text-main); }
            .price-input:focus { border: 1px solid var(--primary); background: #fff;}

            .bills-grid {
                flex: 1; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
            }
            .bill-card {
                background: var(--card-bg); padding: 20px; border-radius: var(--border-radius); box-shadow: var(--shadow);
                display: flex; flex-direction: column; justify-content: center;
                border-top: 3px solid var(--primary);
            }
            .bill-card:nth-child(1) { border-top-color: #36cfc9; }
            .bill-card:nth-child(2) { border-top-color: #9254de; }
            .bill-card:nth-child(3) { border-top-color: #1677ff; }
            .bill-card:nth-child(4) { border-top-color: #ff4d4f; }
            .bill-title { color: var(--text-muted); font-size: 16px; margin-bottom: 15px; font-weight: 600;}
            .bill-val { font-size: 24px; font-weight: 800; color: var(--text-main);}
            .bill-card:nth-child(4) .bill-val { color: var(--danger); }

            .main-content {
                flex: 1 1 auto; display: grid; grid-template-columns: 740px 750px 1fr; gap: 16px; min-height: 0;
            }
            .chart-card {
                background: var(--card-bg); padding: 16px; border-radius: var(--border-radius); box-shadow: var(--shadow);
                height: 95%; box-sizing: border-box;
            }

            .project-list-box {
                background: var(--card-bg); border-radius: var(--border-radius); box-shadow: var(--shadow); 
                display: flex; flex-direction: column; height: 95%;
            }
            .project-list-header { padding: 12px 16px; border-bottom: 1px solid #f0f0f0; font-weight: 600; display: flex; justify-content: space-between; align-items: center;}
            .project-items { flex: 1; overflow-y: auto; padding: 12px; }
            .proj-item { padding: 10px; border: 1px solid #f0f0f0; border-radius: 6px; margin-bottom: 8px; font-size: 12px; }
            .proj-name { font-weight: 700; margin-bottom: 4px; color: var(--primary); }
            .proj-key { font-family: monospace; color: var(--text-muted); background: #f5f5f5; padding: 2px 4px; border-radius: 4px; word-break: break-all; }

            .custom-tooltip { font-family: monospace; line-height: 1.5; color: #1f1f1f; font-size: 12px;}

            /* ========================================================= */
            /* 📱 移动端/安卓响应式适配 (当屏幕宽度 <= 992px 触发) */
            /* ========================================================= */
            @media (max-width: 992px) {
                body {
                    height: auto; /* 解除高度锁定，允许页面纵向滚动 */
                    overflow-y: auto;
                    padding: 10px;
                }

                /* 头部导航折叠 */
                .header-bar {
                    flex-direction: column;
                    align-items: stretch;
                    gap: 12px;
                }
                .selectors {
                    flex-direction: column;
                    align-items: stretch;
                }
                .selectors select, .selectors button {
                    width: 100%; /* 按钮和下拉框撑满屏幕 */
                    margin: 4px 0 !important;
                }
                .separator { display: none; } /* 隐藏竖线分隔符 */

                /* 计费面板折叠 */
                .billing-panel {
                    flex-direction: column;
                }
                .price-editor {
                    flex: auto; width: 100%; box-sizing: border-box;
                }
                .bills-grid {
                    grid-template-columns: repeat(2, 1fr); /* 手机端账单改为 2x2 网格 */
                }
                .bill-val { font-size: 20px; } /* 稍微缩小字体防溢出 */

                /* 图表与项目列表重排 */
                .main-content {
                    display: flex; /* 改用 Flex 列堆叠 */
                    flex-direction: column;
                }
                .chart-card, .project-list-box {
                    height: 380px; /* 为每个卡片赋予固定高度，以便在滚动中正常渲染 */
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="header-bar">
            <h1>🦾 Jarvis 算力观测台</h1>
            <div class="selectors">
                <label>📅 月份：</label>
                <select id="monthSelector" onchange="fetchData()"></select>
                <span class="separator" style="margin: 0 8px; color:#eee;">|</span>
                <label>📊 视角：</label>
                <select id="viewSelector" onchange="fetchData()">
                    <option value="">全部项目 (全局汇总)</option>
                </select>
                <button class="danger" style="margin-left:12px;" onclick="clearAllData()">🗑️ 清空大盘</button>
            </div>
        </div>

        <div class="billing-panel">
            <div class="price-editor">
                <div class="price-header">
                    <span>💳 单价配置 (￥/1M Token)</span>
                    <button id="priceEditBtn" onclick="togglePriceEdit()" style="padding: 2px 8px; font-size: 12px;">⚙️ 修改</button>
                </div>
                <div class="price-row">
                    <span style="color:var(--instant-color)">⚡ Instant 输入/输出</span>
                    <div>
                        <input class="price-input" id="p_ins_in" type="number" step="0.1" disabled> / 
                        <input class="price-input" id="p_ins_out" type="number" step="0.1" disabled>
                    </div>
                </div>
                <div class="price-row">
                    <span style="color:var(--expert-color)">🧠 Expert 输入/输出</span>
                    <div>
                        <input class="price-input" id="p_exp_in" type="number" step="0.1" disabled> / 
                        <input class="price-input" id="p_exp_out" type="number" step="0.1" disabled>
                    </div>
                </div>
            </div>

            <div class="bills-grid">
                <div class="bill-card">
                    <div class="bill-title">日账单 </div>
                    <div class="bill-val" id="cost-today">￥0.00</div>
                </div>
                <div class="bill-card">
                    <div class="bill-title">周账单 </div>
                    <div class="bill-val" id="cost-week">￥0.00</div>
                </div>
                <div class="bill-card">
                    <div class="bill-title">月账单 </div>
                    <div class="bill-val" id="cost-month">￥0.00</div>
                </div>
                <div class="bill-card">
                    <div class="bill-title">🔥 历史总计账单</div>
                    <div class="bill-val" id="cost-total">￥0.00</div>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="chart-card" id="tokenChart"></div>
            <div class="chart-card" id="reqChart"></div>

            <div class="project-list-box">
                <div class="project-list-header">
                    <span>🔑 API 项目管理</span>
                    <button onclick="createNewProject()" style="padding: 2px 6px; font-size: 12px;">+ 新建</button>
                </div>
                <div class="project-items" id="projectList"></div>
            </div>
        </div>

        <script>
            const tokenChart = echarts.init(document.getElementById('tokenChart'));
            const reqChart = echarts.init(document.getElementById('reqChart'));

            let globalData = null;
            let isEditingPrice = false;

            function initPrices() {
                const defaults = { p_ins_in: '1.0', p_ins_out: '2.0', p_exp_in: '10.0', p_exp_out: '20.0' };
                for (let k in defaults) {
                    const saved = localStorage.getItem(k);
                    document.getElementById(k).value = saved !== null ? saved : defaults[k];
                }
            }

            function togglePriceEdit() {
                const inputs = document.querySelectorAll('.price-input');
                const btn = document.getElementById('priceEditBtn');
                if (isEditingPrice) {
                    inputs.forEach(i => { i.disabled = true; localStorage.setItem(i.id, i.value); });
                    btn.innerText = '⚙️ 修改';
                    btn.style.background = 'var(--primary)';
                    isEditingPrice = false;
                    renderBills(); 
                } else {
                    inputs.forEach(i => i.disabled = false);
                    btn.innerText = '💾 保存';
                    btn.style.background = 'var(--success)';
                    isEditingPrice = true;
                }
            }

            function calcCost(usageObj) {
                if(!usageObj) return 0;
                const pi = parseFloat(document.getElementById('p_ins_in').value) || 0;
                const po = parseFloat(document.getElementById('p_ins_out').value) || 0;
                const ei = parseFloat(document.getElementById('p_exp_in').value) || 0;
                const eo = parseFloat(document.getElementById('p_exp_out').value) || 0;

                return (usageObj.instant_prompt / 1e6) * pi + 
                       (usageObj.instant_completion / 1e6) * po + 
                       (usageObj.expert_prompt / 1e6) * ei + 
                       (usageObj.expert_completion / 1e6) * eo;
            }

            function renderBills() {
                if(!globalData) return;
                document.getElementById('cost-today').innerText = '￥' + calcCost(globalData.summary.today).toFixed(2);
                document.getElementById('cost-week').innerText = '￥' + calcCost(globalData.summary.week).toFixed(2);
                document.getElementById('cost-month').innerText = '￥' + calcCost(globalData.summary.month).toFixed(2);
                document.getElementById('cost-total').innerText = '￥' + calcCost(globalData.summary.total).toFixed(2);
            }

            function initMonthSelector() {
                const sel = document.getElementById('monthSelector');
                const d = new Date();
                for(let i=0; i<12; i++) {
                    let m = d.getMonth() + 1;
                    let y = d.getFullYear();
                    let val = y + '-' + (m < 10 ? '0'+m : m);
                    sel.add(new Option(val, val));
                    d.setMonth(d.getMonth() - 1); 
                }
            }

            async function loadProjects() {
                const res = await fetch('/api/projects');
                const json = await res.json();
                const sel = document.getElementById('viewSelector');
                const listDiv = document.getElementById('projectList');

                const currentVal = sel.value;
                sel.innerHTML = '<option value="">全部项目 (全局汇总)</option>';
                listDiv.innerHTML = '';

                json.data.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.api_key; opt.text = p.name;
                    if(p.api_key === currentVal) opt.selected = true;
                    sel.add(opt);

                    listDiv.innerHTML += `
                        <div class="proj-item">
                            <div class="proj-name">${p.name}</div>
                            <div class="proj-key">${p.api_key}</div>
                            <div style="text-align:right; margin-top:6px;">
                                <button class="danger" style="padding:2px 6px; font-size:12px;" onclick="deleteProject('${p.api_key}')">删除</button>
                            </div>
                        </div>
                    `;
                });
            }

            async function createNewProject() {
                const name = prompt("请输入新 API 租户名称：");
                if(!name) return;
                await fetch('/api/projects', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: name}) });
                await loadProjects();
            }

            async function deleteProject(key) {
                if(!confirm("确定吊销此 Key 吗？数据保留，但无法再请求。")) return;
                await fetch(`/api/projects/${key}`, { method: 'DELETE' });
                await loadProjects();
                fetchData();
            }

            async function clearAllData() {
                if(!confirm("⚠️ 危险操作：将永久删除所有日志，Token与金额归零（保留密钥）。确定清空？")) return;
                await fetch('/api/metrics', { method: 'DELETE' });
                fetchData(); 
            }

            async function fetchData() {
                const apiKey = document.getElementById('viewSelector').value;
                const month = document.getElementById('monthSelector').value;

                let url = `/api/metrics?target_month=${month}`;
                if(apiKey) url += `&api_key=${apiKey}`;

                const res = await fetch(url);
                const json = await res.json();
                globalData = json.data;

                renderBills();

                const stats = globalData.daily_stats || [];
                const dates = stats.map(i => i.dt);

                // --- 图表1：Token吞吐量 ---
                tokenChart.setOption({
                    title: { text: '📦 Token 吞吐趋势', textStyle: { fontSize: 14 } },
                    tooltip: { 
                        trigger: 'axis', axisPointer: { type: 'shadow'},
                        formatter: function (params) {
                            let d = stats[params[0].dataIndex];
                            let avgTtft = (d.avg_ttft_ms / 1000).toFixed(2);
                            let avgTotal = (d.avg_latency_ms / 1000).toFixed(2);
                            return `<div class="custom-tooltip">
                                <b>📅 ${d.dt}</b><br/><hr style="margin:4px 0">
                                上行: ${d.prompt_len} tk<br/>
                                下行: ${d.completion_len} tk<br/>
                                平均首字: ${avgTtft}s<br/>
                                平均耗时: ${avgTotal}s
                            </div>`;
                        }
                    },
                    legend: { data: ['输入', '输出'], top: 0, right: 0, itemSize: 10 },
                    grid: { left: '3%', right: '3%', bottom: '3%', top: '35px', containLabel: true },
                    xAxis: { type: 'category', data: dates },
                    yAxis: { type: 'value' },
                    series: [
                        { name: '输入', type: 'bar', stack: 'T', barMaxWidth: 50, itemStyle: {color:'#1677ff', borderRadius: [0,0,0,0]}, data: stats.map(i => i.prompt_len) },
                        { name: '输出', type: 'bar', stack: 'T', barMaxWidth: 50, itemStyle: {color:'#722ed1', borderRadius: [4,4,0,0]}, data: stats.map(i => i.completion_len) }
                    ]
                });

                // --- 图表2：请求计数器 ---
                reqChart.setOption({
                    title: { text: '📈 请求频次流速 (Req/日)', textStyle: { fontSize: 14 } },
                    tooltip: { trigger: 'axis' },
                    grid: { left: '3%', right: '3%', bottom: '3%', top: '35px', containLabel: true },
                    xAxis: { type: 'category', data: dates, boundaryGap: false },
                    yAxis: { 
                        type: 'value', 
                        minInterval: 1, 
                        max: function (value) {
                            return value.max < 5 ? 5 : undefined;
                        }
                    },
                    series: [
                        { 
                            name: '请求次数', type: 'line', smooth: true, 
                            itemStyle: {color:'#52c41a'}, areaStyle: { color: 'rgba(82,196,26,0.2)' },
                            data: stats.map(i => i.req_count) 
                        }
                    ]
                });
            }

            initPrices();
            initMonthSelector();
            loadProjects().then(fetchData);

            setInterval(fetchData, 10000);
            window.addEventListener('resize', () => {
                tokenChart.resize();
                reqChart.resize();
            });
        </script>
    </body>
    </html>
    """
    return html_content