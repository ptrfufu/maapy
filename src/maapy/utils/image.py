"""截图数据处理——BGR → numpy / PIL。"""

from __future__ import annotations

from typing import Any


def to_numpy(bgr_data: bytes, width: int, height: int) -> Any:
    """将原始 BGR bytes 转为 numpy 数组。需要已安装 numpy。"""
    try:
        import numpy as np
    except ImportError:
        raise ImportError("需要 numpy: pip install numpy")
    arr = np.frombuffer(bgr_data, dtype=np.uint8)
    return arr.reshape((height, width, 3))


def to_pil(bgr_data: bytes, width: int, height: int) -> Any:
    """将原始 BGR bytes 转为 PIL Image。需要已安装 numpy + Pillow。"""
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("需要 Pillow: pip install Pillow")
    arr = to_numpy(bgr_data, width, height)
    # BGR → RGB
    rgb = arr[:, :, ::-1]
    return Image.fromarray(rgb)
