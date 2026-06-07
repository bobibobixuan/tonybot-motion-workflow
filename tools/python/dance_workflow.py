import argparse
import html
import json
import pathlib

from rob_compose import WORKSPACE_ROOT, compile_recipe, detect_actions_dir, load_recipe_from_spec, load_recipe_spec, workspace_path


DEFAULT_ACTIONS_DIR = WORKSPACE_ROOT / "动作"


def relative_path(path):
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def resolve_output_path(value, fallback):
    if value:
        return workspace_path(value)
    return fallback


def create_template(output_path, name, prompt):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "prompt": prompt,
        "research": {
            "query": prompt,
            "summary": [
                "先用网页资料总结舞蹈的关键动作、节奏和情绪。",
                "再把动作拆成可复用的机器人动作段，并写进 segments。",
            ],
            "references": [],
        },
        "visualization": {
            "title": name,
            "theme": "sunset",
        },
        "output": {
            "rob": "动作/{}.rob".format(name),
            "report_json": "编舞/{}.report.json".format(name),
            "visualization_html": "编舞/{}.timeline.html".format(name),
        },
        "segments": [],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_payload(spec_path, spec, report, output_paths):
    total_duration = sum(item["duration_ms"] for item in report["segments"])
    return {
        "name": spec.get("name", spec_path.stem),
        "prompt": spec.get("prompt", ""),
        "research": spec.get("research", {}),
        "visualization": spec.get("visualization", {}),
        "outputs": {
            "rob": relative_path(output_paths["rob"]),
            "report_json": relative_path(output_paths["report_json"]),
            "visualization_html": relative_path(output_paths["visualization_html"]),
        },
        "compile": {
            "frame_count": report["frame_count"],
            "total_duration_ms": total_duration,
            "reference_files": report["reference_files"],
            "reference_frames": report["reference_frames"],
            "duration_range": report["duration_range"],
            "duration_p95": report["duration_p95"],
            "transition_l1_p95": report["transition_l1_p95"],
            "transition_l1_max": report["transition_l1_max"],
            "composed_max_l1": report["composed_max_l1"],
            "violations": report["violations"],
        },
        "segments": report["segments"],
        "boundaries": report["boundaries"],
    }


def render_timeline_html(payload):
    segments = payload["segments"]
    boundaries = payload["boundaries"]
    total_duration = max(payload["compile"]["total_duration_ms"], 1)
    summary_html = "".join(
        "<li>{}</li>".format(html.escape(str(item)))
        for item in payload.get("research", {}).get("summary", [])
    ) or "<li>暂无网页总结。</li>"
    reference_html = "".join(
        "<li><a href=\"{url}\">{title}</a></li>".format(
            url=html.escape(item.get("url", "#"), quote=True),
            title=html.escape(item.get("title") or item.get("url") or "reference"),
        )
        for item in payload.get("research", {}).get("references", [])
    ) or "<li>暂无参考链接。</li>"

    segment_cards = []
    current_start = 0
    for item in segments:
        width = max(6.0, item["duration_ms"] / total_duration * 100.0)
        segment_cards.append(
            """
            <article class=\"segment\" style=\"width: {width:.2f}%\">
              <div class=\"segment-top\">{label}</div>
              <div class=\"segment-meta\">{source}</div>
              <div class=\"segment-meta\">{duration} ms / {frames} 帧</div>
              <div class=\"segment-meta\">起始帧 {start}，结束帧 {end}</div>
              <p>{notes}</p>
            </article>
            """.format(
                width=width,
                label=html.escape(item["label"]),
                source=html.escape(item["source"]),
                duration=item["duration_ms"],
                frames=item["frame_count"],
                start=current_start,
                end=current_start + item["duration_ms"],
                notes=html.escape(item.get("notes") or "无备注"),
            )
        )
        current_start += item["duration_ms"]

    boundary_rows = []
    for item in boundaries:
        boundary_rows.append(
            """
            <tr class=\"level-{level}\">
              <td>{left} -> {right}</td>
              <td>{level}</td>
              <td>{max_delta}</td>
              <td>{l1}</td>
            </tr>
            """.format(
                left=html.escape(item["left"]),
                right=html.escape(item["right"]),
                level=html.escape(item["level"]),
                max_delta=item["max_delta"],
                l1=item["l1"],
            )
        )

    violations = payload["compile"]["violations"]
    violation_html = "<li>violations=0</li>" if not violations else "".join(
        "<li>{}</li>".format(html.escape(item)) for item in violations
    )

    return """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{title}</title>
  <style>
    :root {{
      --bg: linear-gradient(135deg, #f3efe6 0%, #f6d8ae 45%, #d9ecff 100%);
      --panel: rgba(255, 252, 245, 0.88);
      --ink: #1f2a32;
      --muted: #58666f;
      --accent: #c95d38;
      --accent-2: #2b7a78;
      --warn: #d98f00;
      --error: #b53232;
      --line: rgba(31, 42, 50, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Segoe UI", "PingFang SC", sans-serif; color: var(--ink); background: var(--bg); }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
    .hero {{ background: var(--panel); border: 1px solid var(--line); border-radius: 24px; padding: 28px; backdrop-filter: blur(12px); box-shadow: 0 14px 60px rgba(31, 42, 50, 0.08); }}
    h1, h2 {{ margin: 0 0 12px; }}
    p, li, td {{ line-height: 1.6; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-top: 20px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(31, 42, 50, 0.06); }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
    .metric {{ padding: 14px; border-radius: 16px; background: rgba(255,255,255,0.65); border: 1px solid var(--line); }}
    .metric strong {{ display: block; font-size: 24px; margin-bottom: 4px; color: var(--accent); }}
    .timeline {{ display: flex; gap: 10px; align-items: stretch; overflow-x: auto; padding-bottom: 10px; }}
    .segment {{ min-width: 180px; padding: 16px; border-radius: 18px; background: linear-gradient(180deg, rgba(201,93,56,0.16), rgba(43,122,120,0.10)); border: 1px solid rgba(31,42,50,0.14); flex: 0 0 auto; }}
    .segment-top {{ font-weight: 700; font-size: 18px; margin-bottom: 8px; }}
    .segment-meta {{ color: var(--muted); font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); }}
    .level-ok td:nth-child(2) {{ color: var(--accent-2); font-weight: 700; }}
    .level-warn td:nth-child(2) {{ color: var(--warn); font-weight: 700; }}
    .level-error td:nth-child(2) {{ color: var(--error); font-weight: 700; }}
    a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>{title}</h1>
      <p>{prompt}</p>
      <div class=\"metrics\">
        <div class=\"metric\"><strong>{frames}</strong><span>总帧数</span></div>
        <div class=\"metric\"><strong>{duration}</strong><span>总时长 ms</span></div>
        <div class=\"metric\"><strong>{max_l1}</strong><span>最大姿态跳变</span></div>
        <div class=\"metric\"><strong>{violations}</strong><span>安全违规数</span></div>
      </div>
    </section>
    <section class=\"grid\">
      <article class=\"card\">
        <h2>网页总结</h2>
        <ul>{summary_html}</ul>
      </article>
      <article class=\"card\">
        <h2>参考链接</h2>
        <ul>{reference_html}</ul>
      </article>
      <article class=\"card\">
        <h2>输出文件</h2>
        <ul>
          <li>.rob: {rob_output}</li>
          <li>report: {report_output}</li>
          <li>html: {html_output}</li>
        </ul>
      </article>
      <article class=\"card\">
        <h2>安全结论</h2>
        <ul>{violation_html}</ul>
      </article>
    </section>
    <section class=\"card\" style=\"margin-top: 18px;\">
      <h2>动作时间线</h2>
      <div class=\"timeline\">{segments_html}</div>
    </section>
    <section class=\"card\" style=\"margin-top: 18px;\">
      <h2>拼接边界审计</h2>
      <table>
        <thead>
          <tr><th>边界</th><th>级别</th><th>最大关节差</th><th>L1 总差</th></tr>
        </thead>
        <tbody>{boundary_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
""".format(
        title=html.escape(payload["visualization"].get("title") or payload["name"]),
        prompt=html.escape(payload["prompt"] or "暂无用户舞蹈需求说明。"),
        frames=payload["compile"]["frame_count"],
        duration=payload["compile"]["total_duration_ms"],
        max_l1=payload["compile"]["composed_max_l1"],
        violations=len(violations),
        summary_html=summary_html,
        reference_html=reference_html,
        rob_output=html.escape(payload["outputs"]["rob"]),
        report_output=html.escape(payload["outputs"]["report_json"]),
        html_output=html.escape(payload["outputs"]["visualization_html"]),
        violation_html=violation_html,
        segments_html="".join(segment_cards),
        boundary_rows="".join(boundary_rows),
    )


def write_build_outputs(spec_path, payload, output_paths):
    output_paths["report_json"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_paths["visualization_html"].write_text(render_timeline_html(payload), encoding="utf-8")
    print("spec={}".format(relative_path(spec_path)))
    print("rob={}".format(relative_path(output_paths["rob"])))
    print("report_json={}".format(relative_path(output_paths["report_json"])))
    print("visualization_html={}".format(relative_path(output_paths["visualization_html"])))
    print("frames={}".format(payload["compile"]["frame_count"]))
    print("total_duration_ms={}".format(payload["compile"]["total_duration_ms"]))
    print("violations={}".format(len(payload["compile"]["violations"])))


def build_workflow(spec_path, actions_dir=DEFAULT_ACTIONS_DIR):
    spec_path = workspace_path(spec_path)
    spec = load_recipe_spec(spec_path)
    actions_dir = detect_actions_dir(actions_dir)
    output_config = spec.get("output", {})
    output_paths = {
        "rob": resolve_output_path(output_config.get("rob"), WORKSPACE_ROOT / "动作" / "{}.rob".format(spec.get("name", spec_path.stem))),
        "report_json": resolve_output_path(output_config.get("report_json"), spec_path.with_suffix(".report.json")),
        "visualization_html": resolve_output_path(output_config.get("visualization_html"), spec_path.with_suffix(".timeline.html")),
    }
    recipe = load_recipe_from_spec(spec, actions_dir=actions_dir)
    report = compile_recipe(recipe, output_paths["rob"], actions_dir=actions_dir, write_output=True)
    payload = build_payload(spec_path, spec, report, output_paths)
    write_build_outputs(spec_path, payload, output_paths)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("output")
    init_parser.add_argument("--name", required=True)
    init_parser.add_argument("--prompt", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("spec")
    build_parser.add_argument("--actions-dir", default=str(DEFAULT_ACTIONS_DIR))

    args = parser.parse_args()
    if args.command == "init":
        output_path = workspace_path(args.output)
        create_template(output_path, args.name, args.prompt)
        print("template={}".format(relative_path(output_path)))
        return

    build_workflow(args.spec, actions_dir=workspace_path(args.actions_dir))


if __name__ == "__main__":
    main()