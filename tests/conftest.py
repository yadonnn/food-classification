import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "image_pipeline"))
sys.path.insert(0, str(ROOT / "model_training"))