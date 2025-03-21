# Docker 使用说明

本项目支持使用 Docker 进行部署，使用 Docker 可以更方便地在不同环境中运行应用，无需担心环境依赖问题。

## 使用 Docker Compose (推荐)

推荐使用 Docker Compose 来管理容器，这样可以更轻松地配置和管理服务。

### 步骤：

1. 确保已安装 Docker 和 Docker Compose
   ```bash
   docker --version
   docker-compose --version
   ```

2. 在项目根目录下运行：
   ```bash
   docker-compose up -d
   ```
   `-d` 参数使容器在后台运行

3. 应用将在 http://localhost:1832 运行

4. 查看容器日志：
   ```bash
   docker-compose logs -f
   ```

5. 停止和移除容器：
   ```bash
   docker-compose down
   ```

## 直接使用 Docker

如果您不想使用 Docker Compose，也可以直接使用 Docker 命令：

1. 构建镜像：
   ```bash
   docker build -t datasheet-ai-analyzer .
   ```

2. 运行容器：
   ```bash
   docker run -d -p 1832:1832 --name datasheet-ai-analyzer -v $(pwd)/uploads:/app/uploads datasheet-ai-analyzer
   ```

3. 应用将在 http://localhost:1832 运行

4. 查看容器日志：
   ```bash
   docker logs -f datasheet-ai-analyzer
   ```

5. 停止和移除容器：
   ```bash
   docker stop datasheet-ai-analyzer
   docker rm datasheet-ai-analyzer
   ```

## 数据持久化

上传的文件将被保存在主机的 `uploads` 目录中，通过卷映射到容器内部的 `/app/uploads` 目录。这样即使容器被移除，数据仍然保留在主机上。

## 配置说明

如果需要修改配置，可以通过以下方式：

1. 在运行容器前，编辑 `config.json` 文件

2. 如果需要更改端口映射，可以编辑 `docker-compose.yml` 文件中的端口配置：
   ```yaml
   ports:
     - "自定义端口:1832"
   ```

3. 重启容器以应用更改：
   ```bash
   docker-compose down
   docker-compose up -d
   ``` 