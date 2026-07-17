# VPS 剩余价值计算器

一个用于估算 VPS 套餐剩余价值的开源工具，基于 [hahabye/vps_jsq](https://github.com/hahabye/vps_jsq) 维护和增强。

本项目保留原项目的 GPL-3.0 许可证，并在此基础上增加了简洁的响应式前端、输入校验完善的 Python API、SVG 分享卡片、Docker Compose 部署、自动化测试和 GitHub Actions。

在线示例：https://tool.beaver1376.top/

## 功能特点

- 支持月付、季付、半年付、年付、两年付、三年付和五年付
- 自动获取参考汇率，同时支持自定义汇率估值
- 按自然月和实际天数计算，不简单按每月 30 天处理
- 自动生成简洁、清晰的 SVG 分享卡片
- 一键复制 Markdown 图片格式
- 响应式页面，兼容电脑和手机浏览器
- 请求体大小、输入数值和生成文件数量均有限制
- Web 与 API 使用独立的非 root 容器运行
- 内置健康检查、自动化测试和持续集成

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/Tumb1er1376/vps-residual-value-calculator.git
cd vps-residual-value-calculator
```

### 2. 创建配置

```bash
cp .env.example .env
```

编辑 `.env`，将 `PUBLIC_BASE_URL` 改成你的实际访问地址：

```env
PUBLIC_BASE_URL=https://vps.example.com
WEB_PORT=18088
API_PORT=18089
```

### 3. 启动服务

```bash
docker compose up -d --build
```

默认监听地址：

- Web 页面（同时代理 `/api/` 和 `/share/`）：`http://127.0.0.1:18088`
- API 调试端口：`http://127.0.0.1:18089`

服务端口默认只绑定到本机回环地址，建议通过 Caddy、Nginx 或其他反向代理提供 HTTPS 访问。

项目提供了 Caddy 配置示例：

```text
deploy/Caddyfile.example
```

使用时请将示例域名 `vps.example.com` 替换成你的域名。

## 配置说明

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `PUBLIC_BASE_URL` | `http://localhost:18088` | 生成分享图片链接时使用的公开访问地址 |
| `WEB_PORT` | `18088` | Web 服务绑定的本机端口 |
| `API_PORT` | `18089` | API 服务绑定的本机端口 |
| `WEB_IMAGE` | 本地构建 | 可选的预构建 Web 镜像 |
| `API_IMAGE` | 本地构建 | 可选的预构建 API 镜像 |

生成的 SVG 分享卡片保存在 Docker 的 `share-data` 数据卷中。程序最多保留 2,000 个分享文件，也可以额外配置定时任务清理超过指定天数的文件。

## 计算口径

用户填写的续费价格被视为所选付款周期的完整价格，例如：

- 月付 10 美元：显示为 `人民币/月`
- 年付 10 美元：显示为 `人民币/年`

剩余价值按照交易日期到到期日期之间的全部实际天数计算，不限制在单个付款周期内。

因此，一台月付 VPS 如果剩余时间超过一个月，其剩余价值可能高于页面显示的单月周期价格。这是本项目有意保留的计算规则。

## 本地开发与测试

### 运行后端测试

```bash
python3 -m unittest discover -s tests -v
```

### 检查前端资源

```bash
python3 scripts/check_web_assets.py
```

### 构建容器

```bash
docker compose build
```

## API 说明

### 获取参考汇率

```http
GET /api/vps/rates
```

返回当前支持币种相对于人民币的参考汇率。当上游汇率服务暂时不可用时，API 会使用内置的备用汇率，保证页面仍可使用。

### 计算 VPS 剩余价值

```http
POST /api/vps/jsq
Content-Type: application/json
```

请求示例：

```json
{
  "exchange_rate": "6.780",
  "custom_exchange_rate": "7.000",
  "renew_money": "10",
  "currency_code": "USD",
  "cycle": "monthly",
  "expiry_date": "2026-12-31",
  "trade_date": "2026-07-18"
}
```

API 请求体上限为 16 KiB，并且必须使用 `application/json`。

## 目录结构

```text
.
├── api_server.py              # Python API、计算逻辑和 SVG 生成
├── web/                       # 前端页面和静态资源
├── tests/                     # 后端回归测试
├── docker/                    # Web/API 镜像与 Nginx 配置
├── deploy/                    # 反向代理配置示例
├── scripts/                   # 项目检查脚本
├── docker-compose.yml         # 完整容器编排
└── .github/workflows/         # CI 和镜像发布工作流
```

## 安全与部署建议

- 建议仅将 Web/API 端口绑定到 `127.0.0.1`，通过 HTTPS 反向代理对外提供服务
- 公网流量较大时，建议对 `/api/vps/jsq` 增加限流
- 不要将 `.env`、分享 SVG、备份文件、日志或运行缓存提交到 Git
- Web 和 API 镜像均使用非 root 用户运行
- API 容器默认使用只读根文件系统，并移除全部 Linux capabilities

## GitHub Actions

项目包含两个工作流：

- `CI`：检查 Python 语法、运行单元测试、验证前端资源并构建容器
- `Publish container images`：创建版本标签后，将 Web/API 多架构镜像发布到 GHCR

## 上游项目与许可证

本项目基于 [hahabye/vps_jsq](https://github.com/hahabye/vps_jsq) 修改和维护，并保留原项目 Git 历史及署名。

项目使用 [GNU General Public License v3.0](LICENSE.txt)。公开分发修改版本时，需要继续遵循 GPL-3.0，并保留相应的许可证和版权声明。

项目内置的 flatpickr 4.6.13 使用 MIT 许可证，完整第三方软件声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
