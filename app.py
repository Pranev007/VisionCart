"""Phase 4: run with `python -m streamlit run app.py`."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path

import streamlit as st

from billing import build_bill, grand_total, save_bill
from cart import PersistentCart
from live import LiveCheckout
from prices import CURRENCY, ITEM_PRICES
from ui import (camera_placeholder, cart_items, cart_summary, icon, load_styles,
                panel_header, workspace_header)


ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="VisionCart", page_icon="🛒", layout="wide",
                   initial_sidebar_state="expanded")
load_styles(ROOT)

# Resources belong to this browser session, not a global cached model/tracker.
for key, default in {
    "live": None, "lines": [], "frame": None, "receipt": None,
    "notice": None, "failure": None,
    "page": "Home",
    "config": {"camera": 1, "model": "yolov8n.pt", "confidence": 0.5,
               "classes": "all", "image_size": 480},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "cart" not in st.session_state:
    # Preserve a bill that was open before this cart-behavior update.
    st.session_state.cart = PersistentCart()
    for line in st.session_state.lines:
        st.session_state.cart.counts[line.name] = line.quantity
    if st.session_state.live is not None:
        st.session_state.live.close()
        st.session_state.live = None
        st.session_state.frame = None


def update_bill():
    st.session_state.lines = build_bill(st.session_state.cart.counts, ITEM_PRICES)


def remove_item(name):
    st.session_state.cart.remove_one(name)
    update_bill()


def stop_camera():
    """Freeze the last displayed frame and bill for review."""
    if st.session_state.live is not None:
        st.session_state.live.close()
        st.session_state.live = None


def checkout():
    """Export exactly the last displayed bill before clearing the session."""
    try:
        path, data = save_bill(st.session_state.lines, ROOT / "bills")
    except (OSError, ValueError) as error:
        st.session_state.failure = f"Checkout failed: {error}"
        return
    stop_camera()
    st.session_state.receipt = (path.name, data)
    st.session_state.cart.clear()
    st.session_state.lines = []
    st.session_state.frame = None
    st.session_state.failure = None
    st.session_state.notice = f"Checkout complete. Saved bills/{path.name}"


def start_camera():
    config = st.session_state.config
    try:
        classes = [name.strip() for name in config["classes"].split(",") if name.strip()]
        if not classes:
            raise ValueError("Enter at least one class, or all.")
        path = Path(config["model"].strip()).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        with st.spinner("Loading the model and opening your webcam…"):
            st.session_state.live = LiveCheckout(
                str(path), int(config["camera"]), classes, config["confidence"],
                image_size=config.get("image_size", 480),
            )
        st.session_state.cart.begin_scan()
        update_bill()
        st.session_state.frame = None
        st.session_state.notice = None
        st.session_state.failure = None
    except Exception as error:
        stop_camera()
        st.session_state.failure = f"Could not start detection: {error}"


def navigate(page):
    # Moving away from checkout releases the camera and freezes the current bill.
    if page != "Home":
        stop_camera()
    st.session_state.page = page


with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand"><span class="brand-mark">{icon("cart", 21)}</span>'
        'VisionCart</div>', unsafe_allow_html=True,
    )
    for name, symbol in [("Home", "home"), ("Analytics", "bar_chart"),
                         ("History", "history"), ("Settings", "settings")]:
        st.button(name, icon=f":material/{symbol}:", key=f"nav_{name.lower()}",
                  type="primary" if st.session_state.page == name else "secondary",
                  on_click=navigate, args=(name,), width="stretch")
    st.markdown(
        '<div class="sidebar-footer"><b><span class="tiny-dot"></span>Local workspace</b>'
        '<br>VisionCart · Smart checkout<br>Made for a smoother everyday.</div>',
        unsafe_allow_html=True,
    )

workspace_header(st.session_state.page, st.session_state.live is not None)

if st.session_state.failure:
    st.error(st.session_state.failure)
if st.session_state.notice:
    st.success(st.session_state.notice)
if st.session_state.receipt:
    filename, contents = st.session_state.receipt
    st.download_button("Download last bill (CSV)", contents, filename, "text/csv")


# One frame per fragment rerun keeps buttons responsive; no endless while loop.
@st.fragment(run_every=0.05 if st.session_state.live is not None else None)
def show_live_checkout():
    if st.session_state.live is not None:
        try:
            frame, detections = st.session_state.live.read()
            # Non-retail classes stay visible in the feed without entering the cart.
            st.session_state.cart.observe(
                (track_id, name) for track_id, name in detections
                if name not in ITEM_PRICES or ITEM_PRICES[name] is not None
            )
            update_bill()
            st.session_state.frame = frame
        except Exception as error:
            stop_camera()
            st.session_state.frame = None
            st.session_state.failure = f"Detection stopped: {error}"
            st.rerun()

    video_col, bill_col = st.columns([1.9, 1], gap="medium")
    with video_col, st.container(border=True, key="camera_panel"):
        running = st.session_state.live is not None
        panel_header("Live Camera Feed", "Real-time object detection and recognition", "camera",
                     "Active" if running else "Paused" if st.session_state.frame is not None else "Standby",
                     active=running)
        if st.session_state.frame is None:
            camera_placeholder()
        else:
            st.image(st.session_state.frame, channels="BGR", width="stretch")
        index = st.session_state.config["camera"]
        st.markdown(
            f'<div class="camera-note"><span>CAMERA {index:02d} <b> / External feed</b></span>'
            f'<span>{"● LIVE" if running else "● PAUSED" if st.session_state.frame is not None else "○ READY TO CONNECT"}</span></div>',
            unsafe_allow_html=True,
        )
        start_col, stop_col = st.columns(2)
        with start_col:
            if st.button("Start camera", icon=":material/videocam:", disabled=running,
                         type="primary", width="stretch"):
                start_camera()
                st.rerun()
        with stop_col:
            if st.button("Stop camera", icon=":material/pause:", disabled=not running,
                         width="stretch"):
                stop_camera()
                st.rerun()
        selected_classes = st.session_state.config["classes"]
        if selected_classes.strip().lower() == "all":
            st.caption("Detecting all classes supported by the loaded model.")
        else:
            st.caption(f"Detection filter: {selected_classes}. Other classes are hidden.")
            if st.button("Detect all classes", key="detect_all", width="stretch"):
                stop_camera()
                st.session_state.config = {**st.session_state.config, "classes": "all"}
                start_camera()
                st.rerun()
        if running and not st.session_state.lines:
            st.caption("No billable items detected. Check the filter above, lighting, and object size. Try confidence 0.30 in Settings.")
    with bill_col, st.container(border=True, key="cart_panel"):
        lines = st.session_state.lines
        panel_header("Shopping Cart", "Your items, automatically added", "cart")
        cart_items(lines, on_remove=remove_item)
        cart_summary(lines)
        missing = [line.name for line in lines if line.unit_price is None]
        if missing:
            st.warning("Set prices in prices.py before checkout: " + ", ".join(missing))
            st.metric("Total", "Price needed")
        else:
            st.metric("Total", f"{CURRENCY} {grand_total(lines):.2f}")
        # Callback exports the displayed snapshot before another frame is read.
        if st.button("Checkout", icon=":material/account_balance_wallet:",
                     type="primary", key="checkout_action", width="stretch",
                     on_click=checkout):
            st.rerun()
        st.markdown(
            f'<div class="cart-footer">{icon("check", 12)} Scanned items stay in your cart.'
            '<br>Delete to remove one unit · Checkout to save your receipt</div>',
            unsafe_allow_html=True,
        )


def read_receipts():
    """Read only receipts with our expected CSV structure; skip invalid files."""
    receipts = []
    for path in sorted((ROOT / "bills").glob("bill_*.csv"), reverse=True):
        try:
            data = path.read_bytes()
            rows = list(csv.DictReader(StringIO(data.decode("utf-8"))))
            if not rows or rows[-1]["Item Name"] != "GRAND TOTAL":
                continue
            total = Decimal(rows[-1]["Line Total"])
            if not total.is_finite():
                continue
            receipts.append({"file": path.name, "data": data, "rows": rows,
                             "total": total, "issued": rows[-1]["Issued At"]})
        except (OSError, UnicodeError, KeyError, InvalidOperation, csv.Error):
            continue
    return receipts


if st.session_state.page == "Home":
    show_live_checkout()
elif st.session_state.page == "Settings":
    config = st.session_state.config
    with st.form("camera_settings"):
        st.subheader("Camera & detection")
        left, right = st.columns(2)
        with left:
            camera_index = st.number_input("Camera index", min_value=0,
                                           value=config["camera"], step=1,
                                           help="External webcams are often index 1. Try 0 or 2 if needed.")
            model_path = st.text_input("Model weights", config["model"])
        with right:
            confidence = st.slider("Confidence", .10, .95, config["confidence"], .05)
            class_text = st.text_input("Classes (comma-separated, or all)", config["classes"])
            st.caption("Use all to include scissors and every other supported class. A list limits detection to only those labels.")
            sizes = [320, 480, 640]
            image_size = st.selectbox(
                "Detection image size", sizes,
                index=sizes.index(config.get("image_size", 480)),
                help="480 is the faster default. Use 640 for small objects or 320 for more speed.",
            )
        if st.form_submit_button("Save settings", type="primary"):
            if not model_path.strip() or not any(name.strip() for name in class_text.split(",")):
                st.error("Enter model weights and at least one class, or all.")
            else:
                st.session_state.config = {"camera": int(camera_index), "model": model_path,
                                           "confidence": confidence, "classes": class_text,
                                           "image_size": image_size}
                st.success("Settings saved. Return to Home to start your camera.")
    with st.expander("Item prices · INR", expanded=True):
        st.table([{"Item": name.title(), "Unit Price (INR)": "Not billed" if price is None else price}
                  for name, price in ITEM_PRICES.items()])
        st.caption("Illustrative Indian prices per item. People, animals, and non-retail infrastructure are not billed. Edit prices.py to change prices or add custom model labels.")
elif st.session_state.page == "History":
    receipts = read_receipts()
    if not receipts:
        st.info("Your saved receipts will appear here after your first checkout.")
    for receipt in receipts:
        with st.expander(f"{receipt['issued']} · {CURRENCY} {receipt['total']:.2f}"):
            st.table([{key: row[key] for key in ("Item Name", "Quantity", "Unit Price", "Line Total")}
                      for row in receipt["rows"][:-1]])
            st.download_button("Download receipt", receipt["data"], receipt["file"],
                               "text/csv", key=receipt["file"])
else:
    receipts = read_receipts()
    quantities = {}
    for receipt in receipts:
        for row in receipt["rows"][:-1]:
            try:
                quantities[row["Item Name"]] = quantities.get(row["Item Name"], 0) + int(row["Quantity"])
            except (ValueError, KeyError):
                continue
    first, second, third = st.columns(3)
    first.metric("Completed checkouts", len(receipts))
    second.metric("Total billed", f"{CURRENCY} {sum((r['total'] for r in receipts), Decimal('0.00')):,.2f}")
    third.metric("Items checked out", sum(quantities.values()))
    if quantities:
        st.subheader("Items across completed checkouts")
        st.bar_chart(quantities, color="#579fff")
    else:
        st.info("Complete a checkout to see your item activity here.")
