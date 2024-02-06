from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from db import DB


class OnBreak(DB.Model):
    __tablename__ = 'on_break'

    guild_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    went_on_break_at: Mapped[datetime] = mapped_column()
