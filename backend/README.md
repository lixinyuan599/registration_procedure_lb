# 门诊挂号系统 - 后端 API

FastAPI 异步 RESTful API，提供门诊预约挂号全部业务接口。

## 启动

```bash
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --reload
```

## API 快速测试 (curl)

### 1. 获取门店列表

```bash
curl http://127.0.0.1:8000/api/v1/clinics
```

返回：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "仁心堂中医门诊（总院）",
      "address": "北京市朝阳区建国路100号",
      "phone": "010-12345678",
      "description": "综合门诊，专注中西医结合治疗，拥有20年历史",
      "image_url": "https://picsum.photos/seed/clinic1/400/200",
      "is_active": true,
      "created_at": "2026-02-15T13:55:21"
    }
  ]
}
```

### 2. 获取门店医生列表

```bash
curl http://127.0.0.1:8000/api/v1/clinics/1/doctors
```

返回：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "张明",
      "title": "主任医师",
      "specialty": "内科",
      "description": "从医25年，擅长心血管疾病...",
      "avatar_url": "https://picsum.photos/seed/doc1/100/100",
      "clinic_id": 1,
      "is_active": true,
      "created_at": "2026-02-15T13:55:21"
    }
  ]
}
```

### 3. 获取医生排班

```bash
# 默认查询未来7天
curl http://127.0.0.1:8000/api/v1/doctors/1/schedules

# 指定日期范围
curl "http://127.0.0.1:8000/api/v1/doctors/1/schedules?date_from=2026-02-16&date_to=2026-02-20"
```

返回：
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
      "start_time": "09:00:00",
      "end_time": "12:00:00",
      "max_patients": 20,
      "current_patients": 0,
      "status": "open",
      "created_at": "2026-02-15T13:55:21"
    }
  ]
}
```

### 4. 创建预约

```bash
curl -X POST http://127.0.0.1:8000/api/v1/appointments \
  -H "Content-Type: application/json" \
  -H "X-User-OpenID: test_user_001" \
  -d '{
    "doctor_id": 1,
    "clinic_id": 1,
    "schedule_id": 1,
    "notes": "头痛三天，伴有低烧"
  }'
```

成功返回：
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
    "notes": "头痛三天，伴有低烧",
    "created_at": "2026-02-15T13:55:58"
  }
}
```

重复预约返回：
```json
{
  "code": 40004,
  "message": "您已预约该时段，请勿重复预约",
  "data": null
}
```

### 5. 查看我的预约

```bash
curl http://127.0.0.1:8000/api/v1/appointments/me \
  -H "X-User-OpenID: test_user_001"
```

返回（含医生和门店嵌套信息）：
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
      "notes": "头痛三天，伴有低烧",
      "doctor": {
        "id": 1,
        "name": "张明",
        "title": "主任医师",
        "specialty": "内科"
      },
      "clinic": {
        "id": 1,
        "name": "仁心堂中医门诊（总院）",
        "address": "北京市朝阳区建国路100号"
      },
      "created_at": "2026-02-15T13:55:58"
    }
  ]
}
```

### 6. 取消预约

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/appointments/1/cancel \
  -H "X-User-OpenID: test_user_001"
```

返回：
```json
{
  "code": 0,
  "message": "预约已取消",
  "data": {
    "id": 1,
    "status": "cancelled",
    "..."
  }
}
```

## 统一错误格式

所有错误均返回统一结构：

```json
{
  "code": 40002,
  "message": "该时段已约满",
  "data": null
}
```

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40001 | 资源不存在 |
| 40002 | 该时段已约满 |
| 40003 | 排班已关闭 |
| 40004 | 重复预约 |
| 40101 | 用户未认证 |
| 50001 | 服务器内部错误 |

## 数据库表

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| users | 用户 | openid (唯一索引) |
| clinics | 门店 | name, address, is_active |
| doctors | 医生 | clinic_id (FK), title, specialty |
| schedules | 排班 | doctor_id (FK), clinic_id (FK), date, max_patients |
| appointments | 预约 | user_id, doctor_id, clinic_id, schedule_id (全FK) |

## 切换 PostgreSQL

修改 `.env` 或环境变量：

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/clinic_db
```

需额外安装：`pip install asyncpg`
