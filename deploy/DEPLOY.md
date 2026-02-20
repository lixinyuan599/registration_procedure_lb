# 部署指南

## 前置条件

1. 一台云服务器 (推荐腾讯云/阿里云 2核4G)
2. 已备案的域名
3. SSL 证书 (可在云平台免费申请)
4. 安装 Docker + Docker Compose

## 部署步骤

### 1. 上传代码到服务器

```bash
# 在本地
scp -r 挂号小程序/ root@your-server-ip:/opt/clinic-app/

# 或使用 git
git clone your-repo /opt/clinic-app
```

### 2. 配置环境变量

```bash
cd /opt/clinic-app/backend
cp .env.example .env
vim .env  # 修改以下关键配置
```

必须修改的配置：
- `WX_APPID` - 微信小程序 AppID
- `WX_SECRET` - 微信小程序 AppSecret
- `JWT_SECRET_KEY` - 随机字符串，如: `openssl rand -hex 32`
- `ADMIN_PASSWORD` - 管理后台密码
- `ADMIN_SECRET_KEY` - 随机字符串

### 3. 配置 SSL 证书

```bash
# 将证书文件放入 ssl 目录
cp fullchain.pem /opt/clinic-app/deploy/ssl/
cp privkey.pem /opt/clinic-app/deploy/ssl/
```

### 4. 修改 nginx 域名

```bash
vim /opt/clinic-app/deploy/nginx.conf
# 将 your-domain.com 替换为你的域名
```

### 5. 启动服务

```bash
cd /opt/clinic-app

# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend

# 初始化数据库 (首次部署)
docker-compose exec backend python seed_data.py
```

### 6. 验证

```bash
# 健康检查
curl https://your-domain.com/

# API 测试
curl https://your-domain.com/api/v1/clinics

# 管理后台
# 浏览器访问 https://your-domain.com/admin
```

### 7. 配置小程序域名

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 开发管理 → 开发设置 → 服务器域名
3. request 合法域名添加: `https://your-domain.com`

### 8. 更新小程序 API 地址

修改 `miniprogram/utils/request.js`：

```javascript
const BASE_URL = 'https://your-domain.com/api/v1';
```

## 日常运维

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f --tail 100 backend

# 重启服务
docker-compose restart backend

# 更新代码后重新构建
git pull
docker-compose up -d --build

# 备份 SQLite 数据库
docker-compose exec backend cp clinic.db /tmp/clinic_backup_$(date +%Y%m%d).db
```

## 切换 PostgreSQL (推荐生产环境)

1. 取消 `docker-compose.yml` 中 `db` 服务的注释
2. 修改 `.env`：
   ```
   DATABASE_URL=postgresql+asyncpg://clinic_user:your_secure_password@db:5432/clinic_db
   ```
3. 安装驱动: 在 `requirements.txt` 中添加 `asyncpg>=0.29.0`
4. 重新构建: `docker-compose up -d --build`
