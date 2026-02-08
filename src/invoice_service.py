class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    # ---------- Validation ----------
    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            return ["Invoice is missing"]

        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")

        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")

        return problems

    # ---------- Calculation helpers ----------
    def _calc_subtotal(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0
        for it in items:
            subtotal += it.unit_price * it.qty
            if it.fragile:
                fragile_fee += 5.0 * it.qty
        return subtotal, fragile_fee

    def _calc_shipping(self, country: str, subtotal: float) -> float:
        rules = {
            "TH": [(500, 60)],
            "JP": [(4000, 600)],
            "US": [(100, 15), (300, 8)]
        }

        for limit, fee in rules.get(country, [(200, 25)]):
            if subtotal < limit:
                return fee
        return 0.0

    def _calc_membership_discount(self, membership: str, subtotal: float) -> float:
        rates = {
            "gold": 0.03,
            "platinum": 0.05
        }
        if membership in rates:
            return subtotal * rates[membership]
        if subtotal > 3000:
            return 20
        return 0.0

    def _calc_coupon_discount(self, coupon: Optional[str], subtotal: float, warnings: List[str]) -> float:
        if coupon:
            code = coupon.strip()
            if code in self._coupon_rate:
                return subtotal * self._coupon_rate[code]
            warnings.append("Unknown coupon")
        return 0.0

    def _calc_tax(self, country: str, taxable: float) -> float:
        tax_rate = {
            "TH": 0.07,
            "JP": 0.10,
            "US": 0.08
        }.get(country, 0.05)
        return taxable * tax_rate

    # ---------- Main ----------
    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._calc_subtotal(inv.items)
        shipping = self._calc_shipping(inv.country, subtotal)

        discount = self._calc_membership_discount(inv.membership, subtotal)
        discount += self._calc_coupon_discount(inv.coupon, subtotal, warnings)

        tax = self._calc_tax(inv.country, subtotal - discount)

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(total, 0)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings