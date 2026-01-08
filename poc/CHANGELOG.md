# Changelog

All notable changes to the novel-to-toon workflow will be documented in this file.

## [0.2.0] - In Progress

### Added
- Artifact reference workflow (Phase 3) for consistent weapon/item rendering
- Enhanced panel specifications with camera angles, positions, actions, tempo, context
- Panel shape variety system (diagonal, irregular, circular panels)
- Speech bubble safe zones for dialogue placement
- Cost optimization strategy (hybrid model selection, batch processing, context caching)
- Spending tracker implementation (`scripts/cost_tracker.py`)
- Resolution strategy (2K for references, 1K for panels)

### Changed
- Phase 3 renamed from "Backgrounds" to "Backgrounds and Artifacts"
- Panel specification data structure expanded with 15+ new fields
- Target cost per panel reduced from $0.134 to $0.03-0.05

### Goals
- Artifact consistency score > 85%
- Safe zone compliance > 90%
- 70-80% cost reduction from v0.1.0

## [0.1.0] - 2024-12-30

### Added
- Initial 5-phase workflow structure
- Phase 1: Character design with reference image-based generation
- Phase 2: Art style definition with Claude Agent SDK
- Phase 3: Background and material generation
- Phase 4: Storyboard generation from novel text
- Phase 5: Panel image generation with quality control
- Reference image workflow for character consistency
- Twin character differentiation workflow
- Basic panel specification structure
- Quality validation system

### Scripts
- `character_generator.py` - Character reference sheet generation
- `style_agent.py` - Art style analysis and prompt generation
- `background_generator.py` - Location and material generation
- `storyboard_generator.py` - Novel to panel specification conversion
- `panel_generator.py` - Final panel image generation

### Test Material
- Source: Disciple of the Villain (Korean Wuxia novel)
- 3 test scenes with 18 panel specifications

### Known Issues
- Artifact inconsistency across panels (addressed in 0.2.0)
- All panels rectangular (addressed in 0.2.0)
- Speech bubble areas getting cut off (addressed in 0.2.0)
- High cost (~$12 for POC) (addressed in 0.2.0)
