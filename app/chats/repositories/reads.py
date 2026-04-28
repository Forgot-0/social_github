from dataclasses import dataclass

from sqlalchemy import Select
from app.chats.models.read_receipts import ReadReceipt
from app.core.db.repository import IRepository
from app.core.filters.base import BaseFilter



@dataclass
class ReadReceiptRepository(IRepository[ReadReceipt]):

    def apply_relationship_filters(self, stmt: Select, filters: BaseFilter) -> Select:
        return stmt
