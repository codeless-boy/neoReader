# 电子书管理系统设计方案 (TXT 专用版)

## 1. 项目概述
本项目旨在构建一个基于 Web 的轻量级电子书管理系统，**当前阶段仅支持 TXT 格式**电子书的管理与阅读。
- **前端**: Vue 3 + Vite + Element Plus
- **后端**: Python + FastAPI + SQLModel (SQLAlchemy + Pydantic)
- **数据库**: SQLite (默认)

## 2. 系统功能模块
1.  **书籍管理**
    - 书籍列表展示（支持分页、搜索、筛选）
    - **TXT 书籍上传**（支持拖拽上传，自动使用文件名作为标题）
    - 编辑书籍信息（标题、作者、简介等）
    - 删除书籍
2.  **分类与标签**
    - 管理书籍分类
    - 标签系统
3.  **在线阅读**
    - **纯文本阅读器**：支持章节划分（可选，基于正则匹配）或分页加载。
    - 自定义阅读设置（字体大小、背景色、行高）。
4.  **系统设置**
    - 存储路径配置

## 3. 技术栈详细选型
- **前端**:
    - 框架: Vue 3 (Composition API)
    - 构建工具: Vite
    - UI 组件库: Element Plus
    - 状态管理: Pinia
    - 路由: Vue Router
    - HTTP 客户端: Axios
- **后端**:
    - 框架: FastAPI
    - 数据库 ORM: SQLModel
    - 依赖管理: pip/requirements.txt
    - **文本处理**: 
        - `chardet`: 用于自动检测 TXT 文件编码（UTF-8, GBK 等），防止乱码。
        - 封面生成: 由于 TXT 无封面，后端可生成带有书名的默认图片，或前端直接展示占位图。

## 4. 实施步骤计划

### 第一阶段：环境搭建与基础架构
1.  **创建项目结构**
    - `backend/`: 后端代码
    - `frontend/`: 前端代码
2.  **后端初始化**
    - 设置虚拟环境
    - 安装 FastAPI, SQLModel, uvicorn, chardet, python-multipart 等依赖
    - 配置数据库连接 (SQLite)
3.  **前端初始化**
    - 使用 `npm create vite@latest` 创建 Vue 3 项目
    - 安装 Element Plus, Axios, Pinia, Vue Router

### 第二阶段：后端核心开发
1.  **数据模型设计**
    - 定义 `Book` 模型 (id, title, author, path, file_size, encoding, added_at 等)
2.  **API 开发 - 书籍管理**
    - `POST /api/books/upload`: 处理 TXT 文件上传。
        - 检测文件编码。
        - 保存文件到 `static/uploads`。
        - 存入数据库。
    - `GET /api/books`: 获取书籍列表。
    - `GET /api/books/{id}`: 获取书籍元数据。
    - `DELETE /api/books/{id}`: 删除书籍及文件。
    - `PUT /api/books/{id}`: 更新书籍信息。
3.  **API 开发 - 阅读内容**
    - `GET /api/books/{id}/content`: 获取书籍内容。
        - 支持分页参数 `start` (byte offset) 和 `limit` (length) 以实现按需加载，避免大文件卡顿。
        - 或者简单的按行/章节读取。

### 第三阶段：前端核心开发
1.  **基础布局**
    - 侧边栏/顶部导航，主内容区。
2.  **书籍列表页**
    - Grid 布局展示书籍卡片（使用默认封面样式）。
    - 搜索栏。
3.  **书籍详情页**
    - 展示书籍详细信息。
    - 提供“阅读”按钮。
4.  **上传组件**
    - 限制仅允许 `.txt` 文件上传。

### 第四阶段：阅读器开发
1.  **阅读页面 (`/read/:id`)**
    - 调用 `GET /api/books/{id}/content` 获取文本。
    - 实现文本渲染区域。
    - 实现“上一页/下一页”或“加载更多”功能（配合后端的分页接口）。
    - 简单的样式设置面板（字号、背景）。

### 第五阶段：测试与优化
1.  **联调测试**
    - 测试不同编码（UTF-8, GBK）的 TXT 文件显示是否正常。
2.  **UI/UX 优化**
    - 优化大文件加载体验。

## 5. 目录结构预览
```
neoReader/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── api/
│   │   │   ├── books.py
│   │   │   └── reader.py
│   │   └── utils/ (file_handler.py - 编码检测等)
│   ├── static/ 
│   │   └── uploads/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   └── ReaderView.vue
│   │   └── api/
│   └── package.json
└── README.md
```

## 6. 前端界面详细设计

### 6.1. 主布局 (Layout)
- **TopBar**:
  - Logo: 左侧展示应用名称 "NeoReader"。
  - Search: 顶部居中搜索框，支持按书名/作者搜索。
  - Actions: 右侧上传按钮、设置图标。
- **Content Area**: 占据主体空间，展示路由视图。

### 6.2. 首页 (HomeView) - 书架模式
- **书籍网格 (Book Grid)**:
  - 使用 `el-card` 展示每本书。
  - **封面区**: 由于 TXT 无封面，显示一个带有书名首字母或随机颜色的占位图，书名居中显示在封面上。
  - **信息区**: 书名（截断显示）、作者（如有）、文件大小。
  - **操作**: 悬停时显示 "阅读"、"编辑"、"删除" 按钮。
- **空状态**: 无书籍时显示友好的引导上传提示。
- **上传交互**: 页面支持文件拖拽上传，或点击顶部上传按钮弹出文件选择框。

### 6.3. 阅读页 (ReaderView)
- **极简模式**: 隐藏 TopBar，进入沉浸式阅读。
- **工具栏 (Toolbar)**:
  - 顶部/底部悬浮（鼠标移动时显示）。
  - 返回书架按钮。
  - 目录/章节跳转（如果实现了章节解析）。
  - 设置按钮（唤起设置面板）。
- **内容区域 (Content)**:
  - 居中显示的文本容器，模拟纸张效果（可选）。
  - 支持滚动阅读或分页点击。
- **设置面板 (Settings Panel)**:
  - **字号**: 滑块调节。
  - **背景**: 预设主题（亮白、羊皮纸、夜间模式）。
  - **行高/边距**: 微调排版。
