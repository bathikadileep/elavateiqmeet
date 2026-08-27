-- ============================================================
-- ElevateIQ Meeting Platform — Complete Database Schema
-- Target: Neon PostgreSQL
-- Architect: Senior PostgreSQL Database Architect
-- Best Practices: UUID PKs, Audit Columns, Soft Deletes,
--                 Partial Indexes, Check Constraints, ENUMs
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Full-text trigram search on names/emails

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE user_status       AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');
CREATE TYPE meeting_status    AS ENUM ('scheduled', 'live', 'ended', 'cancelled');
CREATE TYPE meeting_type      AS ENUM ('instant', 'scheduled', 'recurring');
CREATE TYPE participant_role  AS ENUM ('host', 'co_host', 'participant', 'guest');
CREATE TYPE participant_status AS ENUM ('invited', 'joined', 'left', 'kicked', 'declined');
CREATE TYPE message_type      AS ENUM ('text', 'file', 'system', 'reaction');
CREATE TYPE notif_type        AS ENUM ('meeting_invite', 'meeting_start', 'meeting_end', 'participant_join', 'participant_leave', 'recording_ready', 'file_shared', 'system_alert');
CREATE TYPE file_category     AS ENUM ('avatar', 'attachment', 'recording', 'transcript');
CREATE TYPE recording_status  AS ENUM ('processing', 'available', 'failed', 'deleted');

-- ============================================================
-- FUNCTION: Auto-update updated_at timestamp
-- ============================================================

CREATE OR REPLACE FUNCTION fn_update_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- ============================================================
-- TABLE 1: roles
-- Defines application-level roles (admin, host, participant, guest)
-- ============================================================

CREATE TABLE roles (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(60)  NOT NULL UNIQUE,
  description   TEXT,
  is_system     BOOLEAN      NOT NULL DEFAULT FALSE,  -- system roles cannot be deleted
  -- Audit
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
  deleted_at    TIMESTAMPTZ,

  CONSTRAINT chk_roles_name_nonempty CHECK (TRIM(name) <> '')
);

CREATE TRIGGER trg_roles_updated_at
  BEFORE UPDATE ON roles
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_roles_name        ON roles (name) WHERE is_deleted = FALSE;
CREATE INDEX idx_roles_is_deleted  ON roles (is_deleted);

-- Seed system roles
INSERT INTO roles (name, description, is_system) VALUES
  ('super_admin', 'Platform administrator with full control', TRUE),
  ('host',        'Can create and manage meetings', TRUE),
  ('co_host',     'Can assist in managing meetings', TRUE),
  ('participant', 'Regular authenticated participant', TRUE),
  ('guest',       'Unauthenticated or anonymous attendee', TRUE);

-- ============================================================
-- TABLE 2: permissions
-- Granular permission tokens (e.g., meeting:create, user:ban)
-- ============================================================

CREATE TABLE permissions (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(100) NOT NULL UNIQUE,          -- e.g. "meeting:create"
  description   TEXT,
  module        VARCHAR(60)  NOT NULL,                 -- e.g. "meetings", "users"
  -- Audit
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,

  CONSTRAINT chk_permissions_name_format CHECK (name ~ '^[a-z_]+:[a-z_]+$')
);

CREATE TRIGGER trg_permissions_updated_at
  BEFORE UPDATE ON permissions
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_permissions_module     ON permissions (module) WHERE is_deleted = FALSE;
CREATE INDEX idx_permissions_name       ON permissions (name)   WHERE is_deleted = FALSE;

-- Seed core permissions
INSERT INTO permissions (name, description, module) VALUES
  ('meeting:create',           'Create a new meeting',                    'meetings'),
  ('meeting:delete',           'Delete any meeting',                      'meetings'),
  ('meeting:read',             'View meeting details',                    'meetings'),
  ('meeting:update',           'Update meeting settings',                 'meetings'),
  ('meeting:lock',             'Lock/unlock a meeting room',              'meetings'),
  ('meeting:record',           'Start/stop a meeting recording',          'meetings'),
  ('participant:kick',         'Remove a participant from a meeting',     'participants'),
  ('participant:mute',         'Mute a participant',                      'participants'),
  ('participant:promote',      'Promote participant to co-host',          'participants'),
  ('message:send',             'Send a chat message',                     'messages'),
  ('message:delete_own',       'Delete own chat messages',                'messages'),
  ('message:delete_any',       'Delete any chat message',                 'messages'),
  ('file:upload',              'Upload files to a meeting',               'files'),
  ('file:download',            'Download files from a meeting',           'files'),
  ('user:ban',                 'Suspend a user account',                  'users'),
  ('user:read',                'View user profiles',                      'users'),
  ('notification:manage',      'Manage system notifications',             'notifications');

-- ============================================================
-- TABLE 3: role_permissions
-- Many-to-many join: which permissions belong to which role
-- ============================================================

CREATE TABLE role_permissions (
  role_id        UUID  NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
  permission_id  UUID  NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  granted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  granted_by     UUID,   -- FK to users.id (nullable for seeds)

  PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role_id       ON role_permissions (role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions (permission_id);

-- ============================================================
-- TABLE 4: users
-- Core identity table
-- ============================================================

CREATE TABLE users (
  id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  username          VARCHAR(60)   NOT NULL UNIQUE,
  email             VARCHAR(254)  NOT NULL UNIQUE,
  password_hash     VARCHAR(255)  NOT NULL,
  display_name      VARCHAR(100),
  avatar_url        VARCHAR(500),
  bio               TEXT,
  status            user_status   NOT NULL DEFAULT 'pending_verification',
  email_verified    BOOLEAN       NOT NULL DEFAULT FALSE,
  reset_token_hash  VARCHAR(255),
  reset_token_expires_at TIMESTAMPTZ,
  last_login_at     TIMESTAMPTZ,
  last_login_ip     INET,

  -- Audit
  created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  is_deleted        BOOLEAN       NOT NULL DEFAULT FALSE,
  deleted_at        TIMESTAMPTZ,

  CONSTRAINT chk_users_username_length    CHECK (LENGTH(TRIM(username)) >= 3),
  CONSTRAINT chk_users_email_format       CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  CONSTRAINT chk_users_display_name_len   CHECK (display_name IS NULL OR LENGTH(TRIM(display_name)) >= 1)
);

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

-- Indexes
CREATE UNIQUE INDEX idx_users_email_active     ON users (email)    WHERE is_deleted = FALSE;
CREATE UNIQUE INDEX idx_users_username_active  ON users (username) WHERE is_deleted = FALSE;
CREATE INDEX        idx_users_status           ON users (status)   WHERE is_deleted = FALSE;
CREATE INDEX        idx_users_created_at       ON users (created_at DESC);
CREATE INDEX        idx_users_email_trgm       ON users USING GIN (email gin_trgm_ops);
CREATE INDEX        idx_users_username_trgm    ON users USING GIN (username gin_trgm_ops);

-- ============================================================
-- TABLE 5: user_roles
-- Many-to-many: assigns global roles to users
-- ============================================================

CREATE TABLE user_roles (
  user_id     UUID  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id     UUID  NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  assigned_by UUID  REFERENCES users(id) ON DELETE SET NULL,

  PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles (user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles (role_id);

-- ============================================================
-- TABLE 6: meetings
-- Core meeting entity
-- ============================================================

CREATE TABLE meetings (
  id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_code     VARCHAR(20)    NOT NULL UNIQUE,        -- e.g. "abc-defg-hij"
  title            VARCHAR(200)   NOT NULL DEFAULT 'Untitled Meeting',
  description      TEXT,
  host_id          UUID           NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  status           meeting_status NOT NULL DEFAULT 'scheduled',
  meeting_type     meeting_type   NOT NULL DEFAULT 'instant',

  -- Scheduling
  scheduled_start  TIMESTAMPTZ,
  scheduled_end    TIMESTAMPTZ,
  actual_start     TIMESTAMPTZ,
  actual_end       TIMESTAMPTZ,

  -- Settings
  is_locked        BOOLEAN        NOT NULL DEFAULT FALSE,
  is_recorded      BOOLEAN        NOT NULL DEFAULT FALSE,
  chat_enabled     BOOLEAN        NOT NULL DEFAULT TRUE,
  screenshare_enabled BOOLEAN     NOT NULL DEFAULT TRUE,
  guest_access     BOOLEAN        NOT NULL DEFAULT FALSE,
  max_participants INTEGER        NOT NULL DEFAULT 50,
  password_hash    VARCHAR(255),                          -- optional meeting password

  -- Recurrence
  recurring_rule   TEXT,                                  -- iCal RRULE string

  -- Audit
  created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  is_deleted       BOOLEAN        NOT NULL DEFAULT FALSE,
  deleted_at       TIMESTAMPTZ,

  CONSTRAINT chk_meetings_max_participants  CHECK (max_participants BETWEEN 2 AND 500),
  CONSTRAINT chk_meetings_schedule_order   CHECK (
    scheduled_end IS NULL OR scheduled_start IS NULL OR scheduled_end > scheduled_start
  ),
  CONSTRAINT chk_meetings_actual_order     CHECK (
    actual_end IS NULL OR actual_start IS NULL OR actual_end > actual_start
  ),
  CONSTRAINT chk_meetings_code_format      CHECK (meeting_code ~ '^[a-z0-9\-]+$')
);

CREATE TRIGGER trg_meetings_updated_at
  BEFORE UPDATE ON meetings
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_meetings_meeting_code   ON meetings (meeting_code) WHERE is_deleted = FALSE;
CREATE INDEX idx_meetings_host_id        ON meetings (host_id)      WHERE is_deleted = FALSE;
CREATE INDEX idx_meetings_status         ON meetings (status)       WHERE is_deleted = FALSE;
CREATE INDEX idx_meetings_scheduled_start ON meetings (scheduled_start DESC NULLS LAST) WHERE is_deleted = FALSE;
CREATE INDEX idx_meetings_created_at     ON meetings (created_at DESC);

-- ============================================================
-- TABLE 7: meeting_participants
-- Per-meeting role + status for each user/guest attending
-- ============================================================

CREATE TABLE meeting_participants (
  id              UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id      UUID               NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  user_id         UUID               REFERENCES users(id) ON DELETE SET NULL,  -- NULL for guests
  guest_name      VARCHAR(100),                    -- used when user_id IS NULL
  guest_email     VARCHAR(254),
  socket_id       VARCHAR(100),                    -- active Socket.IO socket id
  role            participant_role   NOT NULL DEFAULT 'participant',
  status          participant_status NOT NULL DEFAULT 'invited',
  is_audio_on     BOOLEAN            NOT NULL DEFAULT TRUE,
  is_video_on     BOOLEAN            NOT NULL DEFAULT TRUE,
  hand_raised     BOOLEAN            NOT NULL DEFAULT FALSE,
  is_screen_sharing BOOLEAN          NOT NULL DEFAULT FALSE,

  -- Audit
  created_at      TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ        NOT NULL DEFAULT NOW(),

  CONSTRAINT chk_mp_user_or_guest CHECK (
    (user_id IS NOT NULL) OR (guest_name IS NOT NULL)
  ),
  CONSTRAINT chk_mp_one_per_user_meeting UNIQUE (meeting_id, user_id)
);

CREATE TRIGGER trg_meeting_participants_updated_at
  BEFORE UPDATE ON meeting_participants
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_mp_meeting_id     ON meeting_participants (meeting_id);
CREATE INDEX idx_mp_user_id        ON meeting_participants (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_mp_status         ON meeting_participants (meeting_id, status);
CREATE INDEX idx_mp_active         ON meeting_participants (meeting_id) WHERE status = 'joined';

-- ============================================================
-- TABLE 8: attendance_logs
-- Immutable log of every join/leave event per participant
-- ============================================================

CREATE TABLE attendance_logs (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id       UUID        NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  participant_id   UUID        NOT NULL REFERENCES meeting_participants(id) ON DELETE CASCADE,
  user_id          UUID        REFERENCES users(id) ON DELETE SET NULL,
  event            VARCHAR(20) NOT NULL,         -- 'joined', 'left', 'kicked', 'muted'
  event_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip_address       INET,
  user_agent       TEXT,
  duration_seconds INTEGER,                      -- populated on 'left' event

  CONSTRAINT chk_al_event CHECK (event IN ('joined', 'left', 'kicked', 'muted', 'unmuted'))
);

-- Attendance logs are append-only; no UPDATE trigger needed
CREATE INDEX idx_al_meeting_id      ON attendance_logs (meeting_id);
CREATE INDEX idx_al_participant_id  ON attendance_logs (participant_id);
CREATE INDEX idx_al_user_id         ON attendance_logs (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_al_event_at        ON attendance_logs (event_at DESC);
CREATE INDEX idx_al_meeting_event   ON attendance_logs (meeting_id, event, event_at DESC);

-- ============================================================
-- TABLE 9: messages
-- In-meeting real-time chat messages
-- ============================================================

CREATE TABLE messages (
  id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id       UUID          NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  participant_id   UUID          REFERENCES meeting_participants(id) ON DELETE SET NULL,
  user_id          UUID          REFERENCES users(id) ON DELETE SET NULL,
  message_type     message_type  NOT NULL DEFAULT 'text',
  content          TEXT          NOT NULL,
  reply_to_id      UUID          REFERENCES messages(id) ON DELETE SET NULL,
  is_pinned        BOOLEAN       NOT NULL DEFAULT FALSE,

  -- Audit
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  is_deleted       BOOLEAN       NOT NULL DEFAULT FALSE,
  deleted_at       TIMESTAMPTZ,
  deleted_by       UUID          REFERENCES users(id) ON DELETE SET NULL,

  CONSTRAINT chk_messages_content_nonempty CHECK (
    message_type = 'system' OR LENGTH(TRIM(content)) > 0
  )
);

CREATE TRIGGER trg_messages_updated_at
  BEFORE UPDATE ON messages
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_messages_meeting_id    ON messages (meeting_id, created_at ASC) WHERE is_deleted = FALSE;
CREATE INDEX idx_messages_user_id       ON messages (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_messages_reply_to      ON messages (reply_to_id) WHERE reply_to_id IS NOT NULL;
CREATE INDEX idx_messages_pinned        ON messages (meeting_id) WHERE is_pinned = TRUE AND is_deleted = FALSE;

-- ============================================================
-- TABLE 10: notifications
-- Per-user notification inbox
-- ============================================================

CREATE TABLE notifications (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type           notif_type  NOT NULL,
  title          VARCHAR(200) NOT NULL,
  body           TEXT,
  metadata       JSONB,                         -- e.g. { meeting_id, sender_id }
  is_read        BOOLEAN     NOT NULL DEFAULT FALSE,
  read_at        TIMESTAMPTZ,
  reference_id   UUID,                          -- generic FK to meeting/message etc.

  -- Audit
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at     TIMESTAMPTZ,                   -- optional TTL for ephemeral notifications

  CONSTRAINT chk_notif_read_at CHECK (
    (is_read = FALSE AND read_at IS NULL) OR (is_read = TRUE AND read_at IS NOT NULL)
  )
);

CREATE INDEX idx_notif_user_unread   ON notifications (user_id, created_at DESC) WHERE is_read = FALSE;
CREATE INDEX idx_notif_user_id       ON notifications (user_id, created_at DESC);
CREATE INDEX idx_notif_reference_id  ON notifications (reference_id) WHERE reference_id IS NOT NULL;
CREATE INDEX idx_notif_expires_at    ON notifications (expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_notif_metadata      ON notifications USING GIN (metadata);

-- ============================================================
-- TABLE 11: files
-- Uploaded file metadata (avatars, meeting attachments)
-- ============================================================

CREATE TABLE files (
  id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  uploader_id      UUID          REFERENCES users(id) ON DELETE SET NULL,
  meeting_id       UUID          REFERENCES meetings(id) ON DELETE CASCADE,
  file_category    file_category NOT NULL,
  original_name    VARCHAR(500)  NOT NULL,
  stored_name      VARCHAR(500)  NOT NULL UNIQUE,
  storage_path     VARCHAR(1000) NOT NULL,
  mime_type        VARCHAR(127)  NOT NULL,
  size_bytes       BIGINT        NOT NULL,
  checksum_sha256  CHAR(64),

  -- Audit
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  is_deleted       BOOLEAN       NOT NULL DEFAULT FALSE,
  deleted_at       TIMESTAMPTZ,

  CONSTRAINT chk_files_size_positive    CHECK (size_bytes > 0),
  CONSTRAINT chk_files_size_limit       CHECK (size_bytes <= 524288000),  -- 500 MB hard cap
  CONSTRAINT chk_files_mime_nonempty    CHECK (TRIM(mime_type) <> '')
);

CREATE TRIGGER trg_files_updated_at
  BEFORE UPDATE ON files
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_files_uploader_id   ON files (uploader_id)  WHERE is_deleted = FALSE;
CREATE INDEX idx_files_meeting_id    ON files (meeting_id)   WHERE is_deleted = FALSE AND meeting_id IS NOT NULL;
CREATE INDEX idx_files_category      ON files (file_category) WHERE is_deleted = FALSE;
CREATE INDEX idx_files_created_at    ON files (created_at DESC);

-- ============================================================
-- TABLE 12: meeting_recordings
-- Metadata for meeting recordings (video/audio)
-- ============================================================

CREATE TABLE meeting_recordings (
  id               UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id       UUID              NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
  initiated_by     UUID              REFERENCES users(id) ON DELETE SET NULL,
  file_id          UUID              REFERENCES files(id) ON DELETE SET NULL,
  status           recording_status  NOT NULL DEFAULT 'processing',
  started_at       TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
  ended_at         TIMESTAMPTZ,
  duration_seconds INTEGER,
  size_bytes       BIGINT,
  download_url     VARCHAR(1000),
  error_message    TEXT,

  -- Audit
  created_at       TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ       NOT NULL DEFAULT NOW(),

  CONSTRAINT chk_mr_duration_positive  CHECK (duration_seconds IS NULL OR duration_seconds > 0),
  CONSTRAINT chk_mr_size_positive      CHECK (size_bytes IS NULL OR size_bytes > 0),
  CONSTRAINT chk_mr_end_after_start    CHECK (ended_at IS NULL OR ended_at > started_at)
);

CREATE TRIGGER trg_meeting_recordings_updated_at
  BEFORE UPDATE ON meeting_recordings
  FOR EACH ROW EXECUTE FUNCTION fn_update_timestamp();

CREATE INDEX idx_mr_meeting_id    ON meeting_recordings (meeting_id);
CREATE INDEX idx_mr_status        ON meeting_recordings (status);
CREATE INDEX idx_mr_initiated_by  ON meeting_recordings (initiated_by) WHERE initiated_by IS NOT NULL;
CREATE INDEX idx_mr_created_at    ON meeting_recordings (created_at DESC);

-- ============================================================
-- FOREIGN KEY: role_permissions.granted_by → users.id
-- Added after users table to avoid forward-reference issues
-- ============================================================

ALTER TABLE role_permissions
  ADD CONSTRAINT fk_role_permissions_granted_by
  FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================
-- VIEW: v_active_meetings
-- Convenient view of live/scheduled non-deleted meetings
-- ============================================================

CREATE OR REPLACE VIEW v_active_meetings AS
  SELECT
    m.id,
    m.meeting_code,
    m.title,
    m.status,
    m.meeting_type,
    m.host_id,
    u.display_name  AS host_name,
    u.avatar_url    AS host_avatar,
    m.scheduled_start,
    m.actual_start,
    m.is_locked,
    m.chat_enabled,
    m.max_participants,
    COUNT(mp.id) FILTER (WHERE mp.status = 'joined') AS participant_count,
    m.created_at
  FROM meetings m
  JOIN users u ON u.id = m.host_id
  LEFT JOIN meeting_participants mp ON mp.meeting_id = m.id
  WHERE m.is_deleted = FALSE
    AND m.status IN ('scheduled', 'live')
  GROUP BY m.id, u.display_name, u.avatar_url;

-- ============================================================
-- VIEW: v_user_meeting_history
-- Per-user meeting history with duration
-- ============================================================

CREATE OR REPLACE VIEW v_user_meeting_history AS
  SELECT
    mp.user_id,
    m.id            AS meeting_id,
    m.meeting_code,
    m.title,
    m.status,
    mp.role,
    mp.status       AS participation_status,
    m.actual_start,
    m.actual_end,
    EXTRACT(EPOCH FROM (m.actual_end - m.actual_start))::INTEGER AS duration_seconds,
    m.created_at    AS meeting_created_at
  FROM meeting_participants mp
  JOIN meetings m ON m.id = mp.meeting_id
  WHERE mp.user_id IS NOT NULL
    AND m.is_deleted = FALSE;

-- ============================================================
-- END OF SCHEMA
-- ============================================================
