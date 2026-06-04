# 3D 平面立方体绘制

一个 Vue + Three.js + FastAPI 的前后端练习项目。前端先创建一个大平面，再通过函数输入平面相对坐标和高度，在对应位置生成立方体；后端提供初始立方体数据和新增立方体接口。

## 技术栈

| 部分 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Three.js |
| 后端 | Python + FastAPI + Uvicorn |
| 接口数据 | 内存列表，适合先学习接口调用 |

## 目录

```text
frontend/        Vue + Three.js 前端
backend/main.py  FastAPI 后端入口
```

## 安装依赖

前端：

```bash
cd /Users/wangyiqiu/Desktop/programe/3D/frontend
pnpm install
```

后端：

```bash
cd /Users/wangyiqiu/Desktop/programe/3D/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动后端

```bash
cd /Users/wangyiqiu/Desktop/programe/3D/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

```text
http://localhost:8000
```

检查接口：

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/cubes
```

## 启动前端

```bash
cd /Users/wangyiqiu/Desktop/programe/3D/frontend
pnpm dev
```

浏览器打开：

```text
http://localhost:5173
```

Vite 会把前端的 `/api` 请求代理到 `http://localhost:8000`。

## 核心绘制函数

核心函数在 [frontend/src/App.vue](/Users/wangyiqiu/Desktop/programe/3D/frontend/src/App.vue)：

```js
function addCubeAt(relativeX, relativeZ, height, options = {}) {
  // relativeX 和 relativeZ 的范围是 -1 到 1
  // -1 表示平面负方向边缘，0 表示中心，1 表示正方向边缘
}
```

接口数据格式：

```json
{
  "name": "立方体",
  "x": 0.2,
  "z": -0.4,
  "height": 2,
  "color": "#2563eb"
}
```

手动新增一个立方体：

```bash
curl -X POST http://localhost:8000/api/cubes \
  -H "Content-Type: application/json" \
  -d '{"name":"测试立方体","x":0.25,"z":-0.3,"height":2.6,"color":"#7c3aed"}'
```
