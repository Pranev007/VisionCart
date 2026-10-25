# VisionCart

Real-time automated checkout using **YOLOv8n, OpenCV, and Streamlit**.

## Features

- Live webcam detection with bounding boxes and all 80 pretrained COCO classes.
- Persistent cart: items stay after leaving the camera; delete removes one unit.
- Quantities, editable sample Indian prices, and automatic totals.
- CSV receipts, downloads, receipt history, and basic analytics.
- Custom detection weights and camera selection through Settings.

## Run locally

Use Python 3.11 or newer. In Windows PowerShell, from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.
On macOS/Linux, create the environment with `python3` and use `.venv/bin/python`
for the remaining commands. A GPU is optional. The first run downloads
`yolov8n.pt` if needed. Connect the webcam to the computer running Streamlit.

## Use

1. In **Settings**, select the camera index: usually `0` for the built-in camera
   or `1` for an external USB webcam. Save and return to **Home**.
2. Click **Start camera** and show items clearly. Each new tracking ID adds one unit.
3. Scroll inside the cart to review all items; use trash buttons to remove units.
4. Click **Checkout** to save a receipt in `bills/`, stop the camera, and clear the cart.

Edit `ITEM_PRICES` in `prices.py` to change the sample INR prices per item.
Entries set to `None` are detected but not billed. For custom classes, select
trained `.pt` weights in Settings and add prices matching their labels.

## Limitations

- The model recognizes categories, not brands, sizes, or product SKUs.
- Bread, biscuits, pens, and pencils require custom-trained weights.
- Scan each item once: losing tracking or restarting the camera can add duplicates.
- The cart lasts for the current browser session; CSV receipts persist on disk.
- Fast enrollment can admit false positives. Review the bill before checkout.

## Tests and webcam check

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe webcam_test.py --camera 1
.\.venv\Scripts\python.exe detect.py --camera 1 --classes all
```

Close the webcam test before running another camera script. Virtual environments,
model weights, and generated bills are excluded from Git.
