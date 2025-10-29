from typing import Type, TypeVar, Generic
from django.db import models

T = TypeVar('T', bound=models.Model)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get_all(self):
        return self.model.objects.all()

    def get_by_id(self, obj_id: int):
        return self.model.objects.filter(id=obj_id).first()

    def create(self, **kwargs) -> T:
        return self.model.objects.create(**kwargs)

    def update(self, obj_id: int, **kwargs):
        obj = self.get_by_id(obj_id)
        print(kwargs)
        if not obj:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        obj.save()
        return obj

    def delete(self, obj_id: int) -> bool:
        deleted, _ = self.model.objects.filter(id=obj_id).delete()
        return bool(deleted)
