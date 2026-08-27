"""
ElevateIQ — Socket.IO Namespace & Event Handler Registration
==============================================================
"""

import logging
from backend.sockets.connection import register_connection_handlers
from backend.sockets.chat import register_chat_handlers
from backend.sockets.signaling import register_signaling_handlers
from backend.sockets.sfu_signaling import register_sfu_signaling_handlers
from backend.sockets.whiteboard import register_whiteboard_handlers
from backend.sockets.captions import register_caption_handlers

log = logging.getLogger("elevateiq.sockets")


def init_sockets(sio):
    """
    Registers connection, chat, signaling, SFU, whiteboard, and caption handlers onto Socket.IO.
    """
    register_connection_handlers(sio)
    register_chat_handlers(sio)
    register_signaling_handlers(sio)
    register_sfu_signaling_handlers(sio)
    register_whiteboard_handlers(sio)
    register_caption_handlers(sio)
    log.info("Socket.IO connection, chat, signaling, SFU, whiteboard, and caption handlers registered successfully.")
