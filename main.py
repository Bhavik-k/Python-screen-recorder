import datetime
from datetime import datetime

import moviepy.editor as mp
from PIL import ImageGrab
import numpy as np
import cv2
from win32api import GetSystemMetrics
import pyautogui

import multiprocessing
import argparse
import queue
import sys

import sounddevice as sd
import soundfile as sf
import numpy
assert numpy


Filename = datetime.now().strftime('%Y-%m-%d--%H_%M_')


Xs = [0,8,6,14,12,4,2,0]
Ys = [0,2,4,12,14,6,8,0]


def recScreen():

    whd = GetSystemMetrics(0)
    hei = GetSystemMetrics(1)

    global Filename
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    captured_vid = cv2.VideoWriter(Filename+'.mp4', fourcc,20, (whd, hei))

    while True:
        ####
        img = pyautogui.screenshot()
        mouseX, mouseY = pyautogui.position()
        ####



        img = ImageGrab.grab(bbox=(0, 0, whd, hei))
        img_np = np.array(img)
        img_final = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)


        ####
        Xthis = [x + mouseX for x in Xs]
        Ythis = [y + mouseY for y in Ys]
        points = list(zip(Xthis, Ythis))
        points = np.array(points, 'int32')
        cv2.fillPoly(img_final, [points], color=[0, 0, 255])
        ####


        cv2.imshow('SuperRec', img_final)
        captured_vid.write(img_final)

        break
        if cv2.waitKey(30) == ord('q'):
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
            global Filename
            args.filename = Filename+'.wav'


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
    process2.start()
    process1.start()
    # process1.join()
    # process2.join()

    while True:
        if process1.is_alive() == False:
            process2.terminate()
            clip = mp.VideoFileClip (Filename+'.mp4')
            Audio = mp.AudioFileClip(Filename+'.wav')

            finalClip = clip.set_audio(Audio)

            finalClip.write_videofile('final' + Filename + '.mp4');
            break
