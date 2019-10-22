#!/usr/bin/env python3
"""
    This file is part of cencro.
    cencro is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    cencro is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with cencro. If not, see <http://www.gnu.org/licenses/>.

    Author: Steve Göring
"""
import os
import sys
import shutil
import json
import logging
import subprocess


formatter = logging.Formatter(
    fmt='%(levelname)s: %(message)s'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

# \033[1;30m - black
# \033[1;31m - red
# \033[1;32m - green
# \033[1;33m - yellow
# \033[1;34m - blue
# \033[1;35m - magenta
# \033[1;36m - cyan
# \033[1;37m - white

logging.addLevelName(logging.CRITICAL, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))
logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.DEBUG, "\033[1;35m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
logging.basicConfig(level=logging.DEBUG)


def assert_file(filename, error_msg):
    if not os.path.isfile(filename):
        logging.error(error_msg)
        raise Exception()


def shell_call(call):
    """
    Run a program via system call and return stdout + stderr.
    @param call programm and command line parameter list, e.g ["ls", "/"]
    @return stdout and stderr of programm call
    """
    try:
        output = subprocess.check_output(call, universal_newlines=True, shell=True)
    except Exception as e:
        output = str(e.output)
    return output


def ffprobe(filename):
    """ run ffprobe to get some information of a given video file
    """
    if shutil.which("ffprobe") is None:
        raise Exception("you need to have ffprobe installed, please read README.md.")

    if not os.path.isfile(filename):
        raise Exception("{} is not a valid file".format(filename))

    cmd = "ffprobe -show_format -select_streams v:0 -show_streams -of json {filename} 2>/dev/null".format(filename=filename)

    res = shell_call(cmd).strip()

    if len(res) == 0:
        raise Exception("{} is somehow not valid, so ffprobe could not extract anything".format(filename))

    res = json.loads(res)

    needed = {"pix_fmt": "unknown",
              "bits_per_raw_sample": "unknown",
              "width": "unknown",
              "height": "unknown",
              "avg_frame_rate": "unknown",
              "codec_name": "unknown"
             }
    for stream in res["streams"]:
        for n in needed:
            if n in stream:
                needed[n] = stream[n]
                if n == "avg_frame_rate":  # convert framerate to numeric integer value
                    needed[n] = round(eval(needed[n]))
    needed["bitrate"] = res.get("format", {}).get("bit_rate", -1)
    needed["codec"] = needed["codec_name"]

    return needed


def get_basename(filename):
    return os.path.splitext(filename)[0]


def flat_name(filename):
    return filename.replace("../", "").replace("/", "_").replace("./", "").replace(".", "")
