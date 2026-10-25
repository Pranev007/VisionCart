"""Illustrative Indian retail prices in INR, per detected sale unit.

All 80 COCO labels are accounted for, plus bread/biscuit for custom models.
These are editable demo amounts, not brand-specific prices or live quotations.
None means detected but not sold/billed (people, animals, infrastructure).
"""

# Strings avoid introducing floating-point rounding into money calculations.
# Keys must match the model's class labels. One detection is one sale unit.
ITEM_PRICES: dict[str, str | None] = {
    "person": None,
    "bicycle": "6000.00",
    "car": "650000.00",
    "motorcycle": "85000.00",
    "airplane": None,
    "bus": None,
    "train": None,
    "truck": None,
    "boat": None,
    "traffic light": None,
    "fire hydrant": None,
    "stop sign": None,
    "parking meter": None,
    "bench": "3500.00",
    "bird": None,
    "cat": None,
    "dog": None,
    "horse": None,
    "sheep": None,
    "cow": None,
    "elephant": None,
    "bear": None,
    "zebra": None,
    "giraffe": None,
    "backpack": "599.00",
    "umbrella": "250.00",
    "handbag": "799.00",
    "tie": "199.00",
    "suitcase": "2499.00",
    "frisbee": "199.00",
    "skis": "14999.00",
    "snowboard": "19999.00",
    "sports ball": "499.00",
    "kite": "30.00",
    "baseball bat": "1499.00",
    "baseball glove": "999.00",
    "skateboard": "2499.00",
    "surfboard": "14999.00",
    "tennis racket": "1499.00",
    "bottle": "20.00",
    "wine glass": "149.00",
    "cup": "40.00",
    "fork": "20.00",
    "knife": "50.00",
    "spoon": "15.00",
    "bowl": "60.00",
    "banana": "10.00",
    "apple": "30.00",
    "sandwich": "60.00",
    "orange": "25.00",
    "broccoli": "60.00",  # one small head, not one kilogram
    "carrot": "10.00",    # one carrot
    "hot dog": "80.00",
    "pizza": "199.00",    # one small pizza
    "donut": "50.00",
    "cake": "80.00",      # one slice/pastry
    "chair": "799.00",
    "couch": "14999.00",
    "potted plant": "199.00",
    "bed": "9999.00",
    "dining table": "5999.00",
    "toilet": "2999.00",
    "tv": "19999.00",
    "laptop": "39999.00",
    "mouse": "399.00",
    "remote": "299.00",
    "keyboard": "699.00",
    "cell phone": "9999.00",
    "microwave": "5999.00",
    "oven": "4999.00",
    "toaster": "1499.00",
    "sink": "1999.00",
    "refrigerator": "14999.00",
    "book": "150.00",
    "clock": "299.00",
    "vase": "199.00",
    "scissors": "50.00",
    "teddy bear": "299.00",
    "hair drier": "799.00",  # COCO uses this spelling
    "toothbrush": "30.00",
    # Extra classes recognized only if your custom weights were trained on them.
    "bread": "45.00",
    "biscuit": "20.00",
}

CURRENCY = "INR"
