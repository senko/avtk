import os
import subprocess
import json

from .exceptions import NoMediaError

BASE_FLAGS = ['-hide_banner', '-v', 'error']
FFMPEG_FLAGS = BASE_FLAGS + ['-y']
FFMPEG_FLAGS_PROGRESS = FFMPEG_FLAGS + ['-progress', '-']
FFPROBE_FLAGS = BASE_FLAGS + ['-of', 'json']

SUBPROCESS_TIMEOUT = 5  # in seconds


def _find_ffmpeg():
    path = os.getenv('FFMPEG_PATH')
    if not path:
        return 'ffmpeg'
    if not os.path.isfile(path):
        raise ValueError("Specified FFMpeg path is invalid: %s" % path)
    return path


def _find_ffprobe():
    path = os.getenv('FFPROBE_PATH')
    if not path:
        return 'ffprobe'
    if not os.path.isfile(path):
        raise ValueError("Specified FFprobe path is invalid: %s" % path)
    return path


def _prepare_ffmpeg_cmdline(args, progress=False):
    return (
        [_find_ffmpeg()] +
        (FFMPEG_FLAGS_PROGRESS if progress else FFMPEG_FLAGS) +
        args
    )


def _prepare_ffprobe_cmdline(args):
    return [_find_ffprobe()] + FFPROBE_FLAGS + args


def _run_simple(cmdline, quick=False, text=True):
    res = subprocess.run(
        cmdline,
        capture_output=True,
        text=text,
        timeout=SUBPROCESS_TIMEOUT if quick else None,
        env=dict(
            PATH=os.environ['PATH'],
            AV_LOG_FORCE_NOCOLOR='1'
        )
    )
    if res.returncode != 0:
        # FIXME - use logger to log the details and raise something sensible
        raise RuntimeError(res.stderr.strip())
    return res.stdout


def ffprobe(args, parse_json=True):
    try:
        output = _run_simple(_prepare_ffprobe_cmdline(args), quick=True)
    except RuntimeError as e:
        raise NoMediaError(e)

    return json.loads(output) if parse_json else output


def ffmpeg(args, quick=False, text=True):
    return _run_simple(
        _prepare_ffmpeg_cmdline(args, progress=False),
        quick=quick,
        text=text
    )
