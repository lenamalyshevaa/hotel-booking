from typing import ClassVar

from pydantic import BaseModel, ConfigDict, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class PatchSchema(Schema):
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_explicit_nulls(self):
        nulls = sorted(
            name
            for name in self.model_fields_set
            if getattr(self, name) is None and name not in self.nullable_fields
        )
        if nulls:
            raise ValueError(f"Fields cannot be null: {', '.join(nulls)}")
        return self


class ErrorResponse(BaseModel):
    detail: str


def error_responses(*codes: int) -> dict:
    descriptions = {
        400: "Некорректные данные (нарушено бизнес-правило)",
        404: "Объект не найден",
        409: "Конфликт: операция нарушает целостность данных",
    }
    return {code: {"model": ErrorResponse, "description": descriptions[code]} for code in codes}
