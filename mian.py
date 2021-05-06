import datetime

from PIL import ImageGrab
import numpy as np
import cv2
from win32api import GetSystemMetrics

import multiprocessing
import argparse
import tempfile
import queue
import sys

import sounddevice as sd
import soundfile as sf
import numpy
import os

assert numpy

finished = 0

def recScreen():

    whd = GetSystemMetrics(0)
    hei = GetSystemMetrics(1)

    Filename = datetime.datetime.now().strftime('%Y-%m-%d--%H_%M_%S.mp4')
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    captured_vid = cv2.VideoWriter(Filename, fourcc, 10, (whd, hei))

    while True:
        img = ImageGrab.grab(bbox=(0, 0, whd, hei))
        img_np = np.array(img)
        img_final = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        cv2.imshow('SuperRec', img_final)
        captured_vid.write(img_final)

        if cv2.waitKey(10) == ord('q'):
            break


def recAudio():
    def int_or_str(text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        'filename', nargs='?', metavar='FILENAME',
        help='audio file to store recording to')
    parser.add_argument(
        '-d', '--device', type=int_or_str,
        help='input device (numeric ID or substring)')
    parser.add_argument(
        '-r', '--samplerate', type=int, help='sampling rate')
    parser.add_argument(
        '-c', '--channels', type=int, default=1, help='number of input channels')
    parser.add_argument(
        '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
    args = parser.parse_args(remaining)

    q = queue.Queue()

    def callback(indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    try:
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info['default_samplerate'])
        if args.filename is None:
            args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                            suffix='.wav', dir='')

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(args.filename, mode='x', samplerate=args.samplerate,
                          channels=args.channels, subtype=args.subtype) as file:
            with sd.InputStream(samplerate=args.samplerate, device=args.device,
                                channels=args.channels, callback=callback):
                while True:
                    file.write(q.get())
    except KeyboardInterrupt:
        print('\nRecording finished: ' + repr(args.filename))
        parser.exit(0)
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))





process1 = multiprocessing.Process(target=recScreen)
process2 = multiprocessing.Process(target=recAudio)

if __name__ == '__main__':
    process1.start()
    process2.start()
    # process1.join

    while True:
        if process1.is_alive() == False:
            process2.terminate()
            break
