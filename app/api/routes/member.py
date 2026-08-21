from fastapi import (
    APIRouter,
    Depends,
    Form,
    File,
    UploadFile,
    HTTPException
)
from fastapi.responses import FileResponse
from openpyxl import Workbook
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)
from reportlab.lib import colors
from sqlalchemy.orm import Session
import os
import uuid
import qrcode
from datetime import datetime
from fastapi.responses import FileResponse
from app.db.session import get_db
from app.models.member import Member
from app.services.registration_service import generate_registration_no
from app.utils.membership_card_generator import (
    generate_membership_card
)

router = APIRouter(
    prefix="/api/members",
    tags=["Members"]
)

import os
import traceback

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.db.session import get_db
from app.models.member import Member
from app.services.registration_service import generate_registration_no


import qrcode


register_heif_opener()

router = APIRouter()


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
        # ---------------------------------------------------------
        # CREATE UPLOAD DIRECTORIES
        # ---------------------------------------------------------
        os.makedirs("uploads/passports", exist_ok=True)
        os.makedirs("uploads/qr", exist_ok=True)
        os.makedirs("uploads/cards", exist_ok=True)

        # ---------------------------------------------------------
        # GENERATE REGISTRATION NUMBER
        # ---------------------------------------------------------
        registration_no = generate_registration_no(db)

        # ---------------------------------------------------------
        # READ UPLOADED PASSPORT
        # ---------------------------------------------------------
        passport_data = await passport.read()

        if not passport_data:
            raise HTTPException(
                status_code=400,
                detail="Passport image is empty."
            )

        # ---------------------------------------------------------
        # VALIDATE + NORMALIZE IMAGE
        #
        # This supports:
        # - JPG/JPEG
        # - PNG
        # - HEIC
        # - HEIF
        # - WebP
        #
        # We do NOT trust the uploaded filename extension.
        # Everything is converted to a real JPEG.
        # ---------------------------------------------------------
        try:
            from io import BytesIO

            image = Image.open(BytesIO(passport_data))

            # Fix iPhone/EXIF orientation
            image = ImageOps.exif_transpose(image)

            # Convert to RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            passport_path = (
                f"uploads/passports/{registration_no}.jpg"
            )

            # Save as a genuine JPEG
            image.save(
                passport_path,
                format="JPEG",
                quality=92,
                optimize=True,
            )

            image.close()

        except Exception as image_error:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid passport image. "
                    "Please upload a valid JPG, PNG, HEIC, HEIF or WebP image."
                ),
            ) from image_error

        # ---------------------------------------------------------
        # GENERATE QR CODE
        # ---------------------------------------------------------
        qr_path = f"uploads/qr/{registration_no}.png"

        qr = qrcode.make(registration_no)
        qr.save(qr_path)

        # ---------------------------------------------------------
        # CREATE MEMBER
        # ---------------------------------------------------------
        member = Member(
            registration_no=registration_no,

            passport=passport_path,
            qr_code=qr_path,

            name=name,
            phone=phone,
            gender=gender,
            age=age,

            lga=lga,
            ward=ward,
            unit=unit,

            highest_qualification=highest_qualification,
            additional_qualification=additional_qualification,

            specialization=specialization,

            employment_status=employment_status,

            physically_challenged=physically_challenged,

            youth_org_member=youth_org_member,

            organization_name=organization_name,
            position=position,

            expectation=expectation,
        )

        db.add(member)
        db.commit()
        db.refresh(member)

        # ---------------------------------------------------------
        # GENERATE MEMBERSHIP CARD
        # ---------------------------------------------------------
        membership_card_path = generate_membership_card(
            member,
            qr_path,
        )

        # ---------------------------------------------------------
        # SAVE CARD PATH
        # ---------------------------------------------------------
        member.id_card = membership_card_path

        db.commit()
        db.refresh(member)

        # ---------------------------------------------------------
        # SUCCESS RESPONSE
        # ---------------------------------------------------------
        return {
            "success": True,
            "message": "Registration successful",
            "registration_no": registration_no,
            "member_id": member.id,
            "passport": passport_path,
            "qr_code": qr_path,
            "id_card": membership_card_path,
        }

    except HTTPException:
        db.rollback()

        # Clean up generated files if registration fails
        for path in [
            passport_path,
            qr_path,
            membership_card_path,
        ]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        # If a member was already inserted, remove it
        if member is not None and member.id is not None:
            try:
                db.delete(member)
                db.commit()
            except Exception:
                db.rollback()

        raise

    except Exception as e:
        traceback.print_exc()

        db.rollback()

        # Clean up generated files
        for path in [
            passport_path,
            qr_path,
            membership_card_path,
        ]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        # Remove partially-created member record
        if member is not None and member.id is not None:
            try:
                db.delete(member)
                db.commit()
            except Exception:
                db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}",
        )
@router.get("/")
def get_all_members(db: Session = Depends(get_db)):
    members = db.query(Member).all()
    
    return {
        "count": len(members),
        "data": members
    }

@router.get("/stats/summary")
def statistics(db: Session = Depends(get_db)):
    return {
        "total_members": db.query(Member).count(),
        "male": db.query(Member)
            .filter(Member.gender.ilike("male"))
            .count(),
        "female": db.query(Member)
            .filter(Member.gender.ilike("female"))
            .count(),
        "employed": db.query(Member)
            .filter(Member.employment_status.ilike("employed"))
            .count(),
        "unemployed": db.query(Member)
            .filter(Member.employment_status.ilike("unemployed"))
            .count(),
        "physically_challenged": db.query(Member)
            .filter(Member.physically_challenged == True)
            .count(),
        "youth_org_members": db.query(Member)
            .filter(Member.youth_org_member == True)
            .count()
    }

@router.get("/search/{registration_no}")
def search_member(registration_no: str, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.registration_no == registration_no)
        .first()
    )
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )
    return member

@router.get("/{member_id}")
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.id == member_id)
        .first()
    )
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )
    return member

@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.id == member_id)
        .first()
    )
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )
    db.delete(member)
    db.commit()
    return {
        "success": True,

        "message": "Member deleted successfully"
    }
@router.get("/membership-card/{registration_no}")
def download_membership_card(
    registration_no: str,
    db: Session = Depends(get_db)
):
    member = db.query(
        Member
    ).filter(
        Member.registration_no ==
        registration_no
    ).first()

    return FileResponse(
        member.id_card,
        media_type="application/pdf",
        filename=f"{registration_no}-membership-card.pdf"
    )
@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db)
):
    members = db.query(
        Member
    ).all()

    wb = Workbook()

    ws = wb.active
    ws.title = "Members"

    ws.append([
        "Reg No",
        "Name",
        "Phone",
        "Gender",
        "Age",
        "LGA",
        "Ward",
        "Unit",
        "Qualification"
    ])

    for v in members:
        ws.append([
            v.registration_no,
            v.name,
            v.phone,
            v.gender,
            v.age,
            v.lga,
            v.ward,
            v.unit,
            v.highest_qualification
        ])

    path = "uploads/members.xlsx"

    wb.save(path)

    return FileResponse(
        path,
        filename="members.xlsx"
    )
@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db)
):
    members = db.query(
        Member
    ).all()

    path = "uploads/members.pdf"

    pdf = SimpleDocTemplate(path)

    data = [[
        "Reg No",
        "Name",
        "Phone",
        "LGA"
    ]]

    for v in members:
        data.append([
            v.registration_no,
            v.name,
            v.phone,
            v.lga
        ])

    table = Table(data)

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.green
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),
        ])
    )

    pdf.build([table])

    return FileResponse(
        path,
        filename="members.pdf"
    )