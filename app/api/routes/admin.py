from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import os

from app.core.dependencies import get_current_admin
from app.db.session import get_db
from app.models.member import Member
from app.utils.excel_export import generate_members_excel
from app.utils.membership_card_generator import (
    generate_membership_card,
    BASE_DIR,
)


# ============================================================
# ADMIN ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(get_current_admin)],
)


# ============================================================
# PATH HELPER
# ============================================================

def resolve_file_path(file_path):
    """
    Convert database/file paths into absolute filesystem paths.

    Supports both:

        uploads/cards/file.pdf

    and:

        /app/uploads/cards/file.pdf
    """

    if not file_path:
        return None

    file_path = str(file_path).strip()

    if not file_path:
        return None

    if os.path.isabs(file_path):
        return file_path

    return os.path.abspath(
        os.path.join(
            BASE_DIR,
            file_path,
        )
    )


# ============================================================
# CONVERT ABSOLUTE PATH TO DATABASE PATH
# ============================================================

def relative_project_path(file_path):
    """
    Store a project-relative path in the database.

    Example:

        /app/uploads/cards/YPADN-000006-membership-card.pdf

    becomes:

        uploads/cards/YPADN-000006-membership-card.pdf
    """

    if not file_path:
        return None

    absolute_path = os.path.abspath(
        file_path
    )

    try:
        return os.path.relpath(
            absolute_path,
            BASE_DIR,
        )
    except ValueError:
        return absolute_path


# ============================================================
# REGISTRATION TOGGLE
# ============================================================

registration_open = True


@router.get("/registration-status")
def get_registration_status():

    return {
        "open": registration_open
    }


@router.post("/registration-status/toggle")
def toggle_registration_status():

    global registration_open

    registration_open = not registration_open

    return {
        "open": registration_open,
        "message": (
            "Registration is now "
            f"{'open' if registration_open else 'closed'}"
        ),
    }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
):

    total = (
        db.query(Member)
        .count()
    )

    male = (
        db.query(Member)
        .filter(
            Member.gender.ilike("male")
        )
        .count()
    )

    female = (
        db.query(Member)
        .filter(
            Member.gender.ilike("female")
        )
        .count()
    )

    employed = (
        db.query(Member)
        .filter(
            Member.employment_status.ilike(
                "employed"
            )
        )
        .count()
    )

    unemployed = (
        db.query(Member)
        .filter(
            Member.employment_status.ilike(
                "unemployed"
            )
        )
        .count()
    )

    youth_members = (
        db.query(Member)
        .filter(
            Member.youth_org_member == True
        )
        .count()
    )

    physically_challenged = (
        db.query(Member)
        .filter(
            Member.physically_challenged == True
        )
        .count()
    )

    return {
        "total_members": total,
        "male": male,
        "female": female,
        "employed": employed,
        "unemployed": unemployed,
        "youth_members": youth_members,
        "physically_challenged": physically_challenged,
    }


# ============================================================
# ALL MEMBERS
# ============================================================

@router.get("/members")
def all_members(
    db: Session = Depends(get_db),
    limit: Optional[int] = None,
    sort: Optional[str] = None,
):

    query = db.query(Member)

    if sort:

        try:

            field, order = sort.split(":")

            if hasattr(Member, field):

                column = getattr(
                    Member,
                    field,
                )

                if order.lower() == "desc":

                    query = query.order_by(
                        column.desc()
                    )

                else:

                    query = query.order_by(
                        column.asc()
                    )

        except Exception:

            query = query.order_by(
                Member.id.desc()
            )

    else:

        query = query.order_by(
            Member.id.desc()
        )

    if limit:

        query = query.limit(
            limit
        )

    members = query.all()

    return {
        "count": len(members),
        "data": members,
    }


# ============================================================
# RECENT MEMBERS
# ============================================================

@router.get("/members/recent")
def recent_members(
    db: Session = Depends(get_db),
):

    members = (
        db.query(Member)
        .order_by(
            Member.id.desc()
        )
        .limit(5)
        .all()
    )

    return members


# ============================================================
# SINGLE MEMBER
# ============================================================

@router.get("/member/{member_id}")
def member_details(
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

@router.delete("/member/{member_id}")
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

    # --------------------------------------------------------
    # Delete associated files
    # --------------------------------------------------------

    file_paths = [
        getattr(
            member,
            "passport",
            None,
        ),
        getattr(
            member,
            "qr_code",
            None,
        ),
        getattr(
            member,
            "id_card",
            None,
        ),
    ]

    for file_path in file_paths:

        absolute_path = resolve_file_path(
            file_path
        )

        if (
            absolute_path
            and os.path.isfile(
                absolute_path
            )
        ):

            try:

                os.remove(
                    absolute_path
                )

                print(
                    f"🗑️ Deleted file: "
                    f"{absolute_path}"
                )

            except Exception as exc:

                print(
                    f"⚠️ Could not delete "
                    f"{absolute_path}: {exc}"
                )

    # --------------------------------------------------------
    # Delete database record
    # --------------------------------------------------------

    db.delete(
        member
    )

    db.commit()

    return {
        "success": True,
        "message": "Member deleted",
    }


# ============================================================
# SEARCH MEMBERS
# ============================================================

@router.get("/search")
def search_members(
    keyword: str,
    db: Session = Depends(get_db),
):

    keyword = keyword.strip()

    if not keyword:

        return []

    members = (
        db.query(Member)
        .filter(
            Member.name.ilike(
                f"%{keyword}%"
            )
            |
            Member.phone.ilike(
                f"%{keyword}%"
            )
            |
            Member.registration_no.ilike(
                f"%{keyword}%"
            )
        )
        .all()
    )

    return members


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
    """
    Download a member's YPADN membership card.

    IMPORTANT:

    1. Find member.
    2. Check database card path.
    3. Check if physical PDF exists.
    4. If missing, regenerate the card.
    5. Save the correct relative path.
    6. Return FileResponse using absolute path.
    """

    print(
        "================================================"
    )

    print(
        "🪪 MEMBERSHIP CARD REQUEST"
    )

    print(
        f"Registration: {registration_no}"
    )

    print(
        "================================================"
    )

    # --------------------------------------------------------
    # Find member
    # --------------------------------------------------------

    member = (
        db.query(Member)
        .filter(
            Member.registration_no
            == registration_no
        )
        .first()
    )

    if not member:

        print(
            "❌ Member not found"
        )

        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    print(
        f"✅ Member found: "
        f"{member.name}"
    )

    # --------------------------------------------------------
    # Existing card path
    # --------------------------------------------------------

    existing_card_path = getattr(
        member,
        "id_card",
        None,
    )

    absolute_card_path = resolve_file_path(
        existing_card_path
    )

    print(
        f"Database card path: "
        f"{existing_card_path}"
    )

    print(
        f"Resolved card path: "
        f"{absolute_card_path}"
    )

    # --------------------------------------------------------
    # Check existing PDF
    # --------------------------------------------------------

    card_exists = (
        absolute_card_path
        and os.path.isfile(
            absolute_card_path
        )
    )

    if card_exists:

        print(
            "✅ Existing membership card found"
        )

    else:

        print(
            "⚠️ Membership card PDF missing."
        )

        print(
            "🔄 Regenerating membership card..."
        )

        # ----------------------------------------------------
        # QR PATH
        # ----------------------------------------------------

        qr_path = getattr(
            member,
            "qr_code",
            None,
        )

        qr_path = resolve_file_path(
            qr_path
        )

        # ----------------------------------------------------
        # Generate card
        # ----------------------------------------------------

        try:

            generated_path = (
                generate_membership_card(
                    member,
                    qr_path,
                )
            )

        except FileNotFoundError as exc:

            print(
                "❌ Membership card generation "
                f"failed: {exc}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Membership card assets "
                    f"are missing: {exc}"
                ),
            )

        except Exception as exc:

            print(
                "❌ Membership card generation "
                f"failed: {exc}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not generate "
                    f"membership card: {exc}"
                ),
            )

        # ----------------------------------------------------
        # Verify generated PDF
        # ----------------------------------------------------

        generated_path = resolve_file_path(
            generated_path
        )

        if (
            not generated_path
            or not os.path.isfile(
                generated_path
            )
        ):

            print(
                "❌ Generator returned a path "
                "but the PDF does not exist:"
            )

            print(
                generated_path
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Membership card was "
                    "not generated successfully."
                ),
            )

        # ----------------------------------------------------
        # Save relative path in database
        # ----------------------------------------------------

        member.id_card = (
            relative_project_path(
                generated_path
            )
        )

        db.commit()

        db.refresh(
            member
        )

        absolute_card_path = (
            generated_path
        )

        print(
            "✅ Membership card regenerated:"
        )

        print(
            absolute_card_path
        )

        print(
            "💾 Database path:"
        )

        print(
            member.id_card
        )

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    if (
        not absolute_card_path
        or not os.path.isfile(
            absolute_card_path
        )
    ):

        print(
            "❌ FINAL CARD FILE CHECK FAILED"
        )

        print(
            f"Path: {absolute_card_path}"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Membership card file "
                "could not be found or generated."
            ),
        )

    # --------------------------------------------------------
    # Return PDF
    # --------------------------------------------------------

    print(
        "📤 Sending membership card:"
    )

    print(
        absolute_card_path
    )

    print(
        f"📦 Size: "
        f"{os.path.getsize(absolute_card_path):,} bytes"
    )

    return FileResponse(
        path=absolute_card_path,
        media_type="application/pdf",
        filename=(
            f"{registration_no}"
            "-membership-card.pdf"
        ),
    )


# ============================================================
# CURRENT ADMIN
# ============================================================

@router.get("/me")
def current_admin(
    current_user: dict = Depends(
        get_current_admin
    ),
):

    return {
        "username": current_user.get(
            "sub"
        ),
        "role": current_user.get(
            "role"
        ),
    }


# ============================================================
# EXPORT EXCEL
# ============================================================

@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
):

    members = (
        db.query(Member)
        .order_by(
            Member.id.desc()
        )
        .all()
    )

    file_path = (
        generate_members_excel(
            members
        )
    )

    file_path = resolve_file_path(
        file_path
    )

    if (
        not file_path
        or not os.path.isfile(
            file_path
        )
    ):

        raise HTTPException(
            status_code=500,
            detail="Excel file could not be generated.",
        )

    return FileResponse(
        path=file_path,
        media_type=(
            "application/vnd."
            "openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        filename=os.path.basename(
            file_path
        ),
    )


# ============================================================
# LGA ANALYTICS
# ============================================================

@router.get("/analytics/lga")
def lga_analytics(
    db: Session = Depends(get_db),
):

    results = (
        db.query(
            Member.lga,
            func.count(Member.id),
        )
        .group_by(
            Member.lga
        )
        .all()
    )

    return [
        {
            "lga": lga,
            "count": count,
        }
        for lga, count in results
    ]


# ============================================================
# GENDER ANALYTICS
# ============================================================

@router.get("/analytics/gender")
def gender_analytics(
    db: Session = Depends(get_db),
):

    male = (
        db.query(Member)
        .filter(
            Member.gender.ilike(
                "male"
            )
        )
        .count()
    )

    female = (
        db.query(Member)
        .filter(
            Member.gender.ilike(
                "female"
            )
        )
        .count()
    )

    return {
        "male": male,
        "female": female,
    }


# ============================================================
# NOTIFICATIONS
# ============================================================

@router.get("/notifications")
def notifications():

    return []