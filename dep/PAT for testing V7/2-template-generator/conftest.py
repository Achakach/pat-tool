import sys
from pathlib import Path

# Add tool root to sys.path so tests can `from generate import main`
sys.path.insert(0, str(Path(__file__).parent))
