from backend.extensions import db, bcrypt
from backend.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        
    def check_password(self, password):
        """Check password correctness."""
        return bcrypt.check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        """Serialize user model but exclude sensitive password hash."""
        data = super().to_dict()
        data.pop("password_hash", None)
        return data
