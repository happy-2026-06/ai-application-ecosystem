#!/bin/bash
# ============================================================
# 灵眸电商AI中台 — 一键代码审查 + 测试脚本
# ============================================================
# 用法:
#   bash check-all.sh           # 全量检查（ruff + eslint + pytest）
#   bash check-all.sh --quick   # 快速检查（只 ruff，不跑测试）
#   bash check-all.sh --test    # 只跑 pytest
# ============================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
QUICK=false
TEST_ONLY=false

[[ "$1" == "--quick" ]] && QUICK=true
[[ "$1" == "--test" ]] && TEST_ONLY=true

PASS=0
FAIL=0

green() { echo -e "\033[32m$1\033[0m"; }
red()   { echo -e "\033[31m$1\033[0m"; }
cyan()  { echo -e "\033[36m$1\033[0m"; }

check_dir() {
    # Find project backend dirs by pattern: 0X-*/backend
    for p in "$BASE_DIR"/0[1-8]-*/backend; do
        [ -d "$p" ] && echo "$p"
    done
}

# ─── Ruff 后端检查 ───────────────────────────────
if ! $TEST_ONLY; then
    cyan "=============================================="
    cyan "  第1步: Python 代码风格 + 潜在问题 (ruff)"
    cyan "=============================================="
    echo ""
    for dir in $(check_dir); do
        proj_name=$(echo "$dir" | sed 's|.*/0\([0-9]\)-.*|项目\1|')
        if ruff check "$dir" --quiet 2>/dev/null; then
            green "  ✓ $proj_name 后端  — 代码风格通过"
            PASS=$((PASS + 1))
        else
            red "  ✗ $proj_name 后端  — 有问题（详情见下）"
            ruff check "$dir" 2>&1 | head -20
            FAIL=$((FAIL + 1))
        fi
    done
fi

# ─── 前端检查（有 Node.js 才跑）─────────────────
if ! $TEST_ONLY && ! $QUICK; then
    echo ""
    cyan "=============================================="
    cyan "  第2步: 前端 Vue/TS 检查 (vue-tsc)"
    cyan "=============================================="
    echo ""
    if command -v npx &>/dev/null; then
        for dir in "$BASE_DIR"/0[1-8]-*/frontend; do
            [ -d "$dir" ] || continue
            proj_name=$(echo "$dir" | sed 's|.*/0\([0-9]-.*\)/frontend|项目\1|')
            if (cd "$dir" && npx vue-tsc --noEmit 2>&1 | tail -5) then
                green "  ✓ $proj_name 前端  — 类型检查通过"
                PASS=$((PASS + 1))
            else
                red "  ✗ $proj_name 前端  — 类型错误"
                FAIL=$((FAIL + 1))
            fi
        done
    else
        echo "  (跳过 — Node.js/npx 不可用)"
    fi
fi

# ─── 安全扫描 ───────────────────────────────────
if ! $TEST_ONLY && ! $QUICK; then
    echo ""
    cyan "=============================================="
    cyan "  第3步: 安全扫描（密钥泄露 + 大文件）"
    cyan "=============================================="
    echo ""
    # 扫描硬编码密钥
    KEYS_FOUND=$(grep -rn "sk-[a-zA-Z0-9]\{20,\}" "$BASE_DIR" \
        --include="*.py" --include="*.ts" --include="*.env*" \
        --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__ \
        --exclude-dir=chroma --exclude-dir=data 2>/dev/null | wc -l || true)
    if [ "$KEYS_FOUND" -gt 0 ]; then
        red "  ✗ 发现 $KEYS_FOUND 处疑似硬编码 API Key"
        FAIL=$((FAIL + 1))
    else
        green "  ✓ 未发现硬编码密钥"
        PASS=$((PASS + 1))
    fi

    # 检查 .gitignore
    if [ -f "$BASE_DIR/.gitignore" ]; then
        for pattern in ".env" "*.db" "__pycache__" "node_modules" "dist" "chroma"; do
            if ! grep -q "$pattern" "$BASE_DIR/.gitignore"; then
                red "  ✗ .gitignore 缺少: $pattern"
                FAIL=$((FAIL + 1))
            fi
        done
        green "  ✓ .gitignore 检查完成"
        PASS=$((PASS + 1))
    fi
fi

# ─── Pytest 单元测试 ─────────────────────────────
if ! $QUICK; then
    echo ""
    cyan "=============================================="
    cyan "  第4步: 后端单元测试 (pytest)"
    cyan "=============================================="
    echo ""
    for dir in $(check_dir); do
        proj_name=$(echo "$dir" | sed 's|.*/0\([0-9]-.*\)/backend|项目\1|')
        if [ -f "$dir/pytest.ini" ] || [ -f "$dir/tests/conftest.py" ]; then
            if (cd "$dir" && python -m pytest tests/ -q --tb=short -x 2>&1); then
                green "  ✓ $proj_name 后端  — 测试全部通过"
                PASS=$((PASS + 1))
            else
                red "  ✗ $proj_name 后端  — 测试失败"
                FAIL=$((FAIL + 1))
            fi
        else
            echo "  - $proj_name 后端  — 无测试配置，跳过"
        fi
    done
fi

# ─── 汇总 ───────────────────────────────────────
echo ""
cyan "=============================================="
cyan "  审查完成"
cyan "=============================================="
echo ""
green "  通过: $PASS"
if [ "$FAIL" -gt 0 ]; then
    red "  失败: $FAIL"
    exit 1
else
    green "  全部通过！🎉"
    exit 0
fi
