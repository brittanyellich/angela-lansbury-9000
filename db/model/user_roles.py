from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class UserRoles(DB.Model):
    __tablename__ = 'user_roles'

    user_id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(primary_key=True)
