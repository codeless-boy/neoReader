# NeoReader

NeoReader 是一个轻量级的基于 Web 的电子书管理与阅读系统。

## 功能特性

- **书籍管理**：支持上传、查看、删除 TXT 格式的电子书。
- **自动编码识别**：后端自动检测 TXT 文件编码（如 UTF-8, GBK, ASCII），解决中文乱码问题。
- **在线阅读**：
  - 分页加载机制，流畅阅读大文件。
  - 支持字号调整（12px - 32px）。
  - 支持主题切换（亮色、暗色、护眼模式）。
- **响应式界面**：基于 Vue 3 + Element Plus 构建，包含侧边栏导航和自适应布局。

## 技术栈

- **后端**：Python 3.11+, FastAPI, SQLModel (SQLite), aiofiles, chardet
- **前端**：Vue 3, TypeScript, Vite, Element Plus, Pinia, Vue Router

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd neoReader
```

### 2. 后端启动

建议使用虚拟环境运行后端。

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
# 激活虚拟环境 (Linux/macOS)
# source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 启动后端服务
# 注意：在项目根目录下运行
python -m uvicorn backend.app.main:app --reload --port 8000
```

后端 API 文档地址：[http://localhost:8000/docs](http://localhost:8000/docs)

### 3. 前端启动

请确保已安装 Node.js (推荐 v18+)。

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端访问地址：[http://localhost:5173/](http://localhost:5173/)

## 目录结构

```
neoReader/
├── backend/            # 后端代码
│   ├── app/            # 应用核心逻辑
│   │   ├── api/        # API 路由
│   │   ├── utils/      # 工具函数 (文件处理等)
│   │   ├── models.py   # 数据库模型
│   │   └── main.py     # 入口文件
│   ├── static/         # 静态文件 (上传的书籍)
│   └── requirements.txt
├── frontend/           # 前端代码
│   ├── src/
│   │   ├── api/        # API 接口封装
│   │   ├── layouts/    # 布局组件
│   │   ├── views/      # 页面视图
│   │   └── router/     # 路由配置
│   └── package.json
└── README.md
```

## 注意事项

- 目前仅支持 `.txt` 格式文件。
- 默认上传文件存储在 `backend/static/uploads` 目录下。
- 数据库使用 SQLite，文件位于根目录 `database.db`。
