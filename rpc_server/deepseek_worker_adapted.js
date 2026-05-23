// deepseek_worker_adapted.js
const fs = require('fs');
const path = require('path');
const util = require('util'); // 引入 util 处理文本编码

console.log("🛠️ [适配器] 正在构建伪装浏览器环境...");

// ==========================================
// 0. 植入最高级别“探照灯”（捕获所有静默错误）
// ==========================================
process.on('uncaughtException', (err) => {
    console.error("\n💥 [系统崩溃] 捕获到未处理的致命异常:", err);
});
process.on('unhandledRejection', (reason, promise) => {
    console.error("\n💥 [系统崩溃] Wasm或胶水代码中发生 Promise 静默拒绝:", reason);
});

// ==========================================
// 1. 植入伪造的浏览器维生系统 (火力全开版)
// ==========================================
global.self = global;      
global.window = global;    
global.document = {};
global.navigator = { userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" };
global.location = { href: "https://chat.deepseek.com/worker.js", origin: "https://chat.deepseek.com", toString: function() { return this.href; } };

// 【关键补丁】：Wasm-bindgen 强依赖的底层 API，Node.js 默认不在全局提供！
global.TextEncoder = util.TextEncoder;
global.TextDecoder = util.TextDecoder;
global.crypto = require('crypto').webcrypto; // 提供加密硬件支持
global.performance = require('perf_hooks').performance; // 提供精准计时

// 拦截 Webpack chunk 请求
global.importScripts = function(...urls) {
    console.log("⚠️ [适配器] 拦截到 Webpack 尝试加载外部模块: ", urls);
    urls.forEach(url => {
        if (url.includes('60816')) {
            console.log("📥 [适配器] 正在欺骗引擎，注入本地下载的 chunk 模块...");
            try {
                const chunkCode = fs.readFileSync(path.resolve(__dirname, './pom_ds_code/60816_worker_chunk.js'), 'utf-8');
                eval(chunkCode);
                console.log("✅ [适配器] 本地 chunk 模块注入成功！");
            } catch (err) {
                console.error("❌ [适配器] 注入 chunk 失败！", err);
            }
        }
    });
};

// 捕获监听器
let capturedWorkerListener = null;
global.addEventListener = function(type, listener) {
    if (type === 'message') {
        capturedWorkerListener = listener;
        console.log("🔗 [适配器] 成功捕获敌方 addEventListener('message')");
    }
};
Object.defineProperty(global, 'onmessage', {
    set: function(listener) {
        capturedWorkerListener = listener;
        console.log("🔗 [适配器] 成功捕获敌方 self.onmessage");
    }
});

// 拦截 Wasm
const originalInstantiateStreaming = WebAssembly.instantiateStreaming;
WebAssembly.instantiateStreaming = async (response, imports) => {
    console.log("🪤 [适配器] 拦截到 Wasm 流式加载，正在挂载本地黑盒...");
    try {
        const wasmBuffer = fs.readFileSync(path.resolve(__dirname, './pom_ds_code/deepseek_pow.wasm'));
        const result = await WebAssembly.instantiate(wasmBuffer, imports);
        // 【关键探针】：确认黑盒彻底加载完毕！
        console.log("✅✅✅ [核心突破] Wasm 黑盒底层实例化彻底完成！"); 
        return result;
    } catch (e) {
        console.error("❌ [灾难] Wasm 实例化失败，可能是版本或内存问题：", e);
        throw e;
    }
};

let pendingResolve = null;
let pendingReject = null;

global.postMessage = function(msg) {
    if (msg.type === "pow-answer" && pendingResolve) {
        // 截胡整个大对象！里面包含了 Wasm 算出来的终极签名 (signature)
        console.log(`📦 [适配器] 成功截胡终极通行证，耗时卓越！`);
        pendingResolve(msg.answer); 
        pendingResolve = null;
    } else if (msg.type === "pow-error" && pendingReject) {
        console.error(`💥 [敌方上报错误] 内部算法崩溃:`, msg.error);
        pendingReject(msg.error);
        pendingReject = null;
    }
};

try {
    require('./pom_ds_code/original_worker.js');
    console.log("✅ [适配器] 完整版胶水代码加载完毕，已解除武装。");
} catch (e) {
    console.error("❌ [适配器] 加载异常：", e);
}

// ==========================================
// 3. 封装为我方 API (全透传版)
// ==========================================
module.exports = function solvePow(challengeParams) {
    return new Promise((resolve, reject) => {
        if (!capturedWorkerListener) return reject("❌ 未抓取到敌方监听器");

        pendingResolve = resolve;
        pendingReject = reject;
        
        // 🔮 魔法时刻：给数据包套上窃听器
        const handler = {
            get: function(target, prop) {
                // 排除一些系统自带的内部方法读取，只监听核心字符串属性
                if (typeof prop === 'string' && prop !== 'toJSON') {
                    const value = target[prop];
                    if (value === undefined) {
                        console.log(`🚨 [Proxy 警报] 敌方代码试图读取【不存在】的字段: >>> ${prop} <<<`);
                    } else {
                        console.log(`🕵️ [Proxy 探针] 敌方代码成功读取了字段: ${prop} = ${value}`);
                    }
                }
                return target[prop];
            }
        };
        
        // 伪造包裹，内部包裹 Proxy
        const exactPayload = {
            type: "pow-challenge",
            challenge: new Proxy(challengeParams, handler)
        };

        console.log("⚡ [适配器] 带有窃听器的弹药已装填，发射！");
        capturedWorkerListener({ data: exactPayload });
    });
};