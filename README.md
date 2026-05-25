# BioFlow API

基于 FastAPI 的生物信息学后端服务，采用 Laravel 风格的目录结构。

## 功能特性

- **用户认证**: JWT Token 认证
- **数据库**: SQLite 支持
- **项目结构**: Laravel 风格的分层架构
- **环境配置**: 使用 .env 管理配置

## 目录结构

```
backend/
├── app/
│   ├── http/
│   │   ├── controllers/    # 控制器层
│   │   ├── middleware/     # 中间件层
│   │   └── requests/       # 请求验证层
│   ├── models/             # 数据模型层
│   └── services/           # 业务逻辑层
├── config/                 # 配置文件
├── database/               # 数据库连接
├── routes/                 # 路由定义
├── main.py                 # 应用入口
└── migrate_seed.py         # 数据库迁移/种子数据
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，修改 JWT_SECRET_KEY
```

### 3. 初始化数据库

```bash
python migrate_seed.py
```

### 4. 启动服务

```bash
uvicorn main:app --reload
```

服务将在 `http://localhost:8000` 启动。

## API 端点

### 认证

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 用户

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/users/` | 获取用户列表 |
| GET | `/api/users/{id}` | 获取指定用户 |
| POST | `/api/users/` | 创建新用户 |
| PUT | `/api/users/{id}` | 更新用户 |
| DELETE | `/api/users/{id}` | 删除用户 |

## 测试账号

初始化后可使用以下账号测试：

| 邮箱 | 密码 |
|------|------|
| admin@bioflow.com | admin123 |
| researcher@bioflow.com | research123 |
| student@bioflow.com | student123 |

## API 使用示例

### 登录

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@bioflow.com", "password": "admin123"}'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@bioflow.com",
    "username": "admin",
    "full_name": "Administrator"
  }
}
```

### 认证请求

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your-token>"
```

## 技术栈

- **FastAPI** - Web 框架
- **SQLAlchemy** - ORM
- **Pydantic** - 数据验证
- **python-jose** - JWT 处理
- **passlib** - 密码哈希
- **python-dotenv** - 环境变量

## 开发

### 添加新的 Model

1. 在 `app/models/` 创建模型文件
2. 继承 `Model` 基类
3. 运行 `python migrate_seed.py` 创建表

### 添加新的 Controller

1. 在 `app/http/controllers/` 创建控制器
2. 在 `routes/` 添加路由文件
3. 在 `routes/api.py` 中引入路由

## License

MIT
