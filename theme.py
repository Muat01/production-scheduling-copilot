"""
MH Emerald & Gold: the personal design system of Muatasem Hadi.
One source of truth for colours and fonts across apps, figures and carousels.
Categorical chart colours are validated for colour-vision deficiency on SURFACE.
"""
# surfaces & text
BG = "#0E1311"          # ground
SURFACE = "#171E1B"
SURFACE_2 = "#1F2824"
LINE = "#2A3530"
GRID = "#232D29"
TEXT = "#EEF2EF"        # ink
TEXT_SOFT = "#B7C2BC"
MUTED = "#7E8C85"

# brand
EMERALD = "#22C98A"
GOLD = "#E6B94A"
STEEL = "#6FA8FF"
ON_EMERALD = "#0E1311"

# charts: fixed categorical order (emerald, steel, gold, rose, lilac)
CHART = ["#16A673", "#4F86E0", "#B88A26", "#D05A74", "#9479E6"]
C_EMERALD, C_STEEL, C_GOLD, C_ROSE, C_LILAC = CHART

# status (reserved, always with an icon or label)
GOOD = EMERALD
WARN = GOLD
CRITICAL = "#F0616D"

FONT = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'JetBrains Mono', ui-monospace, Consolas, monospace"

TONES = {"emerald": EMERALD, "gold": GOLD, "steel": STEEL, "critical": CRITICAL, "muted": MUTED}
