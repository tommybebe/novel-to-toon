"""
Phase 4: Enhanced Storyboard Generator for PoC v0.2.0

Converts novel scenes to detailed panel specifications with:
- Enhanced camera direction (ShotType, CameraAngle, CameraMovement)
- Variable panel shapes (PanelShape enum)
- Speech bubble safe zones (SpeechBubbleSafeZone)
- Artifact placements (ArtifactPlacement)
- Panel context for narrative flow (PanelContext)
- Tempo/pacing control

3 scenes x 6 panels = 18 panels total.
"""

import sys
import json
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path
from enum import Enum


# Base paths
BASE_DIR = Path(__file__).parent.parent
REPO_ROOT = BASE_DIR.parent.parent
PHASE4_DIR = BASE_DIR / "phase4_storyboard"
SOURCE_DIR = REPO_ROOT / "source" / "001"

# Previous phase paths
PHASE1_DIR = BASE_DIR / "phase1_characters"
PHASE3_DIR = BASE_DIR / "phase3_backgrounds_artifacts"


# ─────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────

class ShotType(Enum):
    EXTREME_CLOSE_UP = "extreme_close_up"
    CLOSE_UP = "close_up"
    MEDIUM_CLOSE_UP = "medium_close_up"
    MEDIUM_SHOT = "medium_shot"
    MEDIUM_WIDE = "medium_wide"
    WIDE_SHOT = "wide_shot"
    ESTABLISHING = "establishing"


class CameraAngle(Enum):
    EYE_LEVEL = "eye_level"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    DUTCH_ANGLE = "dutch_angle"
    BIRDS_EYE = "birds_eye"
    WORMS_EYE = "worms_eye"


class CameraMovement(Enum):
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"


class PanelShape(Enum):
    RECTANGLE_WIDE = "rectangle_wide"
    RECTANGLE_STANDARD = "rectangle_standard"
    RECTANGLE_TALL = "rectangle_tall"
    SQUARE = "square"
    DIAGONAL_LEFT = "diagonal_left"
    DIAGONAL_RIGHT = "diagonal_right"
    IRREGULAR_JAGGED = "irregular_jagged"
    BORDERLESS = "borderless"
    CIRCULAR = "circular"
    INSET = "inset"


class Tempo(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    FREEZE = "freeze"


# ─────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────

@dataclass
class CharacterPosition:
    character_id: str
    frame_position: str
    x_percent: float
    y_percent: float
    scale: float
    posture: str
    pose_description: str
    expression: str
    facing: str


@dataclass
class ActionDescription:
    action_type: str
    motion_description: str
    motion_direction: Optional[str]
    motion_intensity: float
    requires_speed_lines: bool
    requires_motion_blur: bool
    impact_point: Optional[str]


@dataclass
class ArtifactPlacement:
    artifact_id: str
    position: str
    visibility: str
    state: str
    lighting_context: str
    importance: str


@dataclass
class SpeechBubbleSafeZone:
    zone_id: str
    position: str
    x_percent: float
    y_percent: float
    width_percent: float
    height_percent: float
    speaker_id: Optional[str]
    bubble_type: str
    text_preview: Optional[str]


@dataclass
class PanelContext:
    previous_panel_summary: str
    scene_context: str
    emotional_state: str
    narrative_purpose: str


@dataclass
class EnhancedPanelSpec:
    panel_id: str
    scene_id: str
    sequence_number: int
    context: PanelContext
    shot_type: ShotType
    camera_angle: CameraAngle
    camera_movement: CameraMovement
    focus_point: str
    depth_of_field: str
    panel_shape: PanelShape
    aspect_ratio: str
    page_position: Optional[str]
    bleed: bool
    characters: List[CharacterPosition]
    action: Optional[ActionDescription]
    artifacts: List[ArtifactPlacement]
    tempo: Tempo
    panel_duration: str
    safe_zones: List[SpeechBubbleSafeZone]
    location_id: str
    time_of_day: str
    lighting_preset: str
    weather: Optional[str]
    effects: List[str]
    mood: str
    color_emphasis: Optional[str]
    generation_model: Optional[str] = None
    generation_notes: Optional[str] = None
    source_text: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to serializable dict with enum values as strings."""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Enum):
                d[k] = v.value
            elif isinstance(v, list):
                d[k] = [asdict(item) if hasattr(item, '__dataclass_fields__') else item for item in v]
            elif hasattr(v, '__dataclass_fields__'):
                d[k] = asdict(v)
            else:
                d[k] = v
        return d


# ─────────────────────────────────────────────────────────────────────
# Reference paths
# ─────────────────────────────────────────────────────────────────────

CHARACTER_REFS = {
    "jin_sohan": str(PHASE1_DIR / "jin_sohan" / "base_reference.png"),
    "dokma": str(PHASE1_DIR / "dokma" / "base_reference.png"),
    "uiseon": str(PHASE1_DIR / "uiseon" / "base_reference.png"),
}

BACKGROUND_REFS = {
    "magic_tower_exterior": str(PHASE3_DIR / "locations" / "magic_tower" / "base_reference.png"),
    "magic_tower_interior": str(PHASE3_DIR / "locations" / "magic_tower" / "interior_hall.png"),
}

ARTIFACT_REFS = {
    "twin_crescent_blades": str(PHASE3_DIR / "artifacts" / "twin_crescent_blades" / "base_reference.png"),
    "white_fan": str(PHASE3_DIR / "artifacts" / "white_fan" / "base_reference.png"),
    "golden_peach": str(PHASE3_DIR / "artifacts" / "golden_peach" / "base_reference.png"),
    "two_headed_snake": str(PHASE3_DIR / "artifacts" / "two_headed_snake" / "base_reference.png"),
    "poison_pouch": str(PHASE3_DIR / "artifacts" / "poison_pouch" / "base_reference.png"),
}


# ─────────────────────────────────────────────────────────────────────
# StoryboardGenerator
# ─────────────────────────────────────────────────────────────────────

class StoryboardGenerator:
    def __init__(self):
        pass

    def _save_json(self, data, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Scene 1: The Request to Leave ──────────────────────────────

    def generate_scene_01_request(self) -> list[EnhancedPanelSpec]:
        """Scene 1: Jin Sohan asks masters for permission to leave. Dialogue heavy."""
        panels = []

        # S1P01: Establishing - Magic Tower exterior
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p01",
            scene_id="scene_01_request",
            sequence_number=1,
            context=PanelContext(
                previous_panel_summary="Chapter opening - no previous panel",
                scene_context="Jin Sohan approaches his masters to make a formal request",
                emotional_state="Tense formality, respectful determination",
                narrative_purpose="Establish setting and atmosphere",
            ),
            shot_type=ShotType.ESTABLISHING,
            camera_angle=CameraAngle.LOW_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Tower silhouette through fog",
            depth_of_field="deep",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="top_full_width",
            bleed=True,
            characters=[],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[
                SpeechBubbleSafeZone("narration_top", "top_center", 30, 5, 40, 15, None, "narration", "The fog-shrouded Magic Tower..."),
            ],
            location_id="magic_tower_exterior",
            time_of_day="twilight",
            lighting_preset="fog_day",
            weather="heavy_fog",
            effects=["atmospheric_fog", "subtle_glow"],
            mood="mysterious, isolated",
            color_emphasis="cool_blues_grays",
            generation_model="fal-ai/flux-pro/kontext/text-to-image",
            generation_notes="No character refs needed. Pure environment establishing shot.",
            source_text="안개가 자욱한 마선루(魔仙樓).",
        ))

        # S1P02: Medium wide - Jin Sohan kneeling before masters
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p02",
            scene_id="scene_01_request",
            sequence_number=2,
            context=PanelContext(
                previous_panel_summary="Establishing shot of Magic Tower exterior",
                scene_context="Moving inside to the main hall",
                emotional_state="Formal, respectful tension",
                narrative_purpose="Show Jin Sohan's humble request posture",
            ),
            shot_type=ShotType.MEDIUM_WIDE,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Jin Sohan kneeling",
            depth_of_field="medium",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="landscape_4_3",
            page_position="middle_left",
            bleed=False,
            characters=[
                CharacterPosition("jin_sohan", "center", 50, 70, 1.0, "kneeling", "Formal kneeling position, hands on thighs, head slightly bowed", "determined_but_respectful", "away"),
                CharacterPosition("dokma", "background_left", 25, 30, 0.7, "sitting", "Seated on elevated platform, leaning back casually", "skeptical_smirk", "camera"),
                CharacterPosition("uiseon", "background_right", 75, 30, 0.7, "sitting", "Seated on elevated platform, leaning forward", "thoughtful_concern", "camera"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.NORMAL,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("jin_speech", "bottom_center", 25, 80, 50, 18, "jin_sohan", "speech", "Masters, I wish to request leave..."),
            ],
            location_id="magic_tower_interior",
            time_of_day="twilight",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["subtle_fog_interior"],
            mood="formal, tense",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with all 3 character references.",
            source_text="'하산?' '예.'",
        ))

        # S1P03: Close-up - Dokma cynical
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p03",
            scene_id="scene_01_request",
            sequence_number=3,
            context=PanelContext(
                previous_panel_summary="Wide shot showing Jin Sohan kneeling before both masters",
                scene_context="Dokma responds with characteristic cynicism",
                emotional_state="Skeptical, testing",
                narrative_purpose="Show Dokma's reaction and personality",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.LOW_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Dokma's face",
            depth_of_field="shallow",
            panel_shape=PanelShape.RECTANGLE_TALL,
            aspect_ratio="portrait_4_3",
            page_position="middle_right",
            bleed=False,
            characters=[
                CharacterPosition("dokma", "center", 50, 50, 1.2, "sitting", "Upper body and face, chin slightly raised", "cynical_smirk, raised_eyebrow", "camera_slight_left"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.NORMAL,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("dokma_speech", "top_right", 50, 5, 45, 25, "dokma", "speech", "After all these years, you finally want to leave?"),
            ],
            location_id="magic_tower_interior",
            time_of_day="twilight",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["dramatic_shadow"],
            mood="skeptical, testing",
            color_emphasis="dark_shadows",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="Single character close-up with Dokma reference.",
            source_text="'자신만만하구나. 고작 십이 년을 수련해놓고……'",
        ))

        # S1P04: Close-up - Uiseon concerned
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p04",
            scene_id="scene_01_request",
            sequence_number=4,
            context=PanelContext(
                previous_panel_summary="Dokma's cynical close-up response",
                scene_context="Uiseon adds his perspective with gentle concern",
                emotional_state="Wise concern, gentle warning",
                narrative_purpose="Show contrast between twin masters",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Uiseon's face",
            depth_of_field="shallow",
            panel_shape=PanelShape.SQUARE,
            aspect_ratio="square_1_1",
            page_position="bottom_left",
            bleed=False,
            characters=[
                CharacterPosition("uiseon", "center", 50, 50, 1.2, "sitting", "Face close-up, gentle expression", "thoughtful_concern, gentle_warning", "camera"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.NORMAL,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("uiseon_speech", "bottom_center", 15, 75, 70, 20, "uiseon", "speech", "If it were a proper faction's territory, we would let you go..."),
            ],
            location_id="magic_tower_interior",
            time_of_day="twilight",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["soft_light"],
            mood="wise, concerned",
            color_emphasis="warm_tones",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="Single character close-up with Uiseon reference.",
            source_text="'차라리 명문정파가 지배하는 지역이라면 보내주겠다만...'",
        ))

        # S1P05: Two-shot - Masters exchanging glances
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p05",
            scene_id="scene_01_request",
            sequence_number=5,
            context=PanelContext(
                previous_panel_summary="Uiseon's concerned close-up",
                scene_context="The twins share a meaningful look",
                emotional_state="Unspoken understanding, reluctant acceptance",
                narrative_purpose="Show twin bond and silent communication",
            ),
            shot_type=ShotType.MEDIUM_CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Eye contact between the twins",
            depth_of_field="medium",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="bottom_center",
            bleed=False,
            characters=[
                CharacterPosition("dokma", "left", 30, 50, 1.0, "sitting", "Slight turn toward brother", "subtle_acknowledgment", "right"),
                CharacterPosition("uiseon", "right", 70, 50, 1.0, "sitting", "Slight turn toward brother", "knowing_look", "left"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="moment",
            safe_zones=[],
            location_id="magic_tower_interior",
            time_of_day="twilight",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=[],
            mood="unspoken understanding",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with Dokma + Uiseon refs.",
            source_text="독마와 의선이 동시에 혀를 찼다. '쯧……'",
        ))

        # S1P06: Reaction - Jin Sohan determined
        panels.append(EnhancedPanelSpec(
            panel_id="s1_p06",
            scene_id="scene_01_request",
            sequence_number=6,
            context=PanelContext(
                previous_panel_summary="Masters exchange a meaningful silent glance",
                scene_context="Jin Sohan's resolve is clear",
                emotional_state="Unwavering determination",
                narrative_purpose="Establish protagonist's resolve",
            ),
            shot_type=ShotType.MEDIUM_CLOSE_UP,
            camera_angle=CameraAngle.LOW_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Jin Sohan's determined expression",
            depth_of_field="shallow",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="portrait_4_3",
            page_position="bottom_right",
            bleed=False,
            characters=[
                CharacterPosition("jin_sohan", "center", 50, 50, 1.0, "kneeling", "Looking up at masters with resolve", "determined_calm", "camera"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[
                SpeechBubbleSafeZone("jin_speech", "bottom_center", 15, 78, 70, 18, "jin_sohan", "speech", "Even if just one person remains, I will repay the debt I owe."),
            ],
            location_id="magic_tower_interior",
            time_of_day="twilight",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["dramatic_lighting"],
            mood="determined, resolute",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="Single character with Jin Sohan reference.",
            source_text="'한 명이라도 있다면 제자가 받았던 은혜, 갚겠습니다.'",
        ))

        return panels

    # ── Scene 2: The Backstory (Flashback + Atmosphere) ────────────

    def generate_scene_02_backstory(self) -> list[EnhancedPanelSpec]:
        """Scene 2: Jin Sohan tells the story of the golden peach. Flashback panels with special shapes."""
        panels = []

        # S2P01: Storytelling setup
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p01",
            scene_id="scene_02_storytelling",
            sequence_number=1,
            context=PanelContext(
                previous_panel_summary="Scene transition from the request scene",
                scene_context="Jin Sohan begins telling his masters a story",
                emotional_state="Intimate, storytelling warmth",
                narrative_purpose="Set up the storytelling frame",
            ),
            shot_type=ShotType.MEDIUM_SHOT,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Jin Sohan gesturing while speaking",
            depth_of_field="medium",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="landscape_4_3",
            page_position="top",
            bleed=False,
            characters=[
                CharacterPosition("jin_sohan", "center", 50, 60, 1.0, "kneeling", "Formal kneeling, gesturing expressively", "earnest", "toward_masters"),
                CharacterPosition("dokma", "right_bg", 75, 30, 0.7, "sitting", "Seated, leaning forward slightly", "amused_skeptical", "toward_jin_sohan"),
                CharacterPosition("uiseon", "left_bg", 25, 30, 0.7, "sitting", "Seated, gentle attention", "gentle_curious", "toward_jin_sohan"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("narration_top", "top_center", 10, 3, 80, 12, None, "narration", "Jin Sohan began his tale..."),
            ],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["warm_glow"],
            mood="intimate, storytelling",
            color_emphasis="warm_tones",
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with all three character refs. Warm indoor lighting.",
            source_text="'예, 그럼 이제부터 제자가 허언신공을 한 번 펼쳐보겠습니다.'",
        ))

        # S2P02: Flashback - Golden Peach (CIRCULAR panel)
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p02",
            scene_id="scene_02_storytelling",
            sequence_number=2,
            context=PanelContext(
                previous_panel_summary="Jin Sohan begins telling his childhood story",
                scene_context="Flashback to the golden peach tree at night",
                emotional_state="Mystical wonder",
                narrative_purpose="Introduce the supernatural element",
            ),
            shot_type=ShotType.WIDE_SHOT,
            camera_angle=CameraAngle.LOW_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Golden peach tree glowing in moonlight",
            depth_of_field="medium",
            panel_shape=PanelShape.CIRCULAR,
            aspect_ratio="square_1_1",
            page_position="middle",
            bleed=False,
            characters=[],
            action=None,
            artifacts=[
                ArtifactPlacement("golden_peach", "center", "full", "glowing", "moonlight_supernatural", "focus"),
            ],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[],
            location_id="countryside_night",
            time_of_day="night",
            lighting_preset="fog_night",
            weather=None,
            effects=["ethereal_glow", "soft_particles", "dreamlike_blur"],
            mood="mystical, dreamlike",
            color_emphasis="golden_luminous",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="CIRCULAR flashback panel. Use golden_peach artifact ref. Dreamlike quality.",
            source_text="그 나무에 다른 복숭아와 빛깔이 전혀 다른 황금 복숭아가 높은 곳에 달려있었는데...",
        ))

        # S2P03: Flashback - Two-headed snake (JAGGED panel)
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p03",
            scene_id="scene_02_storytelling",
            sequence_number=3,
            context=PanelContext(
                previous_panel_summary="The golden peach glowing on the tree",
                scene_context="The mysterious two-headed snake appears",
                emotional_state="Ominous wonder",
                narrative_purpose="Reveal the supernatural creature",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Two-headed snake emerging from roots",
            depth_of_field="shallow",
            panel_shape=PanelShape.IRREGULAR_JAGGED,
            aspect_ratio="landscape_4_3",
            page_position="middle",
            bleed=False,
            characters=[],
            action=ActionDescription("reveal", "Snake slowly emerging", None, 0.3, False, False, None),
            artifacts=[
                ArtifactPlacement("two_headed_snake", "center", "full", "coiled_alert", "moonlight_supernatural", "focus"),
            ],
            tempo=Tempo.SLOW,
            panel_duration="moment",
            safe_zones=[],
            location_id="countryside_night",
            time_of_day="night",
            lighting_preset="fog_night",
            weather=None,
            effects=["eerie_atmosphere", "mist"],
            mood="ominous, wondrous",
            color_emphasis="cool_greens_with_gold",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="JAGGED-edge panel for supernatural tension. Use two_headed_snake artifact ref.",
            source_text="머리가 두 개지 뭡니까?",
        ))

        # S2P04: Flashback - Young Jin Sohan (BORDERLESS panel)
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p04",
            scene_id="scene_02_storytelling",
            sequence_number=4,
            context=PanelContext(
                previous_panel_summary="The two-headed snake revealed",
                scene_context="Young Jin Sohan stands unaffected among sleeping crowd",
                emotional_state="Isolation, wonder",
                narrative_purpose="Show Jin Sohan's unique nature",
            ),
            shot_type=ShotType.MEDIUM_SHOT,
            camera_angle=CameraAngle.HIGH_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Young Jin Sohan standing amid sleeping figures",
            depth_of_field="medium",
            panel_shape=PanelShape.BORDERLESS,
            aspect_ratio="portrait_3_4",
            page_position="middle",
            bleed=True,
            characters=[
                CharacterPosition("jin_sohan_young", "center", 50, 50, 1.0, "standing", "Standing still among sleeping bodies around", "calm_confused", "camera"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[
                SpeechBubbleSafeZone("narration_bottom", "bottom_center", 15, 82, 70, 15, None, "narration", "Everyone had collapsed... except the boy."),
            ],
            location_id="performance_grounds",
            time_of_day="evening",
            lighting_preset="fog_night",
            weather="light_fog",
            effects=["sleeping_bodies_around", "fog_wisps"],
            mood="isolation, wonder",
            color_emphasis="muted_with_spotlight_on_jin",
            generation_model="fal-ai/flux-2/flash",
            generation_notes="BORDERLESS flashback. No existing ref (young version). Text-to-image with style prompt.",
            source_text="모든 사람이 쓰러졌는데 저만 멀쩡했습니다.",
        ))

        # S2P05: Back to present - Masters react
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p05",
            scene_id="scene_02_storytelling",
            sequence_number=5,
            context=PanelContext(
                previous_panel_summary="Flashback of young Jin Sohan's supernatural immunity",
                scene_context="Back to present, masters react to the story",
                emotional_state="Impressed acknowledgment",
                narrative_purpose="Show the masters silently agree it's time",
            ),
            shot_type=ShotType.MEDIUM_CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Dokma and Uiseon exchanging a meaningful glance",
            depth_of_field="medium",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="landscape_4_3",
            page_position="bottom_left",
            bleed=False,
            characters=[
                CharacterPosition("dokma", "left", 30, 50, 1.0, "sitting", "Slight lean forward", "impressed_reluctant", "toward_uiseon"),
                CharacterPosition("uiseon", "right", 70, 50, 1.0, "sitting", "Slight nod", "knowing_smile", "toward_dokma"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("thought_left", "top_left", 5, 5, 25, 20, "dokma", "thought", "(This kid...)"),
                SpeechBubbleSafeZone("thought_right", "top_right", 70, 5, 25, 20, "uiseon", "thought", "(It's time.)"),
            ],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=[],
            mood="unspoken_affection, acknowledgment",
            color_emphasis="warm_amber",
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with Dokma + Uiseon refs.",
            source_text="독마와 의선이 동시에 고개를 끄덕였다.",
        ))

        # S2P06: Transition - Tower exterior night
        panels.append(EnhancedPanelSpec(
            panel_id="s2_p06",
            scene_id="scene_02_storytelling",
            sequence_number=6,
            context=PanelContext(
                previous_panel_summary="Masters silently agree to let Jin Sohan go",
                scene_context="Night settles over the tower, transition to departure",
                emotional_state="Quiet transition, passage of time",
                narrative_purpose="Bridge between storytelling and departure",
            ),
            shot_type=ShotType.ESTABLISHING,
            camera_angle=CameraAngle.BIRDS_EYE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Magic Tower exterior at night in fog",
            depth_of_field="deep",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="bottom_full_width",
            bleed=True,
            characters=[],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[],
            location_id="magic_tower_exterior",
            time_of_day="night",
            lighting_preset="fog_night",
            weather="dense_fog",
            effects=["moonlight_through_fog"],
            mood="transition, passage_of_time",
            color_emphasis="cool_blues_muted",
            generation_model="fal-ai/flux-2/flash",
            generation_notes="Transition panel. No characters, pure atmosphere.",
        ))

        return panels

    # ── Scene 3: The Departure (Emotional + Artifacts) ─────────────

    def generate_scene_03_departure(self) -> list[EnhancedPanelSpec]:
        """Scene 3: Masters give Jin Sohan parting gifts. Artifact-heavy, emotional."""
        panels = []

        # S3P01: Artifact focus - Twin crescent moon blades
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p01",
            scene_id="scene_03_departure",
            sequence_number=1,
            context=PanelContext(
                previous_panel_summary="Masters have agreed to let Jin Sohan leave",
                scene_context="Dokma presents the twin crescent moon blades",
                emotional_state="Reverent, significant moment",
                narrative_purpose="Introduce the signature weapons with proper weight",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.ZOOM_IN,
            focus_point="Twin crescent moon blades on table",
            depth_of_field="shallow",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="top_full_width",
            bleed=True,
            characters=[],
            action=None,
            artifacts=[
                ArtifactPlacement("twin_crescent_blades", "center", "full", "displayed", "warm_lamp_reverent", "focus"),
            ],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["subtle_glow_on_blades"],
            mood="reverent, significant",
            color_emphasis="warm_gold_highlights",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="CRITICAL: Use twin_crescent_blades reference. Blade design must match exactly.",
            source_text="독마가 두 자루의 칼을 탁자 위에 내밀었다. '쌍월(雙月)은 네가 앞으로 써라.'",
        ))

        # S3P02: Medium - Dokma handing blades
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p02",
            scene_id="scene_03_departure",
            sequence_number=2,
            context=PanelContext(
                previous_panel_summary="Close-up of twin blades on table",
                scene_context="Dokma hands the blades to Jin Sohan",
                emotional_state="Gruff affection, hidden care",
                narrative_purpose="Show master-student bond through gift-giving",
            ),
            shot_type=ShotType.MEDIUM_SHOT,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Exchange of weapons between hands",
            depth_of_field="medium",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="landscape_4_3",
            page_position="middle_left",
            bleed=False,
            characters=[
                CharacterPosition("dokma", "left", 30, 50, 1.0, "standing", "Holding out blades with both hands, formal", "stern_but_fond", "right"),
                CharacterPosition("jin_sohan", "right", 70, 50, 1.0, "standing", "Receiving with both hands, slight bow", "grateful_moved", "left"),
            ],
            action=ActionDescription("static", "Formal handover moment, frozen in time", None, 0, False, False, None),
            artifacts=[
                ArtifactPlacement("twin_crescent_blades", "center_between_characters", "full", "held", "warm_lamp", "focus"),
            ],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[
                SpeechBubbleSafeZone("dokma_speech", "top_left", 5, 5, 40, 20, "dokma", "speech", "Take these. They've served me well."),
            ],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=[],
            mood="gruff_affection, significant_moment",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="CRITICAL: Use Kontext Multi with Dokma + Jin Sohan + twin_crescent_blades refs.",
            source_text="'내가 사용하는 것보다 네게 더 도움이 될 거다.'",
        ))

        # S3P03: Artifact focus - White fan
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p03",
            scene_id="scene_03_departure",
            sequence_number=3,
            context=PanelContext(
                previous_panel_summary="Dokma handed the twin blades to Jin Sohan",
                scene_context="Uiseon offers his white fan",
                emotional_state="Gentle, meaningful",
                narrative_purpose="Second gift - contrasting gentle personality",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="White fan being offered",
            depth_of_field="shallow",
            panel_shape=PanelShape.RECTANGLE_STANDARD,
            aspect_ratio="portrait_4_3",
            page_position="middle_right",
            bleed=False,
            characters=[
                CharacterPosition("uiseon", "left", 20, 50, 0.6, "standing", "Hands extending fan, only hands and lower arms visible", "gentle_offering", "right"),
            ],
            action=None,
            artifacts=[
                ArtifactPlacement("white_fan", "center", "full", "held", "warm_lamp_gentle", "focus"),
            ],
            tempo=Tempo.SLOW,
            panel_duration="moment",
            safe_zones=[
                SpeechBubbleSafeZone("uiseon_speech", "bottom_center", 10, 75, 80, 20, "uiseon", "speech", "Take the White Fan as well."),
            ],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["soft_light"],
            mood="gentle, meaningful",
            color_emphasis="white_highlight",
            generation_model="fal-ai/flux-pro/kontext",
            generation_notes="Use white_fan artifact ref. Uiseon hands partially visible.",
            source_text="의선이 자신의 쥘부채를 내밀면서 말했다. '백선(白扇)도 챙겨라.'",
        ))

        # S3P04: Wide - Jin Sohan bowing
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p04",
            scene_id="scene_03_departure",
            sequence_number=4,
            context=PanelContext(
                previous_panel_summary="Uiseon offered his white fan",
                scene_context="Jin Sohan performs a deep formal bow of farewell",
                emotional_state="Deep gratitude, solemn farewell",
                narrative_purpose="The formal farewell after 12 years",
            ),
            shot_type=ShotType.WIDE_SHOT,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Jin Sohan in deep bow",
            depth_of_field="deep",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="bottom_left",
            bleed=False,
            characters=[
                CharacterPosition("jin_sohan", "center", 50, 70, 1.0, "kneeling", "Deep formal bow, forehead to floor", "deep_gratitude", "down"),
                CharacterPosition("dokma", "left_bg", 25, 35, 0.7, "standing", "Standing stoically", "stoic_hiding_emotion", "toward_jin_sohan"),
                CharacterPosition("uiseon", "right_bg", 75, 35, 0.7, "standing", "Standing with gentle sadness", "gentle_sadness", "toward_jin_sohan"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=[],
            mood="solemn, emotional",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with all 3 character refs.",
            source_text="얼떨떨한 진소한이 서둘러서 절을 올렸다.",
        ))

        # S3P05: Two-shot - Masters' hidden emotions
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p05",
            scene_id="scene_03_departure",
            sequence_number=5,
            context=PanelContext(
                previous_panel_summary="Jin Sohan bows deeply in farewell",
                scene_context="The masters hide their sadness",
                emotional_state="Restrained emotion, bittersweet",
                narrative_purpose="Show depth of the bond",
            ),
            shot_type=ShotType.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC,
            focus_point="Both masters' faces showing hidden emotion",
            depth_of_field="shallow",
            panel_shape=PanelShape.RECTANGLE_WIDE,
            aspect_ratio="landscape_16_9",
            page_position="bottom_center",
            bleed=False,
            characters=[
                CharacterPosition("dokma", "left", 30, 50, 1.0, "standing", "Face forward, stoic exterior", "stoic_but_eyes_betray_emotion", "camera"),
                CharacterPosition("uiseon", "right", 70, 50, 1.0, "standing", "Face forward, gentle sadness", "gentle_sadness_in_eyes", "camera"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[
                SpeechBubbleSafeZone("dokma_speech", "bottom_left", 5, 75, 40, 20, "dokma", "speech", "Go, and do well. Guard your neck."),
                SpeechBubbleSafeZone("uiseon_speech", "bottom_right", 55, 75, 40, 20, "uiseon", "speech", "We'll hear your news through the fame that spreads."),
            ],
            location_id="magic_tower_interior",
            time_of_day="evening",
            lighting_preset="indoor_lamp",
            weather=None,
            effects=["subtle_vignette"],
            mood="restrained emotion, bittersweet",
            color_emphasis=None,
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Use Kontext Multi with Dokma + Uiseon refs. Emotional close-up.",
            source_text="'가서, 잘해라. 목덜미 잘 간수하고.'",
        ))

        # S3P06: Silhouette - Walking into fog
        panels.append(EnhancedPanelSpec(
            panel_id="s3_p06",
            scene_id="scene_03_departure",
            sequence_number=6,
            context=PanelContext(
                previous_panel_summary="Masters give final words with hidden emotion",
                scene_context="Jin Sohan walks into the fog, leaving the tower",
                emotional_state="Bittersweet hope, new beginning",
                narrative_purpose="The final departure — a new journey begins",
            ),
            shot_type=ShotType.WIDE_SHOT,
            camera_angle=CameraAngle.LOW_ANGLE,
            camera_movement=CameraMovement.STATIC,
            focus_point="Jin Sohan's silhouette walking into fog",
            depth_of_field="deep",
            panel_shape=PanelShape.RECTANGLE_TALL,
            aspect_ratio="portrait_9_16",
            page_position="right_full_height",
            bleed=True,
            characters=[
                CharacterPosition("jin_sohan", "center", 50, 60, 0.8, "walking", "Silhouette walking into dense fog, back to viewer", "determined", "away"),
                CharacterPosition("dokma", "far_left_bg", 15, 85, 0.3, "standing", "Small silhouette at tower entrance", "watching", "toward_jin_sohan"),
                CharacterPosition("uiseon", "far_right_bg", 25, 85, 0.3, "standing", "Small silhouette at tower entrance", "watching", "toward_jin_sohan"),
            ],
            action=None,
            artifacts=[],
            tempo=Tempo.SLOW,
            panel_duration="extended",
            safe_zones=[],
            location_id="magic_tower_exterior",
            time_of_day="twilight",
            lighting_preset="fog_day",
            weather="dense_fog",
            effects=["dense_fog", "silhouette_backlight", "atmospheric"],
            mood="bittersweet, hopeful, new beginning",
            color_emphasis="fog_white_gradient",
            generation_model="fal-ai/flux-pro/kontext/multi",
            generation_notes="Silhouette composition. Use all 3 character refs for consistency even in silhouette.",
            source_text="진소한은 자신의 예상과 다르게 시원섭섭한 감정을 맛보고 있었다.",
        ))

        return panels

    # ── Generation entry points ────────────────────────────────────

    def save_scene_panels(self, scene_id: str, panels: list[EnhancedPanelSpec]) -> dict:
        """Save panel specifications for a scene."""
        scene_dir = PHASE4_DIR / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        for panel in panels:
            panel_data = panel.to_dict()
            panel_path = scene_dir / f"{panel.panel_id}_spec.json"
            self._save_json(panel_data, panel_path)

        # Save scene-level combined spec
        all_specs = [p.to_dict() for p in panels]
        self._save_json({
            "scene_id": scene_id,
            "total_panels": len(panels),
            "panels": all_specs,
            "generated_at": datetime.now().isoformat(),
        }, scene_dir / "enhanced_panel_specs.json")

        manifest = {
            "scene_id": scene_id,
            "total_panels": len(panels),
            "panel_ids": [p.panel_id for p in panels],
            "generated_at": datetime.now().isoformat(),
        }
        self._save_json(manifest, scene_dir / "scene_manifest.json")

        return manifest

    def generate_all_scenes(self) -> dict:
        """Generate storyboards for all three scenes."""
        results = {
            "phase": "Phase 4: Enhanced Storyboarding",
            "timestamp": datetime.now().isoformat(),
            "scenes": {}
        }

        scene_generators = [
            ("scene_01_request", "The Request to Leave", self.generate_scene_01_request),
            ("scene_02_storytelling", "The Backstory", self.generate_scene_02_backstory),
            ("scene_03_departure", "The Departure", self.generate_scene_03_departure),
        ]

        for scene_id, title, gen_func in scene_generators:
            print(f"  Generating {title}...")
            panels = gen_func()
            manifest = self.save_scene_panels(scene_id, panels)
            results["scenes"][scene_id] = {
                "title": title,
                "panel_count": len(panels),
                "manifest": manifest,
                "panel_shapes": [p.panel_shape.value for p in panels],
                "models_needed": list(set(p.generation_model for p in panels if p.generation_model)),
            }
            print(f"    {len(panels)} panels generated")

        total_panels = sum(s["panel_count"] for s in results["scenes"].values())
        results["total_panels"] = total_panels
        results["success"] = True

        results_path = PHASE4_DIR / "phase4_results.json"
        self._save_json(results, results_path)

        return results


def main():
    test_mode = "--test" in sys.argv

    print("=" * 60)
    print("Phase 4: Enhanced Storyboard Generation")
    if test_mode:
        print("*** TEST MODE - Scene 1 only ***")
    print("=" * 60)

    generator = StoryboardGenerator()

    if test_mode:
        print("\n  Generating Scene 1: The Request to Leave...")
        panels = generator.generate_scene_01_request()
        manifest = generator.save_scene_panels("scene_01_request", panels)
        print(f"    {len(panels)} panels saved")
        print(f"    Panel shapes: {[p.panel_shape.value for p in panels]}")
        print(f"    Safe zones: {sum(len(p.safe_zones) for p in panels)} total")
        results = {"scenes": {"scene_01_request": {"panel_count": len(panels)}}, "total_panels": len(panels)}
    else:
        results = generator.generate_all_scenes()

    print("\n" + "=" * 60)
    print("Phase 4 Summary")
    print("=" * 60)
    print(f"  Total scenes: {len(results['scenes'])}")
    print(f"  Total panels: {results['total_panels']}")
    for scene_id, scene_data in results["scenes"].items():
        print(f"    {scene_id}: {scene_data['panel_count']} panels")
    print(f"\n  Results: {PHASE4_DIR / 'phase4_results.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
