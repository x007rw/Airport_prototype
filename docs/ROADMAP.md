# 🗺️ Project Roadmap: Airport -> Stratosphere

Our ultimate goal is to evolve `Airport` into a universal GUI automation agent capable of controlling Windows Desktop applications using LLMs.

## Phase 1: Robust Web Automation (✅ Completed)
- [x] Hybrid Analysis (DOM + OpenCV)
- [x] CLI & GUI Mode Support
- [x] Basic Logging & Screenshots

## Phase 2: Action Chains & Workflows (Current Focus)
- [ ] **Flight Plans (YAML)**: Define complex sequences of actions (Click -> Type -> Wait -> Verify).
- [ ] **State Management**: Carry over data (variables) between steps.
- [ ] **Error Handling**: Retry logic and conditional branching (If ... then ...).

## Phase 3: The "Vision" Upgrade (LLM Integration)
- [ ] **LLM Brain**: Replace/Augment OpenCV with Multimodal LLMs (GPT-4o, Gemini 1.5 Pro).
    - Input: Screenshot + Natural Language Instruction ("Click the blue Save button")
    - Output: Coordinates (x, y)
- [ ] **Natural Language Planner**: Convert user prompts ("Log in to Outlook and delete the first email") into Flight Plan YAMLs.

## Phase 4: Beyond the Browser (Desktop Automation)
- [ ] **Windows Driver**: Create an abstraction layer to switch between `PlaywrightDriver` (Web) and `PyWinAutoDriver` / `NativeDriver` (Windows).
- [ ] **Window Management**: Ability to focus, move, and recognize application windows (Notepad, Excel, Explorer).
- [ ] **Universal OCR**: Read text from any UI element, independent of DOM.

## Phase 5: Autonomous Desktop Agent
- [ ] **Long-running Tasks**: Agent can operate autonomously for extended periods.
- [ ] **Self-Correction**: Analyze error messages on screen and attempt fixes without human intervention.
