from sqlalchemy import Column, Integer, String, text, DateTime, Boolean
import datetime

from ...models import ORMBase


class Warning(ORMBase):
    __tablename__ = "tg_warnings"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    date_added = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    forgiven = Column(Boolean, default=False, nullable=False)
    forgiven_by = Column(String(), nullable=True)
    forgiven_by_id = Column(Integer, nullable=False)
    warned_by = Column(String(), nullable=False)
    warned_by_id = Column(Integer, nullable=False)
    reason = Column(String(), nullable=False)
