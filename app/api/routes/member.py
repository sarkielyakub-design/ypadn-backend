import os
import traceback
from io import BytesIO
from pathlib import Path

import qrcode
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from openpyxl import Workbook
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from sqlalchemy.orm import Session

from app.config import BACKEND_URL
from app.db.session import get_db
from app.models.member import Member
from app.services.registration_service import generate_registration_no
from app.utils.membership_card_generator import generate_membership_card


# ============================================================
# HEIC / HEIF SUPPORT
# ============================================================

register_heif_opener()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/members",
    tags=["Members"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

UPLOADS_DIR = BASE_DIR / "uploads"
PASSPORTS_DIR = UPLOADS_DIR / "passports"
QR_DIR = UPLOADS_DIR / "qr"
CARDS_DIR = UPLOADS_DIR / "cards"


for directory in (
    UPLOADS_DIR,
    PASSPORTS_DIR,
    QR_DIR,
    CARDS_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# PUBLIC URL HELPER
# ============================================================

def public_upload_url(path):
    """
    Convert an internal filesystem path into a public
    browser-accessible URL.

    Example:

    uploads/cards/YPADN-000068-membership-card.pdf

    becomes:

    https://ypadn-backend-production.up.railway.app/
    uploads/cards/YPADN-000068-membership-card.pdf
    """

    if not path:
        return None

    path = str(path).replace("\\", "/")

    # Handle absolute paths such as:
    # /app/uploads/cards/file.pdf
    if "/uploads/" in path:
        path = path.split("/uploads/", 1)[1]

    # Handle:
    # uploads/cards/file.pdf
    if path.startswith("uploads/"):
        path = path[len("uploads/"):]

    return f"{BACKEND_URL}/uploads/{path.lstrip('/')}"


# ============================================================
# INTERNAL PATH HELPER
# ============================================================

def absolute_upload_path(path):
    """
    Convert stored database path into an absolute filesystem path.
    """

    if not path:
        return None

    path = str(path).replace("\\", "/")

    if os.path.isabs(path):
        return Path(path)

    if path.startswith("uploads/"):
        return BASE_DIR / path

    return UPLOADS_DIR / path


# ============================================================
# RELATIVE DATABASE PATH
# ============================================================

def relative_upload_path(path):
    """
    Always store uploads using:

    uploads/...

    instead of:

    /app/uploads/...
    """

    path = Path(path)

    try:
        return path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return path.as_posix()


# ============================================================
# REGISTER MEMBER
# ============================================================

@router.post("/register")
async def register(
    name: str = Form(...),
    phone: str = Form(...),
    gender: str = Form(...),
    age: int = Form(...),
    lga: str = Form(...),
    ward: str = Form(...),
    unit: str = Form(...),
    highest_qualification: str = Form(...),
    additional_qualification: str = Form(None),
    specialization: str = Form(None),
    employment_status: str = Form(...),
    physically_challenged: bool = Form(False),
    youth_org_member: bool = Form(False),
    organization_name: str = Form(None),
    position: str = Form(None),
    expectation: str = Form(None),
    passport: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    registration_no = None
    passport_path = None
    qr_path = None
    membership_card_path = None
    member = None

    try:

        # ========================================================
        # REGISTRATION NUMBER
        # ========================================================

        registration_no = generate_registration_no(db)


        # ========================================================
        # PASSPORT
        # ========================================================

        passport_data = await passport.read()

        if not passport_data:
            raise HTTPException(
                status_code=400,
                detail="Passport image is empty.",
            )

        try:

            image = Image.open(
                BytesIO(passport_data)
            )

            image = ImageOps.exif_transpose(image)

            if image.mode != "RGB":
                image = image.convert("RGB")

            passport_file = (
                PASSPORTS_DIR
                / f"{registration_no}.jpg"
            )

            image.save(
                passport_file,
                format="JPEG",
                quality=92,
                optimize=True,
            )

            image.close()

            passport_path = relative_upload_path(
                passport_file
            )

        except Exception as image_error:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid passport image. "
                    "Please upload a valid JPG, PNG, "
                    "HEIC, HEIF or WebP image."
                ),
            ) from image_error


        # ========================================================
        # QR CODE
        # ========================================================

        qr_file = (
            QR_DIR
            / f"{registration_no}.png"
        )

        verification_url = (
            f"{BACKEND_URL}"
            f"/api/members/verify/{registration_no}"
        )

        qr = qrcode.make(
            verification_url
        )

        qr.save(qr_file)

        qr_path = relative_upload_path(
            qr_file
        )


        # ========================================================
        # CREATE MEMBER
        # ========================================================

        member = Member(
            registration_no=registration_no,

            passport=passport_path,
            qr_code=qr_path,

            name=name.strip(),
            phone=phone.strip(),
            gender=gender.strip(),
            age=age,

            lga=lga.strip(),
            ward=ward.strip(),
            unit=unit.strip(),

            highest_qualification=(
                highest_qualification.strip()
            ),

            additional_qualification=(
                additional_qualification.strip()
                if additional_qualification
                else None
            ),

            specialization=(
                specialization.strip()
                if specialization
                else None
            ),

            employment_status=(
                employment_status.strip()
            ),

            physically_challenged=(
                physically_challenged
            ),

            youth_org_member=(
                youth_org_member
            ),

            organization_name=(
                organization_name.strip()
                if organization_name
                else None
            ),

            position=(
                position.strip()
                if position
                else None
            ),

            expectation=(
                expectation.strip()
                if expectation
                else None
            ),
        )

        db.add(member)

        db.commit()

        db.refresh(member)


        # ========================================================
        # MEMBERSHIP CARD
        # ========================================================

        card_file = Path(
            generate_membership_card(
                member,
                str(
                    absolute_upload_path(
                        qr_path
                    )
                ),
            )
        )

        membership_card_path = (
            relative_upload_path(
                card_file
            )
        )


        # ========================================================
        # SAVE CARD PATH
        # ========================================================

        member.id_card = membership_card_path

        db.commit()

        db.refresh(member)


        # ========================================================
        # SUCCESS
        # ========================================================

        return {
            "success": True,

            "message": (
                "YPADN membership registration "
                "successful."
            ),

            "organization": (
                "Youth Political Awareness "
                "& Development Network"
            ),

            "short_name": "YPADN",

            "registration_no": (
                registration_no
            ),

            "member_id": member.id,

            "passport": public_upload_url(
                passport_path
            ),

            "qr_code": public_upload_url(
                qr_path
            ),

            "id_card": public_upload_url(
                membership_card_path
            ),

            "membership_card": public_upload_url(
                membership_card_path
            ),

            "verification_url": (
                f"{BACKEND_URL}"
                f"/api/members/verify/"
                f"{registration_no}"
            ),
        }


    except HTTPException:

        db.rollback()

        _cleanup_files(
            [
                passport_path,
                qr_path,
                membership_card_path,
            ]
        )

        if member is not None:

            try:

                db.delete(member)
                db.commit()

            except Exception:

                db.rollback()

        raise


    except Exception as error:

        traceback.print_exc()

        db.rollback()

        _cleanup_files(
            [
                passport_path,
                qr_path,
                membership_card_path,
            ]
        )

        if member is not None:

            try:

                db.delete(member)
                db.commit()

            except Exception:

                db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Registration failed: {error}"
            ),
        ) from error


# ============================================================
# CLEANUP
# ============================================================

def _cleanup_files(paths):

    for path in paths:

        if not path:
            continue

        absolute = absolute_upload_path(
            path
        )

        if not absolute:
            continue

        try:

            if absolute.is_file():
                absolute.unlink()

        except OSError:

            pass


# ============================================================
# GET ALL MEMBERS
# ============================================================

@router.get("/")
def get_all_members(
    db: Session = Depends(get_db),
):

    members = (
        db.query(Member)
        .order_by(Member.id.desc())
        .all()
    )

    return {
        "count": len(members),
        "data": members,
    }


# ============================================================
# STATISTICS
# ============================================================

@router.get("/stats/summary")
def statistics(
    db: Session = Depends(get_db),
):

    return {

        "total_members":
            db.query(Member).count(),

        "male":
            db.query(Member)
            .filter(
                Member.gender.ilike("male")
            )
            .count(),

        "female":
            db.query(Member)
            .filter(
                Member.gender.ilike("female")
            )
            .count(),

        "employed":
            db.query(Member)
            .filter(
                Member.employment_status.ilike(
                    "employed"
                )
            )
            .count(),

        "unemployed":
            db.query(Member)
            .filter(
                Member.employment_status.ilike(
                    "unemployed"
                )
            )
            .count(),

        "physically_challenged":
            db.query(Member)
            .filter(
                Member.physically_challenged.is_(True)
            )
            .count(),

        "youth_org_members":
            db.query(Member)
            .filter(
                Member.youth_org_member.is_(True)
            )
            .count(),
    }


# ============================================================
# VERIFY MEMBER
# ============================================================

@router.get("/verify/{registration_no}")
def verify_member(
    registration_no: str,
    db: Session = Depends(get_db),
):

    member = (
        db.query(Member)
        .filter(
            Member.registration_no
            == registration_no
        )
        .first()
    )

    if not member:

        raise HTTPException(
            status_code=404,
            detail="YPADN member not found",
        )

    return {

        "verified": True,

        "organization": (
            "Youth Political Awareness "
            "& Development Network"
        ),

        "short_name": "YPADN",

        "registration_no":
            member.registration_no,

        "name":
            member.name,

        "gender":
            member.gender,

        "age":
            member.age,

        "lga":
            member.lga,

        "ward":
            member.ward,

        "unit":
            member.unit,

        "passport":
            public_upload_url(
                member.passport
            ),

        "joined":
            member.created_at,
    }


# ============================================================
# SEARCH
# ============================================================

@router.get("/search/{registration_no}")
def search_member(
    registration_no: str,
    db: Session = Depends(get_db),
):

    member = (
        db.query(Member)
        .filter(
            Member.registration_no
            == registration_no
        )
        .first()
    )

    if not member:

        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    return member


# ============================================================
# GET MEMBER
# ============================================================

@router.get("/{member_id}")
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
):

    member = (
        db.query(Member)
        .filter(
            Member.id == member_id
        )
        .first()
    )

    if not member:

        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    return member


# ============================================================
# DELETE MEMBER
# ============================================================

@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
):

    member = (
        db.query(Member)
        .filter(
            Member.id == member_id
        )
        .first()
    )

    if not member:

        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    _cleanup_files(
        [
            member.passport,
            member.qr_code,
            member.id_card,
        ]
    )

    db.delete(member)

    db.commit()

    return {
        "success": True,
        "message": (
            "Member deleted successfully"
        ),
    }


# ============================================================
# MEMBERSHIP CARD DOWNLOAD
# ============================================================

@router.get(
    "/membership-card/{registration_no}"
)
def download_membership_card(
    registration_no: str,
    db: Session = Depends(get_db),
):

    member = (
        db.query(Member)
        .filter(
            Member.registration_no
            == registration_no
        )
        .first()
    )

    if not member:

        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )


    # --------------------------------------------------------
    # Existing card
    # --------------------------------------------------------

    card_path = absolute_upload_path(
        member.id_card
    )


    # --------------------------------------------------------
    # Regenerate if missing
    # --------------------------------------------------------

    if not card_path or not card_path.is_file():

        qr_path = absolute_upload_path(
            member.qr_code
        )

        generated = Path(
            generate_membership_card(
                member,
                str(qr_path)
                if qr_path
                else None,
            )
        )

        member.id_card = relative_upload_path(
            generated
        )

        db.commit()

        card_path = generated


    return FileResponse(
        path=str(card_path),
        media_type="application/pdf",
        filename=(
            f"{registration_no}"
            "-membership-card.pdf"
        ),
    )


# ============================================================
# EXCEL EXPORT
# ============================================================

@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
):

    members = (
        db.query(Member)
        .order_by(Member.id.asc())
        .all()
    )

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = "YPADN Members"


    worksheet.append(
        [
            "Registration No",
            "Name",
            "Phone",
            "Gender",
            "Age",
            "LGA",
            "Ward",
            "Unit",
            "Qualification",
        ]
    )


    for member in members:

        worksheet.append(
            [
                member.registration_no,
                member.name,
                member.phone,
                member.gender,
                member.age,
                member.lga,
                member.ward,
                member.unit,
                member.highest_qualification,
            ]
        )


    file_path = (
        UPLOADS_DIR
        / "members.xlsx"
    )

    workbook.save(file_path)


    return FileResponse(
        path=str(file_path),
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        filename="YPADN-members.xlsx",
    )


# ============================================================
# PDF EXPORT
# ============================================================

@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
):

    members = (
        db.query(Member)
        .order_by(Member.id.asc())
        .all()
    )

    file_path = (
        UPLOADS_DIR
        / "members.pdf"
    )


    pdf = SimpleDocTemplate(
        str(file_path)
    )


    data = [
        [
            "Registration No",
            "Name",
            "Phone",
            "LGA",
        ]
    ]


    for member in members:

        data.append(
            [
                member.registration_no,
                member.name,
                member.phone,
                member.lga,
            ]
        )


    table = Table(data)


    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#0B3D2E"
                    ),
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )


    pdf.build(
        [table]
    )


    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename="YPADN-members.pdf",
    )