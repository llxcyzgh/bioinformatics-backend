from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from pkg.helpers.time_helper import get_timestamp, get_utc_now

Base = declarative_base()


class Model(Base):
    """Base model class, similar to Laravel's Eloquent Model"""
    __abstract__ = True

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=get_utc_now, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(Integer, default=0, nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        from datetime import datetime, date
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            elif isinstance(val, date):
                val = val.isoformat()
            result[c.name] = val
        return result

    @classmethod
    def find(cls, db, id):
        """Find by ID, similar to Laravel's find()"""
        return db.query(cls).filter(cls.id == id, cls.deleted_at == 0).first()

    @classmethod
    def all(cls, db):
        """Get all records, similar to Laravel's all()"""
        return db.query(cls).filter(cls.deleted_at == 0).all()

    @classmethod
    def where(cls, db, **kwargs):
        """Query with conditions, similar to Laravel's where()"""
        return db.query(cls).filter_by(**kwargs).filter(cls.deleted_at == 0)

    @classmethod
    def with_trashed(cls, db):
        """Include soft-deleted records, similar to Laravel's withTrashed()"""
        return db.query(cls)

    @classmethod
    def only_trashed(cls, db):
        """Get only soft-deleted records, similar to Laravel's onlyTrashed()"""
        return db.query(cls).filter(cls.deleted_at != 0)

    def save(self, db):
        """Save model, similar to Laravel's save()"""
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db):
        """Soft delete model, similar to Laravel's delete()"""
        self.deleted_at = get_timestamp()
        db.commit()
        return True

    def force_delete(self, db):
        """Permanently delete model, similar to Laravel's forceDelete()"""
        db.delete(self)
        db.commit()
        return True

    def restore(self, db):
        """Restore soft-deleted model, similar to Laravel's restore()"""
        self.deleted_at = 0
        db.commit()
        return True
