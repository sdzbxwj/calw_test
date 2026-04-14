#!/bin/bash
# git-ci-trigger.sh - Git 感知 CI 触发脚本（精简版）
# 用于 pre-push hook 调用，检测变更并准备测试

set -e

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BRANCH="${TARGET_BRANCH:-main}"
LAST_TESTED_FILE="$REPO_ROOT/.git/last-tested-commit"
PENDING_FILE="$REPO_ROOT/.git/last-pending-commit"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检测当前分支
current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
if [[ "$current_branch" != "$BRANCH" && "$current_branch" != "master" ]]; then
  log_warn "当前分支为 $current_branch，非 $BRANCH/master，跳过测试触发"
  exit 0
fi

# 获取当前 commit
current_commit=$(git rev-parse HEAD 2>/dev/null)
if [[ -z "$current_commit" ]]; then
  log_error "无法获取当前 commit"
  exit 1
fi

# 读取上次已测试的 commit
last_tested_commit=""
if [[ -f "$LAST_TESTED_FILE" ]]; then
  last_tested_commit=$(cat "$LAST_TESTED_FILE")
fi

# 判断是否需要跑测试
if [[ "$current_commit" == "$last_tested_commit" ]]; then
  log_info "✅ 无新变更，已测试至 ${current_commit:0:8}"
  exit 0
fi

# 获取变更文件列表
if [[ -n "$last_tested_commit" ]]; then
  changed_files=$(git diff --name-only "$last_tested_commit" "$current_commit" 2>/dev/null)
else
  # 首次运行，获取最近 5 个 commit 的变更
  changed_files=$(git diff --name-only HEAD~5 HEAD 2>/dev/null || git ls-files)
fi

# 过滤出源代码文件 (Python, Go, Java, JS/TS 等)
source_files=$(echo "$changed_files" | grep -E '\.(py|go|java|js|ts|jsx|tsx)$' || true)

if [[ -z "$source_files" ]]; then
  log_info "📄 无源代码变更，跳过测试"
  echo "$current_commit" > "$LAST_TESTED_FILE"
  rm -f "$PENDING_FILE"
  exit 0
fi

log_info "📝 检测到 ${source_files} 行代码变更"

# 输出待检测的文件供后续流程使用
echo "$source_files" > "$REPO_ROOT/.git/pending-changes.txt"
echo "$current_commit" > "$PENDING_FILE"

exit 0
