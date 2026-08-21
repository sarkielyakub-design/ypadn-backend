from sqlalchemy.orm import Session
from app.models.member import Member


def generate_registration_no(db: Session):

    last = db.query(Member)\
        .order_by(Member.id.desc())\
        .first()

    if not last:
        return "YPADN-000001"

    next_id = last.id + 1

    return f"YPADN-{next_id:06d}"