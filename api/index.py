"""
Vercel serverless entrypoint.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가 (중요!)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 이제 src 모듈을 import 할 수 있음
from src.server import app

# Vercel은 'app' 변수를 찾습니다
__all__ = ["app"]