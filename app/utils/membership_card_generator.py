from datetime import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth


# ============================================================
# YPADN MEMBERSHIP CARD GENERATOR
# Youth Political Awareness & Development Network
# ============================================================

CARD_DIR = "uploads/cards"

# Keep this compatible with Railway / local development.
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

ASSET_DIR = os.path.join(BASE_DIR, "assets", "membership")

os.makedirs(CARD_DIR, exist_ok=True)
os.makedirs(ASSET_DIR, exist_ok=True)


# ============================================================
# ORGANIZATION
# ============================================================

ORG_NAME = "YOUTH POLITICAL AWARENESS & DEVELOPMENT NETWORK"
ORG_SHORT = "YPADN"

MOTTO = "AWARENESS TODAY, LEADERSHIP TOMORROW."

CHAIRMAN_NAME = "Abdullahi Sani Idris"
CHAIRMAN_TITLE = "CHAIRMAN, YPADN"


# ============================================================
# COLORS
# ============================================================

NAVY = HexColor("#0B2347")
GREEN = HexColor("#087A3D")
DARK_GREEN = HexColor("#075B30")
WHITE = colors.white


# ============================================================
# CARD SIZE
#
# Original artwork:
# 1536 x 1024
#
# Ratio:
# 3 : 2
#
# We keep the exact same ratio.
# ============================================================

WIDTH = 750
HEIGHT = 500


# ============================================================
# ASSETS
# ============================================================

FRONT_BACKGROUND = os.path.join(
    ASSET_DIR,
    "card_front_background.png",
)

BACK_BACKGROUND = os.path.join(
    ASSET_DIR,
    "card_back_background.png",
)


# ============================================================
# FALLBACK ASSET LOCATIONS
#
# Your earlier project showed some assets directly inside
# /assets, so support those names too.
# ============================================================

FRONT_FALLBACKS = [
    os.path.join(BASE_DIR, "assets", "card-background.png"),
    os.path.join(BASE_DIR, "assets", "id_front_bg.png"),
]

BACK_FALLBACKS = [
    os.path.join(BASE_DIR, "assets", "id_back_bg.png"),
]


def resolve_asset(primary, fallbacks=None):
    """
    Find an asset using the primary path first,
    then fallback paths.
    """

    if os.path.exists(primary):
        return primary

    for path in fallbacks or []:
        if os.path.exists(path):
            return path

    return primary


# ============================================================
# HELPER: DRAW BACKGROUND
# ============================================================

def draw_background(c, image_path):
    """
    Draw membership-card background without stretching
    the visible artwork beyond the card dimensions.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Membership card background not found: {image_path}"
        )

    c.drawImage(
        ImageReader(image_path),
        0,
        0,
        width=WIDTH,
        height=HEIGHT,
        preserveAspectRatio=False,
        mask="auto",
    )


# ============================================================
# HELPER: FIT TEXT
# ============================================================

def draw_fitted_text(
    c,
    text,
    x,
    y,
    max_width,
    font="Helvetica-Bold",
    font_size=10,
    min_font_size=6,
    color=NAVY,
):
    """
    Draw text while automatically reducing its font size
    when the value is too long.
    """

    text = str(text or "—").strip()

    size = font_size

    while size > min_font_size:
        if stringWidth(
            text,
            font,
            size,
        ) <= max_width:
            break

        size -= 0.5

    c.setFont(font, size)
    c.setFillColor(color)

    c.drawString(
        x,
        y,
        text,
    )


# ============================================================
# HELPER: DRAW PHOTO
# ============================================================

def draw_member_photo(c, member):
    """
    Draw member passport photo.

    Coordinates are based on the 750 x 500 card.
    """

    passport = getattr(
        member,
        "passport",
        None,
    )

    if not passport:
        return

    if not os.path.exists(passport):
        print(
            f"⚠️ Passport photo not found: {passport}"
        )
        return

    # --------------------------------------------------------
    # PHOTO POSITION
    # --------------------------------------------------------
    #
    # The photo box in the artwork is approximately:
    #
    # X = 35
    # Y = 55
    # W = 165
    # H = 170
    #
    # --------------------------------------------------------

    x = 35
    y = 55

    photo_width = 165
    photo_height = 170

    try:

        # White frame
        c.setFillColor(WHITE)

        c.roundRect(
            x - 3,
            y - 3,
            photo_width + 6,
            photo_height + 6,
            10,
            fill=1,
            stroke=0,
        )

        # Green border
        c.setStrokeColor(GREEN)
        c.setLineWidth(2)

        c.roundRect(
            x,
            y,
            photo_width,
            photo_height,
            8,
            fill=0,
            stroke=1,
        )

        # ----------------------------------------------------
        # Draw passport image
        # ----------------------------------------------------

        c.drawImage(
            ImageReader(passport),
            x + 2,
            y + 2,
            width=photo_width - 4,
            height=photo_height - 4,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    except Exception as exc:

        print(
            f"⚠️ Could not draw passport photo: {exc}"
        )


# ============================================================
# HELPER: DRAW QR
# ============================================================

def draw_member_qr(
    c,
    qr_path,
):
    """
    Draw the generated QR code over the QR placeholder.
    """

    if not qr_path:
        return

    if not os.path.exists(qr_path):
        print(
            f"⚠️ QR code not found: {qr_path}"
        )
        return

    # --------------------------------------------------------
    # QR POSITION
    # --------------------------------------------------------

    x = 527
    y = 165

    size = 96

    try:

        # White backing
        c.setFillColor(WHITE)

        c.roundRect(
            x - 6,
            y - 6,
            size + 12,
            size + 12,
            8,
            fill=1,
            stroke=0,
        )

        c.drawImage(
            ImageReader(qr_path),
            x,
            y,
            width=size,
            height=size,
            preserveAspectRatio=False,
            mask="auto",
        )

    except Exception as exc:

        print(
            f"⚠️ Could not draw QR code: {exc}"
        )


# ============================================================
# HELPER: MEMBER DATE
# ============================================================

def get_joined_date(member):

    created_at = getattr(
        member,
        "created_at",
        None,
    )

    if created_at:

        return created_at.strftime(
            "%d %B %Y"
        )

    return datetime.now().strftime(
        "%d %B %Y"
    )


# ============================================================
# FRONT MEMBER INFORMATION
# ============================================================

def draw_member_information(
    c,
    member,
):
    """
    Draw only the dynamic member values.

    IMPORTANT:
    The labels are already part of the background artwork.

    The Y positions below were moved upward so that each
    value sits directly on its corresponding dotted line.
    """

    # ========================================================
    # VALUE X
    # ========================================================
    #
    # The value starts immediately after the labels.
    #
    # ========================================================

    value_x = 350

    # ========================================================
    # MEMBERSHIP NUMBER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "registration_no",
            "",
        ),
        value_x,
        282,
        175,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # FULL NAME
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "name",
            "",
        ),
        value_x,
        256,
        245,
        font="Helvetica-Bold",
        font_size=10,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # GENDER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "gender",
            "",
        ),
        value_x,
        231,
        100,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # AGE
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "age",
            "",
        ),
        value_x,
        206,
        80,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # PHONE NUMBER
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "phone",
            "",
        ),
        value_x,
        181,
        230,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # LGA
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "lga",
            "",
        ),
        value_x,
        157,
        165,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # WARD
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "ward",
            "",
        ),
        value_x,
        133,
        165,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # UNIT
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "unit",
            "",
        ),
        value_x,
        109,
        140,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # ========================================================
    # JOINED
    # ========================================================

    draw_fitted_text(
        c,
        get_joined_date(member),
        value_x,
        85,
        155,
        font="Helvetica-Bold",
        font_size=8,
        min_font_size=6,
        color=NAVY,
    )


# ============================================================
# FRONT SIDE
# ============================================================

def draw_front(
    c,
    member,
    qr_path,
):
    """
    Generate front side.
    """

    draw_background(
        c,
        FRONT_BACKGROUND,
    )

    draw_member_photo(
        c,
        member,
    )

    draw_member_information(
        c,
        member,
    )

    draw_member_qr(
        c,
        qr_path,
    )


# ============================================================
# BACK SIDE
# ============================================================

def draw_back(c):
    """
    Generate back side.

    The background already contains:
        - YPADN branding
        - mission
        - values
        - terms
        - motto
        - signatory line
    """

    draw_background(
        c,
        BACK_BACKGROUND,
    )

    # --------------------------------------------------------
    # Authorized signatory
    # --------------------------------------------------------

    c.setFillColor(NAVY)

    c.setFont(
        "Helvetica-Bold",
        8,
    )

    c.drawCentredString(
        575,
        74,
        CHAIRMAN_NAME,
    )

    c.setFont(
        "Helvetica",
        7,
    )

    c.drawCentredString(
        575,
        63,
        CHAIRMAN_TITLE,
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_membership_card(
    member,
    qr_path,
):
    """
    Generate a professional two-page YPADN
    membership card.

    PAGE 1:
        Front membership card

    PAGE 2:
        Back membership card

    Returns:
        PDF file path
    """

    registration_no = getattr(
        member,
        "registration_no",
        None,
    )

    if not registration_no:
        raise ValueError(
            "Member registration number is required."
        )

    # --------------------------------------------------------
    # Resolve assets
    # --------------------------------------------------------

    global FRONT_BACKGROUND
    global BACK_BACKGROUND

    FRONT_BACKGROUND = resolve_asset(
        FRONT_BACKGROUND,
        FRONT_FALLBACKS,
    )

    BACK_BACKGROUND = resolve_asset(
        BACK_BACKGROUND,
        BACK_FALLBACKS,
    )

    # --------------------------------------------------------
    # PDF path
    # --------------------------------------------------------

    pdf_path = os.path.join(
        CARD_DIR,
        f"{registration_no}-membership-card.pdf",
    )

    # --------------------------------------------------------
    # Verify backgrounds
    # --------------------------------------------------------

    if not os.path.exists(FRONT_BACKGROUND):

        raise FileNotFoundError(
            "Front membership background not found: "
            f"{FRONT_BACKGROUND}"
        )

    if not os.path.exists(BACK_BACKGROUND):

        raise FileNotFoundError(
            "Back membership background not found: "
            f"{BACK_BACKGROUND}"
        )

    # --------------------------------------------------------
    # Create PDF
    # --------------------------------------------------------

    c = canvas.Canvas(
        pdf_path,
        pagesize=(WIDTH, HEIGHT),
    )

    # ========================================================
    # PAGE 1 — FRONT
    # ========================================================

    draw_front(
        c,
        member,
        qr_path,
    )

    c.showPage()

    # ========================================================
    # PAGE 2 — BACK
    # ========================================================

    draw_back(c)

    c.showPage()

    # ========================================================
    # SAVE
    # ========================================================

    c.save()

    print(
        f"✅ Membership card generated: {pdf_path}"
    )

    return pdf_path