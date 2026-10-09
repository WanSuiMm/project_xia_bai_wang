"""Offline, non-renormalizing finite-stimulus analysis of OSI48."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean

import run_opponent_strategy_inference as study


def action(p):
    return "A" if p > .75 else "B" if p < .25 else "ABSTAIN"


def loss(decision, posterior):
    return 1-posterior if decision == "A" else posterior if decision == "B" else .25


def _item(run, row):
    out = {key: row[key] for key in ("request_id", "model", "simulation_condition",
           "history_ones", "ones_seat", "repeat", "posterior_A", "plugin_posterior_A")}
    path = run / f"responses/{row['request_id']}.json"
    out.update(status="missing", strict_valid=False, p_A=None, p_1111=None, decision=None)
    if not path.exists():
        return out
    rec = study.read(path)
    out.update(status="invalid", receipt_status=rec["status"], parse_status=rec["parse_status"],
               completion_parse_status=rec["completion_parse_status"])
    if (rec["status"] != "response_received" or rec.get("returned_model") != row["model"]
            or rec["completion_parse_status"] != "valid"):
        return out
    parsed = rec["completion_parsed"]
    p, gold = parsed["p_A"], row["posterior_A"]
    out.update(status="valid", strict_valid=rec["parse_status"] == "valid",
               p_A=p, p_1111=p if row["ones_seat"] == "A" else 1-p,
               decision=parsed["decision"], squared_error=(p-gold)**2,
               absolute_error=abs(p-gold), plugin_squared_distance=(p-row["plugin_posterior_A"])**2,
               expected_decision_loss=loss(parsed["decision"], gold),
               optimal_decision_loss=min(gold, 1-gold, .25),
               action_matches_report=parsed["decision"] == action(p),
               action_matches_oracle=parsed["decision"] == action(gold),
               within_1e4=abs(p-gold) <= 1e-4, format_acceptance=rec["format_acceptance"])
    return out


def _cell(items, model, condition, strict=False):
    group = [r for r in items if r["model"] == model and r["simulation_condition"] == condition]
    valid = [r for r in group if r["status"] == "valid" and (r["strict_valid"] or not strict)]
    complete = len(valid) == len(group) == 12
    out = {"model": model, "simulation_condition": condition, "planned": len(group),
           "valid": len(valid), "complete": complete,
           "posterior_mse": None, "posterior_mae": None, "max_absolute_error": None,
           "plugin_squared_distance": None, "expected_decision_loss": None,
           "optimal_decision_loss": None, "excess_decision_loss": None,
           "within_1e4_count": sum(r["within_1e4"] for r in valid),
           "observed_squared_error_sum": sum(r["squared_error"] for r in valid),
           "action_matches_report_count": sum(r["action_matches_report"] for r in valid),
           "action_matches_oracle_count": sum(r["action_matches_oracle"] for r in valid),
           "history_means": {}, "history_delta": None,
           "seat_complement_mean_absolute_residual": None,
           "repeat_mean_bias_squared": None, "repeat_mean_within_cell_variance": None}
    for s in study.HISTORIES:
        sub = [r for r in valid if r["history_ones"] == s]
        out["history_means"][str(s)] = {
            "planned": 4, "valid": len(sub),
            "p_1111": mean(r["p_1111"] for r in sub) if len(sub) == 4 else None}
    if not complete:
        return out
    out.update(posterior_mse=mean(r["squared_error"] for r in valid),
               posterior_mae=mean(r["absolute_error"] for r in valid),
               max_absolute_error=max(r["absolute_error"] for r in valid),
               plugin_squared_distance=mean(r["plugin_squared_distance"] for r in valid),
               expected_decision_loss=mean(r["expected_decision_loss"] for r in valid),
               optimal_decision_loss=mean(r["optimal_decision_loss"] for r in valid))
    out["excess_decision_loss"] = out["expected_decision_loss"]-out["optimal_decision_loss"]
    out["history_delta"] = out["history_means"]["1"]["p_1111"]-out["history_means"]["7"]["p_1111"]
    indexed = {(r["history_ones"], r["ones_seat"], r["repeat"]): r for r in valid}
    out["seat_complement_mean_absolute_residual"] = mean(
        abs(indexed[s, "A", rep]["p_A"]+indexed[s, "B", rep]["p_A"]-1)
        for s in study.HISTORIES for rep in (1, 2))
    biases, variances = [], []
    for s in study.HISTORIES:
        for seat in ("A", "B"):
            pair = [indexed[s, seat, rep] for rep in (1, 2)]
            avg = mean(r["p_A"] for r in pair)
            biases.append((avg-pair[0]["posterior_A"])**2)
            variances.append(mean((r["p_A"]-avg)**2 for r in pair))
    out["repeat_mean_bias_squared"] = mean(biases)
    out["repeat_mean_within_cell_variance"] = mean(variances)
    assert abs(out["posterior_mse"]-mean(biases)-mean(variances)) < 1e-12
    return out


def analyze(run, write=True):
    manifest = study.audit(run, live_sources=False)
    rows = study.read(run / "schedule.json")
    items = [_item(run, row) for row in rows]
    valid = [r for r in items if r["status"] == "valid"]
    cells = [_cell(items, model, condition) for model in study.MODELS for condition in study.CONDITIONS]
    strict_cells = [_cell(items, model, condition, strict=True) for model in study.MODELS for condition in study.CONDITIONS]
    contrasts = []
    for model in study.MODELS:
        persistent = next(c for c in cells if c["model"] == model and c["simulation_condition"] == "PERSISTENT")
        refreshed = next(c for c in cells if c["model"] == model and c["simulation_condition"] == "REFRESHED")
        complete = persistent["complete"] and refreshed["complete"]
        difference = persistent["history_delta"]-refreshed["history_delta"] if complete else None
        contrasts.append({"model": model, "complete": complete,
            "persistent_delta": persistent["history_delta"], "persistent_delta_target": 65/67,
            "refreshed_delta": refreshed["history_delta"], "refreshed_delta_target": 0,
            "interaction": difference, "interaction_target": 65/67,
            "interaction_absolute_error": abs(difference-65/67) if complete else None})
    receipts = [study.read(p) for p in (run / "responses").glob("*.json")]
    usage = defaultdict(float)
    for rec in receipts:
        for key, value in rec.get("usage", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                usage[key] += value
    dispatched = len(list((run / "dispatches").glob("*.json")))
    received = len(receipts)
    state = ("COMPLETE_VALID" if len(valid) == study.TOTAL
             else "COMPLETE_WITH_INVALID" if received == study.TOTAL else "INCOMPLETE")
    summary = {
        "schema_version": 1, "study_id": manifest["study_id"], "analysis_utc": study.now(),
        "manifest_sha256": study.sha(run / "manifest.json"), "completion": state,
        "planned": study.TOTAL, "provider_requests": dispatched, "responses_received": received,
        "valid": len(valid), "strict_valid": sum(r["strict_valid"] for r in valid),
        "invalid": sum(r["status"] == "invalid" for r in items),
        "missing": sum(r["status"] == "missing" for r in items),
        "unreceived_dispatches": dispatched-received,
        "format_exception_count": sum(r.get("format_acceptance") == "identical_duplicate_trailer" for r in valid),
        "configuration_by_model": manifest["configuration_by_model"],
        "weighting": manifest["weighting"], "cells": cells, "contrasts": contrasts,
        "strict_only_cells": strict_cells, "usage_scalar_fields_summed": dict(usage),
        "limitations": [
            "Twelve selected mechanism-conditioned stimuli; 48 calls are not independent task families.",
            "No LLM Speaker, naturalistic interrogation, unknown model-family inference, or population capability estimate.",
            "Two repeats provide a descriptive finite-sample bias/variance identity only.",
            "Primary endpoints and contrasts are not renormalized when registered cells are invalid or missing.",
            "No scientific all-or-nothing threshold or correctness-selected retry."],
        "items": items}
    if write:
        folder = run / "analysis"
        study.dump(folder / "summary.json", summary)
        study.write_bytes(folder / "RESULTS.md", render(summary).encode("utf8"))
    return summary


def _fmt(value):
    return "—" if value is None else f"{value:.8f}"


def render(result):
    lines = ["# OSI48：对手历史与来源身份归因", "",
        f"状态：**{result['completion']}**。计划 {result['planned']} 次，已发送 {result['provider_requests']} 次，"
        f"收到 {result['responses_received']} 条，接受有效 {result['valid']} 条，严格有效 {result['strict_valid']} 条；"
        f"无效 {result['invalid']}、缺失 {result['missing']}。精确重复尾巴例外使用 {result['format_exception_count']} 次。", "",
        "当前四项回答固定，操纵历史中 1 的次数和历史／当前是否共享策略参数。没有新 LLM Speaker。"
        "以下是预先选定刺激的等权描述，48 次调用不是 48 个独立任务。缺失格不补权、不改写为完整结果。", "",
        "## 主要结果", "",
        "| 模型 | 条件 | 有效/计划 | 后验 MSE ↓ | 后验 MAE ↓ | 预期决策损失 ↓ | 超额决策损失 ↓ |", 
        "|---|---|---:|---:|---:|---:|---:|"]
    for cell in result["cells"]:
        lines.append(f"| {cell['model']} | {cell['simulation_condition']} | {cell['valid']}/{cell['planned']} | "
                     f"{_fmt(cell['posterior_mse'])} | {_fmt(cell['posterior_mae'])} | "
                     f"{_fmt(cell['expected_decision_loss'])} | {_fmt(cell['excess_decision_loss'])} |")
    lines += ["", "## 历史效应与策略重置", "",
        "座位已统一为 1111 回答者为 Reader 的概率。Δ 为 s=1 的平均概率减 s=7 的平均概率。"
        "理论目标：Persistent Δ=65/67，Refreshed Δ=0，二者之差为 65/67。", "",
        "| 模型 | Persistent Δ | Refreshed Δ | 两条件之差 | 与理论交互的绝对误差 |",
        "|---|---:|---:|---:|---:|"]
    for item in result["contrasts"]:
        lines.append(f"| {item['model']} | {_fmt(item['persistent_delta'])} | {_fmt(item['refreshed_delta'])} | "
                     f"{_fmt(item['interaction'])} | {_fmt(item['interaction_absolute_error'])} |")
    lines += ["", "| 模型 | 条件 | s=1 | s=4 | s=7 |", "|---|---|---:|---:|---:|"]
    for cell in result["cells"]:
        values = [_fmt(cell["history_means"][str(s)]["p_1111"]) for s in study.HISTORIES]
        lines.append(f"| {cell['model']} | {cell['simulation_condition']} | {' | '.join(values)} |")
    lines += ["", "## 预测积分、重复与座位", "",
        "精确积分目标为 66/67、1/2、1/67；用参数后验均值直接代入则为 256/257、1/2、1/257。"
        "两者都能反转且动作相同，因此方向正确不能单独证明正确积分或内部算法。"
        "两次重复的均值偏差平方与组内方差之和等于本刺激集 MSE；这不是总体方差估计。", "",
        "| 模型 | 条件 | 到 plug-in 的均方距离 | 均值偏差平方 | 组内方差 | 席位互补平均绝对残差 |",
        "|---|---|---:|---:|---:|---:|"]
    for cell in result["cells"]:
        lines.append(f"| {cell['model']} | {cell['simulation_condition']} | {_fmt(cell['plugin_squared_distance'])} | "
                     f"{_fmt(cell['repeat_mean_bias_squared'])} | {_fmt(cell['repeat_mean_within_cell_variance'])} | "
                     f"{_fmt(cell['seat_complement_mean_absolute_residual'])} |")
    lines += ["", "## 证据边界与复现", "",
        "报告连续偏差、方向、重置敏感性与缺失情况；没有新的总 PASS/FAIL 门槛。"
        "所有输出按精确提示词和接收记录绑定，严格解析敏感性、逐条结果及 token 用量见 summary.json。"
        "真实 LLM Bluffer 的策略学习、未知模型族推断、自然语言主动追问及跨任务泛化均未测试。", "",
        "从项目根离线运行：", "",
        "    python -X utf8 -B scripts/analyze_opponent_strategy_inference.py", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=study.DEFAULT_RUN)
    args = parser.parse_args()
    result = analyze(args.run.resolve())
    print(json.dumps({key: result[key] for key in (
        "completion", "planned", "provider_requests", "responses_received", "valid", "strict_valid", "invalid", "missing")}))


if __name__ == "__main__":
    main()
