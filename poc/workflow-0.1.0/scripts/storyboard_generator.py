"""
Phase 4: Storyboard Generator

Converts novel scenes to visual panel descriptions for webtoon generation.
Uses Claude Agent SDK for scene analysis and panel breakdown.
"""

import os
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

# Claude SDK imports
try:
    from claude_code_sdk import Claude, ClaudeAPIError, query
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    print("Warning: claude_code_sdk not available. Using manual panel generation.")


# Base paths
BASE_DIR = Path(__file__).parent.parent
REPO_ROOT = BASE_DIR.parent.parent
POC_DIR = BASE_DIR
PHASE4_DIR = POC_DIR / "phase4_storyboard"
SOURCE_DIR = REPO_ROOT / "source" / "001"

# Load style spec from Phase 2
STYLE_SPEC_PATH = POC_DIR / "phase2_style" / "style_spec.json"
PROMPT_TEMPLATES_PATH = POC_DIR / "phase2_style" / "prompt_templates.json"

# Load character info from Phase 1
PHASE1_RESULTS_PATH = POC_DIR / "phase1_characters" / "phase1_results.json"

# Load background info from Phase 3
PHASE3_RESULTS_PATH = POC_DIR / "phase3_backgrounds" / "phase3_results.json"


@dataclass
class Character:
    name: str
    korean: str
    position: str
    expression: str
    pose: str
    reference_path: Optional[str] = None


@dataclass
class PanelSpec:
    id: str
    scene_id: str
    sequence_number: int
    panel_type: str
    aspect_ratio: str
    shot_type: str
    camera_angle: str
    scene_description: str
    narrative_moment: str
    characters: list
    location: str
    background_reference: Optional[str]
    lighting_preset: str
    mood: str
    dialogue_space: str
    special_effects: list
    prompt_template_id: str
    source_text: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class StoryboardGenerator:
    def __init__(self):
        self.style_spec = self._load_json(STYLE_SPEC_PATH)
        self.prompt_templates = self._load_json(PROMPT_TEMPLATES_PATH)
        self.phase1_results = self._load_json(PHASE1_RESULTS_PATH)
        self.phase3_results = self._load_json(PHASE3_RESULTS_PATH)

        # Character reference paths
        self.character_refs = {
            "jin_sohan": str(POC_DIR / "phase1_characters" / "jin_sohan" / "base_reference.png"),
            "dokma": str(POC_DIR / "phase1_characters" / "dokma" / "base_reference.png"),
            "uiseon": str(POC_DIR / "phase1_characters" / "uiseon" / "base_reference.png"),
        }

        # Background reference paths
        self.background_refs = {
            "magic_tower_exterior": str(POC_DIR / "phase3_backgrounds" / "locations" / "magic_tower" / "base_reference.png"),
            "magic_tower_interior": str(POC_DIR / "phase3_backgrounds" / "locations" / "magic_tower" / "interior_hall.png"),
            "magic_tower_quarters": str(POC_DIR / "phase3_backgrounds" / "locations" / "magic_tower" / "interior_quarters.png"),
        }

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_json(self, data: dict, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def generate_scene_01_request(self) -> list:
        """
        Scene 1: The Request to Leave (Dialogue Heavy)

        Novel context: Jin Sohan asks his masters for permission to return to his hometown.
        Located in the fog-shrouded Magic Tower.
        Key tension: Jin Sohan's determination vs masters' reluctance.
        """
        panels = []

        # Panel 1: Establishing shot - Magic Tower exterior
        panels.append(PanelSpec(
            id="s1_p01",
            scene_id="scene_01_request",
            sequence_number=1,
            panel_type="establishing",
            aspect_ratio="16:9",
            shot_type="wide shot",
            camera_angle="low angle",
            scene_description="Magic Tower (Maseunru) shrouded in perpetual dense fog",
            narrative_moment="Introduction to the mysterious tower where the masters live in seclusion",
            characters=[],
            location="Magic Tower exterior",
            background_reference=self.background_refs.get("magic_tower_exterior"),
            lighting_preset="fog_day",
            mood="mysterious, isolated",
            dialogue_space="none",
            special_effects=["dense_fog", "atmospheric_glow"],
            prompt_template_id="establishing_tower",
            source_text="안개가 자욱한 마선루(魔仙樓). 외부에서 보면 사람이 있다는 것조차 보이지 않을 정도로 짙은 안개 속에..."
        ))

        # Panel 2: Medium shot - Jin Sohan kneeling before masters
        panels.append(PanelSpec(
            id="s1_p02",
            scene_id="scene_01_request",
            sequence_number=2,
            panel_type="dialogue",
            aspect_ratio="16:9",
            shot_type="medium shot",
            camera_angle="slightly low angle",
            scene_description="Interior of Magic Tower main hall, Jin Sohan kneeling before the twin masters",
            narrative_moment="Jin Sohan formally requests permission to leave",
            characters=[
                Character("Jin Sohan", "진소한", "center-bottom", "determined, respectful", "kneeling formally", self.character_refs.get("jin_sohan")).__dict__,
                Character("Dokma", "독마", "left-back", "skeptical, arms crossed", "seated on elevated position", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "right-back", "thoughtful, calm", "seated on elevated position", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior hall",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="tense, formal",
            dialogue_space="top",
            special_effects=[],
            prompt_template_id="dialogue_group",
            source_text="'하산?' '예.' '자신만만하구나. 고작 십이 년을 수련해놓고……'"
        ))

        # Panel 3: Close-up - Dokma's cynical expression
        panels.append(PanelSpec(
            id="s1_p03",
            scene_id="scene_01_request",
            sequence_number=3,
            panel_type="close-up",
            aspect_ratio="1:1",
            shot_type="close-up",
            camera_angle="straight on",
            scene_description="Dokma's face showing cynical skepticism",
            narrative_moment="Dokma questions Jin Sohan's readiness with dark humor",
            characters=[
                Character("Dokma", "독마", "center", "cynical smirk, narrowed eyes", "face only", self.character_refs.get("dokma")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="intimidating, dark humor",
            dialogue_space="bottom",
            special_effects=["dark_vignette"],
            prompt_template_id="closeup_emotional",
            source_text="독마가 눈을 가늘게 뜬 채로 말했다. '흑도에 가봤자 강호의 일에 휘말릴 게다.'"
        ))

        # Panel 4: Close-up - Uiseon's thoughtful expression
        panels.append(PanelSpec(
            id="s1_p04",
            scene_id="scene_01_request",
            sequence_number=4,
            panel_type="close-up",
            aspect_ratio="1:1",
            shot_type="close-up",
            camera_angle="straight on",
            scene_description="Uiseon's face showing scholarly concern",
            narrative_moment="Uiseon adds his wisdom about the dangers of the Black Road territory",
            characters=[
                Character("Uiseon", "의선", "center", "thoughtful, gentle concern", "face only", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="wise, concerned",
            dialogue_space="bottom",
            special_effects=["soft_light"],
            prompt_template_id="closeup_emotional",
            source_text="잠자코 있던 의선이 한마디를 보탰다. '차라리 명문정파가 지배하는 지역이라면 보내주겠다만...'"
        ))

        # Panel 5: Two-shot - Twin masters exchanging glances
        panels.append(PanelSpec(
            id="s1_p05",
            scene_id="scene_01_request",
            sequence_number=5,
            panel_type="two-shot",
            aspect_ratio="16:9",
            shot_type="medium close-up",
            camera_angle="eye level",
            scene_description="The twin masters look at each other, sharing unspoken communication",
            narrative_moment="Silent understanding between the twins about their disciple's determination",
            characters=[
                Character("Dokma", "독마", "left", "subtle acknowledgment", "slight turn toward brother", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "right", "knowing look", "slight turn toward brother", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="unspoken understanding",
            dialogue_space="none",
            special_effects=[],
            prompt_template_id="dialogue_two_shot",
            source_text="독마와 의선이 동시에 혀를 찼다. '쯧……'"
        ))

        # Panel 6: Reaction shot - Jin Sohan's determined expression
        panels.append(PanelSpec(
            id="s1_p06",
            scene_id="scene_01_request",
            sequence_number=6,
            panel_type="reaction",
            aspect_ratio="4:3",
            shot_type="medium close-up",
            camera_angle="slightly low angle",
            scene_description="Jin Sohan's face showing unwavering determination",
            narrative_moment="Jin Sohan's resolve is clear - he will not be deterred",
            characters=[
                Character("Jin Sohan", "진소한", "center", "determined, calm resolve", "looking up at masters", self.character_refs.get("jin_sohan")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="determined, resolute",
            dialogue_space="bottom",
            special_effects=["dramatic_lighting"],
            prompt_template_id="reaction_shot",
            source_text="진소한은 끝까지 고집을 부렸다. '예. 한 명이라도 있다면 제자가 받았던 은혜, 갚겠습니다.'"
        ))

        return panels

    def generate_scene_02_storytelling(self) -> list:
        """
        Scene 2: The Storytelling (Performance)

        Novel context: Jin Sohan performs "Heoeon Singong" - the art of storytelling.
        He tells the tale of the golden peach and the two-headed snake.
        The masters listen with fascination.
        """
        panels = []

        # Panel 1: Wide shot - Jin Sohan in storytelling pose
        panels.append(PanelSpec(
            id="s2_p01",
            scene_id="scene_02_storytelling",
            sequence_number=1,
            panel_type="wide",
            aspect_ratio="16:9",
            shot_type="wide shot",
            camera_angle="eye level",
            scene_description="Jin Sohan begins his storytelling performance, masters watching intently",
            narrative_moment="The beginning of Heoeon Singong - Jin Sohan's art of storytelling",
            characters=[
                Character("Jin Sohan", "진소한", "center-front", "theatrical, expressive", "storytelling gesture, animated", self.character_refs.get("jin_sohan")).__dict__,
                Character("Dokma", "독마", "left-back", "intrigued, leaning forward", "seated, attentive", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "right-back", "delighted, engaged", "seated, attentive", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior hall",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="theatrical, engaging",
            dialogue_space="top",
            special_effects=["warm_glow"],
            prompt_template_id="dialogue_group",
            source_text="'예, 그럼 이제부터 제자가 허언신공을 한 번 펼쳐보겠습니다.'"
        ))

        # Panel 2: Fantasy insert - Young Jin Sohan discovering the peach
        panels.append(PanelSpec(
            id="s2_p02",
            scene_id="scene_02_storytelling",
            sequence_number=2,
            panel_type="fantasy_insert",
            aspect_ratio="9:16",
            shot_type="medium shot",
            camera_angle="low angle looking up",
            scene_description="Flashback/story visualization: Young Jin Sohan looking up at a golden peach on a tree",
            narrative_moment="The discovery of the mystical golden peach in the courtyard",
            characters=[
                Character("Young Jin Sohan", "어린 진소한", "bottom-center", "wonder, curiosity", "looking up at tree", None).__dict__,
            ],
            location="Sword Dance Troupe courtyard with peach tree",
            background_reference=None,
            lighting_preset="emotional_soft",
            mood="nostalgic, wondrous",
            dialogue_space="none",
            special_effects=["golden_glow", "dreamy_filter", "vignette"],
            prompt_template_id="emotional_farewell",
            source_text="그 나무에 다른 복숭아와 빛깔이 전혀 다른 황금 복숭아가 높은 곳에 달려있었는데..."
        ))

        # Panel 3: Fantasy insert - Two-headed snake wrapped around the peach
        panels.append(PanelSpec(
            id="s2_p03",
            scene_id="scene_02_storytelling",
            sequence_number=3,
            panel_type="fantasy_insert",
            aspect_ratio="1:1",
            shot_type="close-up",
            camera_angle="straight on",
            scene_description="The mystical two-headed snake (ssangdusa) coiled around the golden peach",
            narrative_moment="The strange sight of the yin-yang snake drunk on the golden peach",
            characters=[],
            location="Fantasy - peach tree branch",
            background_reference=None,
            lighting_preset="mystical",
            mood="mysterious, supernatural",
            dialogue_space="none",
            special_effects=["golden_glow", "ethereal_mist", "translucent_body"],
            prompt_template_id="object_focus",
            source_text="그 손오공 복숭아에 기이하게 생긴 뱀 한 마리가 머리를 넣은 채로 대롱대롱 매달려 있는 겁니다. 머리가 두 개지 뭡니까?"
        ))

        # Panel 4: Close-up - Dokma's eyes widening with interest
        panels.append(PanelSpec(
            id="s2_p04",
            scene_id="scene_02_storytelling",
            sequence_number=4,
            panel_type="close-up",
            aspect_ratio="1:1",
            shot_type="extreme close-up",
            camera_angle="straight on",
            scene_description="Dokma's eyes widening with intense interest at the mention of rare snake",
            narrative_moment="The poison master's fascination with the rare creature",
            characters=[
                Character("Dokma", "독마", "center", "eyes wide, intense interest", "eyes focus", self.character_refs.get("dokma")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="fascinated, greedy interest",
            dialogue_space="bottom",
            special_effects=["eye_highlight"],
            prompt_template_id="closeup_emotional",
            source_text="독마가 놀랐다. 희귀한 뱀이라면 사족을 못 쓰는 사람이었으니까."
        ))

        # Panel 5: Fantasy insert - Young Jin Sohan swallowing the inner cores
        panels.append(PanelSpec(
            id="s2_p05",
            scene_id="scene_02_storytelling",
            sequence_number=5,
            panel_type="fantasy_insert",
            aspect_ratio="9:16",
            shot_type="close-up",
            camera_angle="slightly low angle",
            scene_description="Young Jin Sohan making a fateful decision, holding the two glowing inner cores",
            narrative_moment="The moment of transformation - consuming the snake's inner cores",
            characters=[
                Character("Young Jin Sohan", "어린 진소한", "center", "determined, nervous", "holding two glowing orbs near mouth", None).__dict__,
            ],
            location="Kitchen of Sword Dance Troupe",
            background_reference=None,
            lighting_preset="dramatic",
            mood="fateful, tense",
            dialogue_space="none",
            special_effects=["dual_glow_red_gold", "dramatic_lighting"],
            prompt_template_id="closeup_action",
            source_text="저는 눈을 딱 감고 먹기로 결심했습니다... 저는 그 두 개를 즉시 꿀꺽 삼켰습니다."
        ))

        # Panel 6: Return to present - Jin Sohan finishing with subtle smile
        panels.append(PanelSpec(
            id="s2_p06",
            scene_id="scene_02_storytelling",
            sequence_number=6,
            panel_type="dialogue",
            aspect_ratio="4:3",
            shot_type="medium shot",
            camera_angle="eye level",
            scene_description="Back to present: Jin Sohan finishing his story with a subtle knowing smile",
            narrative_moment="The storytelling concludes - truth hidden within the tale",
            characters=[
                Character("Jin Sohan", "진소한", "center", "subtle smile, knowing", "relaxed storytelling pose", self.character_refs.get("jin_sohan")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="satisfied, knowing",
            dialogue_space="top",
            special_effects=[],
            prompt_template_id="reaction_shot",
            source_text="'재미있었다. 허언신공이 날이 갈수록 깊어지는구나.'"
        ))

        return panels

    def generate_scene_03_departure(self) -> list:
        """
        Scene 3: The Departure (Emotional)

        Novel context: Masters give Jin Sohan parting gifts and final words.
        Bittersweet farewell after 12 years together.
        """
        panels = []

        # Panel 1: Object focus - Twin crescent moon blades
        panels.append(PanelSpec(
            id="s3_p01",
            scene_id="scene_03_departure",
            sequence_number=1,
            panel_type="object_focus",
            aspect_ratio="16:9",
            shot_type="close-up",
            camera_angle="top-down slight angle",
            scene_description="Twin crescent moon blades (Ssangwol) laid on a wooden table",
            narrative_moment="Dokma's precious weapon, now passed to his disciple",
            characters=[],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="reverent, meaningful",
            dialogue_space="none",
            special_effects=["metallic_gleam", "warm_light"],
            prompt_template_id="object_focus",
            source_text="독마가 두 자루의 칼을 탁자 위에 내밀었다. '쌍월(雙月)은 네가 앞으로 써라.'"
        ))

        # Panel 2: Medium shot - Dokma presenting the blades
        panels.append(PanelSpec(
            id="s3_p02",
            scene_id="scene_03_departure",
            sequence_number=2,
            panel_type="dialogue",
            aspect_ratio="16:9",
            shot_type="medium shot",
            camera_angle="eye level",
            scene_description="Dokma presenting the twin blades to Jin Sohan with gruff affection",
            narrative_moment="The poison master shows his care in his own way",
            characters=[
                Character("Dokma", "독마", "left", "gruff but caring", "extending weapons", self.character_refs.get("dokma")).__dict__,
                Character("Jin Sohan", "진소한", "right", "moved, grateful", "receiving with both hands", self.character_refs.get("jin_sohan")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="gruff affection",
            dialogue_space="top",
            special_effects=[],
            prompt_template_id="dialogue_two_shot",
            source_text="'내가 사용하는 것보다 네게 더 도움이 될 거다. 잔말 말고 받아라.'"
        ))

        # Panel 3: Object focus - White fan offered by Uiseon
        panels.append(PanelSpec(
            id="s3_p03",
            scene_id="scene_03_departure",
            sequence_number=3,
            panel_type="object_focus",
            aspect_ratio="4:3",
            shot_type="close-up",
            camera_angle="slight angle",
            scene_description="Elegant white fan (Baekseon) being offered by Uiseon's hands",
            narrative_moment="Uiseon's gift - the fan Jin Sohan always admired",
            characters=[
                Character("Uiseon", "의선", "partial-hands only", "gentle offering", "extending fan", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="gentle, meaningful",
            dialogue_space="bottom",
            special_effects=["soft_light"],
            prompt_template_id="object_focus",
            source_text="의선이 자신의 쥘부채를 내밀면서 말했다. '백선(白扇)도 챙겨라.'"
        ))

        # Panel 4: Wide shot - Jin Sohan bowing deeply
        panels.append(PanelSpec(
            id="s3_p04",
            scene_id="scene_03_departure",
            sequence_number=4,
            panel_type="wide",
            aspect_ratio="16:9",
            shot_type="wide shot",
            camera_angle="side angle",
            scene_description="Jin Sohan bowing deeply to both masters in formal farewell",
            narrative_moment="The formal farewell after 12 years as their disciple",
            characters=[
                Character("Jin Sohan", "진소한", "center-bottom", "deep gratitude", "deep bow, formal", self.character_refs.get("jin_sohan")).__dict__,
                Character("Dokma", "독마", "left-back", "stoic, hiding emotion", "standing", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "right-back", "gentle sadness", "standing", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior hall",
            background_reference=self.background_refs.get("magic_tower_interior"),
            lighting_preset="indoor_lamp",
            mood="solemn, emotional",
            dialogue_space="none",
            special_effects=[],
            prompt_template_id="dialogue_group",
            source_text="얼떨떨한 진소한이 서둘러서 절을 올렸다."
        ))

        # Panel 5: Close-up - Masters' expressions
        panels.append(PanelSpec(
            id="s3_p05",
            scene_id="scene_03_departure",
            sequence_number=5,
            panel_type="two-shot",
            aspect_ratio="16:9",
            shot_type="close-up",
            camera_angle="eye level",
            scene_description="Close-up of both masters' faces showing hidden emotion behind stoic exteriors",
            narrative_moment="The masters hide their sadness behind composure",
            characters=[
                Character("Dokma", "독마", "left", "stoic but eyes betray emotion", "facing forward", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "right", "gentle sadness in eyes", "facing forward", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower interior",
            background_reference=None,
            lighting_preset="indoor_lamp",
            mood="restrained emotion, bittersweet",
            dialogue_space="bottom",
            special_effects=["subtle_vignette"],
            prompt_template_id="dialogue_two_shot",
            source_text="'가서, 잘해라. 목덜미 잘 간수하고.' '네 소식은 강호에 퍼지는 위명으로 대신 듣겠다.'"
        ))

        # Panel 6: Silhouette - Jin Sohan walking into the fog
        panels.append(PanelSpec(
            id="s3_p06",
            scene_id="scene_03_departure",
            sequence_number=6,
            panel_type="silhouette",
            aspect_ratio="2:3",
            shot_type="wide shot",
            camera_angle="low angle",
            scene_description="Jin Sohan's silhouette walking into the dense fog, masters watching from tower entrance",
            narrative_moment="The final departure - a new journey begins",
            characters=[
                Character("Jin Sohan", "진소한", "center-mid", "walking away, determined", "silhouette walking into fog", self.character_refs.get("jin_sohan")).__dict__,
                Character("Dokma", "독마", "far-left-back", "watching silhouette", "standing at tower", self.character_refs.get("dokma")).__dict__,
                Character("Uiseon", "의선", "far-right-back", "watching silhouette", "standing at tower", self.character_refs.get("uiseon")).__dict__,
            ],
            location="Magic Tower entrance, foggy exterior",
            background_reference=self.background_refs.get("magic_tower_exterior"),
            lighting_preset="fog_day",
            mood="bittersweet, hopeful, new beginning",
            dialogue_space="none",
            special_effects=["dense_fog", "silhouette_backlight", "atmospheric"],
            prompt_template_id="silhouette_dramatic",
            source_text="정말로 사부들을 떠나 고향에 돌아갈 시간이 다가온 것이다. 진소한은 자신의 예상과 다르게 시원섭섭한 감정을 맛보고 있었다."
        ))

        return panels

    def save_scene_panels(self, scene_id: str, panels: list):
        """Save panel specifications for a scene."""
        scene_dir = PHASE4_DIR / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        # Save individual panel JSONs
        for panel in panels:
            panel_data = panel.to_dict()
            panel_path = scene_dir / f"{panel.id}_spec.json"
            self._save_json(panel_data, panel_path)

        # Save scene manifest
        manifest = {
            "scene_id": scene_id,
            "total_panels": len(panels),
            "panel_ids": [p.id for p in panels],
            "generated_at": datetime.now().isoformat(),
            "phase": "Phase 4: Storyboarding"
        }
        manifest_path = scene_dir / "scene_manifest.json"
        self._save_json(manifest, manifest_path)

        return manifest

    def generate_all_scenes(self) -> dict:
        """Generate storyboards for all three test scenes."""
        results = {
            "phase": "Phase 4: Storyboarding",
            "timestamp": datetime.now().isoformat(),
            "scenes": {}
        }

        # Scene 1: The Request to Leave
        print("Generating Scene 1: The Request to Leave...")
        scene1_panels = self.generate_scene_01_request()
        scene1_manifest = self.save_scene_panels("scene_01_request", scene1_panels)
        results["scenes"]["scene_01_request"] = {
            "title": "The Request to Leave",
            "title_korean": "하산 요청",
            "description": "Jin Sohan asks his masters for permission to return to his hometown",
            "panel_count": len(scene1_panels),
            "manifest": scene1_manifest
        }
        print(f"  Generated {len(scene1_panels)} panels")

        # Scene 2: The Storytelling
        print("Generating Scene 2: The Storytelling...")
        scene2_panels = self.generate_scene_02_storytelling()
        scene2_manifest = self.save_scene_panels("scene_02_storytelling", scene2_panels)
        results["scenes"]["scene_02_storytelling"] = {
            "title": "The Storytelling",
            "title_korean": "허언신공",
            "description": "Jin Sohan performs his art of storytelling, telling the tale of the golden peach",
            "panel_count": len(scene2_panels),
            "manifest": scene2_manifest
        }
        print(f"  Generated {len(scene2_panels)} panels")

        # Scene 3: The Departure
        print("Generating Scene 3: The Departure...")
        scene3_panels = self.generate_scene_03_departure()
        scene3_manifest = self.save_scene_panels("scene_03_departure", scene3_panels)
        results["scenes"]["scene_03_departure"] = {
            "title": "The Departure",
            "title_korean": "이별",
            "description": "Masters give Jin Sohan parting gifts and final words of wisdom",
            "panel_count": len(scene3_panels),
            "manifest": scene3_manifest
        }
        print(f"  Generated {len(scene3_panels)} panels")

        # Calculate totals
        total_panels = sum(s["panel_count"] for s in results["scenes"].values())
        results["total_panels"] = total_panels
        results["success"] = True

        # Save overall results
        results_path = PHASE4_DIR / "phase4_results.json"
        self._save_json(results, results_path)
        print(f"\nPhase 4 complete: {total_panels} panels generated across {len(results['scenes'])} scenes")

        return results


def generate_panel_templates() -> dict:
    """Generate reusable panel templates based on the POC specification."""
    templates = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "phase": "Phase 4: Storyboarding",
        "panel_types": {
            "establishing": {
                "description": "Wide establishing shot to set the scene",
                "typical_aspect_ratios": ["16:9", "2:3"],
                "shot_types": ["wide shot", "extreme wide shot"],
                "character_presence": "none or minimal",
                "dialogue_space": "none",
                "use_cases": ["scene introduction", "location reveal", "time passage"]
            },
            "dialogue": {
                "description": "Conversation panel with character interaction",
                "typical_aspect_ratios": ["16:9", "4:3"],
                "shot_types": ["medium shot", "medium close-up"],
                "character_presence": "2-4 characters",
                "dialogue_space": "top or sides",
                "use_cases": ["conversation", "exposition", "character interaction"]
            },
            "close-up": {
                "description": "Focus on character expression or detail",
                "typical_aspect_ratios": ["1:1", "4:3"],
                "shot_types": ["close-up", "extreme close-up"],
                "character_presence": "1 character (face focus)",
                "dialogue_space": "bottom or none",
                "use_cases": ["emotional moment", "reaction", "emphasis"]
            },
            "two-shot": {
                "description": "Two characters in frame together",
                "typical_aspect_ratios": ["16:9", "4:3"],
                "shot_types": ["medium shot", "medium close-up"],
                "character_presence": "2 characters",
                "dialogue_space": "top",
                "use_cases": ["dialogue exchange", "relationship dynamic", "confrontation"]
            },
            "action": {
                "description": "Dynamic action sequence panel",
                "typical_aspect_ratios": ["9:16", "1:1"],
                "shot_types": ["dynamic", "low angle", "dutch angle"],
                "character_presence": "1-2 characters",
                "dialogue_space": "none",
                "use_cases": ["combat", "movement", "impact"],
                "special_effects": ["speed_lines", "motion_blur", "impact_burst"]
            },
            "reaction": {
                "description": "Character reaction to event",
                "typical_aspect_ratios": ["4:3", "1:1"],
                "shot_types": ["medium close-up", "close-up"],
                "character_presence": "1-3 characters",
                "dialogue_space": "bottom",
                "use_cases": ["surprise", "realization", "emotional response"]
            },
            "object_focus": {
                "description": "Focus on significant object",
                "typical_aspect_ratios": ["16:9", "4:3", "1:1"],
                "shot_types": ["close-up", "macro"],
                "character_presence": "none or partial (hands)",
                "dialogue_space": "none or bottom",
                "use_cases": ["symbolic item", "plot device", "gift/weapon reveal"]
            },
            "silhouette": {
                "description": "Dramatic silhouette composition",
                "typical_aspect_ratios": ["2:3", "9:16"],
                "shot_types": ["wide shot", "medium shot"],
                "character_presence": "1+ as silhouettes",
                "dialogue_space": "none",
                "use_cases": ["dramatic moment", "departure", "mystery"],
                "special_effects": ["backlight", "atmospheric_fog"]
            },
            "fantasy_insert": {
                "description": "Flashback or story visualization panel",
                "typical_aspect_ratios": ["9:16", "1:1"],
                "shot_types": ["varies"],
                "character_presence": "varies",
                "dialogue_space": "none",
                "use_cases": ["flashback", "memory", "story within story"],
                "special_effects": ["dreamy_filter", "vignette", "color_shift"]
            }
        },
        "camera_angles": {
            "eye_level": "Neutral, straightforward view",
            "low_angle": "Looking up, conveys power or importance",
            "high_angle": "Looking down, conveys vulnerability or smallness",
            "dutch_angle": "Tilted frame, conveys tension or unease",
            "top_down": "Bird's eye view, overview perspective",
            "straight_on": "Direct frontal view"
        },
        "lighting_presets": {
            "fog_day": {"mood": "mysterious", "color_temp": "neutral", "shadows": "soft"},
            "fog_night": {"mood": "eerie", "color_temp": "cool", "shadows": "medium"},
            "indoor_lamp": {"mood": "warm", "color_temp": "warm", "shadows": "dramatic"},
            "emotional_soft": {"mood": "intimate", "color_temp": "warm", "shadows": "minimal"},
            "combat_intense": {"mood": "intense", "color_temp": "cool", "shadows": "high_contrast"},
            "mystical": {"mood": "supernatural", "color_temp": "varies", "shadows": "ethereal"}
        },
        "special_effects_library": [
            "dense_fog", "atmospheric_glow", "dark_vignette", "soft_light",
            "dramatic_lighting", "metallic_gleam", "warm_light", "subtle_vignette",
            "silhouette_backlight", "golden_glow", "dreamy_filter", "vignette",
            "dual_glow_red_gold", "eye_highlight", "ethereal_mist", "translucent_body",
            "speed_lines", "motion_blur", "impact_burst"
        ]
    }

    return templates


def main():
    print("=" * 60)
    print("Phase 4: Storyboard Generation")
    print("=" * 60)

    # Initialize generator
    generator = StoryboardGenerator()

    # Generate all scenes
    results = generator.generate_all_scenes()

    # Generate and save panel templates
    print("\nGenerating panel templates...")
    templates = generate_panel_templates()
    templates_path = PHASE4_DIR / "panel_templates.json"
    generator._save_json(templates, templates_path)
    print(f"  Panel templates saved to {templates_path}")

    print("\n" + "=" * 60)
    print("Phase 4 Summary")
    print("=" * 60)
    print(f"Total scenes: {len(results['scenes'])}")
    print(f"Total panels: {results['total_panels']}")
    for scene_id, scene_data in results["scenes"].items():
        print(f"  - {scene_data['title']}: {scene_data['panel_count']} panels")
    print(f"\nResults saved to: {PHASE4_DIR / 'phase4_results.json'}")

    return results


if __name__ == "__main__":
    main()
