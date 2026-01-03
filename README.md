# NeuroSpeller
SSVEP-based BCI speller 

## Quick Start

### Requirements
- Python 3.11 or higher 
- [Poetry](https://python-poetry.org/)

### Installation 
1. Clone the repository 
2. Install the dependencies using Poetry 
```bash
poetry install 
```

For working with **Experiment App** use **app** group dependencies as well:
```bash
poetry install --with app
cd experiment
```

For working with **Data & ML** use **data** group dependencies:
```bash
poetry install --with data
cd data
```

## 🧠 Architecture
- **Experiment App:** High-precision visual stimulation and real-time data streaming.
```bash
poetry run python experiment/main.py
```
- **Data & ML:** EEG data **offline** analysis with preprocessing and classification.