# 门诊挂号小程序 MVP

一个基于 **微信小程序 + FastAPI + SQLite** 的门诊预约挂号系统最小可行产品。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | 微信小程序原生框架 | WXML + WXSS + JS |
| 后端 | Python FastAPI | 异步 RESTful API |
| ORM | SQLAlchemy 2.0 | 异步 ORM，支持 SQLite / PostgreSQL |
| 数据库 | SQLite (开发) | 零配置，可切换 PostgreSQL |
| 校验 | Pydantic v2 | 请求/响应数据校验 |

## 快速启动

### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 填充测试数据 (3门店 + 7医生 + 84排班)
python seed_data.py

# 启动服务 (热重载模式)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动成功后：
- API 服务: http://127.0.0.1:8000
- Swagger 文档: http://127.0.0.1:8000/docs
- ReDoc 文档: http://127.0.0.1:8000/redoc

### 2. 启动小程序

1. 下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开微信开发者工具，选择"导入项目"
3. 项目目录选择 `miniprogram/` 文件夹
4. AppID 可使用测试号或替换 `project.config.json` 中的 appid
5. 在"详情 → 本地设置"中勾选 **"不校验合法域名"**（开发阶段必须）
6. 编译运行即可

### 3. 测试账号

| openid | 昵称 |
|--------|------|
| `test_user_001` | 测试用户A |
| `test_user_002` | 测试用户B |

## 项目结构

```
挂号小程序/
├── backend/                    # 后端 (FastAPI)
│   ├── app/
│   │   ├── main.py             # 应用入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── models/             # ORM 模型 (5张表)
│   │   ├── schemas/            # Pydantic 校验
│   │   ├── routers/            # API 路由 (4个模块)
│   │   ├── services/           # 业务逻辑 (4个服务)
│   │   └── utils/              # 异常处理 + 依赖注入
│   ├── seed_data.py            # 测试数据
│   └── requirements.txt
│
├── miniprogram/                # 前端 (微信小程序)
│   ├── app.js / json / wxss   # 全局文件
│   ├── pages/                  # 5个页面
│   ├── services/api.js         # API 接口层
│   └── utils/                  # 工具函数
│
├── ARCHITECTURE.md             # 架构设计文档
└── README.md                   # 本文件
```

## API 接口一览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/clinics` | 门店列表 | 否 |
| GET | `/api/v1/clinics/{id}` | 门店详情 | 否 |
| GET | `/api/v1/clinics/{id}/doctors` | 门店医生列表 | 否 |
| GET | `/api/v1/doctors/{id}/schedules` | 医生排班 | 否 |
| POST | `/api/v1/appointments` | 创建预约 | 是 |
| GET | `/api/v1/appointments/me` | 我的预约 | 是 |
| PUT | `/api/v1/appointments/{id}/cancel` | 取消预约 | 是 |

> 认证方式: Header `X-User-OpenID: <openid>` (MVP 模拟微信登录)

## 用户流程

```
选择门店 → 选择医生 → 选择时段 → 填写备注 → 确认预约 → 查看我的预约
```

## 扩展方向

本 MVP 已为以下功能预留扩展空间：

- **支付**: appointments 表扩展 payment_status 字段
- **AI 问诊**: 新增 consultations 表
- **推荐医生**: 基于 specialty / 评分的推荐算法
- **管理后台**: 后端已模块化，直接新增管理端路由
- **消息通知**: 新增 notifications 表 + 微信模板消息
