from sqlalchemy.orm.session import Session

from models.user import User


class GetUserInfoServices:
    def __init__(self, db: Session):
        self.db = db


    def get_user_info(self):
        user = self.db.query(User).filter().first()

