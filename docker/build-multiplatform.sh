#!/usr/bin/env bash
# Git Bash / WSL / Linux / macOS；构建一个包含全部服务的镜像。
# 在项目根目录运行：
# 本机：bash docker/build-multiplatform.sh --load && docker compose --env-file .env -f docker/docker-compose.yml up -d --no-build
# 发布：DOCKER_NAMESPACE=your-name IMAGE_VERSION=1.0.0 bash docker/build-multiplatform.sh --push
# PowerShell：docker compose --env-file .env -f docker/docker-compose.yml up -d --build
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

mode="${1:---load}"
if [[ $# -gt 1 ]] || [[ "$mode" != '--load' && "$mode" != '--push' ]]; then
    echo "Usage: bash build-multiplatform.sh [--load|--push]" >&2
    exit 1
fi

docker buildx version
docker buildx inspect --bootstrap >/dev/null

if [[ "$mode" == '--push' ]]; then
    : "${DOCKER_NAMESPACE:?Set DOCKER_NAMESPACE to your registry namespace first}"
    registry="${DOCKER_REGISTRY:-docker.io}"
    if [[ "$registry" == *://* ]]; then
        echo "DOCKER_REGISTRY must be a hostname, e.g. docker.io (no https://)." >&2
        exit 1
    fi
    platforms="${PLATFORMS:-linux/amd64,linux/arm64}"
    version="${IMAGE_VERSION:-latest}"
    image="${registry%/}/${DOCKER_NAMESPACE}/testhub:${version}"
    # 发布前手动 docker login；多架构构建器可用以下命令创建：
    # docker buildx create --name testhub-builder --driver docker-container --use
else
    platforms="${PLATFORMS:-$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')}"
    if [[ "$platforms" == *,* ]]; then
        echo "--load requires one platform; use --push for multiple platforms." >&2
        exit 1
    fi
    image="${TESTHUB_IMAGE:-testhub:local}"
fi

docker buildx build --platform "$platforms" \
    --file docker/Dockerfile.multiplatform \
    --tag "$image" "$mode" .

printf 'TestHub image: %s\n' "$image"
