import pytest
from invoice_service import InvoiceService, Invoice, LineItem

def test_compute_total_basic():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-001",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert isinstance(warnings, list)

def test_invalid_qty_raises():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-002",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=0)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_thailand_shipping_low_subtotal():
    """Test Thailand with subtotal < 500 → shipping 60"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-003",
        customer_id="C-002",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="B", category="electronics", unit_price=100.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 200  # 200 subtotal + 60 shipping + tax - no discount

def test_thailand_shipping_high_subtotal():
    """Test Thailand with subtotal >= 500 → shipping 0"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-004",
        customer_id="C-003",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="C", category="food", unit_price=100.0, qty=6)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 600  # 600 subtotal + 0 shipping + tax

def test_japan_shipping():
    """Test Japan shipping rules"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-005",
        customer_id="C-004",
        country="JP",
        membership="none",
        coupon=None,
        items=[LineItem(sku="D", category="book", unit_price=1000.0, qty=5)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 5000  # 5000 subtotal + 0 shipping (>= 4000) + tax

def test_usa_shipping_tiered():
    """Test USA tiered shipping (< 100: 15, < 300: 8, else 0)"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-006",
        customer_id="C-005",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="E", category="electronics", unit_price=50.0, qty=3)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 150  # 150 subtotal + 8 shipping + tax

def test_gold_membership_discount():
    """Test gold membership (3% discount)"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-007",
        customer_id="C-006",
        country="US",
        membership="gold",
        coupon=None,
        items=[LineItem(sku="F", category="book", unit_price=100.0, qty=10)]
    )
    total, warnings = service.compute_total(inv)
    # 1000 subtotal * 0.03 = 30 discount, shipping 0
    assert total < 1100  # after discount and tax

def test_platinum_membership_discount():
    """Test platinum membership (5% discount)"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-008",
        customer_id="C-007",
        country="TH",
        membership="platinum",
        coupon=None,
        items=[LineItem(sku="G", category="food", unit_price=100.0, qty=10)]
    )
    total, warnings = service.compute_total(inv)
    # 1000 subtotal * 0.05 = 50 discount
    assert total < 1100

def test_coupon_valid():
    """Test valid coupon code"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-009",
        customer_id="C-008",
        country="US",
        membership="none",
        coupon="WELCOME10",
        items=[LineItem(sku="H", category="electronics", unit_price=100.0, qty=5)]
    )
    total, warnings = service.compute_total(inv)
    # 500 subtotal * 0.10 = 50 coupon discount
    assert total < 550  # after discount and tax

def test_coupon_invalid():
    """Test invalid coupon code generates warning"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-010",
        customer_id="C-009",
        country="US",
        membership="none",
        coupon="INVALID99",
        items=[LineItem(sku="I", category="book", unit_price=100.0, qty=3)]
    )
    total, warnings = service.compute_total(inv)
    assert "Unknown coupon" in warnings

def test_fragile_items_fee():
    """Test fragile items add $5 per unit"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-011",
        customer_id="C-010",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="GLASS", category="electronics", unit_price=100.0, qty=2, fragile=True)]
    )
    total, warnings = service.compute_total(inv)
    # 200 subtotal + 10 fragile_fee (5*2) + shipping + tax
    assert total > 210

def test_high_subtotal_membership_upgrade_warning():
    """Test membership upgrade warning for high subtotal"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-012",
        customer_id="C-011",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="BULK", category="book", unit_price=100.0, qty=150)]
    )
    total, warnings = service.compute_total(inv)
    # 15000 subtotal > 10000 and membership is none → warning
    assert "Consider membership upgrade" in warnings

def test_high_subtotal_platinum_no_warning():
    """Test no warning for platinum member with high subtotal"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-013",
        customer_id="C-012",
        country="US",
        membership="platinum",
        coupon=None,
        items=[LineItem(sku="BULK2", category="electronics", unit_price=100.0, qty=150)]
    )
    total, warnings = service.compute_total(inv)
    assert "Consider membership upgrade" not in warnings

def test_missing_invoice_id():
    """Test validation for missing invoice_id"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="",
        customer_id="C-013",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="TEST", category="book", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_missing_customer_id():
    """Test validation for missing customer_id"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-014",
        customer_id="",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="TEST", category="book", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_missing_items():
    """Test validation for missing items"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-015",
        customer_id="C-014",
        country="US",
        membership="none",
        coupon=None,
        items=[]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_invalid_item_price():
    """Test validation for negative item price"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-016",
        customer_id="C-015",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="BADPRICE", category="book", unit_price=-10.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_invalid_item_category():
    """Test validation for invalid category"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-017",
        customer_id="C-016",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="BAD", category="invalid_cat", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_vip_coupon():
    """Test VIP20 coupon code"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-018",
        customer_id="C-017",
        country="US",
        membership="none",
        coupon="VIP20",
        items=[LineItem(sku="ITEM", category="book", unit_price=100.0, qty=5)]
    )
    total, warnings = service.compute_total(inv)
    # 500 * 0.20 = 100 discount
    assert total < 450

def test_student_coupon():
    """Test STUDENT5 coupon code"""
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-019",
        customer_id="C-018",
        country="JP",
        membership="none",
        coupon="STUDENT5",
        items=[LineItem(sku="BOOK", category="book", unit_price=100.0, qty=4)]
    )
    total, warnings = service.compute_total(inv)
    # 400 subtotal * 0.05 = 20 discount, JP shipping 600 + tax
    assert total > 1000  # 400 + 600 + tax - 20
