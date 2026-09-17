#!/usr/bin/env python3
"""Compat: ALWAYS use the same Telegram lib as the running Client. # NEW
Root cause of 'all new cmds dead': src used pyrogram.enums while the
running client is kittygram — kittygram's parser rejects pyrogram's
ParseMode enum (ValueError: Invalid parse mode). Import from here.
"""
try:
    from kittygram import filters, enums
    from kittygram.types import (
        Message, InlineKeyboardMarkup, CallbackQuery,
    )
    from kittygram.types import InlineKeyboardButton as _BTN
    _COLORED = True
except ImportError:
    from pyrogram import filters, enums
    from pyrogram.types import (
        Message, InlineKeyboardMarkup, CallbackQuery,
    )
    from pyrogram.types import InlineKeyboardButton as _BTN
    _COLORED = False


def IKB(text, callback_data=None, url=None, style=None, **kwargs):
    """Colored-button wrapper (mirrors riruru.py). style=success/danger/primary."""
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if _COLORED and style is not None:
        kwargs["style"] = style
    return _BTN(text, **kwargs)


HTML = enums.ParseMode.HTML
