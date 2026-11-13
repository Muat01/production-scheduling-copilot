"""
MH Emerald & Gold: the personal design system of Muatasem Hadi.
One source of truth for colours and fonts across apps, figures and carousels.
Categorical chart colours are validated for colour-vision deficiency on SURFACE.
"""
# surfaces & text
BG = "#0B100E"          # page
BG_2 = "#0E1311"        # ground (sidebar)
SURFACE = "#131A17"     # card
SURFACE_2 = "#19221E"   # raised card / table head
LINE = "#24302A"
LINE_2 = "#2F3C36"
GRID = "#1F2925"
TEXT = "#EEF2EF"        # ink
TEXT_SOFT = "#B7C2BC"
MUTED = "#7E8C85"

# brand
EMERALD = "#22C98A"
GOLD = "#E6B94A"
STEEL = "#6FA8FF"
ROSE = "#D05A74"
LILAC = "#9479E6"
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

TONES = {"emerald": EMERALD, "gold": GOLD, "steel": STEEL, "rose": ROSE, "critical": CRITICAL, "muted": MUTED}
