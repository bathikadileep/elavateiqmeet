"""
SQLAlchemy models reflecting the ElevateIQ Neon PostgreSQL schema.
Uses pg8000 driver with UUID primary keys and all enum types.

Cross-dialect design:
- IpAddress : INET on Postgres, VARCHAR(45) on SQLite (tests)
- JsonField : JSONB on Postgres, JSON on others
- ENUMs     : native ENUM on Postgres, VARCHAR fallback on SQLite
"""
import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, BigInteger, DateTime,
    ForeignKey, Enum as SAEnum, UniqueConstraint, CheckConstraint,
    CHAR, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy import DateTime as TIMESTAMPTZ
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, String as SAString
from backend.extensions import db


# ── Cross-dialect IP address type ─────────────────────────────────────────────

class IpAddress(TypeDecorator):
    """INET on PostgreSQL, VARCHAR(45) on SQLite (tests)."""
    impl      = SAString(45)
    cache_ok  = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(INET())
        return dialect.type_descriptor(SAString(45))

    def process_bind_param(self, value, dialect):
        return str(value) if value else None

    def process_result_value(self, value, dialect):
        return value


# ── Cross-dialect JSON type ────────────────────────────────────────────────────

class JsonField(TypeDecorator):
    """JSONB on PostgreSQL, JSON (stored as TEXT) on SQLite (tests)."""
    impl      = Text
    cache_ok  = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql":
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql" and isinstance(value, str):
            return json.loads(value)
        return value


# ─── Enum definitions ─────────────────────────────────────────────────────────
# native_enum=False → uses VARCHAR on SQLite, preserving cross-dialect compatibility.
# On PostgreSQL the database-level ENUM was already created by schema.sql.

_e = dict(create_constraint=False, native_enum=False)

UserStatusEnum        = SAEnum('active', 'inactive', 'suspended', 'pending_verification', name='user_status',        **_e)
MeetingStatusEnum     = SAEnum('scheduled', 'live', 'ended', 'cancelled',                  name='meeting_status',    **_e)
MeetingTypeEnum       = SAEnum('instant', 'scheduled', 'recurring',                        name='meeting_type',      **_e)
ParticipantRoleEnum   = SAEnum('host', 'co_host', 'participant', 'guest',                   name='participant_role',  **_e)
ParticipantStatusEnum = SAEnum('invited', 'joined', 'left', 'kicked', 'declined',          name='participant_status',**_e)
MessageTypeEnum       = SAEnum('text', 'file', 'system', 'reaction',                        name='message_type',     **_e)
NotifTypeEnum         = SAEnum('meeting_invite', 'meeting_start', 'meeting_end',
                               'participant_join', 'participant_leave',
                               'recording_ready', 'file_shared', 'system_alert',           name='notif_type',        **_e)
FileCategoryEnum      = SAEnum('avatar', 'attachment', 'recording', 'transcript',           name='file_category',    **_e)
RecordingStatusEnum   = SAEnum('processing', 'available', 'failed', 'deleted',              name='recording_status', **_e)


def gen_uuid():
    return str(uuid.uuid4())

    return str(uuid.uuid4())


# ─── Role ─────────────────────────────────────────────────────────────────────

class Role(db.Model):
    __tablename__ = 'roles'

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name        = Column(String(60), nullable=False, unique=True)
    description = Column(Text)
    is_system   = Column(Boolean, nullable=False, default=False)
    created_at  = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at  = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted  = Column(Boolean, nullable=False, default=False)
    deleted_at  = Column(TIMESTAMPTZ)

    permissions = relationship(
        'Permission',
        secondary='role_permissions',
        back_populates='roles',
        primaryjoin='Role.id == RolePermission.role_id',
        secondaryjoin='Permission.id == RolePermission.permission_id',
    )
    users = relationship(
        'User',
        secondary='user_roles',
        back_populates='roles',
        primaryjoin='Role.id == UserRole.role_id',
        secondaryjoin='User.id == UserRole.user_id',
    )

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description,
                'is_system': self.is_system}


# ─── Permission ───────────────────────────────────────────────────────────────

class Permission(db.Model):
    __tablename__ = 'permissions'

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    module      = Column(String(60), nullable=False)
    created_at  = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at  = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted  = Column(Boolean, nullable=False, default=False)

    roles = relationship(
        'Role',
        secondary='role_permissions',
        back_populates='permissions',
        primaryjoin='Permission.id == RolePermission.permission_id',
        secondaryjoin='Role.id == RolePermission.role_id',
    )


# ─── RolePermission (join) ────────────────────────────────────────────────────

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    role_id       = Column(UUID(as_uuid=False), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(UUID(as_uuid=False), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
    granted_at    = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    granted_by    = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)


# ─── User ─────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    username       = Column(String(60), nullable=False, unique=True)
    email          = Column(String(254), nullable=False, unique=True)
    password_hash  = Column(String(255), nullable=False)
    display_name   = Column(String(100))
    avatar_url     = Column(String(500))
    bio            = Column(Text)
    status                = Column(UserStatusEnum, nullable=False, default='pending_verification')
    email_verified        = Column(Boolean, nullable=False, default=False)
    reset_token_hash      = Column(String(255), nullable=True)
    reset_token_expires_at= Column(TIMESTAMPTZ, nullable=True)
    last_login_at         = Column(TIMESTAMPTZ)
    last_login_ip         = Column(IpAddress)
    created_at            = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at            = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted            = Column(Boolean, nullable=False, default=False)
    deleted_at            = Column(TIMESTAMPTZ)

    roles = relationship(
        'Role',
        secondary='user_roles',
        back_populates='users',
        primaryjoin='User.id == UserRole.user_id',
        secondaryjoin='Role.id == UserRole.role_id',
    )
    hosted_meetings = relationship('Meeting', foreign_keys='Meeting.host_id', back_populates='host')
    participations  = relationship('MeetingParticipant', foreign_keys='MeetingParticipant.user_id', back_populates='user')
    messages        = relationship('Message', foreign_keys='Message.user_id', back_populates='user')
    notifications   = relationship('Notification', foreign_keys='Notification.user_id', back_populates='user')
    files           = relationship('File', foreign_keys='File.uploader_id', back_populates='uploader')

    def set_password(self, password: str):
        from backend.extensions import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        from backend.extensions import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None,
        }


# ─── UserRole (join) ──────────────────────────────────────────────────────────

class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id     = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id     = Column(UUID(as_uuid=False), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_at = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)


# ─── Meeting ──────────────────────────────────────────────────────────────────

class Meeting(db.Model):
    __tablename__ = 'meetings'

    id                  = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code        = Column(String(20), nullable=False, unique=True)
    title               = Column(String(200), nullable=False, default='Untitled Meeting')
    description         = Column(Text)
    host_id             = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    status              = Column(MeetingStatusEnum, nullable=False, default='scheduled')
    meeting_type        = Column(MeetingTypeEnum, nullable=False, default='instant')
    scheduled_start     = Column(TIMESTAMPTZ)
    scheduled_end       = Column(TIMESTAMPTZ)
    actual_start        = Column(TIMESTAMPTZ)
    actual_end          = Column(TIMESTAMPTZ)
    is_locked           = Column(Boolean, nullable=False, default=False)
    is_recorded         = Column(Boolean, nullable=False, default=False)
    chat_enabled        = Column(Boolean, nullable=False, default=True)
    screenshare_enabled = Column(Boolean, nullable=False, default=True)
    guest_access        = Column(Boolean, nullable=False, default=False)
    max_participants    = Column(Integer, nullable=False, default=50)
    password_hash       = Column(String(255))
    recurring_rule      = Column(Text)
    created_at          = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at          = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted          = Column(Boolean, nullable=False, default=False)
    deleted_at          = Column(TIMESTAMPTZ)

    host         = relationship('User', foreign_keys=[host_id], back_populates='hosted_meetings')
    participants = relationship('MeetingParticipant', back_populates='meeting', cascade='all, delete-orphan')
    messages     = relationship('Message', back_populates='meeting', cascade='all, delete-orphan')
    files        = relationship('File', back_populates='meeting')
    recordings   = relationship('MeetingRecording', back_populates='meeting', cascade='all, delete-orphan')
    attendance   = relationship('AttendanceLog', back_populates='meeting', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'title': self.title,
            'description': self.description,
            'host_id': self.host_id,
            'status': self.status,
            'meeting_type': self.meeting_type,
            'scheduled_start': self.scheduled_start.isoformat() + 'Z' if self.scheduled_start else None,
            'is_locked': self.is_locked,
            'is_recorded': self.is_recorded,
            'chat_enabled': self.chat_enabled,
            'screenshare_enabled': self.screenshare_enabled,
            'guest_access': self.guest_access,
            'max_participants': self.max_participants,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }


# ─── MeetingParticipant ───────────────────────────────────────────────────────

class MeetingParticipant(db.Model):
    __tablename__ = 'meeting_participants'
    __table_args__ = (
        UniqueConstraint('meeting_id', 'user_id', name='chk_mp_one_per_user_meeting'),
    )

    id               = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_id       = Column(UUID(as_uuid=False), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    user_id          = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    guest_name       = Column(String(100))
    guest_email      = Column(String(254))
    socket_id        = Column(String(100))
    role             = Column(ParticipantRoleEnum, nullable=False, default='participant')
    status           = Column(ParticipantStatusEnum, nullable=False, default='invited')
    is_audio_on      = Column(Boolean, nullable=False, default=True)
    is_video_on      = Column(Boolean, nullable=False, default=True)
    hand_raised      = Column(Boolean, nullable=False, default=False)
    is_screen_sharing = Column(Boolean, nullable=False, default=False)
    created_at       = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at       = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    meeting       = relationship('Meeting', back_populates='participants')
    user          = relationship('User', foreign_keys=[user_id], back_populates='participations')
    attendance    = relationship('AttendanceLog', back_populates='participant')

    def to_dict(self):
        return {
            'id': self.id, 'meeting_id': self.meeting_id,
            'user_id': self.user_id, 'guest_name': self.guest_name,
            'role': self.role, 'status': self.status,
            'is_audio_on': self.is_audio_on, 'is_video_on': self.is_video_on,
            'hand_raised': self.hand_raised, 'is_screen_sharing': self.is_screen_sharing,
        }


# ─── AttendanceLog ────────────────────────────────────────────────────────────

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'

    id               = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_id       = Column(UUID(as_uuid=False), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    participant_id   = Column(UUID(as_uuid=False), ForeignKey('meeting_participants.id', ondelete='CASCADE'), nullable=False)
    user_id          = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    event            = Column(String(20), nullable=False)
    event_at         = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    ip_address       = Column(IpAddress)
    user_agent       = Column(Text)
    duration_seconds = Column(Integer)

    meeting     = relationship('Meeting', back_populates='attendance')
    participant = relationship('MeetingParticipant', back_populates='attendance')


# ─── Message ──────────────────────────────────────────────────────────────────

class Message(db.Model):
    __tablename__ = 'messages'

    id             = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_id     = Column(UUID(as_uuid=False), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    participant_id = Column(UUID(as_uuid=False), ForeignKey('meeting_participants.id', ondelete='SET NULL'), nullable=True)
    user_id        = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    message_type   = Column(MessageTypeEnum, nullable=False, default='text')
    content        = Column(Text, nullable=False)
    reply_to_id    = Column(UUID(as_uuid=False), ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    is_pinned      = Column(Boolean, nullable=False, default=False)
    created_at     = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at     = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted     = Column(Boolean, nullable=False, default=False)
    deleted_at     = Column(TIMESTAMPTZ)
    deleted_by     = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    meeting  = relationship('Meeting', back_populates='messages')
    user     = relationship('User', foreign_keys=[user_id], back_populates='messages')
    replies  = relationship('Message', foreign_keys=[reply_to_id])

    def to_dict(self):
        return {
            'id': self.id, 'meeting_id': self.meeting_id,
            'user_id': self.user_id, 'message_type': self.message_type,
            'content': self.content, 'reply_to_id': self.reply_to_id,
            'is_pinned': self.is_pinned,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }


# ─── Notification ─────────────────────────────────────────────────────────────

class Notification(db.Model):
    __tablename__ = 'notifications'

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type            = Column(NotifTypeEnum, nullable=False)
    title           = Column(String(200), nullable=False)
    body            = Column(Text)
    notif_metadata  = Column('metadata', JsonField)   # 'metadata' reserved in SQLAlchemy; mapped via column alias
    is_read      = Column(Boolean, nullable=False, default=False)
    read_at      = Column(TIMESTAMPTZ)
    reference_id = Column(UUID(as_uuid=False))
    created_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    expires_at   = Column(TIMESTAMPTZ)

    user = relationship('User', foreign_keys=[user_id], back_populates='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'body': self.body,
            'metadata': self.notif_metadata,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }


# ─── File ─────────────────────────────────────────────────────────────────────

class File(db.Model):
    __tablename__ = 'files'

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    uploader_id     = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    meeting_id      = Column(UUID(as_uuid=False), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=True)
    file_category   = Column(FileCategoryEnum, nullable=False)
    original_name   = Column(String(500), nullable=False)
    stored_name     = Column(String(500), nullable=False, unique=True)
    storage_path    = Column(String(1000), nullable=False)
    mime_type       = Column(String(127), nullable=False)
    size_bytes      = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(CHAR(64))
    created_at      = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at      = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    is_deleted      = Column(Boolean, nullable=False, default=False)
    deleted_at      = Column(TIMESTAMPTZ)

    uploader  = relationship('User', foreign_keys=[uploader_id], back_populates='files')
    meeting   = relationship('Meeting', foreign_keys=[meeting_id], back_populates='files')
    recording = relationship('MeetingRecording', back_populates='file', uselist=False)

    def to_dict(self):
        return {
            'id': self.id, 'uploader_id': self.uploader_id, 'meeting_id': self.meeting_id,
            'file_category': self.file_category, 'original_name': self.original_name,
            'mime_type': self.mime_type, 'size_bytes': self.size_bytes,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }


# ─── MeetingRecording ─────────────────────────────────────────────────────────

class MeetingRecording(db.Model):
    __tablename__ = 'meeting_recordings'

    id               = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_id       = Column(UUID(as_uuid=False), ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    initiated_by     = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    file_id          = Column(UUID(as_uuid=False), ForeignKey('files.id', ondelete='SET NULL'), nullable=True)
    status           = Column(RecordingStatusEnum, nullable=False, default='processing')
    started_at       = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    ended_at         = Column(TIMESTAMPTZ)
    duration_seconds = Column(Integer)
    size_bytes       = Column(BigInteger)
    download_url     = Column(String(1000))
    error_message    = Column(Text)
    created_at       = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    updated_at       = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    meeting = relationship('Meeting', back_populates='recordings')
    file    = relationship('File', back_populates='recording')

    def to_dict(self):
        return {
            'id': self.id, 'meeting_id': self.meeting_id,
            'status': self.status, 'started_at': self.started_at.isoformat() + 'Z',
            'duration_seconds': self.duration_seconds, 'download_url': self.download_url,
        }


# ─── Poll Models ──────────────────────────────────────────────────────────────

class Poll(db.Model):
    __tablename__ = 'polls'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code = Column(String(50), nullable=False, index=True)
    created_by   = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    question     = Column(Text, nullable=False)
    is_multiselect = Column(Boolean, nullable=False, default=False)
    is_published = Column(Boolean, nullable=False, default=False)
    is_closed    = Column(Boolean, nullable=False, default=False)
    created_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    options = relationship('PollOption', back_populates='poll', cascade='all, delete-orphan')
    votes   = relationship('PollVote', back_populates='poll', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'created_by': self.created_by,
            'question': self.question,
            'is_multiselect': self.is_multiselect,
            'is_published': self.is_published,
            'is_closed': self.is_closed,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'options': [opt.to_dict() for opt in self.options],
            'total_votes': len(self.votes)
        }


class PollOption(db.Model):
    __tablename__ = 'poll_options'

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    poll_id     = Column(UUID(as_uuid=False), ForeignKey('polls.id', ondelete='CASCADE'), nullable=False)
    option_text = Column(Text, nullable=False)

    poll  = relationship('Poll', back_populates='options')
    votes = relationship('PollVote', back_populates='option', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'poll_id': self.poll_id,
            'option_text': self.option_text,
            'vote_count': len(self.votes)
        }


class PollVote(db.Model):
    __tablename__ = 'poll_votes'

    id        = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    poll_id   = Column(UUID(as_uuid=False), ForeignKey('polls.id', ondelete='CASCADE'), nullable=False)
    option_id = Column(UUID(as_uuid=False), ForeignKey('poll_options.id', ondelete='CASCADE'), nullable=False)
    user_id   = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    poll   = relationship('Poll', back_populates='votes')
    option = relationship('PollOption', back_populates='votes')


# ─── Breakout Room Models ─────────────────────────────────────────────────────

class BreakoutRoom(db.Model):
    __tablename__ = 'breakout_rooms'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code = Column(String(50), nullable=False, index=True)
    room_name    = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=15)
    is_active    = Column(Boolean, nullable=False, default=True)
    created_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    assignments = relationship('BreakoutAssignment', back_populates='room', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'room_name': self.room_name,
            'duration_minutes': self.duration_minutes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'assigned_users': [a.user_id for a in self.assignments]
        }


class BreakoutAssignment(db.Model):
    __tablename__ = 'breakout_assignments'

    id        = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    room_id   = Column(UUID(as_uuid=False), ForeignKey('breakout_rooms.id', ondelete='CASCADE'), nullable=False)
    user_id   = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    room = relationship('BreakoutRoom', back_populates='assignments')


# ─── Whiteboard Snapshot Model ───────────────────────────────────────────────

class WhiteboardSnapshot(db.Model):
    __tablename__ = 'whiteboard_snapshots'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code = Column(String(50), nullable=False, index=True)
    snapshot_json = Column(JsonField, nullable=False)
    updated_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'snapshot_json': self.snapshot_json,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }


# ─── AI Meeting Intelligence Models ──────────────────────────────────────────

class MeetingTranscriptLine(db.Model):
    __tablename__ = 'meeting_transcript_lines'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code = Column(String(50), nullable=False, index=True)
    speaker_name = Column(String(100), nullable=False)
    transcript_text = Column(Text, nullable=False)
    timestamp    = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'speaker_name': self.speaker_name,
            'transcript_text': self.transcript_text,
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None
        }


class MeetingSummary(db.Model):
    __tablename__ = 'meeting_summaries'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    meeting_code = Column(String(50), nullable=False, unique=True, index=True)
    executive_summary = Column(Text, nullable=False)
    key_decisions     = Column(JsonField, nullable=False) # list of strings
    sentiment_score   = Column(String(20), nullable=False, default='positive') # positive, neutral, negative
    sentiment_value   = Column(Text, nullable=False, default='0.85')
    generated_at      = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    action_items = relationship('ActionItem', back_populates='summary', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'meeting_code': self.meeting_code,
            'executive_summary': self.executive_summary,
            'key_decisions': self.key_decisions,
            'sentiment_score': self.sentiment_score,
            'sentiment_value': self.sentiment_value,
            'generated_at': self.generated_at.isoformat() + 'Z' if self.generated_at else None,
            'action_items': [item.to_dict() for item in self.action_items]
        }


class ActionItem(db.Model):
    __tablename__ = 'action_items'

    id         = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    summary_id = Column(UUID(as_uuid=False), ForeignKey('meeting_summaries.id', ondelete='CASCADE'), nullable=False)
    task_description = Column(Text, nullable=False)
    assigned_to      = Column(String(100), nullable=False, default='Unassigned')
    due_date         = Column(String(50))
    is_completed     = Column(Boolean, nullable=False, default=False)

    summary = relationship('MeetingSummary', back_populates='action_items')

    def to_dict(self):
        return {
            'id': self.id,
            'summary_id': self.summary_id,
            'task_description': self.task_description,
            'assigned_to': self.assigned_to,
            'due_date': self.due_date,
            'is_completed': self.is_completed
        }


# ─── Enterprise Security & SSO Models ────────────────────────────────────────

class SSOProviderConfig(db.Model):
    __tablename__ = 'sso_provider_configs'

    id            = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    provider_name = Column(String(50), nullable=False, unique=True, index=True) # google, azure, okta
    client_id     = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    tenant_id     = Column(String(255))
    is_enabled    = Column(Boolean, nullable=False, default=True)
    created_at    = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'provider_name': self.provider_name,
            'client_id': self.client_id,
            'tenant_id': self.tenant_id,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class SecurityAuditLog(db.Model):
    __tablename__ = 'security_audit_logs'

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    event_type  = Column(String(100), nullable=False, index=True) # SSO_LOGIN, SESSION_REVOKED, DLP_OFFENSE, IP_BLOCKED
    actor_id    = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    ip_address  = Column(IpAddress)
    user_agent  = Column(Text)
    details     = Column(JsonField)
    timestamp   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'actor_id': self.actor_id,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None
        }


class IPRestrictionRule(db.Model):
    __tablename__ = 'ip_restriction_rules'

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    cidr_range  = Column(String(50), nullable=False, unique=True) # e.g. 192.168.1.0/24
    description = Column(String(255))
    is_allowed  = Column(Boolean, nullable=False, default=True)
    created_at  = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'cidr_range': self.cidr_range,
            'description': self.description,
            'is_allowed': self.is_allowed,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class DLPOffenseLog(db.Model):
    __tablename__ = 'dlp_offense_logs'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id      = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    offense_type = Column(String(50), nullable=False) # SSN, CREDIT_CARD, API_KEY, PASSWORD
    detected_in  = Column(String(100), nullable=False) # chat, file_upload, transcript
    snippet      = Column(Text, nullable=False)
    action_taken = Column(String(50), nullable=False, default='BLOCKED')
    timestamp    = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'offense_type': self.offense_type,
            'detected_in': self.detected_in,
            'snippet': self.snippet,
            'action_taken': self.action_taken,
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None
        }


# ─── Developer API Gateway & Webhook Models ────────────────────────────────────

class APIKey(db.Model):
    __tablename__ = 'api_keys'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id      = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key_name     = Column(String(100), nullable=False)
    api_key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix   = Column(String(16), nullable=False)
    rate_limit   = Column(Integer, nullable=False, default=100) # requests per minute
    is_active    = Column(Boolean, nullable=False, default=True)
    created_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key_name': self.key_name,
            'key_prefix': self.key_prefix,
            'rate_limit': self.rate_limit,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class WebhookSubscription(db.Model):
    __tablename__ = 'webhook_subscriptions'

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id      = Column(UUID(as_uuid=False), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    target_url   = Column(String(1000), nullable=False)
    events_json  = Column(JsonField, nullable=False) # list of event names e.g. ["meeting.created", "recording.ready"]
    secret_token = Column(String(255), nullable=False)
    is_active    = Column(Boolean, nullable=False, default=True)
    created_at   = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    logs = relationship('WebhookDeliveryLog', back_populates='subscription', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'target_url': self.target_url,
            'events': self.events_json,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class WebhookDeliveryLog(db.Model):
    __tablename__ = 'webhook_delivery_logs'

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    subscription_id = Column(UUID(as_uuid=False), ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False)
    event_type      = Column(String(100), nullable=False)
    status_code     = Column(Integer)
    response_body   = Column(Text)
    attempts        = Column(Integer, nullable=False, default=1)
    is_success      = Column(Boolean, nullable=False, default=False)
    delivered_at    = Column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)

    subscription = relationship('WebhookSubscription', back_populates='logs')

    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'event_type': self.event_type,
            'status_code': self.status_code,
            'attempts': self.attempts,
            'is_success': self.is_success,
            'delivered_at': self.delivered_at.isoformat() + 'Z' if self.delivered_at else None
        }




