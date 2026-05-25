from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Model(Base):
    """Base model class, similar to Laravel's Eloquent Model"""
    __abstract__ = True

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def find(cls, db, id):
        """Find by ID, similar to Laravel's find()"""
        return db.query(cls).filter(cls.id == id).first()

    @classmethod
    def all(cls, db):
        """Get all records, similar to Laravel's all()"""
        return db.query(cls).all()

    @classmethod
    def where(cls, db, **kwargs):
        """Query with conditions, similar to Laravel's where()"""
        return db.query(cls).filter_by(**kwargs)

    def save(self, db):
        """Save model, similar to Laravel's save()"""
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db):
        """Delete model, similar to Laravel's delete()"""
        db.delete(self)
        db.commit()
        return True
