"""
벤치마크 결과 JSON의 raw 시계열 데이터를 matplotlib 차트로 시각화
Usage: uv run tests/plot_benchmark.py <result.json>
"""
import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt

# Stage별 색상
STAGE_COLORS = {
    "read": "#3498db",
    "transform": "#e67e22",
    "write": "#2ecc71",
}
DEFAULT_COLOR = "#9b59b6"


def plot_round(ax_mem: plt.Axes, result: dict, title: str):
    """단일 라운드의 시계열 차트"""
    raw = result["raw"]
    samples = raw["samples"]
    events = raw["events"]

    t = [s["t"] for s in samples]
    cpu = [s["cpu"] for s in samples]
    mem = [s["mem_mb"] for s in samples]

    # 메모리 (좌측 Y축)
    ax_mem.set_xlabel("Time (sec)")
    ax_mem.set_ylabel("Memory (MB)", color="#3498db")
    ax_mem.plot(t, mem, color="#3498db", linewidth=2.5, label="Memory (MB)", zorder=3)
    ax_mem.tick_params(axis="y", labelcolor="#3498db")

    # CPU (우측 Y축)
    ax_cpu = ax_mem.twinx()
    ax_cpu.set_ylabel("CPU (%)", color="#e74c3c")
    ax_cpu.plot(t, cpu, color="#e74c3c", alpha=0.5, linestyle=":", label="CPU (%)", zorder=2)
    ax_cpu.set_ylim(0, max(cpu) + 20 if cpu else 100)
    ax_cpu.tick_params(axis="y", labelcolor="#e74c3c")

    # Stage 구간 표시
    end_time = t[-1] if t else 0
    for i, event in enumerate(events):
        stage = event["stage"]
        start = event["start_time"]
        end = events[i + 1]["start_time"] if i + 1 < len(events) else end_time
        color = STAGE_COLORS.get(stage, DEFAULT_COLOR)

        ax_mem.axvspan(start, end, color=color, alpha=0.15)
        mid = (start + end) / 2
        ax_cpu.text(
            mid, 0.93, stage,
            horizontalalignment="center",
            fontweight="bold",
            fontsize=10,
            color=color,
            transform=ax_cpu.get_xaxis_transform(),
        )

    ax_mem.set_title(title, fontsize=13, fontweight="bold")
    ax_mem.grid(True, alpha=0.3)

    # 범례 합치기
    lines1, labels1 = ax_mem.get_legend_handles_labels()
    lines2, labels2 = ax_cpu.get_legend_handles_labels()
    ax_mem.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_benchmark.py <result.json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    with open(json_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # strategy별로 그룹핑
    strategies: dict[str, list] = {}
    for r in results:
        strategies.setdefault(r["strategy"], []).append(r)

    # strategy × round 서브플롯
    n_strategies = len(strategies)
    n_rounds = max(len(v) for v in strategies.values())

    fig, axes = plt.subplots(
        n_strategies, n_rounds,
        figsize=(7 * n_rounds, 5 * n_strategies),
        squeeze=False,
    )

    for row, (strategy, rounds) in enumerate(strategies.items()):
        for col, result in enumerate(rounds):
            title = f"{strategy} — Round {result['round']}"
            plot_round(axes[row][col], result, title)

    fig.suptitle(
        f"Benchmark: {json_path.stem}",
        fontsize=16, fontweight="bold", y=1.01,
    )
    plt.tight_layout()

    # 저장
    output_path = json_path.with_suffix(".png")
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"📊 Chart saved to: {output_path}")
    plt.show()


if __name__ == "__main__":
    main()
