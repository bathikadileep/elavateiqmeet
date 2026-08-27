from datetime import datetime
from backend.extensions import db

class BaseModel(db.Model):
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self
        
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        
    def to_dict(self):
        """Generic dictionary serializer for SQLAlchemy models."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() + "Z"
            else:
                result[column.name] = value
        return result
