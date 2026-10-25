from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query


@dataclass
class Pagination:
    skip: int
    limit: int


def pagination(
    skip: Annotated[int, Query(ge=0, description="Сколько записей пропустить")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Сколько записей вернуть")] = 20,
) -> Pagination:
    return Pagination(skip=skip, limit=limit)


PaginationDep = Annotated[Pagination, Depends(pagination)]
