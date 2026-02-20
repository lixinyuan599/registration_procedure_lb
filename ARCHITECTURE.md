# 门诊挂号小程序 MVP - 系统架构设计

## 一、系统整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (Client)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              微信小程序 (WeChat Mini Program)              │  │
│  │                                                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ 门店选择 │→│ 医生列表 │→│ 医生排班 │→│  预约确认   │  │  │
│  │  │   页面   │ │   页面   │ │   页面   │ │    页面     │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  │                                          ┌─────────────┐  │  │
│  │                                          │  我的预约页  │  │  │
│  │                                          └─────────────┘  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │            services/api.js (统一请求层)              │  │  │
│  │  └─────────────────────┬───────────────────────────────┘  │  │
│  └────────────────────────┼──────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTPS / RESTful API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       服务层 (Backend)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 FastAPI Application                        │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌───────────────┐  ┌────────────────┐  │  │
│  │  │   Routers   │  │   Services    │  │   Middleware    │  │  │
│  │  │             │  │  (业务逻辑)    │  │  (CORS/Auth)   │  │  │
│  │  │ /clinics    │  │               │  │                │  │  │
│  │  │ /doctors    │→ │ clinic_svc    │  │  统一错误处理   │  │  │
│  │  │ /schedules  │  │ doctor_svc    │  │  请求日志      │  │  │
│  │  │ /appoint.   │  │ schedule_svc  │  │                │  │  │
│  │  │             │  │ appoint_svc   │  │                │  │  │
│  │  └──────┬──────┘  └───────┬───────┘  └────────────────┘  │  │
│  │         │                 │                                │  │
│  │         ▼                 ▼                                │  │
│  │  ┌───────────────────────────────────────────────────────┐│  │
│  │  │           Schemas (Pydantic 数据校验)                  ││  │
│  │  └───────────────────────┬───────────────────────────────┘│  │
│  │                          │                                │  │
│  │  ┌───────────────────────▼───────────────────────────────┐│  │
│  │  │           Models (SQLAlchemy ORM)                      ││  │
│  │  └───────────────────────┬───────────────────────────────┘│  │
│  └──────────────────────────┼────────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │ SQL
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据层 (Database)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          SQLite (开发) / PostgreSQL (生产)                 │  │
│  │                                                           │  │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │ users  │ │clinics │ │ doctors  │ │    schedules     │ │  │
│  │  └───┬────┘ └───┬────┘ └────┬─────┘ └───────┬──────────┘ │  │
│  │      │          │           │                │            │  │
│  │      │          │     ┌─────┴─────┐          │            │  │
│  │      │          └────→│doctor_    │←─────────┘            │  │
│  │      │                │clinic(关联)│                       │  │
│  │      │                └───────────┘                       │  │
│  │      │                                                    │  │
│  │      │          ┌──────────────┐                          │  │
│  │      └─────────→│ appointments │←── (关联所有实体)        │  │
│  │                 └──────────────┘                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 二、用户预约流程图

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │     │          │
│ 打开小程序│────→│ 选择门店  │────→│ 选择医生 │────→│ 选择时段  │────→│ 确认预约  │
│          │     │          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └─────┬────┘
                                                                         │
                                                                         ▼
                                                                   ┌──────────┐
                 ┌──────────┐                                      │          │
                 │          │◀─────────────────────────────────────│ 预约成功  │
                 │ 我的预约  │                                      │          │
                 │          │                                      └──────────┘
                 └──────────┘

详细流程：
  1. 用户进入小程序 → 展示门店列表 (GET /clinics)
  2. 选择门店 → 跳转医生列表页 (GET /clinics/{id}/doctors)
  3. 选择医生 → 跳转排班页面 (GET /doctors/{id}/schedules)
  4. 选择时段 → 跳转预约确认页
  5. 确认预约 → 提交预约 (POST /appointments)
  6. 预约成功 → 可在"我的预约"查看 (GET /appointments/me)
```

## 三、数据库 ER 图

```
┌──────────────────┐       ┌──────────────────────┐
│      users       │       │       clinics         │
├──────────────────┤       ├──────────────────────┤
│ id (PK)          │       │ id (PK)              │
│ openid (UQ)      │       │ name                 │
│ nickname         │       │ address              │
│ phone            │       │ phone                │
│ avatar_url       │       │ description          │
│ created_at       │       │ image_url            │
│ updated_at       │       │ is_active            │
└────────┬─────────┘       │ created_at           │
         │                 │ updated_at           │
         │                 └──────────┬───────────┘
         │                            │
         │                            │ 1
         │                            │
         │                            ▼ N
         │                 ┌──────────────────────┐
         │                 │      doctors          │
         │                 ├──────────────────────┤
         │                 │ id (PK)              │
         │                 │ clinic_id (FK→clinics)│
         │                 │ name                 │
         │                 │ title                │
         │                 │ specialty            │
         │                 │ description          │
         │                 │ avatar_url           │
         │                 │ is_active            │
         │                 │ created_at           │
         │                 │ updated_at           │
         │                 └──────────┬───────────┘
         │                            │
         │                            │ 1
         │                            │
         │                            ▼ N
         │                 ┌──────────────────────┐
         │                 │     schedules         │
         │                 ├──────────────────────┤
         │                 │ id (PK)              │
         │                 │ doctor_id (FK→doctors)│
         │                 │ clinic_id (FK→clinics)│
         │                 │ date                 │
         │                 │ start_time           │
         │                 │ end_time             │
         │                 │ max_patients         │
         │                 │ current_patients     │
         │                 │ status (开放/已满/关闭)│
         │                 │ created_at           │
         │                 │ updated_at           │
         │                 └──────────┬───────────┘
         │                            │
         │  1                         │ 1
         │                            │
         ▼ N                          ▼ N
┌────────────────────────────────────────────────┐
│                 appointments                    │
├────────────────────────────────────────────────┤
│ id (PK)                                        │
│ user_id (FK → users)                           │
│ doctor_id (FK → doctors)                       │
│ clinic_id (FK → clinics)                       │
│ schedule_id (FK → schedules)                   │
│ appointment_date                               │
│ time_slot                                      │
│ status (待确认/已确认/已取消/已完成)              │
│ notes                                          │
│ created_at                                     │
│ updated_at                                     │
└────────────────────────────────────────────────┘

关系说明：
  clinics  1 ──→ N  doctors       (一个门店有多个医生)
  doctors  1 ──→ N  schedules     (一个医生有多个排班)
  clinics  1 ──→ N  schedules     (排班关联门店，冗余便于查询)
  users    1 ──→ N  appointments  (一个用户有多个预约)
  doctors  1 ──→ N  appointments  (一个医生有多个预约)
  clinics  1 ──→ N  appointments  (预约关联门店)
  schedules 1 ──→ N appointments  (一个时段有多个预约)
```

## 四、前后端交互数据流图

```
┌─────────────┐                          ┌─────────────┐                    ┌──────────┐
│  小程序前端   │                          │ FastAPI后端  │                    │  数据库   │
└──────┬──────┘                          └──────┬──────┘                    └─────┬────┘
       │                                        │                                │
       │  1. GET /clinics                       │                                │
       │───────────────────────────────────────→│  SELECT * FROM clinics         │
       │                                        │───────────────────────────────→│
       │                                        │        clinics data            │
       │        [{id,name,address,...}]         │←───────────────────────────────│
       │←───────────────────────────────────────│                                │
       │                                        │                                │
       │  2. GET /clinics/1/doctors             │                                │
       │───────────────────────────────────────→│  SELECT * FROM doctors         │
       │                                        │  WHERE clinic_id=1             │
       │                                        │───────────────────────────────→│
       │                                        │        doctors data            │
       │     [{id,name,title,specialty,...}]    │←───────────────────────────────│
       │←───────────────────────────────────────│                                │
       │                                        │                                │
       │  3. GET /doctors/1/schedules           │                                │
       │───────────────────────────────────────→│  SELECT * FROM schedules       │
       │                                        │  WHERE doctor_id=1             │
       │                                        │  AND status='open'             │
       │                                        │───────────────────────────────→│
       │                                        │      schedules data            │
       │  [{id,date,start_time,end_time,...}]  │←───────────────────────────────│
       │←───────────────────────────────────────│                                │
       │                                        │                                │
       │  4. POST /appointments                 │                                │
       │  {doctor_id,clinic_id,schedule_id}    │  BEGIN TRANSACTION             │
       │───────────────────────────────────────→│  - 检查排班可用性               │
       │                                        │  - 创建预约记录                │
       │                                        │  - 更新排班已预约人数           │
       │                                        │  COMMIT                        │
       │                                        │───────────────────────────────→│
       │          {appointment detail}          │          OK                    │
       │←───────────────────────────────────────│←───────────────────────────────│
       │                                        │                                │
       │  5. GET /appointments/me               │                                │
       │  Header: X-User-OpenID: xxx           │                                │
       │───────────────────────────────────────→│  SELECT * FROM appointments    │
       │                                        │  JOIN doctors, clinics         │
       │                                        │  WHERE user_id=?              │
       │                                        │───────────────────────────────→│
       │    [{appointment+doctor+clinic}]      │     appointment data           │
       │←───────────────────────────────────────│←───────────────────────────────│
       │                                        │                                │
```

## 五、项目目录结构树

```
挂号小程序/
├── backend/                          # 后端项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口, CORS, 路由注册
│   │   ├── config.py                 # 配置管理
│   │   ├── database.py               # 数据库连接与会话管理
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── clinic.py
│   │   │   ├── doctor.py
│   │   │   ├── schedule.py
│   │   │   └── appointment.py
│   │   │
│   │   ├── schemas/                  # Pydantic 数据校验
│   │   │   ├── __init__.py
│   │   │   ├── common.py             # 统一响应结构
│   │   │   ├── user.py
│   │   │   ├── clinic.py
│   │   │   ├── doctor.py
│   │   │   ├── schedule.py
│   │   │   └── appointment.py
│   │   │
│   │   ├── routers/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── clinic.py
│   │   │   ├── doctor.py
│   │   │   ├── schedule.py
│   │   │   └── appointment.py
│   │   │
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── clinic_service.py
│   │   │   ├── doctor_service.py
│   │   │   ├── schedule_service.py
│   │   │   └── appointment_service.py
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── exceptions.py         # 自定义异常
│   │       └── deps.py               # 依赖注入
│   │
│   ├── seed_data.py                  # 测试数据填充脚本
│   ├── requirements.txt              # Python 依赖
│   └── README.md
│
├── miniprogram/                      # 微信小程序前端
│   ├── app.js                        # 小程序入口
│   ├── app.json                      # 全局配置
│   ├── app.wxss                      # 全局样式
│   │
│   ├── pages/
│   │   ├── clinic-list/              # 门店选择页
│   │   │   ├── clinic-list.js
│   │   │   ├── clinic-list.json
│   │   │   ├── clinic-list.wxml
│   │   │   └── clinic-list.wxss
│   │   │
│   │   ├── doctor-list/              # 医生列表页
│   │   │   ├── doctor-list.js
│   │   │   ├── doctor-list.json
│   │   │   ├── doctor-list.wxml
│   │   │   └── doctor-list.wxss
│   │   │
│   │   ├── doctor-schedule/          # 医生排班页
│   │   │   ├── doctor-schedule.js
│   │   │   ├── doctor-schedule.json
│   │   │   ├── doctor-schedule.wxml
│   │   │   └── doctor-schedule.wxss
│   │   │
│   │   ├── appointment-confirm/      # 预约确认页
│   │   │   ├── appointment-confirm.js
│   │   │   ├── appointment-confirm.json
│   │   │   ├── appointment-confirm.wxml
│   │   │   └── appointment-confirm.wxss
│   │   │
│   │   └── my-appointments/          # 我的预约页
│   │       ├── my-appointments.js
│   │       ├── my-appointments.json
│   │       ├── my-appointments.wxml
│   │       └── my-appointments.wxss
│   │
│   ├── services/
│   │   └── api.js                    # 统一 API 请求封装
│   │
│   ├── utils/
│   │   ├── request.js                # wx.request 封装
│   │   └── util.js                   # 工具函数
│   │
│   └── images/                       # 静态图片资源
│
└── ARCHITECTURE.md                   # 本文件 - 架构设计文档
```

## 六、API 设计详情

### 统一响应格式

**成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误响应：**
```json
{
  "code": 40001,
  "message": "该时段已约满",
  "data": null
}
```

### API 列表

#### 1. GET /api/v1/clinics - 获取门店列表

响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "仁心堂中医门诊（总院）",
      "address": "北京市朝阳区xxx路100号",
      "phone": "010-12345678",
      "description": "综合门诊，专注中西医结合",
      "image_url": "https://example.com/clinic1.jpg"
    }
  ]
}
```

#### 2. GET /api/v1/clinics/{clinic_id}/doctors - 获取门店医生列表

响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "张医生",
      "title": "主任医师",
      "specialty": "内科",
      "description": "从医20年，擅长心血管疾病诊治",
      "avatar_url": "https://example.com/doctor1.jpg",
      "clinic_id": 1
    }
  ]
}
```

#### 3. GET /api/v1/doctors/{doctor_id}/schedules - 获取医生排班

请求参数：`?date_from=2026-02-16&date_to=2026-02-22`

响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "doctor_id": 1,
      "clinic_id": 1,
      "date": "2026-02-16",
      "start_time": "09:00",
      "end_time": "12:00",
      "max_patients": 20,
      "current_patients": 5,
      "status": "open"
    }
  ]
}
```

#### 4. POST /api/v1/appointments - 创建预约

请求体：
```json
{
  "doctor_id": 1,
  "clinic_id": 1,
  "schedule_id": 1,
  "notes": "头痛三天"
}
```

响应示例：
```json
{
  "code": 0,
  "message": "预约成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "doctor_id": 1,
    "clinic_id": 1,
    "schedule_id": 1,
    "appointment_date": "2026-02-16",
    "time_slot": "09:00-12:00",
    "status": "confirmed",
    "notes": "头痛三天",
    "created_at": "2026-02-15T22:00:00"
  }
}
```

#### 5. GET /api/v1/appointments/me - 我的预约

响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "status": "confirmed",
      "appointment_date": "2026-02-16",
      "time_slot": "09:00-12:00",
      "notes": "头痛三天",
      "doctor": {
        "id": 1,
        "name": "张医生",
        "title": "主任医师",
        "specialty": "内科"
      },
      "clinic": {
        "id": 1,
        "name": "仁心堂中医门诊（总院）",
        "address": "北京市朝阳区xxx路100号"
      },
      "created_at": "2026-02-15T22:00:00"
    }
  ]
}
```

### 错误码规范

| 错误码 | 说明 |
|-------|------|
| 0     | 成功 |
| 40001 | 参数错误 |
| 40002 | 该时段已约满 |
| 40003 | 排班不存在或已关闭 |
| 40004 | 重复预约 |
| 40101 | 用户未认证 |
| 50001 | 服务器内部错误 |

## 七、页面跳转关系与数据流

```
┌────────────────┐  选择门店   ┌────────────────┐  选择医生   ┌─────────────────┐
│  clinic-list   │───────────→│  doctor-list   │───────────→│ doctor-schedule  │
│  (门店选择页)   │  clinic_id  │  (医生列表页)   │ doctor_id   │  (医生排班页)     │
└────────────────┘            └────────────────┘  clinic_id  └────────┬────────┘
                                                                      │
                                                              选择时段 │ schedule_id
                                                              clinic_id│ doctor_id
                                                                      ▼
┌────────────────┐  预约成功   ┌───────────────────────┐
│my-appointments │◀───────────│ appointment-confirm    │
│ (我的预约页)    │            │   (预约确认页)          │
└────────────────┘            └───────────────────────┘

TabBar 底部导航：
  [首页(门店列表)]                              [我的预约]
```

## 八、技术决策说明

| 决策项 | 选择 | 理由 |
|-------|------|------|
| 开发数据库 | SQLite | 零配置，快速启动 MVP |
| 生产数据库 | PostgreSQL | 高并发，数据完整性 |
| ORM | SQLAlchemy | Python 生态最成熟 |
| 用户认证 | X-User-OpenID Header | MVP 阶段模拟微信登录 |
| API 版本 | /api/v1/ | 预留版本升级空间 |
| 时间处理 | UTC 存储 | 避免时区问题 |

## 九、扩展预留

当前架构已为以下功能预留扩展空间：
- **支付**：appointments 表可扩展 payment_status、payment_id 字段
- **AI 问诊**：新增 consultations 表，关联 users 和 doctors
- **推荐医生**：基于 specialty、评分等字段实现推荐算法
- **门店管理后台**：后端已模块化，可直接新增管理端 routers
- **消息通知**：新增 notifications 表，结合微信模板消息
