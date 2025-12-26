# 设备监控系统部署指南

本指南将帮助您将设备监控系统部署到免费的云平台上，使其可以从外网访问。

## 1. 平台选择

经过评估，以下是支持Flask+SocketIO(WebSocket)的免费部署平台：

### 1.1 Render（推荐）
- ✅ 完全免费计划（有流量限制）
- ✅ 支持Python和WebSocket
- ✅ 自动部署（从Git仓库）
- ✅ HTTPS支持
- ✅ 自定义域名支持

### 1.2 Railway
- ✅ 免费计划（有使用限制）
- ✅ 支持Python和WebSocket
- ✅ 自动部署
- ✅ HTTPS支持

### 1.3 Glitch
- ✅ 完全免费
- ✅ 支持Python和WebSocket
- ✅ 实时编辑功能
- ❌ 项目可能会进入休眠状态

## 2. 项目准备

在部署之前，需要对项目进行一些调整：

### 2.1 创建requirements.txt文件

确保项目根目录下有完整的`requirements.txt`文件，包含所有依赖：

```txt
Flask==2.3.3
Flask-SocketIO==5.3.6
eventlet==0.33.3
apscheduler==3.10.4
schedule==1.2.2
```

### 2.2 创建Procfile（用于Render）

在项目根目录下创建`Procfile`文件，指定启动命令：

```
web: python app.py
```

### 2.3 配置数据库（重要）

**注意：在部署到云端平台（如Render）时，无法直接使用本地数据库**，因为云端应用运行在远程服务器上，无法访问您本地网络中的数据库。

### 解决方案：迁移到云数据库

您需要将本地数据库迁移到云数据库服务。对于免费选项，您可以考虑：

- MySQL: PlanetScale（免费计划，支持10GB存储）
- PostgreSQL: Supabase（免费计划，支持500MB存储）
- SQLite: 如果数据量较小，可以使用SQLite（文件型数据库，适合小型项目）

### 迁移步骤

#### 从达梦数据库迁移到云数据库

如果您当前使用的是本地达梦数据库，迁移到云数据库需要以下步骤：

1. **导出本地数据**：
   - 使用达梦数据库管理工具（如DMS）导出SQL脚本
   - 或使用命令行工具：`dm_dump -u SYSDBA -p SYSDBA -s localhost:5236 -d DAMENG -f backup.sql`

2. **转换SQL脚本**：
   - 达梦数据库的SQL语法与标准SQL有一些差异
   - 可以使用工具或手动修改SQL脚本，使其兼容目标云数据库（如MySQL/PostgreSQL）
   - 主要修改点：数据类型、函数名、语法结构等

3. **创建云数据库**：
   - 在选择的云数据库平台上创建数据库实例
   - 确保数据库版本与您的应用兼容

4. **导入数据**：
   - 使用云数据库提供的导入工具导入转换后的SQL脚本
   - 或使用命令行工具：`mysql -h your-host -u your-username -p your-database < backup.sql`

5. **更新数据模型**：
   - 如果目标数据库与达梦数据库有较大差异，可能需要修改项目中的数据模型文件
   - 主要修改`models/`目录下的数据库模型类

6. **更新连接配置**：
   - 修改项目中的数据库连接字符串，指向云数据库
   - 使用环境变量管理敏感信息

### 数据库驱动注意事项

如果您从达梦数据库迁移到其他数据库，需要更新项目的数据库驱动：

#### 对于MySQL：
```bash
pip install pymysql
```

#### 对于PostgreSQL：
```bash
pip install psycopg2-binary
```

#### 对于SQLite：
```bash
# SQLite是Python标准库的一部分，不需要额外安装
```

同时，需要修改`utils/db.py`文件中的数据库连接代码，以支持新的数据库驱动。

### 配置文件修改

在`config.py`文件中更新数据库连接配置：

```python
# 云数据库连接配置
DATABASE_CONFIG = {
    'host': 'your-database-host',
    'port': 'your-database-port',
    'database': 'your-database-name',
    'user': 'your-username',
    'password': 'your-password'
}
```

**建议使用环境变量存储敏感信息**，避免将密码等信息硬编码到代码中。

### 2.4 修改app.py配置

确保您的应用可以在不同环境下运行：

```python
# 在app.py中添加
import os

# 使用环境变量获取端口
port = int(os.environ.get('PORT', 5002))

if __name__ == "__main__":
    # 启动服务（支持 WebSocket）
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
```

## 3. Render部署步骤

### 3.1 注册Render账号

访问 https://render.com 并使用GitHub账号注册。

### 3.2 创建Web服务

1. 点击"New" -> "Web Service"
2. 连接您的GitHub仓库（确保仓库是公开的或您已授权Render访问）
3. 选择您的项目仓库
4. 配置部署设置：
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Free Plan**: 选择免费计划

### 3.3 部署项目

1. 点击"Create Web Service"开始部署
2. 等待部署完成（这可能需要几分钟）
3. 部署成功后，您将获得一个公共URL（如 `https://your-project.onrender.com`）

### 3.4 配置环境变量

**强烈建议使用环境变量存储敏感信息**，如数据库连接字符串、API密钥等，避免将这些信息硬编码到代码中。

#### 在项目中使用环境变量

修改`config.py`文件，使用环境变量获取数据库连接信息：

```python
import os

# 从环境变量获取数据库配置
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5236'),
    'database': os.environ.get('DB_NAME', 'your_database'),
    'user': os.environ.get('DB_USER', 'your_username'),
    'password': os.environ.get('DB_PASSWORD', 'your_password')
}
```

#### 在Render上配置环境变量

1. 进入您的Render项目页面
2. 点击"Environment"选项卡
3. 点击"Add Environment Variable"按钮
4. 逐一添加以下环境变量（根据您的云数据库配置填写）：
   
   **达梦数据库环境变量：**
   - `DM_USER`: 数据库用户名（如：SYSDBA）
   - `DM_PASSWORD`: 数据库密码（如：SYSDBA）
   - `DM_SERVER`: 云数据库主机地址（如：your-database-host.com）
   - `DM_PORT`: 云数据库端口（达梦数据库默认5236）
   - `DM_DATABASE`: 数据库名称（如：DAMENG）
   - `DM_SCHEMA`: 数据库模式（如：DEV）
   
   **其他环境变量：**
   - `SECRET_KEY`: Flask应用密钥（建议设置为随机字符串）
   - `DEBUG`: 是否开启调试模式（部署时建议设置为False）
   
5. 点击"Save Changes"
6. 重新部署项目使环境变量生效

#### 验证环境变量配置

您可以在项目的部署日志中查看环境变量是否正确加载，或者在代码中添加调试日志：

```python
import os
from utils.logger import logger

# 记录环境变量加载情况
logger.info(f"Database host: {os.environ.get('DB_HOST')}")
logger.info(f"Database port: {os.environ.get('DB_PORT')}")
```

## 4. Railway部署步骤

### 4.1 注册Railway账号

访问 https://railway.app 并使用GitHub账号注册。

### 4.2 创建项目

1. 点击"New Project" -> "Deploy from GitHub repo"
2. 连接您的GitHub仓库
3. 选择您的项目仓库
4. Railway会自动检测到Python项目并使用正确的配置

### 4.3 部署项目

1. Railway会自动开始部署
2. 部署完成后，您将获得一个公共URL

## 5. 注意事项

### 5.1 WebSocket支持

确保您的Flask-SocketIO配置正确：

```python
# 使用eventlet作为WebSocket的后台
import eventlet
eventlet.monkey_patch()

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
```

### 5.2 免费计划限制

- **Render**: 每月100GB流量，512MB内存，最长15分钟构建时间
- **Railway**: 每月500小时运行时间，1GB内存

### 5.3 数据库连接

如果您使用本地数据库，需要将其迁移到云数据库服务。确保更新`config.py`中的数据库连接配置。

### 5.4 定时任务

由于免费平台可能会在项目不活跃时暂停服务，长期运行的定时任务可能会受到影响。考虑使用外部定时任务服务，如：

- GitHub Actions（免费，用于定时触发API）
- EasyCron（免费计划）

## 6. 访问您的应用

部署成功后，您可以通过平台提供的公共URL访问您的设备监控系统。例如：

```
https://your-project.onrender.com
```

## 7. 自定义域名（可选）

如果您有自己的域名，可以将其指向部署平台提供的URL。具体步骤请参考各平台的文档：

- [Render自定义域名](https://render.com/docs/custom-domains)
- [Railway自定义域名](https://docs.railway.app/deploy/exposing-your-app#custom-domains)

## 8. 故障排除

### 8.1 WebSocket连接失败

- 确保您的平台支持WebSocket
- 检查浏览器控制台中的错误信息
- 确保CORS配置正确：`cors_allowed_origins="*"`

### 8.2 部署失败

- 检查依赖是否完整（requirements.txt）
- 检查启动命令是否正确
- 查看部署日志以获取详细错误信息

### 8.3 应用运行缓慢

- 免费计划通常有资源限制
- 考虑优化数据库查询
- 减少不必要的后台任务

## 9. 后续维护

- 定期更新依赖包
- 监控应用性能和错误日志
- 根据使用情况考虑升级到付费计划（如果需要）

祝您部署成功！