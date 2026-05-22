# NeuroSpeller
SSVEP-based BCI speller 

### Requirements
- Python 3.11 or higher 
- [uv] https://docs.astral.sh/uv/

### Installation 
1. Clone the repository 
2. Create **uv** venv and sync 
```bash
uv venv
source .venv/Scripts/activate # windows
source .venv/bin/activate # linux 
uv sync
```

## 🧠 Architecture
- **Experiment App:** High-precision visual stimulation and real-time data streaming.
```bash
cd experiment
uv run main.py
```
- **Data & ML:** EEG data **offline** analysis with preprocessing and classification.