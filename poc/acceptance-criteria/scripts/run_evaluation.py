#!/usr/bin/env python3
"""Phase-5 acceptance criteria evaluator for existing PoC outputs.

Scope intentionally limited to final panel generation (phase5_generation).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class PanelRecord:
    scene_id: str
    panel_id: str
    image_path: Path
    panel_spec: dict[str, Any]


class TechnicalChecker:
    @staticmethod
    def validate(image_path: Path, panel_spec: dict[str, Any]) -> dict[str, Any]:
        checks: dict[str, dict[str, Any]] = {}
        try:
            with Image.open(image_path) as img:
                img.verify()
            with Image.open(image_path) as img:
                width, height = img.size
                mode = img.mode
                extrema = img.getextrema()
        except Exception as exc:
            return {
                "passed": False,
                "checks_passed": 0,
                "total_checks": 8,
                "checks": {"file_valid": {"passed": False, "details": str(exc)}},
            }

        checks["file_valid"] = {"passed": True}
        checks["resolution"] = {"passed": min(width, height) >= 512}
        ratio_map = {"landscape_16_9": 16 / 9, "portrait_9_16": 9 / 16, "square_1_1": 1.0, "16:9": 16 / 9}
        expected = ratio_map.get(panel_spec.get("aspect_ratio"))
        actual = width / height if height else 0
        checks["aspect_ratio"] = {"passed": True if expected is None else abs(actual - expected) / expected <= 0.15}
        checks["min_file_size"] = {"passed": image_path.stat().st_size >= 10_000}
        checks["color_depth"] = {"passed": mode in {"RGB", "RGBA"}}
        checks["not_blank"] = {"passed": any(a != b for a, b in extrema) if isinstance(extrema[0], tuple) else extrema[0] != extrema[1]}
        checks["dimensions_match"] = {"passed": 256 <= width <= 8192 and 256 <= height <= 8192}
        checks["format_valid"] = {"passed": image_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}}
        passed = sum(1 for c in checks.values() if c["passed"])
        return {"passed": passed == 8, "checks_passed": passed, "total_checks": 8, "checks": checks}


class BaseEvaluator:
    def evaluate_identity(self, ref: Path, img: Path, character_id: str) -> dict[str, Any]: ...
    def evaluate_adherence(self, img: Path, spec: dict[str, Any]) -> dict[str, Any]: ...
    def evaluate_style(self, img: Path) -> dict[str, Any]: ...
    def evaluate_defects(self, img: Path) -> dict[str, Any]: ...
    def evaluate_character_consistency(self, ref: Path, panels: list[Path], character_id: str) -> dict[str, Any]: ...
    def evaluate_style_consistency(self, images: list[Path]) -> dict[str, Any]: ...
    def evaluate_storytelling(self, images: list[Path], scene_title: str, source_text: str, panel_desc: list[str]) -> dict[str, Any]: ...
    def evaluate_emotional_arc(self, images: list[Path], panel_desc: list[str]) -> dict[str, Any]: ...


class HeuristicEvaluator(BaseEvaluator):
    def _arr(self, p: Path) -> np.ndarray:
        return np.array(Image.open(p).convert("RGB"), dtype=np.float32)

    def evaluate_identity(self, ref: Path, img: Path, character_id: str) -> dict[str, Any]:
        a = np.array(Image.fromarray(self._arr(ref).astype(np.uint8)).resize((128, 128)), dtype=np.float32)
        b = np.array(Image.fromarray(self._arr(img).astype(np.uint8)).resize((128, 128)), dtype=np.float32)
        global_diff = np.mean(np.abs(a - b))
        face = max(1, min(10, int(round(10 - global_diff / 18))))
        hair_delta = np.mean(np.abs(a[:40, 44:84, :].mean((0, 1)) - b[:40, 44:84, :].mean((0, 1))))
        hair = max(1, min(10, int(round(10 - hair_delta / 12))))
        identity = min(face, hair)
        return {"face": face, "hair": hair, "clothing": face, "build": face, "identity": identity, "notes": f"heuristic_{character_id}"}

    def evaluate_adherence(self, img: Path, spec: dict[str, Any]) -> dict[str, Any]:
        brightness = self._arr(img).mean()
        mood = (spec.get("mood") or "").lower()
        mood_score = 7
        if any(k in mood for k in ["dark", "mysterious", "tense"]):
            mood_score = 8 if brightness < 120 else 4
        char_score = 8 if spec.get("characters") else 7
        adherence = int(round((6 + char_score + 6 + mood_score) / 4))
        return {"composition": 6, "characters": char_score, "setting": 6, "mood": mood_score, "adherence": adherence, "notes": "heuristic"}

    def evaluate_style(self, img: Path) -> dict[str, Any]:
        contrast = float(self._arr(img).std())
        style = 8 if contrast > 45 else 5
        return {"style": style, "lines": style - 1, "coloring": style, "genre": style - 1, "notes": "heuristic"}

    def evaluate_defects(self, img: Path) -> dict[str, Any]:
        base = 8 if self._arr(img).std() > 25 else 6
        return {"hands": base, "face": base, "anatomy": base, "artifacts": base - 1, "text": 3, "defects_found": ["text_likely_garbled"]}

    def evaluate_character_consistency(self, ref: Path, panels: list[Path], character_id: str) -> dict[str, Any]:
        per = []
        for panel in panels:
            r = self.evaluate_identity(ref, panel, character_id)
            per.append({"image": panel.name, "identity": r["identity"], "style": r["face"]})
        vals = [x["identity"] for x in per]
        overall = round(sum(vals) / len(vals), 2) if vals else None
        return {"per_image": per, "overall_consistency": overall, "worst_offender": min(vals) if vals else None, "notes": "heuristic"}

    def evaluate_style_consistency(self, images: list[Path]) -> dict[str, Any]:
        means = [self._arr(p).mean() for p in images]
        spread = float(np.std(means))
        uniformity = max(1, min(10, int(round(10 - spread / 10))))
        return {"uniformity": uniformity, "color": uniformity, "lines": uniformity - 1, "quality": uniformity, "outlier_panels": [], "notes": "heuristic"}

    def evaluate_storytelling(self, images: list[Path], scene_title: str, source_text: str, panel_desc: list[str]) -> dict[str, Any]:
        return {"narrative_clarity": 5, "sequential_flow": 5, "camera_work": 6, "character_acting": 5, "pacing": 6, "webtoon_quality": 5, "overall_storytelling": 5, "panel_interpretations": panel_desc, "notes": "heuristic_offline"}

    def evaluate_emotional_arc(self, images: list[Path], panel_desc: list[str]) -> dict[str, Any]:
        return {"range": 4, "progression": 4, "expression": 4, "atmosphere": 5, "notes": "heuristic_offline"}


class ClaudeEvaluator(HeuristicEvaluator):
    def __init__(self, model: str) -> None:
        self.client = Anthropic()
        self.model = model

    @staticmethod
    def _image_block(path: Path) -> dict[str, Any]:
        import base64

        media_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(path.read_bytes()).decode()}}

    def _ask(self, prompt: str, images: list[Path]) -> dict[str, Any]:
        content = [self._image_block(p) for p in images] + [{"type": "text", "text": prompt + "\nReturn JSON only."}]
        resp = self.client.messages.create(model=self.model, max_tokens=1000, temperature=0, messages=[{"role": "user", "content": content}])
        text = "\n".join(getattr(x, "text", "") for x in resp.content if getattr(x, "type", "") == "text")
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {"_raw": text}

    def evaluate_identity(self, ref: Path, img: Path, character_id: str) -> dict[str, Any]:
        return self._ask(
            f"Image1 is character reference for {character_id}, image2 is panel. Score face,hair,clothing,build,identity (1-10). 1-3 means clearly different person.",
            [ref, img],
        )

    def evaluate_adherence(self, img: Path, spec: dict[str, Any]) -> dict[str, Any]:
        return self._ask(
            "Score composition,characters,setting,mood,adherence (1-10) against this spec: " + json.dumps(spec, ensure_ascii=False),
            [img],
        )

    def evaluate_style(self, img: Path) -> dict[str, Any]:
        return self._ask(
            "Target style: Korean webtoon/manhwa, cel-shaded with gradients, wuxia genre. Score style,lines,coloring,genre (1-10).",
            [img],
        )

    def evaluate_defects(self, img: Path) -> dict[str, Any]:
        return self._ask("Score hands,face,anatomy,artifacts,text (1-10) and defects_found list.", [img])

    def evaluate_character_consistency(self, ref: Path, panels: list[Path], character_id: str) -> dict[str, Any]:
        return self._ask(
            f"Image1 is base reference for {character_id}; remaining images are scene panels. Return per_image(identity/style), overall_consistency, worst_offender.",
            [ref] + panels,
        )

    def evaluate_style_consistency(self, images: list[Path]) -> dict[str, Any]:
        return self._ask("These are scene panels. Score uniformity,color,lines,quality (1-10) and list outlier_panels.", images)

    def evaluate_storytelling(self, images: list[Path], scene_title: str, source_text: str, panel_desc: list[str]) -> dict[str, Any]:
        prompt = (
            f"Scene: {scene_title}\nSource text: {source_text}\nPanel intents: {panel_desc}\n"
            "Score narrative_clarity,sequential_flow,camera_work,character_acting,pacing,webtoon_quality,overall_storytelling (1-10)."
        )
        return self._ask(prompt, images)

    def evaluate_emotional_arc(self, images: list[Path], panel_desc: list[str]) -> dict[str, Any]:
        return self._ask("Score range,progression,expression,atmosphere (1-10) for emotional arc across these panels.", images)


def collect_panels(version: str) -> list[PanelRecord]:
    base = ROOT / f"poc/workflow-{version}/phase5_generation"
    records: list[PanelRecord] = []
    for meta in sorted(base.glob("scene_*/metadata/*.json")):
        payload = json.loads(meta.read_text())
        if "panel_spec" in payload:
            spec = payload.get("panel_spec", {})
            scene_id = spec.get("scene_id")
            panel_id = spec.get("panel_id")
        else:
            legacy = payload.get("specifications", {})
            scene_id = payload.get("scene_id") or legacy.get("scene_id")
            panel_id = payload.get("panel_id") or legacy.get("id")
            chars = legacy.get("characters", [])
            spec = {
                "scene_id": scene_id,
                "panel_id": panel_id,
                "aspect_ratio": legacy.get("aspect_ratio"),
                "shot_type": legacy.get("shot_type"),
                "camera_angle": legacy.get("camera_angle"),
                "characters": [{"character_id": c if isinstance(c, str) else c.get("character_id")} for c in chars],
                "location_id": legacy.get("location"),
                "mood": legacy.get("mood"),
                "lighting_preset": legacy.get("lighting_preset"),
            }

        if not scene_id or not panel_id:
            continue
        panel_path = base / scene_id / "panels" / f"{panel_id}.png"
        if panel_path.exists():
            records.append(PanelRecord(scene_id=scene_id, panel_id=panel_id, image_path=panel_path, panel_spec=spec))
    return records


def character_refs(version: str) -> dict[str, Path]:
    phase1_dir = ROOT / f"poc/workflow-{version}/phase1_characters"
    return {p.parent.name: p for p in phase1_dir.glob("*/base_reference.png")}


def eval_panel(ev: BaseEvaluator, panel: PanelRecord, refs: dict[str, Path]) -> dict[str, Any]:
    tier1 = TechnicalChecker.validate(panel.image_path, panel.panel_spec)
    adherence = ev.evaluate_adherence(panel.image_path, panel.panel_spec)
    style = ev.evaluate_style(panel.image_path)
    defects = ev.evaluate_defects(panel.image_path)

    identity_details = []
    for c in panel.panel_spec.get("characters", []):
        cid = c.get("character_id") if isinstance(c, dict) else None
        if cid and cid in refs:
            r = ev.evaluate_identity(refs[cid], panel.image_path, cid)
            r["character_id"] = cid
            identity_details.append(r)

    identity_score = min([x.get("identity") for x in identity_details if isinstance(x.get("identity"), (int, float))], default=None)
    defects_min = min([defects.get(k, 10) for k in ["hands", "face", "anatomy", "artifacts", "text"] if isinstance(defects.get(k), (int, float))], default=None)

    tier2 = {
        "identity_match": {"score": identity_score, "threshold": 6, "passed": identity_score is None or identity_score >= 6, "details": identity_details},
        "prompt_adherence": {"score": adherence.get("adherence"), "threshold": 5, "passed": isinstance(adherence.get("adherence"), (int, float)) and adherence.get("adherence") >= 5, "details": adherence},
        "style_match": {"score": style.get("style"), "threshold": 5, "passed": isinstance(style.get("style"), (int, float)) and style.get("style") >= 5, "details": style},
        "technical_defects": {
            "score": defects_min,
            "threshold": 5,
            "passed": all((not isinstance(defects.get(k), (int, float)) or defects.get(k) >= 5) for k in ["hands", "face", "anatomy", "artifacts", "text"]),
            "details": defects,
        },
    }
    scores = [tier2[k]["score"] for k in tier2 if isinstance(tier2[k]["score"], (int, float))]
    return {
        "image_id": panel.panel_id,
        "scene_id": panel.scene_id,
        "image_path": str(panel.image_path.relative_to(ROOT)),
        "tier1": tier1,
        "tier2": tier2,
        "overall_pass": tier1["passed"] and all(x["passed"] for x in tier2.values()),
        "overall_score": round(sum(scores) / len(scores), 2) if scores else None,
    }


def eval_scene(ev: BaseEvaluator, version: str, scene_id: str, panel_reports: list[dict[str, Any]], refs: dict[str, Path], panel_lookup: dict[tuple[str,str], PanelRecord]) -> dict[str, Any]:
    ordered = sorted(panel_reports, key=lambda x: x["image_id"])
    images = [ROOT / p["image_path"] for p in ordered]

    manifest_path = ROOT / f"poc/workflow-{version}/phase4_storyboard/{scene_id}/scene_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    panel_desc = [p.get("context", {}).get("narrative_purpose", "") for p in manifest.get("panels", [])]

    by_char: dict[str, list[Path]] = {}
    for row in ordered:
        spec = panel_lookup.get((scene_id, row["image_id"]))
        if not spec:
            continue
        for c in spec.panel_spec.get("characters", []):
            cid = c.get("character_id") if isinstance(c, dict) else None
            if cid and cid in refs:
                by_char.setdefault(cid, []).append(ROOT / row["image_path"])

    char_consistency = {}
    for cid, char_images in by_char.items():
        if char_images:
            detail = ev.evaluate_character_consistency(refs[cid], char_images, cid)
            char_consistency[cid] = {
                "score": detail.get("overall_consistency"),
                "worst": detail.get("worst_offender"),
                "passed": isinstance(detail.get("overall_consistency"), (int, float)) and detail.get("overall_consistency") >= 6 and isinstance(detail.get("worst_offender"), (int, float)) and detail.get("worst_offender") >= 4,
                "details": detail,
            }

    style_cons = ev.evaluate_style_consistency(images)
    storytelling = ev.evaluate_storytelling(images, manifest.get("scene_title", scene_id), manifest.get("source_text", ""), panel_desc)
    emo = ev.evaluate_emotional_arc(images, panel_desc)

    return {
        "scene_id": scene_id,
        "tier3": {
            "character_consistency": char_consistency,
            "style_consistency": {
                "score": style_cons.get("uniformity"),
                "passed": isinstance(style_cons.get("uniformity"), (int, float)) and style_cons.get("uniformity") >= 6,
                "details": style_cons,
            },
        },
        "tier4": {
            "storytelling": {
                "score": storytelling.get("overall_storytelling"),
                "passed": isinstance(storytelling.get("overall_storytelling"), (int, float)) and storytelling.get("overall_storytelling") >= 5,
                "details": storytelling,
            },
            "emotional_arc": {
                "score": emo.get("range"),
                "passed": isinstance(emo.get("range"), (int, float)) and emo.get("range") >= 4,
                "details": emo,
            },
        },
    }


def average(items: list[dict[str, Any]], path: list[str]) -> float | None:
    vals = []
    for item in items:
        cur: Any = item
        for key in path:
            cur = cur.get(key) if isinstance(cur, dict) else None
        if isinstance(cur, (int, float)):
            vals.append(float(cur))
    return round(sum(vals) / len(vals), 2) if vals else None


def evaluate_version(ev: BaseEvaluator, version: str) -> dict[str, Any]:
    refs = character_refs(version)
    panel_specs = collect_panels(version)
    image_reports = [eval_panel(ev, panel, refs) for panel in panel_specs]

    by_scene: dict[str, list[dict[str, Any]]] = {}
    for r in image_reports:
        by_scene.setdefault(r["scene_id"], []).append(r)

    panel_lookup = {(p.scene_id, p.panel_id): p for p in panel_specs}
    scene_reports = [eval_scene(ev, version, scene_id, rows, refs, panel_lookup) for scene_id, rows in by_scene.items()]

    return {
        "version": version,
        "scope": "phase5_only",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "image_reports": image_reports,
        "scene_reports": scene_reports,
        "summary": {
            "total_panels": len(image_reports),
            "panel_pass_rate": round(sum(1 for r in image_reports if r["overall_pass"]) / max(1, len(image_reports)) * 100, 2),
            "avg_panel_score": average(image_reports, ["overall_score"]),
            "avg_identity_score": average(image_reports, ["tier2", "identity_match", "score"]),
            "avg_style_score": average(image_reports, ["tier2", "style_match", "score"]),
            "avg_adherence_score": average(image_reports, ["tier2", "prompt_adherence", "score"]),
            "avg_storytelling": average(scene_reports, ["tier4", "storytelling", "score"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--versions", nargs="+", default=["0.1.0", "0.2.0"])
    parser.add_argument("--output-dir", default="poc/acceptance-criteria/reports")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    args = parser.parse_args()

    if Anthropic and os.environ.get("ANTHROPIC_API_KEY"):
        evaluator: BaseEvaluator = ClaudeEvaluator(args.model)
        mode = "claude"
    else:
        evaluator = HeuristicEvaluator()
        mode = "heuristic_offline"

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for version in args.versions:
        report = evaluate_version(evaluator, version)
        report["evaluator_mode"] = mode
        reports.append(report)
        (out_dir / f"evaluation_v{version}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"wrote evaluation_v{version}.json")

    comparison = {
        "scope": "phase5_only",
        "evaluator_mode": mode,
        "versions_compared": args.versions,
        "metrics": {
            "avg_identity_score": {r["version"]: r["summary"]["avg_identity_score"] for r in reports},
            "avg_style_score": {r["version"]: r["summary"]["avg_style_score"] for r in reports},
            "avg_adherence_score": {r["version"]: r["summary"]["avg_adherence_score"] for r in reports},
            "avg_storytelling": {r["version"]: r["summary"]["avg_storytelling"] for r in reports},
            "panel_pass_rate": {r["version"]: r["summary"]["panel_pass_rate"] for r in reports},
        },
    }
    (out_dir / "comparison.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False))
    print("wrote comparison.json")


if __name__ == "__main__":
    main()
