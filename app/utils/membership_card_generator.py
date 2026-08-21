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
ASSET_DIR = "assets/membership"

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
# The supplied background images are 1536 x 1024,
# which has a 3:2 ratio.
#
# We keep the same ratio to avoid stretching the artwork.
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
# HELPER: DRAW BACKGROUND
# ============================================================

def draw_background(c, image_path):
    """
    Draw the membership-card background.
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
    Draw text and automatically reduce font size
    if it is too long.
    """

    text = str(text or "-").strip()

    size = font_size

    while size > min_font_size:

        if stringWidth(
            text,
            font,
            size,
        ) <= max_width:

            break

        size -= 0.5

    c.setFont(
        font,
        size,
    )

    c.setFillColor(color)

    c.drawString(
        x,
        y,
        text,
    )


# ============================================================
# HELPER: DRAW PHOTO
# ============================================================

def draw_member_photo(
    c,
    member,
):
    """
    Place the member passport photograph
    over the photo placeholder in the background.
    """

    passport = getattr(
        member,
        "passport",
        None,
    )

    if not passport:
        return

    if not os.path.exists(passport):
        return

    # --------------------------------------------------------
    # Photo position
    #
    # Based on the generated front background.
    # --------------------------------------------------------

    x = 33
    y = 58

    width = 166
    height = 167

    try:

        # White frame
        c.setFillColor(WHITE)

        c.roundRect(
            x - 2,
            y - 2,
            width + 4,
            height + 4,
            8,
            fill=1,
            stroke=0,
        )

        # Green border
        c.setStrokeColor(GREEN)
        c.setLineWidth(2)

        c.roundRect(
            x,
            y,
            width,
            height,
            7,
            fill=0,
            stroke=1,
        )

        # Passport
        c.drawImage(
            ImageReader(passport),
            x + 2,
            y + 2,
            width=width - 4,
            height=height - 4,
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
    Place the generated QR code over the QR placeholder.
    """

    if not qr_path:
        return

    if not os.path.exists(qr_path):
        return

    # QR position based on the generated background.
    x = 526
    y = 167

    size = 94

    try:

        # White backing to completely cover
        # the sample QR from the artwork.
        c.setFillColor(WHITE)

        c.roundRect(
            x - 5,
            y - 5,
            size + 10,
            size + 10,
            7,
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
    Put dynamic member information on top
    of the supplied front-card background.

    The background already contains the labels.
    We only draw the actual values.
    """

    # --------------------------------------------------------
    # Value X position
    #
    # This aligns with the dotted lines in the
    # supplied card design.
    # --------------------------------------------------------

    value_x = 350

    # --------------------------------------------------------
    # Registration number
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "registration_no",
            "",
        ),
        value_x,
        238,
        165,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Full name
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "name",
            "",
        ),
        value_x,
        213,
        260,
        font="Helvetica-Bold",
        font_size=10,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Gender
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "gender",
            "",
        ),
        value_x,
        191,
        100,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Age
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "age",
            "",
        ),
        value_x,
        168,
        80,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Phone
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "phone",
            "",
        ),
        value_x,
        146,
        250,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # LGA
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "lga",
            "",
        ),
        value_x,
        123,
        170,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Ward
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "ward",
            "",
        ),
        value_x,
        100,
        170,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Unit
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        getattr(
            member,
            "unit",
            "",
        ),
        value_x,
        78,
        130,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # Joined date
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        get_joined_date(member),
        value_x,
        57,
        150,
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
    Generate front side using the supplied
    card_front_background.png.
    """

    # Background first
    draw_background(
        c,
        FRONT_BACKGROUND,
    )

    # Dynamic passport
    draw_member_photo(
        c,
        member,
    )

    # Dynamic member information
    draw_member_information(
        c,
        member,
    )

    # Dynamic QR
    draw_member_qr(
        c,
        qr_path,
    )


# ============================================================
# BACK SIDE
# ============================================================

def draw_back(c):
    """
    Generate the back side using
    card_back_background.png.

    The background already contains:
        - YPADN branding
        - mission
        - values
        - terms
        - authorized signatory line
        - motto
    """

    draw_background(
        c,
        BACK_BACKGROUND,
    )

    # --------------------------------------------------------
    # Authorized signatory
    #
    # The background contains the line and
    # "AUTHORISED SIGNATORY".
    #
    # We only add the actual name/title.
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
    Generate a professional two-sided YPADN
    membership card.

    Page 1:
        Front

    Page 2:
        Back

    Returns:
        Generated PDF path.
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
    # PDF path
    # --------------------------------------------------------

    pdf_path = os.path.join(
        CARD_DIR,
        f"{registration_no}-membership-card.pdf",
    )

    # --------------------------------------------------------
    # Verify backgrounds BEFORE creating PDF
    # --------------------------------------------------------

    if not os.path.exists(FRONT_BACKGROUND):

        raise FileNotFoundError(
            f"Front membership background not found: "
            f"{FRONT_BACKGROUND}"
        )

    if not os.path.exists(BACK_BACKGROUND):

        raise FileNotFoundError(
            f"Back membership background not found: "
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

    return pdf_path