#!/usr/bin/env python

import queue
import time

import zmq

from rgbmatrix import graphics
from samplebase import SampleBase

animation_queue = queue.Queue(maxsize=10)

class Tick:
    def __init__(self):
        self.reset()

    def reset(self):
        self._t_start = time.time()

    def tick(self):
        return 1000 * (time.time() - self._t_start)

    def sleep_to_next_msec(self, msec):
        """ Sleep until the next modulo. """
        remainder = msec - (self.tick() % msec)
        time.sleep(remainder / 1000.)


class Animation:
    def __init__(self, *args, **kwargs):
        pass

    def step(self):
        """ Execute step and return True when the animation is finished. """
        return True

class RunText(Animation):
    def __init__(self, text, color, num_times, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.font = graphics.Font()
        self.font.LoadFont("../../../fonts/clR6x12.bdf")
        self.textColor = graphics.Color(*color)
        self.pos = None
        self.num_times = num_times

    def draw(self, canvas, tick):
        if self.pos is None:
            self.pos = canvas.width
        l = graphics.DrawText(canvas, self.font, self.pos, 8, self.textColor, self.text)
        self.pos -= 1
        if (self.pos + l < 0):
            self.num_times -= 1
            if self.num_times == 0:
                return True
            self.pos = canvas.width


class FullFlicker(Animation):
    def draw(self, canvas, tick):
        if tick % 100 > 30:
            canvas.Fill(255, 255, 255)
        else:
            canvas.Clear()
        if tick > 1000:
            canvas.Clear()
        if tick > 1200:
            return True

def parse_command(command):
    print(command)
    if command == '/flicker':
        return FullFlicker()
    if command.startswith('/text '):
        return RunText(command[5:], (200, 200, 0), 1)
    if command.startswith('/rep '):
        rep, num, *rest = command.split()
        try:
            return RunText(' '.join(rest), (250, 0, 250), int(num))
        except:
            return FullFlicker()


class Animator(SampleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("--color", help="Comma separated RGB value", default="120,30,30")
        self.parser.add_argument("--socket", help="Socket")

    def run(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect(self.args.socket)
        self.socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        offscreen_canvas = self.matrix.CreateFrameCanvas()

        tick = Tick()

        current_animation = None

        while True:
            socks = dict(self.poller.poll(5))
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                my_text = self.socket.recv_json()
                animation_queue.put(parse_command(my_text))

            if not current_animation:
                try:
                    current_animation = animation_queue.get(block=False, timeout=0)
                    tick.reset()
                except queue.Empty:
                    pass
#               if my_text.startswith('/'):
#                   if my_text == '/stop':
#                       my_text = ''
#                   if my_text.startswith('/col'):
#                       col_regex = r'''/col\((\d+,\d+,\d+)\) (.*)'''
#                       import re
#                       res = re.search(col_regex, my_text)
#                       try:
#                           col = graphics.Color(*list(map(int, res.group(1).split(","))))
#                           my_text = res.group(2)
#                       except Exception as e:
#                           print(e)
#                           my_text = ''
#                           col = textColor
#               else:
#                   col = textColor
            if current_animation:
                offscreen_canvas.Clear()

                ret = current_animation.draw(offscreen_canvas, tick.tick())
                if ret:
                    current_animation = None
    #            len = graphics.DrawText(offscreen_canvas, font, pos, 9, col, my_text)
    #            pos -= 1
    #            if (pos + len < 0):
    #                pos = offscreen_canvas.width

            tick.sleep_to_next_msec(50)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)


# Main function
if __name__ == "__main__":
    run_text = Animator()
    if (not run_text.process()):
        run_text.print_help()
