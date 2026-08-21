from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import os

from app.core.dependencies import get_current_admin
from app.db.session import get_db
from app.models.member import Member
from app.utils.excel_export import generate_members_excel

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(get_current_admin)]
)

# =====================================
# REGISTRATION TOGGLE
# =====================================
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
        "message": f"Registration is now {'open' if registration_open else 'closed'}"
    }

# =====================================
# DASHBOARD SUMMARY
# =====================================
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(Member).count()
    male = (
        db.query(Member)
        .filter(Member.gender.ilike("male"))
        .count()
    )
    female = (
        db.query(Member)
        .filter(Member.gender.ilike("female"))
        .count()
    )
    employed = (
        db.query(Member)
        .filter(Member.employment_status.ilike("employed"))
        .count()
    )
    unemployed = (
        db.query(Member)
        .filter(Member.employment_status.ilike("unemployed"))
        .count()
    )
    youth_members = (
        db.query(Member)
        .filter(Member.youth_org_member == True)
        .count()
    )
    physically_challenged = (
        db.query(Member)
        .filter(Member.physically_challenged == True)
        .count()
    )
    return {
        "total_members": total,
        "male": male,
        "female": female,
        "employed": employed,
        "unemployed": unemployed,
        "youth_members": youth_members,
        "physically_challenged": physically_challenged
    }

# =====================================
# ALL MEMBERS
# =====================================
@router.get("/members")
def all_members(
    db: Session = Depends(get_db),
    limit: Optional[int] = None,
    sort: Optional[str] = None
):
    query = db.query(Member)
    if sort:
        try:
            field, order = sort.split(":")
            if hasattr(Member, field):
                column = getattr(Member, field)
                if order.lower() == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
        except Exception:
            query = query.order_by(Member.id.desc())
    else:
        query = query.order_by(Member.id.desc())
    if limit:
        query = query.limit(limit)
    members = query.all()
    return {
        "count": len(members),
        "data": members
    }

# =====================================
# RECENT MEMBERS
# =====================================
@router.get("/members/recent")
def recent_members(db: Session = Depends(get_db)):
    members = (
        db.query(Member)
        .order_by(Member.id.desc())
        .limit(5)
        .all()
    )
    return members

# =====================================
# SINGLE MEMBER
# =====================================
@router.get("/member/{member_id}")
def member_details(member_id: int, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.id == member_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

# =====================================
# DELETE MEMBER
# =====================================
@router.delete("/member/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.id == member_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    for file_path in [
        member.passport,       # note: ensure this matches your model field name
        member.qr_code,
        member.id_card
    ]:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    db.delete(member)
    db.commit()
    return {
        "success": True,
        "message": "Member deleted"
    }

# =====================================
# SEARCH MEMBERS
# =====================================
@router.get("/search")
def search_members(keyword: str, db: Session = Depends(get_db)):
    members = (
        db.query(Member)
        .filter(
            Member.name.ilike(f"%{keyword}%") |
            Member.phone.ilike(f"%{keyword}%") |
            Member.registration_no.ilike(f"%{keyword}%")
        )
        .all()
    )
    return members

# =====================================
# MEMBERSHIP CARD DOWNLOAD
# =====================================
@router.get("/membership-card/{registration_no}")
def download_membership_card(registration_no: str, db: Session = Depends(get_db)):
    member = (
        db.query(Member)
        .filter(Member.registration_no == registration_no)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.id_card:
        raise HTTPException(status_code=404, detail="Membership card not found")
    return FileResponse(
        member.id_card,
        media_type="application/pdf",
        filename=f"{registration_no}-membership-card.pdf"
    )

# =====================================
# CURRENT ADMIN
# =====================================
@router.get("/me")
def current_admin(current_user: dict = Depends(get_current_admin)):
    return {
        "username": current_user.get("sub"),
        "role": current_user.get("role")
    }

# =====================================
# EXPORT EXCEL
# =====================================
@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    members = (
        db.query(Member)
        .order_by(Member.id.desc())
        .all()
    )
    file_path = generate_members_excel(members)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(file_path)
    )

# =====================================
# LGA ANALYTICS
# =====================================
@router.get("/analytics/lga")
def lga_analytics(db: Session = Depends(get_db)):
    results = (
        db.query(
            Member.lga,
            func.count(Member.id)
        )
        .group_by(Member.lga)
        .all()
    )
    return [
        {"lga": lga, "count": count}
        for lga, count in results
    ]

# =====================================
# GENDER ANALYTICS
# =====================================
@router.get("/analytics/gender")
def gender_analytics(db: Session = Depends(get_db)):
    male = (
        db.query(Member)
        .filter(Member.gender.ilike("male"))
        .count()
    )
    female = (
        db.query(Member)
        .filter(Member.gender.ilike("female"))
        .count()
    )
    return {
        "male": male,
        "female": female
    }

# =====================================
# NOTIFICATIONS
# =====================================
@router.get("/notifications")
def notifications():
    return []