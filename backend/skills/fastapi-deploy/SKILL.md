---
name: fastapi-deploy
description: FastAPI 应用部署，依赖 Docker 和 Python 编码技能。
version: 1.0.0
keywords:
  - fastapi
  - deploy
  - 部署
  - uvicorn
depends_on:
  - docker
  - python-coding
---

## 部署步骤

1. 编写 Dockerfile
2. 配置 docker-compose
3. 设置反向代理（nginx/caddy）
4. 配置 systemd 服务
5. 健康检查

## Dockerfile 示例

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```

## 健康检查

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```
