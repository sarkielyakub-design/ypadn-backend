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

# This file is:
#
# app/utils/membership_card_generator.py
#
# Therefore:
#
# ../../
#
# points to the project root.
#
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


os.makedirs(
    CARD_DIR,
    exist_ok=True,
)

os.makedirs(
    ASSET_DIR,
    exist_ok=True,
)


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
# Original artwork:
# 1536 x 1024
#
# Ratio:
# 3 : 2
#
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

    Examples:

        uploads/photo.jpg
        assets/qr/qr.png

    become:

        /app/uploads/photo.jpg
        /app/assets/qr/qr.png
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
    Find an asset using the primary path first,
    then fallback paths.
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
    Draw membership-card background.
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
    Draw text while automatically reducing font size
    when the text is too long.
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
    Draw member passport photograph.
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

    # --------------------------------------------------------
    # PHOTO POSITION
    # --------------------------------------------------------

    x = 35

    y = 55

    photo_width = 165

    photo_height = 170

    try:

        # White frame
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

        # Green border
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

        # Passport image
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
    Draw generated QR code over the QR placeholder.
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

    # --------------------------------------------------------
    # QR POSITION
    # --------------------------------------------------------

    x = 527

    y = 165

    size = 96

    try:

        # White backing
        c.setFillColor(
            WHITE
        )

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
    Draw dynamic member values.

    The labels are already contained in
    card_front_background.png.
    """

    # --------------------------------------------------------
    # VALUE X POSITION
    # --------------------------------------------------------

    value_x = 350

    # --------------------------------------------------------
    # MEMBERSHIP NUMBER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # FULL NAME
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GENDER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

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
        157,
        165,
        font="Helvetica-Bold",
        font_size=9,
        min_font_size=6,
        color=NAVY,
    )

    # --------------------------------------------------------
    # WARD
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # UNIT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # JOINED
    # --------------------------------------------------------

    draw_fitted_text(
        c,
        get_joined_date(
            member
        ),
        value_x,
        85,
        155,
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
):

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
# BACK
# ============================================================

def draw_back(
    c,
):

    draw_background(
        c,
        BACK_BACKGROUND,
    )

    # --------------------------------------------------------
    # AUTHORIZED SIGNATORY
    # --------------------------------------------------------

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
    # Resolve backgrounds
    # --------------------------------------------------------

    front_background = resolve_asset(
        FRONT_BACKGROUND,
        FRONT_FALLBACKS,
    )

    back_background = resolve_asset(
        BACK_BACKGROUND,
        BACK_FALLBACKS,
    )

    # --------------------------------------------------------
    # Verify backgrounds
    # --------------------------------------------------------

    if not front_background or not os.path.isfile(
        front_background
    ):

        raise FileNotFoundError(
            "Front membership background not found: "
            f"{front_background}"
        )

    if not back_background or not os.path.isfile(
        back_background
    ):

        raise FileNotFoundError(
            "Back membership background not found: "
            f"{back_background}"
        )

    # --------------------------------------------------------
    # PDF PATH
    # --------------------------------------------------------

    pdf_path = os.path.join(
        CARD_DIR,
        f"{registration_no}-membership-card.pdf",
    )

    # --------------------------------------------------------
    # Make sure directory exists
    # --------------------------------------------------------

    os.makedirs(
        CARD_DIR,
        exist_ok=True,
    )

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

    # --------------------------------------------------------
    # CREATE PDF
    # --------------------------------------------------------

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

    c.showPage()

    # ========================================================
    # PAGE 2 — BACK
    # ========================================================

    draw_background(
        c,
        back_background,
    )

    # Signatory
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

    c.showPage()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    c.save()

    # --------------------------------------------------------
    # VERIFY PDF
    # --------------------------------------------------------

    if not os.path.isfile(
        pdf_path
    ):

        raise FileNotFoundError(
            "Membership card was not generated: "
            f"{pdf_path}"
        )

    file_size = os.path.getsize(
        pdf_path
    )

    if file_size <= 0:

        raise RuntimeError(
            "Membership card PDF was generated "
            "but is empty."
        )

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