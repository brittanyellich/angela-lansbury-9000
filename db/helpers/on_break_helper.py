from typing import List, Tuple
from datetime import datetime

from db import DB

import sqlalchemy as sa
import datetime as dt

from db.model.on_break import OnBreak
from db.model.guild_config import GuildConfig


def add_user_on_break(guild_id: int, user_id: int):
    try:
        # Store all roles
        # Remove roles
        # Get on Break Role
        # Add On Break role
        # Add On Break
        DB.s.add(OnBreak(guild_id=guild_id, user_id=user_id, went_on_break_at=datetime.utcnow()))
        DB.s.commit()
        return True
    except sa.exc.IntegrityError:
        DB.s.rollback()
        return False


def list_on_break_users(guild_id: int):
    return DB.s.execute(
        sa.select(OnBreak)
            .where(OnBreak.guild_id == guild_id)
    ).all()


def remove_user_from_break(guild_id: int, user_id: int):
    try:
        # Get all stored roles
        # Add back to user
        # Get On Break Role
        # Remove On Break role
        # Delete On break
        DB.s.execute(
            sa.delete(OnBreak)
                .where(OnBreak.guild_id == guild_id)
                .where(OnBreak.user_id == user_id)
        )
        DB.s.commit()
        return True
    except:
        DB.s.rollback()
        return False
