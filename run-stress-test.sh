#!/bin/bash
# ============================================================
# 灵眸电商AI中台 — 压力测试运行脚本
# ============================================================
# 用法:
#   bash run-stress-test.sh 01                    # 单项目压测 (100用户, 5分钟)
#   bash run-stress-test.sh 01 --users=200 --run-time=10m  # 自定义
#   bash run-stress-test.sh all                   # 全量顺序压测
#   bash run-stress-test.sh all --users=50 --run-time=3m   # 全量快测
# ============================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_DIR="$BASE_DIR/stress-reports"
mkdir -p "$REPORT_DIR"

# 各项目对应的端口和目录名
# 格式: "项目编号|端口|目录前缀|项目名称"
declare -A PORTS
PORTS[1]="8101|01-RAG智能客服系统|①智能客服助手"
PORTS[2]="8202|02-AI自媒体内容助手|②灵笔内容引擎"
PORTS[3]="8000|03-AI短视频脚本工坊|③视界短视频工坊"
PORTS[4]="8400|04-AI素材管理平台|④图库资产管家"
PORTS[5]="8505|05-AI销售培训系统|⑤话术对战教练"
PORTS[6]="8606|06-AI数据中心平台|⑥数据中枢"
PORTS[7]="8707|07-MCP多智能体协作平台|⑦智能运营引擎"
PORTS[8]="8808|08-AI模型微调训练平台|⑧模型定制工厂"

# 默认参数
USERS=100
SPAWN_RATE=10
RUN_TIME="5m"

cyan()  { echo -e "\033[36m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }

# 解析参数
TARGET="${1:-}"
shift 2>/dev/null || true
while [ $# -gt 0 ]; do
    case "$1" in
        --users=*)     USERS="${1#*=}" ;;
        --spawn-rate=*) SPAWN_RATE="${1#*=}" ;;
        --run-time=*)  RUN_TIME="${1#*=}" ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$TARGET" ]; then
    echo "用法: $0 <项目编号|all> [--users=100] [--spawn-rate=10] [--run-time=5m]"
    echo "项目: 1=①客服 2=②自媒体 3=③短视频 4=④素材 5=⑤销售 6=⑥数据 7=⑦多Agent 8=⑧微调"
    exit 1
fi

run_one() {
    local num=$1
    local info="${PORTS[$num]}"
    local port=$(echo "$info" | cut -d'|' -f1)
    local dirname=$(echo "$info" | cut -d'|' -f2)
    local label=$(echo "$info" | cut -d'|' -f3)
    local dir="$BASE_DIR/$dirname/backend"
    local report="$REPORT_DIR/stress-p${num}-$(date +%Y%m%d-%H%M%S).html"

    if [ ! -f "$dir/tests/locustfile.py" ]; then
        echo "  ⚠ $label — locustfile 不存在，跳过"
        return
    fi

    cyan ""
    cyan "=============================================="
    cyan "  $label — 压力测试"
    cyan "  并发: ${USERS}用户 | 启动速率: ${SPAWN_RATE}/s | 时长: ${RUN_TIME}"
    cyan "=============================================="
    echo ""

    cd "$dir"
    locust -f tests/locustfile.py \
        --host="http://localhost:${port}" \
        --users="$USERS" \
        --spawn-rate="$SPAWN_RATE" \
        --run-time="$RUN_TIME" \
        --headless \
        --html="$report" \
        --csv="$REPORT_DIR/stress-p${num}" \
        --csv-disable-labels \
        --stop-timeout=30 \
        2>&1 || true

    if [ -f "$report" ]; then
        green "  ✓ 报告已保存: $report"
    fi
}

if [ "$TARGET" == "all" ]; then
    cyan "=============================================="
    cyan "  全量压力测试 — 8 个项目顺序执行"
    cyan "  并发: ${USERS} | 时长: ${RUN_TIME}/项目"
    cyan "  预计总耗时: ~$((${#PORTS[@]} * ${RUN_TIME%m} + 2)) 分钟"
    cyan "=============================================="
    for i in 1 2 3 4 5 6 7 8; do
        run_one "$i"
    done
    echo ""
    green "全部压测完成！报告目录: $REPORT_DIR"
else
    run_one "$TARGET"
fi
