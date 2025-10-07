# 小工具登录 API 接口说明

**版本**: v1.0  
**更新时间**: 2025-10-07  
**适用产品**: VideoSage 系列小工具（视频处理辅助工具）

---

## 📋 概述

本文档说明 VideoSage 小工具系列产品的用户登录接口规范。小工具与主客户端软件、网页端共享同一用户体系，支持**三端同时登录**：

- **网页端**（官网）
- **客户端软件**（VideoSage 剪辑软件）
- **小工具端**（各类视频处理辅助工具）

**重要特性**：
- ✅ 同一账号可在三端同时登录互不干扰
- ✅ 同类设备单点登录（同一小工具只能在一台设备登录）
- ✅ 支持订阅权限验证
- ✅ 支持 JWT Token 认证机制

---

## 🔐 登录接口

### 接口信息

- **接口路径**: `/api/v1/auth/login`
- **请求方法**: `POST`
- **认证方式**: 无需认证（公开接口）
- **Content-Type**: `application/json`

---

### 请求参数

```json
{
  "phone": "13800138888",
  "password": "abc123456",
  "client_version": "ToolKit-v1.0.0",
  "system_info": "Windows 10",
  "device_id": "tool-windows-unique-device-id-123"
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 用户手机号 |
| password | string | 是 | 用户密码（明文，服务端验证后不存储） |
| client_version | string | 是 | 小工具版本号，建议格式：`ToolKit-vX.Y.Z` |
| system_info | string | 是 | 系统信息，如"Windows 10"、"macOS 13.0" |
| device_id | string | 是 | **设备唯一标识符，必须包含 "tool" 字样** |

---

### ⚠️ 重要：device_id 规范

**为了确保小工具与其他端（客户端、网页端）独立登录互不干扰，`device_id` 必须遵循以下规范：**

#### ✅ 正确格式（推荐）

```javascript
// 方式一：包含 "tool" 关键字（推荐）
"tool-windows-{UUID}"           // Windows 系统
"tool-macos-{UUID}"             // macOS 系统
"tool-{工具名称}-{UUID}"         // 特定工具标识

// 方式二：包含 "tool" 任意位置
"videotool-{UUID}"
"{UUID}-tool"
"my-awesome-tool-{UUID}"

// UUID 生成示例（Node.js）
const { v4: uuidv4 } = require('uuid');
const deviceId = `tool-windows-${uuidv4()}`;
// 结果: "tool-windows-a3bb189e-8bf9-4558-9f5c-9c3b7d4e6f2a"
```

#### ❌ 错误格式（会导致冲突）

```javascript
// 不包含 "tool" - 会被误判为旧版客户端
"windows-{UUID}"                 // ❌ 错误
"device-{UUID}"                  // ❌ 错误

// 包含 "web" - 会被误判为网页端
"tool-web-{UUID}"                // ❌ 错误

// 包含 "client" - 会被误判为主客户端
"tool-client-{UUID}"             // ❌ 错误
```

#### 🔧 device_id 生成建议

**C# (WPF/WinForms)**
```csharp
using System;

public static string GenerateDeviceId()
{
    string machineId = Environment.MachineName;
    string uuid = Guid.NewGuid().ToString();
    return $"tool-windows-{machineId}-{uuid}";
}
```

**Python**
```python
import uuid
import platform

def generate_device_id():
    system = platform.system().lower()
    unique_id = str(uuid.uuid4())
    return f"tool-{system}-{unique_id}"
```

**JavaScript/Electron**
```javascript
const { v4: uuidv4 } = require('uuid');
const os = require('os');

function generateDeviceId() {
    const platform = os.platform();
    const uniqueId = uuidv4();
    return `tool-${platform}-${uniqueId}`;
}
```

---

### 参数验证规则

| 参数 | 验证规则 |
|------|----------|
| phone | 符合正则 `/^(\+86)?1[3-9]\d{9}$/`（中国大陆手机号） |
| password | 最小长度 6 位 |
| client_version | 非空字符串 |
| system_info | 非空字符串 |
| device_id | 非空字符串，**必须包含 "tool" 字样（不区分大小写）** |

---

### 业务规则

1. **账号验证优先级**：先验证账号状态，再验证密码
2. **账号禁用处理**：账号被禁用时返回 403 错误（错误码 2003）
3. **单设备登录**：登录成功后会删除该用户的其他**同类设备**会话
   - 小工具端只会踢出其他小工具端登录
   - **不会影响**客户端软件和网页端的登录状态
4. **自动记录信息**：
   - 登录 IP 地址
   - 登录时间
   - 设备信息（client_version、system_info）
5. **Token 有效期**：
   - Access Token: 1 小时（默认）
   - Refresh Token: 7 天（默认）

---

### 成功响应 (200 OK)

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_info": {
      "id": 123,
      "phone": "13800138888",
      "nickname": "用户昵称",
      "role": "client_default"
    }
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

#### 返回数据说明

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | JWT 访问令牌，用于后续 API 调用 |
| expires_in | number | 令牌有效期（秒），默认 3600 秒（1小时） |
| refresh_token | string | 刷新令牌，用于获取新的访问令牌，默认 7 天有效 |
| user_info.id | number | 用户 ID |
| user_info.phone | string | 用户手机号 |
| user_info.nickname | string | 用户昵称（可能为 null） |
| user_info.role | string | 用户角色，通常为 "client_default" |

---

### 错误响应

#### 1. 参数验证错误 (400 Bad Request)

```json
{
  "code": 1001,
  "message": "无效的手机号。",
  "error": {
    "details": {
      "field": "phone"
    }
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

**常见参数错误**：

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| 无效的手机号。 | phone 格式不正确 | 检查手机号格式 |
| 密码不能为空或长度不足。 | password 长度 < 6 | 检查密码长度 |
| 客户端版本信息不能为空。 | client_version 为空 | 提供版本号 |
| 客户端系统信息不能为空。 | system_info 为空 | 提供系统信息 |
| 设备标识不能为空。 | device_id 为空 | 提供设备标识 |

---

#### 2. 用户不存在 (401 Unauthorized)

```json
{
  "code": 2001,
  "message": "用户不存在。",
  "error": {
    "details": {}
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

---

#### 3. 密码错误 (401 Unauthorized)

```json
{
  "code": 2002,
  "message": "密码错误。",
  "error": {
    "details": {}
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

---

#### 4. 账号被禁用 (403 Forbidden)

```json
{
  "code": 2003,
  "message": "账号被禁用。",
  "error": {
    "details": {
      "current_status": 0
    }
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

---

#### 5. 服务器错误 (500 Internal Server Error)

```json
{
  "code": 1000,
  "message": "服务器内部错误。",
  "error": {
    "details": {
      "error_message": "具体错误信息"
    }
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1633046400000
}
```

---

## 📡 完整请求示例

### cURL

```bash
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138888",
    "password": "client123",
    "client_version": "ToolKit-v1.0.0",
    "system_info": "Windows 10",
    "device_id": "tool-windows-a3bb189e-8bf9-4558-9f5c-9c3b7d4e6f2a"
  }'
```

### JavaScript (Axios)

```javascript
const axios = require('axios');

async function login() {
  try {
    const response = await axios.post('https://your-domain.com/api/v1/auth/login', {
      phone: '13800138888',
      password: 'client123',
      client_version: 'ToolKit-v1.0.0',
      system_info: 'Windows 10',
      device_id: 'tool-windows-a3bb189e-8bf9-4558-9f5c-9c3b7d4e6f2a'
    });

    const { token, refresh_token, user_info } = response.data.data;
    
    // 保存 Token
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh_token);
    
    console.log('登录成功:', user_info);
  } catch (error) {
    console.error('登录失败:', error.response.data.message);
  }
}

login();
```

### Python (Requests)

```python
import requests
import uuid

def login():
    url = "https://your-domain.com/api/v1/auth/login"
    
    # 生成设备 ID
    device_id = f"tool-windows-{uuid.uuid4()}"
    
    payload = {
        "phone": "13800138888",
        "password": "client123",
        "client_version": "ToolKit-v1.0.0",
        "system_info": "Windows 10",
        "device_id": device_id
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()['data']
        print(f"登录成功: {data['user_info']}")
        return data['token'], data['refresh_token']
    else:
        error = response.json()
        print(f"登录失败: {error['message']}")
        return None, None

token, refresh_token = login()
```

### C# (HttpClient)

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class LoginService
{
    private static readonly HttpClient client = new HttpClient();

    public async Task<LoginResponse> LoginAsync(string phone, string password)
    {
        var deviceId = $"tool-windows-{Guid.NewGuid()}";
        
        var loginData = new
        {
            phone = phone,
            password = password,
            client_version = "ToolKit-v1.0.0",
            system_info = "Windows 10",
            device_id = deviceId
        };

        var json = JsonSerializer.Serialize(loginData);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync(
            "https://your-domain.com/api/v1/auth/login", 
            content
        );

        var responseString = await response.Content.ReadAsStringAsync();
        
        if (response.IsSuccessStatusCode)
        {
            var result = JsonSerializer.Deserialize<ApiResponse>(responseString);
            Console.WriteLine($"登录成功: {result.Data.UserInfo.Phone}");
            return result.Data;
        }
        else
        {
            var error = JsonSerializer.Deserialize<ApiError>(responseString);
            Console.WriteLine($"登录失败: {error.Message}");
            return null;
        }
    }
}

public class LoginResponse
{
    public string Token { get; set; }
    public int ExpiresIn { get; set; }
    public string RefreshToken { get; set; }
    public UserInfo UserInfo { get; set; }
}

public class UserInfo
{
    public int Id { get; set; }
    public string Phone { get; set; }
    public string Nickname { get; set; }
    public string Role { get; set; }
}
```

---

## 🔄 Token 使用说明

### 后续请求携带 Token

登录成功后，所有需要认证的 API 请求都需要在请求头中携带 Access Token：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 示例

```javascript
// JavaScript/Axios
axios.get('/api/v1/user/subscription', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

```python
# Python/Requests
headers = {
    'Authorization': f'Bearer {access_token}'
}
response = requests.get('https://your-domain.com/api/v1/user/subscription', headers=headers)
```

```csharp
// C#/HttpClient
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", access_token);
    
var response = await client.GetAsync("https://your-domain.com/api/v1/user/subscription");
```

---

## ⚙️ 设备会话管理

### 多端登录策略

| 设备类型 | device_id 标识 | 单点登录范围 | 互斥关系 |
|---------|---------------|-------------|---------|
| 网页端 | 包含 "web" | 仅踢出其他网页端 | 独立 |
| 客户端软件 | 包含 "client" | 仅踢出其他客户端 | 独立 |
| **小工具** | **包含 "tool"** | **仅踢出其他小工具** | **独立** |

### 示例场景

```
用户在以下设备同时登录：
1. 网页端：device_id = "web-chrome-xxx"  ✅ 正常登录
2. 客户端：device_id = "client-windows-xxx"  ✅ 正常登录
3. 小工具：device_id = "tool-windows-xxx"  ✅ 正常登录

当用户在另一台设备使用小工具登录：
4. 小工具2：device_id = "tool-macos-yyy"  ✅ 登录成功
   
结果：
- 设备 1（网页端）：✅ 保持登录
- 设备 2（客户端）：✅ 保持登录
- 设备 3（小工具1）：❌ 被踢出
- 设备 4（小工具2）：✅ 登录成功
```

---

## 🔍 常见问题 (FAQ)

### Q1: 为什么 device_id 必须包含 "tool"？

**A**: 这是服务端用于区分设备类型的关键标识。包含 "tool" 的设备会被识别为小工具端，从而实现独立的会话管理，不与客户端软件和网页端冲突。

---

### Q2: device_id 应该如何生成？

**A**: 建议使用以下格式：
```
tool-{平台}-{机器标识}-{UUID}
```

- **平台**: windows、macos、linux 等
- **机器标识**: 机器名或硬件标识（可选）
- **UUID**: 唯一随机 ID

**重要**：device_id 应该在应用首次启动时生成并持久化保存，之后每次登录使用同一个 ID。

---

### Q3: 可以同时在多台设备使用小工具吗？

**A**: 不可以。同一账号在小工具端只能保持一台设备登录。如果在新设备登录，旧设备会被强制退出。

但是，小工具的登录不会影响客户端软件和网页端的登录状态。

---

### Q4: Token 过期了怎么办？

**A**: 使用 Refresh Token 获取新的 Access Token：

```javascript
POST /api/v1/auth/refresh
{
  "refresh_token": "your_refresh_token_here"
}
```

详见后续 **Token 刷新接口** 文档。

---

### Q5: 如何判断用户是否有权使用小工具？

**A**: 登录成功后，需要查询用户的订阅信息：

```javascript
GET /api/v1/user/subscription
Authorization: Bearer {access_token}
```

根据订阅状态判断用户权限。详见 **用户订阅查询接口** 文档。

---

## 🛠️ 错误码速查表

| 错误码 | HTTP 状态码 | 说明 | 解决方法 |
|-------|------------|------|---------|
| 1001 | 400 | 参数验证错误 | 检查请求参数格式 |
| 2001 | 401 | 用户不存在 | 检查手机号是否正确 |
| 2002 | 401 | 密码错误 | 检查密码是否正确 |
| 2003 | 403 | 账号被禁用 | 联系管理员解封 |
| 1000 | 500 | 服务器内部错误 | 联系技术支持 |

---

## 📞 技术支持

如有疑问，请联系技术支持：
- **邮箱**: support@videosage.com
- **文档更新**: 2025-10-07

---

**修改完毕，请手动测试。**


