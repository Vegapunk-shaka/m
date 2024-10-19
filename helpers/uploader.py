import os
import time
import asyncio
import ffmpeg

from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from helpers.display_progress import Progress
from bot import LOGCHANNEL, userBot
from config import Config
from __init__ import LOGGER


async def take_screen_shot(video_file, output_dir, ttl=1):
    """
    Generate a thumbnail from the video at a specific time (in seconds).
    """
    thumb_path = os.path.join(output_dir, f"thumb_{os.path.basename(video_file)}.jpg")
    try:
        (
            ffmpeg
            .input(video_file, ss=ttl)
            .output(thumb_path, vframes=1)
            .run(capture_stdout=True, capture_stderr=True)
        )
        if os.path.exists(thumb_path):
            return thumb_path
        return None
    except Exception as e:
        LOGGER.error(f"Failed to create thumbnail: {str(e)}")
        return None


async def uploadVideo(
    c: Client,
    cb: CallbackQuery,
    merged_video_path,
    width,
    height,
    duration,
    video_thumbnail,
    file_size,
    upload_mode: bool,
):
    """
    Upload a merged video or document to the user and log channel, with progress.
    """
    if Config.IS_PREMIUM:
        sent_ = None
        prog = Progress(cb.from_user.id, c, cb.message)
        async with userBot:
            if upload_mode is False:
                c_time = time.time()
                sent_: Message = await userBot.send_video(
                    chat_id=int(LOGCHANNEL),
                    video=merged_video_path,
                    height=height,
                    width=width,
                    duration=duration,
                    thumb=video_thumbnail,
                    caption=f"`{merged_video_path.rsplit('/',1)[-1]}`\n\nMerged for: {cb.from_user.mention}",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            else:
                c_time = time.time()
                sent_: Message = await userBot.send_document(
                    chat_id=int(LOGCHANNEL),
                    document=merged_video_path,
                    thumb=video_thumbnail,
                    caption=f"`{merged_video_path.rsplit('/',1)[-1]}`\n\nMerged for: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            if sent_ is not None:
                await c.copy_message(
                    chat_id=cb.message.chat.id,
                    from_chat_id=sent_.chat.id,
                    message_id=sent_.id,
                    caption=f"`{merged_video_path.rsplit('/',1)[-1]}`",
                )
    else:
        try:
            sent_ = None
            prog = Progress(cb.from_user.id, c, cb.message)
            if upload_mode is False:
                c_time = time.time()
                sent_: Message = await c.send_video(
                    chat_id=cb.message.chat.id,
                    video=merged_video_path,
                    height=height,
                    width=width,
                    duration=duration,
                    thumb=video_thumbnail,
                    caption=f"`{merged_video_path.rsplit('/',1)[-1]}`",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            else:
                c_time = time.time()
                sent_: Message = await c.send_document(
                    chat_id=cb.message.chat.id,
                    document=merged_video_path,
                    thumb=video_thumbnail,
                    caption=f"`{merged_video_path.rsplit('/',1)[-1]}`",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
        except Exception as err:
            LOGGER.info(err)
            await cb.message.edit("Failed to upload")
        if sent_ is not None:
            if Config.LOGCHANNEL is not None:
                media = sent_.video or sent_.document
                await sent_.copy(
                    chat_id=int(LOGCHANNEL),
                    caption=f"`{media.file_name}`\n\nMerged for: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                )


async def uploadFiles(
    c: Client,
    cb: CallbackQuery,
    up_path,
    n,
    all
):
    """
    Upload multiple files with progress tracking.
    """
    try:
        sent_ = None
        prog = Progress(cb.from_user.id, c, cb.message)
        c_time = time.time()
        sent_: Message = await c.send_document(
            chat_id=cb.message.chat.id,
            document=up_path,
            caption=f"`{up_path.rsplit('/',1)[-1]}`",
            progress=prog.progress_for_pyrogram,
            progress_args=(
                f"Uploading: `{up_path.rsplit('/',1)[-1]}`",
                c_time,
                f"\n**Uploading: {n}/{all}**"
            ),
        )
        if sent_ is not None:
            if Config.LOGCHANNEL is not None:
                media = sent_.video or sent_.document
                await sent_.copy(
                    chat_id=int(LOGCHANNEL),
                    caption=f"`{media.file_name}`\n\nExtracted by: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                )
    except Exception as err:
        LOGGER.error(f"Failed to upload file: {str(err)}")


async def mergeNow(c: Client, cb: CallbackQuery, merged_video_path: str):
    """
    Handles the merging process and uploads the resulting video.
    """
    if not os.path.exists(merged_video_path):
        await cb.message.edit("Merged video not found!")
        return

    try:
        # Extract video metadata
        video_info = ffmpeg.probe(merged_video_path)
        video_stream = next(s for s in video_info['streams'] if s['codec_type'] == 'video')
        
        width = video_stream['width']
        height = video_stream['height']
        duration = int(float(video_info['format']['duration']))
        file_size = os.path.getsize(merged_video_path)
        
        # Generate a thumbnail
        video_thumbnail = await take_screen_shot(merged_video_path, "./thumbnails/", ttl=1)

        # Set upload mode (video or document)
        upload_mode = False  # False for video, True for document

        # Upload the video
        await uploadVideo(
            c=c,
            cb=cb,
            merged_video_path=merged_video_path,
            width=width,
            height=height,
            duration=duration,
            video_thumbnail=video_thumbnail,
            file_size=file_size,
            upload_mode=upload_mode,
        )

        await cb.message.edit("Video merged and uploaded successfully!")

    except Exception as e:
        await cb.message.edit(f"Error: {str(e)}")
