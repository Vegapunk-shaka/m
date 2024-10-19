import asyncio
import subprocess
import shutil
import os
import time
import ffmpeg
from pyrogram.types import CallbackQuery
from config import Config
from pyrogram.types import Message
from __init__ import LOGGER
from helpers.utils import get_path_size


async def MergeVideo(input_file: str, user_id: int, message: Message, format_: str):
    """
    This is for Merging Videos Together!
    :param `input_file`: input.txt file's location.
    :param `user_id`: Pass user_id as integer.
    :param `message`: Pass Editable Message for Showing FFmpeg Progress.
    :param `format_`: Pass File Extension.
    :return: This will return Merged Video File Path
    """
    output_vid = f"downloads/{str(user_id)}/[@yashoswalyo].{format_.lower()}"
    file_generator_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", input_file,
        "-map", "0",
        "-c", "copy",
        output_vid,
    ]
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *file_generator_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except NotImplementedError:
        await message.edit(
            text="Unable to Execute FFmpeg Command! Got `NotImplementedError` ...\n\nPlease run bot in a Linux/Unix Environment."
        )
        await asyncio.sleep(10)
        return None
    await message.edit("Merging Video Now ...\n\nPlease Keep Patience ...")
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    LOGGER.info(output_vid)
    if os.path.exists(output_vid):
        return output_vid
    else:
        return None


async def MergeSub(filePath: str, subPath: str, user_id):
    """
    This is for Merging Video + Subtitle Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitle file.
    - `user_id`: To get parent directory.

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    muxcmd = [
        "ffmpeg",
        "-hide_banner",
        "-i", filePath,
        "-i", subPath,
        "-map", "0:v:0",
        "-map", "0:a:?",
        "-map", "0:s:?",
        "-map", "1:s"
    ]
    videoData = ffmpeg.probe(filename=filePath)
    videoStreamsData = videoData.get("streams")
    subTrack = 0
    for stream in videoStreamsData:
        if stream["codec_type"] == "subtitle":
            subTrack += 1
    muxcmd.extend([
        f"-metadata:s:s:{subTrack}", f"title=Track {subTrack + 1} - tg@yashoswalyo",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "srt",
        f"./downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"
    ])
    LOGGER.info("Muxing subtitles")
    subprocess.call(muxcmd)
    orgFilePath = shutil.move(
        f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv", filePath
    )
    return orgFilePath


def MergeSubNew(filePath: str, subPath: str, user_id, file_list):
    """
    This method is for Merging Video + Subtitle(s) Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitle file.
    - `user_id`: To get parent directory.
    - `file_list`: List of all input files

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    muxcmd = ["ffmpeg", "-hide_banner"]
    videoData = ffmpeg.probe(filename=filePath)
    videoStreamsData = videoData.get("streams")
    subTrack = 0
    for stream in videoStreamsData:
        if stream["codec_type"] == "subtitle":
            subTrack += 1
    for i in file_list:
        muxcmd.extend(["-i", i])
    muxcmd.extend([
        "-map", "0:v:0",
        "-map", "0:a:?",
        "-map", "0:s:?"
    ])
    for j in range(1, len(file_list)):
        muxcmd.extend([
            "-map", f"{j}:s",
            f"-metadata:s:s:{subTrack}", f"title=Track {subTrack + 1} - tg@yashoswalyo"
        ])
        subTrack += 1
    muxcmd.extend([
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "srt",
        f"./downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"
    ])
    LOGGER.info("Sub muxing")
    subprocess.call(muxcmd)
    return f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"


def MergeAudio(videoPath: str, files_list: list, user_id):
    LOGGER.info("Generating Mux Command")
    muxcmd = ["ffmpeg", "-hide_banner"]
    videoData = ffmpeg.probe(filename=videoPath)
    videoStreamsData = videoData.get("streams")
    audioTracks = 0
    for i in files_list:
        muxcmd.extend(["-i", i])
    muxcmd.extend(["-map", "0:v:0", "-map", "0:a:?"])
    audioTracks = 0
    for stream in videoStreamsData:
        if stream["codec_type"] == "audio":
            muxcmd.extend([f"disposition:a:{audioTracks}", "0"])
            audioTracks += 1
    fAudio = audioTracks
    for j in range(1, len(files_list)):
        muxcmd.extend([
            "-map", f"{j}:a",
            f"-metadata:s:a:{audioTracks}", f"title=Track {audioTracks + 1} - tg@yashoswalyo"
        ])
        audioTracks += 1
    muxcmd.extend([
        f"-disposition:s:a:{fAudio}", "default",
        "-map", "0:s:?",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "copy",
        f"downloads/{str(user_id)}/[@yashoswalyo]_export.mkv"
    ])
    LOGGER.info(muxcmd)
    process = subprocess.call(muxcmd)
    LOGGER.info(process)
    return f"downloads/{str(user_id)}/[@yashoswalyo]_export.mkv"


async def cult_small_video(video_file, output_directory, start_time, end_time, format_):
    """
    Function to cut small clips from a video.
    """
    # Convert start_time and end_time to HH:MM:SS format
    start_time = time.strftime('%H:%M:%S', time.gmtime(start_time))
    end_time = time.strftime('%H:%M:%S', time.gmtime(end_time))

    out_put_file_name = os.path.join(output_directory, f"{round(time.time())}.{format_.lower()}")

    file_generator_command = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", video_file,
        "-to", str(end_time),
        "-c:v", "copy",  # Copy video codec
        "-c:a", "copy",  # Copy audio codec
        out_put_file_name
    ]

    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    else:
        return None


async def take_screen_shot(video_file, output_directory, ttl):
    """
    This functions generates custom_thumbnail / Screenshot.

    Parameters:

    - `video_file`: Path to video file.
    - `output_directory`: Path where to save thumbnail
    - `ttl`: Timestamp to generate screenshot

    returns: This will return path of screenshot
    """
    out_put_file_name = os.path.join(output_directory, str(time.time()) + ".jpg")
    if video_file.upper().endswith(
        (
            "MKV", "MP4", "WEBM", "AVI", "MOV", "OGG", "WMV",
            "M4V", "TS", "MPG", "MTS", "M2TS", "3GP"
        )
    ):
        file_generator_command = [
            "ffmpeg",
            "-ss", str(ttl),
            "-i", video_file,
            "-vframes", "1",
            out_put_file_name,
        ]
        subprocess.call(file_generator_command)
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    else:
        return None
