// server.js
// 运行前请安装依赖: npm install express
const express = require('express');
const app = express();
app.use(express.json());

console.log("==================================================");
console.log("🏭 [暗影兵工厂] Wasm 算力节点初始化中...");
console.log("==================================================");


const solvePow = require('./deepseek_worker_adapted.js');

app.post('/api/solve_pow', async (req, res) => {
    // ⚠️ 关键点：这里直接拿完整的 req.body，不要再去解构 { algorithm, ... } 了！
    const challengeParams = req.body; 
    
    console.log(`\n🎯 [接收指令] 开始强袭算力...`);
    const startTime = Date.now();
    try {
        // 直接透传给黑盒适配器
        const finalPowObject = await solvePow(challengeParams);
        
        const costTime = Date.now() - startTime;
        console.log(`✅ [算力压制] 黑盒计算完成! 耗时: ${costTime}ms`);
        console.log(`🔑 [生成钥匙] `, finalPowObject);
        
        res.json({
            status: "success",
            data: finalPowObject
        });
    } catch (error) {
        console.error(`❌ [计算崩溃] ${error}`);
        res.status(500).json({ status: "error", message: error.toString() });
    }
});

app.listen(3099, () => {
    console.log("🚀 [RPC 服务就绪] 监听端口 3099。等待 Python 脚本调用...");
});