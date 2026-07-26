---
name: docker
description: Docker 容器管理、镜像构建、docker-compose 编排。
version: 1.0.0
keywords:
  - docker
  - container
  - docker-compose
  - Dockerfile
  - 镜像
  - 容器
---

## 常用命令

- `docker build -t name:tag .` — 构建镜像
- `docker run -d -p 8080:80 name` — 运行容器
- `docker-compose up -d` — 启动服务栈
- `docker logs -f container_name` — 查看日志

## docker-compose.yml 模板

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8080:80"
    volumes:
      - .:/app
```

## 最佳实践

- 使用多阶段构建减小镜像
- 不要以 root 运行容器进程
- 使用 `.dockerignore` 排除无用文件
