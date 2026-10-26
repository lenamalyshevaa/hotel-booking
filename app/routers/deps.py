from typing import Annotated, Literal

from fastapi import Depends, Query

from app.schemas.common import Pagination, Sorting


def pagination(
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Записей на странице")] = 10,
) -> Pagination:
    return Pagination(page=page, per_page=per_page)


def sorting(
    sort_by: Annotated[str, Query(description="Поле сортировки")] = "id",
    sort_order: Annotated[Literal["asc", "desc"], Query(description="Порядок: asc или desc")] = "asc",
) -> Sorting:
    return Sorting(sort_by=sort_by, sort_order=sort_order)


PaginationDep = Annotated[Pagination, Depends(pagination)]
SortingDep = Annotated[Sorting, Depends(sorting)]
