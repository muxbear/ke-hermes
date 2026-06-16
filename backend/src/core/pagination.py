"""统一分页工具——迭代器模式。

消除 6+ 个 list_* 函数中重复的 offset/limit 分页逻辑。
"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PageResult:
    """分页查询结果。"""

    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20

    @property
    def total_pages(self) -> int:
        if self.total <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class PageIterator:
    """统一分页迭代器。

    封装 offset/limit 查询和 total count 查询，消除各 service 中的重复代码。

    使用方式:
        pager = PageIterator(
            query=select(Agent).where(Agent.status == "active"),
            count_query=select(func.count()).select_from(Agent),
            db=db,
            page_size=20,
        )
        result = await pager.get_page(page=1)
    """

    def __init__(
        self,
        query: Select,
        count_query: Select,
        db: AsyncSession,
        page_size: int = 20,
    ) -> None:
        self._query = query
        self._count_query = count_query
        self._db = db
        self._page_size = max(1, page_size)

    async def get_page(self, page: int = 1) -> PageResult:
        """获取指定页码的结果。"""
        offset = max(0, (page - 1) * self._page_size)

        result = await self._db.execute(
            self._query.offset(offset).limit(self._page_size)
        )
        items = list(result.scalars().all())

        total_result = await self._db.execute(self._count_query)
        total = total_result.scalar() or 0

        return PageResult(
            items=items,
            total=total,
            page=page,
            page_size=self._page_size,
        )
