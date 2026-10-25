"""Visual components for the VisionCart dashboard (no billing logic)."""

from html import escape
from pathlib import Path

import streamlit as st

from prices import CURRENCY


ICONS = {
    "camera": '<rect x="3" y="5" width="13" height="14" rx="3"/><path d="m16 9 5-3v12l-5-3z"/>',
    "cart": '<path d="M3 3h2l3 12h11l2-9H6"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
    "scan": '<path d="M8 3H4a1 1 0 0 0-1 1v4m13-5h4a1 1 0 0 1 1 1v4M3 16v4a1 1 0 0 0 1 1h4m8 0h4a1 1 0 0 0 1-1v-4M7 12h10"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
}


def icon(name, size=24):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )


def load_styles(root: Path):
    st.markdown(f"<style>{(root / 'styles.css').read_text()}</style>", unsafe_allow_html=True)


def panel_header(title, subtitle, kind, status=None, active=False):
    badge = ""
    if status:
        badge = f'<span class="status {"active" if active else ""}"><i></i>{escape(status)}</span>'
    st.markdown(
        f'<div class="panel-heading"><div class="panel-icon">{icon(kind)}</div>'
        f'<div class="panel-title"><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>{badge}</div>',
        unsafe_allow_html=True,
    )


def camera_placeholder():
    st.markdown(
        f'<div class="camera-idle"><span class="viewport-label">CAM 01 <i></i> STANDBY</span>'
        '<div class="scanner-corners"></div><div class="scan-line"></div>'
        f'<div class="idle-content"><div class="idle-icon">{icon("camera", 32)}</div>'
        '<h3>Ready when you are.</h3><p>Start your camera and place your items<br>inside the frame to begin checkout.</p>'
        '<span class="camera-hint">EXTERNAL WEBCAM · LIVE DETECTION</span></div>'
        f'<span class="viewport-cross">{icon("scan", 22)}</span></div>',
        unsafe_allow_html=True,
    )


def cart_items(lines, on_remove):
    emojis = {"bottle": "🧴", "cup": "☕", "apple": "🍎", "banana": "🍌", "orange": "🍊",
              "bread": "🍞", "biscuit": "🍪", "cake": "🍰", "book": "📘", "scissors": "✂️"}
    st.markdown(
        '<div class="cart-brand"><div>Vision<span>Cart</span></div><p>AI-powered smart checkout</p></div>',
        unsafe_allow_html=True,
    )
    total_units = sum(line.quantity for line in lines)
    st.markdown(
        f'<div class="cart-scroll-hint">{total_units} items · {len(lines)} types'
        '<span>Scroll to see all items ↓</span></div>',
        unsafe_allow_html=True,
    )
    # Native fixed-height containers expose scrolling instead of clipping rows.
    # Keep totals/Checkout outside this container so they remain accessible.
    with st.container(height=320, border=False, key="cart_rows"):
        st.markdown('<div class="cart-labels"><span>Item</span><span>Amount</span>'
                    '<span>Qty</span><span></span></div>', unsafe_allow_html=True)
        for line in lines:
            product, amount_col, quantity_col, delete_col = st.columns(
                [4, 1.8, .8, .9], gap="small", vertical_alignment="center",
            )
            price = "Not set" if line.unit_price is None else f"₹{line.unit_price:,.2f}"
            amount = "—" if line.line_total is None else f"₹{line.line_total:,.2f}"
            with product:
                st.markdown(
                    f'<div class="product"><span class="product-thumb">{emojis.get(line.name, "📦")}</span>'
                    f'<span class="product-name">{escape(line.name.title())}<small>{price} / item</small></span></div>',
                    unsafe_allow_html=True,
                )
            with amount_col:
                st.markdown(f'<div class="row-price">{amount}</div>', unsafe_allow_html=True)
            with quantity_col:
                st.markdown(f'<div class="quantity">{line.quantity}</div>', unsafe_allow_html=True)
            with delete_col:
                st.button(f"Remove {line.name.title()}", icon=":material/delete:",
                          key=f"remove_{line.name}", help=f"Remove one {line.name} from the cart",
                          on_click=on_remove, args=(line.name,))
        if not lines:
            st.markdown(
                f'<div class="empty-cart"><div>{icon("cart", 32)}</div><h3>Your cart is waiting</h3>'
                '<p>Scan an item to add it.<br>Items stay until you delete or checkout.</p></div>',
                unsafe_allow_html=True,
            )


def cart_summary(lines):
    count = sum(line.quantity for line in lines)
    subtotal = sum((line.line_total for line in lines if line.line_total is not None), 0)
    unpriced = any(line.unit_price is None for line in lines)
    value = "Price needed" if unpriced else f"₹{subtotal:,.2f}"
    st.markdown(
        f'<div class="subtotal"><span>Subtotal <small>({count} items)</small></span><strong>{value}</strong></div>',
        unsafe_allow_html=True,
    )


def workspace_header(page, running):
    titles = {"Home": ("Checkout workspace", "A little vision. A smoother checkout."),
              "Analytics": ("Checkout overview", "A clear view of your completed checkouts."),
              "History": ("Receipt history", "Every checkout, neatly in one place."),
              "Settings": ("Workspace settings", "Set up your camera and detection preferences.")}
    title, subtitle = titles[page]
    st.markdown(
        '<div class="workspace-heading"><div><div class="eyebrow">VISIONCART / SMART CHECKOUT</div>'
        f'<h1>{title}</h1><p>{subtitle}</p></div><div class="device-status">'
        f'<i class="{"online" if running else ""}"></i>{"Camera connected" if running else "Camera standby"}'
        '</div></div>', unsafe_allow_html=True,
    )
