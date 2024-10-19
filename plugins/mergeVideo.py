import asyncio
import os
import time

from bot import (LOGGER, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, delete_all, formatDB,
                 gDict, queueDB)
from config import Config
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helpers.display_progress import Progress
from helpers.ffmpeg_helper import MergeSub, MergeVideo, take_screen_shot
from helpers.rclone_upload import rclone_driver, rclone_upload
from helpers.uploader import uploadVideo
from helpers.utils import UserSettings
from PIL import Image
from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.types import CallbackQuery

async def mergeNow(c: Client, cb: CallbackQuery, new_file_name: str):
    omess = cb.message.reply_to_message
    vid_list = list()
    sub_list = list()
    sIndex = 0
    await cb.message.edit("⭕ Processing...")
    duration = 0
    list_message_ids = queueDB.get(cb.from_user.id)["videos"]
    list_message_ids.sort()
    list_subtitle_ids = queueDB.get(cb.from_user.id)["subtitles"]
    LOGGER.info(Config.IS_PREMIUM)
    LOGGER.info(f"Videos: {list_message_ids}")
    LOGGER.info(f"Subs: {list_subtitle_ids}")
    
    if list_message_ids is None:
        await cb.answer("Queue Empty", show_alert=True)
        await cb.message.delete(True)
        return
    
    if not os.path.exists(f"downloads/{str(cb.from_user.id)}/"):
        os.makedirs(f"downloads/{str(cb.from_user.id)}/")
    
    input_ = f"downloads/{str(cb.from_user.id)}/input.txt"
    all = len(list_message_ids)
    n = 1
    
    for i in await c.get_messages(chat_id=cb.from_user.id, message_ids=list_message_ids):
        media = i.video or i.document
        await cb.message.edit(f"📥 Starting Download of ... `{media.file_name}`")
        LOGGER.info(f"📥 Starting Download of ... {media.file_name}")
        await asyncio.sleep(5)
        file_dl_path = None
        sub_dl_path = None
        
        try:
            c_time = time.time()
            prog = Progress(cb.from_user.id, c, cb.message)
            file_dl_path = await c.download_media(
                message=media,
                file_name=f"downloads/{str(cb.from_user.id)}/{str(i.id)}/vid.mkv",
                progress=prog.progress_for_pyrogram,
                progress_args=(f"🚀 Downloading: `{media.file_name}`", c_time, f"\n**Downloading: {n}/{all}**"),
            )
            n += 1
            if gDict[cb.message.chat.id] and cb.message.id in gDict[cb.message.chat.id]:
                return
            await cb.message.edit(f"Downloaded Successfully ... `{media.file_name}`")
            LOGGER.info(f"Downloaded Successfully ... {media.file_name}")
            await asyncio.sleep(5)
        except UnknownError as e:
            LOGGER.info(e)
            pass
        except Exception as downloadErr:
            LOGGER.info(f"Failed to download Error: {downloadErr}")
            queueDB.get(cb.from_user.id)["video"].remove(i.id)
            await cb.message.edit("❗File Skipped!")
            await asyncio.sleep(4)
            continue

        # Handle Subtitles
        if list_subtitle_ids[sIndex] is not None:
            a = await c.get_messages(
                chat_id=cb.from_user.id, message_ids=list_subtitle_ids[sIndex]
            )
            sub_dl_path = await c.download_media(
                message=a,
                file_name=f"downloads/{str(cb.from_user.id)}/{str(a.id)}/",
            )
            LOGGER.info(f"Got sub: {a.document.file_name}")
            file_dl_path = await MergeSub(file_dl_path, sub_dl_path, cb.from_user.id)
            LOGGER.info("Added subs")
        sIndex += 1

        # Validate Duration and Add to List
        metadata = extractMetadata(createParser(file_dl_path))
        try:
            if metadata.has("duration"):
                duration += metadata.get("duration").seconds
            vid_list.append(f"file '{file_dl_path}'")
        except Exception as e:
            LOGGER.error(f"Error extracting metadata: {e}")
            await delete_all(root=f"downloads/{str(cb.from_user.id)}")
            queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
            formatDB.update({cb.from_user.id: None})
            await cb.message.edit("⚠️ Video is corrupted")
            return

    # Ensure No Duplicate Files
    vid_list = list(dict.fromkeys(vid_list))

    LOGGER.info(f"Trying to merge videos for user {cb.from_user.id}")
    await cb.message.edit(f"🔀 Trying to merge videos ...")
    with open(input_, "w") as _list:
        _list.write("\n".join(vid_list))

    # Merge videos using FFmpeg with timestamp handling
    merged_video_path = await MergeVideo(
        input_file=input_,
        user_id=cb.from_user.id,
        message=cb.message,
        format_="mkv",
        extra_options="-fflags +genpts -r 30 -vsync vfr"  # Keep this if MergeVideo accepts it
    )

    if merged_video_path is None:
        await cb.message.edit("❌ Failed to merge video!")
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    try:
        await cb.message.edit("✅ Successfully Merged Video!")
    except MessageNotModified:
        await cb.message.edit("Successfully Merged Video! ✅")

    LOGGER.info(f"Video merged for: {cb.from_user.first_name}")
    await asyncio.sleep(3)

    file_size = os.path.getsize(merged_video_path)
    os.rename(merged_video_path, new_file_name)
    await cb.message.edit(f"🔄 Renamed Merged Video to\n **{new_file_name.rsplit('/', 1)[-1]}**")
    await asyncio.sleep(3)
    merged_video_path = new_file_name

    # Handle Upload
    if UPLOAD_TO_DRIVE[f"{cb.from_user.id}"]:
        await rclone_driver(omess, cb, merged_video_path)
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    if file_size > 2044723200 and Config.IS_PREMIUM is False:
        await cb.message.edit(
            f"Video is Larger than 2GB, Can't Upload,\n\nTell {Config.OWNER_USERNAME} to add premium account for 4GB uploads"
        )
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return

    if Config.IS_PREMIUM and file_size > 4241280205:
        await cb.message.edit(
            f"Video is Larger than 4GB, Can't Upload,\n\nTell {Config.OWNER_USERNAME} to die with the premium account"
        )
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        return
    
    upload_mode = True # True for document, False for video


    await cb.message.edit("🎥 Extracting Video Data ...")
    duration = 1
    try:
        metadata = extractMetadata(createParser(merged_video_path))
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as er:
        await delete_all(root=f"downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("⭕ Merged Video is corrupted")
        return

    try:
        user = UserSettings(cb.from_user.id, cb.from_user.first_name)
        thumb_id = user.thumbnail
        if thumb_id is None:
            raise Exception
        video_thumbnail = f"downloads/{str(cb.from_user.id)}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=video_thumbnail)
    except Exception as err:
        LOGGER.info("Generating thumbnail")
        video_thumbnail = await take_screen_shot(merged_video_path, f"downloads/{str(cb.from_user.id)}", (duration / 2))

    width = 1280
    height = 720
    try:
        thumb = extractMetadata(createParser(video_thumbnail))
        height = thumb.get("height")
        width = thumb.get("width")
        img = Image.open(video_thumbnail)
        if width > height:
            img.resize((320, height))
        elif height > width:
            img.resize((width, 320))
        img.convert("RGB")
        img.save(video_thumbnail, "JPEG")
    except:
        video_thumbnail = None

    await cb.message.edit("✅ Merged Video Uploaded Successfully!")
    # Determine the upload mode (whether to upload as a document or a video)

# Fix the uploadVideo function call
    await uploadVideo(
    c,                      # pyrogram client
    cb,                     # CallbackQuery object
    merged_video_path,       # Path to the merged video
    width,                   # Video width
    height,                  # Video height
    duration,                # Duration of the video
    video_thumbnail,         # Path to the video thumbnail
    file_size,               # Size of the merged video file
    upload_mode              # Upload as document or video
)


    await delete_all(root=f"downloads/{str(cb.from_user.id)}")
    queueDB.update({cb.from_user.id: {"videos": [], "subtitles": [], "audios": []}})
    formatDB.update({cb.from_user.id: None})
    return
