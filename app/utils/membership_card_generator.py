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


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)


# ============================================================
# STORAGE DIRECTORIES
# ============================================================

CARD_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "cards",
)

ASSET_DIR = os.path.join(
    BASE_DIR,
    "assets",
    "membership",
)

os.makedirs(CARD_DIR, exist_ok=True)
os.makedirs(ASSET_DIR, exist_ok=True)


# ============================================================
# ORGANIZATION
# ============================================================

ORG_NAME = (
    "YOUTH POLITICAL AWARENESS & DEVELOPMENT NETWORK"
)

ORG_SHORT = "YPADN"

MOTTO = (
    "AWARENESS TODAY, LEADERSHIP TOMORROW."
)

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
# Artwork ratio:
# 1536 x 1024
#
# PDF:
# 750 x 500
#
# Same 3:2 ratio.
# ============================================================

WIDTH = 750
HEIGHT = 500


# ============================================================
# CARD BACKGROUNDS
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
# FALLBACK ASSETS
# ============================================================

FRONT_FALLBACKS = [
    os.path.join(
        BASE_DIR,
        "assets",
        "card-background.png",
    ),
    os.path.join(
        BASE_DIR,
        "assets",
        "id_front_bg.png",
    ),
]

BACK_FALLBACKS = [
    os.path.join(
        BASE_DIR,
        "assets",
        "id_back_bg.png",
    ),
]


# ============================================================
# PATH HELPER
# ============================================================

def resolve_file_path(path):
    """
    Convert a relative project path into an absolute path.
    """

    if not path:
        return None

    path = str(path).strip()

    if not path:
        return None

    if os.path.isabs(path):
        return path

    return os.path.abspath(
        os.path.join(
            BASE_DIR,
            path,
        )
    )


# ============================================================
# ASSET RESOLVER
# ============================================================

def resolve_asset(
    primary,
    fallbacks=None,
):
    """
    Resolve the primary asset first.
    If unavailable, use a fallback.
    """

    if primary and os.path.isfile(primary):
        return primary

    for path in fallbacks or []:
        if path and os.path.isfile(path):
            return path

    return primary


# ============================================================
# DRAW BACKGROUND
# ============================================================

def draw_background(
    c,
    image_path,
):
    """
    Draw the card background.
    """

    image_path = resolve_file_path(
        image_path
    )

    if not image_path or not os.path.isfile(
        image_path
    ):
        raise FileNotFoundError(
            "Membership card background not found: "
            f"{image_path}"
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
# FIT TEXT
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
    Draw text with automatic font-size reduction.
    """

    text = str(
        text if text is not None else "—"
    ).strip()

    if not text:
        text = "—"

    size = font_size

    while size > min_font_size:

        text_width = stringWidth(
            text,
            font,
            size,
        )

        if text_width <= max_width:
            break

        size -= 0.5

    c.setFont(
        font,
        size,
    )

    c.setFillColor(
        color
    )

    c.drawString(
        x,
        y,
        text,
    )


# ============================================================
# DRAW MEMBER PHOTO
# ============================================================

def draw_member_photo(
    c,
    member,
):
    """
    Draw the member passport photograph.

    Coordinates are calibrated for the NEW
    card_front_background.png.
    """

    passport = getattr(
        member,
        "passport",
        None,
    )

    passport = resolve_file_path(
        passport
    )

    if not passport:
        print(
            "⚠️ Member has no passport photo."
        )
        return

    if not os.path.isfile(passport):
        print(
            "⚠️ Passport photo not found: "
            f"{passport}"
        )
        return

    # ========================================================
    # NEW FRONT CARD PHOTO POSITION
    # ========================================================

    x = 40
    y = 58

    photo_width = 180
    photo_height = 205

    try:

        # ----------------------------------------------------
        # White backing
        # ----------------------------------------------------

        c.setFillColor(
            WHITE
        )

        c.roundRect(
            x - 3,
            y - 3,
            photo_width + 6,
            photo_height + 6,
            10,
            fill=1,
            stroke=0,
        )

        # ----------------------------------------------------
        # Green border
        # ----------------------------------------------------

        c.setStrokeColor(
            GREEN
        )

        c.setLineWidth(
            2
        )

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
        # Passport image
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
            "⚠️ Could not draw passport photo: "
            f"{exc}"
        )


# ============================================================
# DRAW QR CODE
# ============================================================

def draw_member_qr(
    c,
    qr_path,
):
    """
    Draw the real member QR code over the
    QR placeholder in the new artwork.
    """

    qr_path = resolve_file_path(
        qr_path
    )

    if not qr_path:
        print(
            "⚠️ No QR code path supplied."
        )
        return

    if not os.path.isfile(qr_path):
        print(
            "⚠️ QR code not found: "
            f"{qr_path}"
        )
        return

    # ========================================================
    # NEW FRONT CARD QR POSITION
    # ========================================================

    x = 610
    y = 205

    size = 92

    try:

        # ----------------------------------------------------
        # White backing
        # ----------------------------------------------------

        c.setFillColor(
            WHITE
        )

        c.roundRect(
            x - 5,
            y - 5,
            size + 10,
            size + 10,
            7,
            fill=1,
            stroke=0,
        )

        # ----------------------------------------------------
        # QR
        # ----------------------------------------------------

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
            "⚠️ Could not draw QR code: "
            f"{exc}"
        )


# ============================================================
# JOINED DATE
# ============================================================

def get_joined_date(
    member,
):
    created_at = getattr(
        member,
        "created_at",
        None,
    )

    if created_at:

        if isinstance(
            created_at,
            datetime,
        ):
            return created_at.strftime(
                "%d %B %Y"
            )

        # Handle date-like SQLAlchemy values
        if hasattr(
            created_at,
            "strftime",
        ):
            return created_at.strftime(
                "%d %B %Y"
            )

    return datetime.now().strftime(
        "%d %B %Y"
    )


# ============================================================
# MEMBER INFORMATION
# ============================================================

def draw_member_information(
    c,
    member,
):
    """
    Draw ONLY dynamic member values.

    The labels are already part of the
    card_front_background.png artwork.

    IMPORTANT:
    All values use the same value column.
    """

    # ========================================================
    # VALUE COLUMN
    # ========================================================
    #
    # The new artwork places the vertical separator
    # around this position.
    #
    # This keeps:
    #
    # Membership No.
    # Full Name
    # Gender
    # Age
    # Phone
    # LGA
    # Ward
    # Unit
    # Joined
    #
    # perfectly aligned vertically.
    # ========================================================

    value_x = 405


    # ========================================================
    # MEMBERSHIP NUMBER
    # ========================================================
    #
    # Deliberately moved slightly DOWN so that
    # YPADN-000006 sits directly on the first
    # dotted line.
    # ========================================================

    draw_fitted_text(
        c,
        getattr(
            member,
            "registration_no",
            "",
        ),
        value_x,
        270,
        185,
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
        244,
        250,
        font="Helvetica-Bold",
        font_size=9.5,
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
        217,
        105,
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
        190,
        70,
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
        164,
        235,
        font="Helvetica-Bold",
        font_size=8.5,
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
        137,
        170,
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
        111,
        170,
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
        84,
        145,
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
        get_joined_date(
            member
        ),
        value_x,
        58,
        165,
        font="Helvetica-Bold",
        font_size=8,
        min_font_size=6,
        color=NAVY,
    )


# ============================================================
# FRONT
# ============================================================

def draw_front(
    c,
    member,
    qr_path,
    front_background,
):
    """
    Generate the front side.
    """

    draw_background(
        c,
        front_background,
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
# BACK
# ============================================================

def draw_back(
    c,
    back_background,
):
    """
    Generate the back side.
    """

    draw_background(
        c,
        back_background,
    )

    # ========================================================
    # AUTHORIZED SIGNATORY
    # ========================================================

    c.setFillColor(
        NAVY
    )

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
    Generate a two-page YPADN membership card.

    Page 1:
        Front

    Page 2:
        Back

    Returns:
        Absolute PDF filesystem path.
    """

    # ========================================================
    # REGISTRATION NUMBER
    # ========================================================

    registration_no = getattr(
        member,
        "registration_no",
        None,
    )

    if not registration_no:
        raise ValueError(
            "Member registration number is required."
        )


    # ========================================================
    # RESOLVE BACKGROUNDS
    # ========================================================

    front_background = resolve_asset(
        FRONT_BACKGROUND,
        FRONT_FALLBACKS,
    )

    back_background = resolve_asset(
        BACK_BACKGROUND,
        BACK_FALLBACKS,
    )


    # ========================================================
    # VERIFY FRONT BACKGROUND
    # ========================================================

    if (
        not front_background
        or not os.path.isfile(front_background)
    ):
        raise FileNotFoundError(
            "Front membership background not found: "
            f"{front_background}"
        )


    # ========================================================
    # VERIFY BACK BACKGROUND
    # ========================================================

    if (
        not back_background
        or not os.path.isfile(back_background)
    ):
        raise FileNotFoundError(
            "Back membership background not found: "
            f"{back_background}"
        )


    # ========================================================
    # PDF PATH
    # ========================================================

    pdf_path = os.path.join(
        CARD_DIR,
        f"{registration_no}-membership-card.pdf",
    )


    # ========================================================
    # MAKE SURE CARD DIRECTORY EXISTS
    # ========================================================

    os.makedirs(
        CARD_DIR,
        exist_ok=True,
    )


    # ========================================================
    # LOGGING
    # ========================================================

    print(
        "📄 Generating membership card..."
    )

    print(
        f"   Member: {registration_no}"
    )

    print(
        f"   Output: {pdf_path}"
    )

    print(
        f"   Front: {front_background}"
    )

    print(
        f"   Back: {back_background}"
    )


    # ========================================================
    # CREATE PDF
    # ========================================================

    c = canvas.Canvas(
        pdf_path,
        pagesize=(
            WIDTH,
            HEIGHT,
        ),
    )


    # ========================================================
    # PAGE 1 — FRONT
    # ========================================================

    draw_front(
        c,
        member,
        qr_path,
        front_background,
    )

    c.showPage()


    # ========================================================
    # PAGE 2 — BACK
    # ========================================================

    draw_back(
        c,
        back_background,
    )

    c.showPage()


    # ========================================================
    # SAVE PDF
    # ========================================================

    c.save()


    # ========================================================
    # VERIFY PDF EXISTS
    # ========================================================

    if not os.path.isfile(
        pdf_path
    ):
        raise FileNotFoundError(
            "Membership card was not generated: "
            f"{pdf_path}"
        )


    # ========================================================
    # VERIFY PDF SIZE
    # ========================================================

    file_size = os.path.getsize(
        pdf_path
    )

    if file_size <= 0:
        raise RuntimeError(
            "Membership card PDF was generated "
            "but is empty."
        )


    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "✅ Membership card generated successfully."
    )

    print(
        f"   PDF: {pdf_path}"
    )

    print(
        f"   Size: {file_size:,} bytes"
    )

    return pdf_path