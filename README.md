# LLM-Enhanced UPPAAL Real-Time Verification System

A powerful web-based platform for formal verification of real-time systems using UPPAAL model checker with integrated LLM support for code generation, property synthesis, and automatic repair.

## 🌟 Features

- **Multi-Language Support**: Ada and Python real-time task code
- **LLM-Powered Code Generation**: Generate task code from natural language requirements
- **Automated UPPAAL Model Generation**: Convert high-level code to formal timed automata
- **Formal Verification**: Run UPPAAL verifyta to prove system properties
- **Intelligent Property Generation**: LLM suggests relevant temporal properties
- **Auto-Repair**: LLM-driven counterexample analysis and code repair
- **Schedulability Analysis**: Rate Monotonic and Liu & Layland bound checks
- **Priority Validation**: Automatic Rate Monotonic priority assignment
- **Real-Time Dashboard**: Monitor verification jobs, success rates, and performance metrics
- **Interactive Task Editor**: Visual task designer with live schedulability feedback

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** with `venv`
2. **UPPAAL 5.0.0+** installed at:
   ```
   C:\Users\akhil\AppData\Local\Programs\UPPAAL-5.0.0\bin\verifyta.exe
   ```
3. **Ollama** (optional, for LLM features):
   ```bash
   ollama pull llama3.1:latest
   ollama serve
   ```

### Installation

1. **Clone or navigate to the project**:
   ```bash
   cd "C:\Users\akhil\OneDrive\Desktop\LLM final year project\LLM final year project"
   ```

2. **Activate virtual environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   python -m pip install flask requests pytest
   ```

4. **Configure UPPAAL path** (if different):
   Edit `config.py` and update `UPPAAL_PATH`

### Running the Server

```bash
python app.py
```

The server will start at **http://127.0.0.1:5000**

## 📖 Usage Guide

### 1. Main Verification Interface (`/`)

**Generate Code from Natural Language**:
1. Enter requirement in the "Natural Language to Code" box:
   ```
   Navigation task with 20ms period, 15ms deadline, priority 10
   ```
2. Click **"Generate Code"**
3. Review generated Ada/Python code
4. Click **"Verify System"**

**Manual Code Entry**:
1. Paste Ada or Python real-time task code
2. Click **"Verify System"**
3. View results:
   - ✅ Task extraction (period, deadline, priority)
   - 📊 Schedulability analysis
   - 🔍 UPPAAL property verification
   - 🔧 Auto-repair attempts (if failures occur)

**Example Ada Code**:
```ada
task Navigation_Task is
   pragma Priority(10);
end Navigation_Task;

task body Navigation_Task is
   Period : constant Time_Span := Milliseconds(20);
   Deadline : constant Time_Span := Milliseconds(15);
   Execution_Time : constant Time_Span := Milliseconds(12);
   Next_Release : Time := Clock;
begin
   loop
      delay until Next_Release;
      -- Navigation logic
      Next_Release := Next_Release + Period;
   end loop;
end Navigation_Task;
```

### 2. Interactive Task Editor (`/editor`)

- **Visual Task Designer**: Add/edit multiple tasks with sliders
- **Live Schedulability**: Real-time utilization and Liu & Layland bound checks
- **What-If Analysis**: Adjust parameters and see immediate feedback
- **Code Preview**: See generated Ada code as you edit
- **Batch Verification**: Verify entire task set at once

### 3. Verification Dashboard (`/dashboard_view`)

Monitor system performance in real-time:
- **Active Jobs**: Currently running verifications
- **Queue Status**: Pending jobs waiting for worker slots
- **Success Metrics**: First-pass success rate, repair convergence
- **History Timeline**: Chart showing verification trends
- **Execution Stats**: Average duration, property counts

Auto-refreshes every 7 seconds.

### 4. REST API Endpoints

#### POST `/verify`
Verify Ada or Python code:
```json
{
  "ada_code": "task body MyTask is ...",
  "language": "ada"
}
```

Response:
```json
{
  "success": true,
  "task_info": { "task_name": "MyTask", "period": 100, ... },
  "verification": {
    "properties_verified": 8,
    "properties_failed": 0,
    "execution_time": 1.234
  },
  "schedulability": {
    "total_utilization": "65.0%",
    "is_schedulable": true
  }
}
```

#### POST `/generate_ada`
Generate Ada code from natural language:
```json
{
  "requirement": "Control task, 10ms period, priority 15"
}
```

#### GET `/dashboard`
Real-time metrics:
```json
{
  "active_jobs": 2,
  "queued_jobs": 5,
  "completed_jobs": 142,
  "success_rate": 87.3,
  "avg_execution_time": 2.15
}
```

#### GET `/metrics`
Detailed benchmark data:
```json
{
  "total_verifications": 142,
  "first_pass_success_rate": 78.5,
  "repair_convergence_rate": 92.3,
  "recent_history": [...]
}
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# UPPAAL Configuration
UPPAAL_PATH = r"C:\path\to\verifyta.exe"

# LLM Settings
OLLAMA_BASE_URL = "http://localhost:11434"
USE_LLM_PROPERTY_GENERATION = True
LLM_FEEDBACK_ENABLED = True
MAX_LLM_REPAIR_ATTEMPTS = 3

# Verification Modes
STRICT_PRIORITY_MODE = False        # Enforce RM priorities
ALLOW_UNSCHEDULABLE = False         # Allow systems above LL bound
USE_SHARED_SCHEDULER = True         # Multi-task shared CPU model
USE_PRIORITY_VALIDATION = True      # Auto-fix priorities

# Output Settings
SHOW_RAW_UPPAAL_OUTPUT = True
ENABLE_BUNDLE_EXPORT = True
```

## 📁 Project Structure

```
LLM final year project/
├── app.py                          # Flask application entry point
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── core/                           # Core verification modules
│   ├── llm_property_generator.py   # LLM-based property synthesis
│   ├── priority_validator.py       # RM priority checking
│   ├── schedulability_analyzer.py  # RM schedulability tests
│   ├── response_time_analyzer.py   # Response time analysis
│   ├── counterexample_analyzer.py  # UPPAAL trace parsing
│   ├── property_repair.py          # Auto-repair engine
│   └── uppaal_rag.py               # RAG for UPPAAL queries
│
├── modules/
│   └── verification_engine.py      # Main verifier orchestrator
│
├── routes/                         # Flask route handlers
│   ├── view_routes.py              # HTML page rendering
│   ├── verification_routes.py      # /verify endpoint logic
│   ├── generation_routes.py        # Code generation endpoints
│   └── async_routes.py             # Async verification + dashboard
│
├── templates/                      # HTML UI templates
│   ├── index.html                  # Main verification interface
│   ├── task_editor.html            # Interactive task designer
│   ├── dashboard.html              # Real-time metrics dashboard
│   └── enhanced_results.html       # Detailed result viewer
│
├── verification_results/           # Generated UPPAAL XML files
└── artifacts/                      # Full pipeline artifacts
    ├── navigation_task_v1/         # 3-task scenario
    │   ├── spec.json
    │   ├── uppaal_model.xml
    │   ├── verifyta_stdout.txt
    │   ├── VerifiedScheduler.hs
    │   └── SDD.md
    └── navigation_task_v2/         # 5-task extended scenario
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest
```

Run specific test:
```bash
python test_scheduler_fix.py
```

## 🎯 Verification Workflow

1. **Input**: Ada/Python code or natural language requirement
2. **Extraction**: Parse task parameters (period, deadline, priority)
3. **Priority Validation**: Auto-fix to Rate Monotonic ordering
4. **Schedulability Check**: Liu & Layland utilization bound
5. **UPPAAL Generation**: Create timed automaton XML
6. **Property Synthesis**: LLM suggests temporal properties
7. **Formal Verification**: Run verifyta model checker
8. **Counterexample Analysis**: Parse failed traces
9. **Auto-Repair**: LLM repairs code based on errors
10. **Iteration**: Repeat until properties pass or max attempts reached

## 📊 Example Scenarios

### Scenario 1: Navigation System (3 Tasks)
- **T_Navigation**: 20ms period, 15ms deadline, priority 1
- **T_Sensor**: 50ms period, 40ms deadline, priority 2
- **T_Logger**: 100ms period, 90ms deadline, priority 3

**Outcome**: ✅ All properties satisfied, system schedulable (U = 62%)

### Scenario 2: Extended System (5 Tasks)
Added:
- **T_Backup**: 200ms period, 180ms deadline
- **T_Diagnostic**: 500ms period, 450ms deadline

**Outcome**: ✅ All properties satisfied, mutual exclusion enforced via `cpu_owner`

## 🐛 Troubleshooting

**"UPPAAL not found"**:
- Update `UPPAAL_PATH` in `config.py`
- Ensure `verifyta.exe` exists and is executable

**"LLM not available"**:
- Start Ollama: `ollama serve`
- Pull model: `ollama pull llama3.1:latest`
- System will still work without LLM (no code generation/repair)

**"Properties failed" repeatedly**:
- Check UPPAAL output for specific errors
- Review task parameters (deadline ≤ period)
- Ensure execution time < deadline
- Try adjusting priorities manually

**Dashboard shows no data**:
- Submit at least one verification job first
- Check browser console for fetch errors
- Verify `/dashboard` and `/metrics` endpoints return JSON

## 📈 Performance Notes

- **First verification**: ~2-5 seconds (UPPAAL startup)
- **Subsequent runs**: ~1-2 seconds (cached)
- **LLM repair**: +10-30 seconds per iteration
- **Dashboard refresh**: Every 7 seconds (configurable)

## 🤝 Contributing

This is a final year project. Core features complete:
- ✅ Multi-language code extraction
- ✅ UPPAAL model generation with scheduler
- ✅ LLM-based code generation and repair
- ✅ Priority validation and schedulability analysis
- ✅ Real-time dashboard and metrics
- ✅ Interactive task editor

## 📄 License

Academic project - LLM Final Year 2025

## 🙏 Acknowledgments

- **UPPAAL Team**: Timed automata model checker
- **Ollama**: Local LLM inference
- **Flask**: Web framework
- **Chart.js**: Dashboard visualizations

---

**Built with ❤️ for Real-Time Systems Verification**

For questions or issues, refer to the inline documentation in source files.
