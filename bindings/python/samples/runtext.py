#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time


import zmq
class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
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
        font = graphics.Font()
        font.LoadFont("../../../fonts/clR6x12.bdf")
        textColor = graphics.Color(*list(map(int, self.args.color.split(","))))
        pos = offscreen_canvas.width

        my_text = ''

        col = textColor

        while True:
            socks = dict(self.poller.poll(5))
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                my_text = self.socket.recv_json()
                if my_text.startswith('/'):
                    if my_text == '/stop':
                        my_text = ''
                    if my_text.startswith('/col'):
                        col_regex = r'''/col\((\d+,\d+,\d+)\) (.*)'''
                        import re
                        res = re.search(col_regex, my_text)
                        try:
                            col = graphics.Color(*list(map(int, res.group(1).split(","))))
                            my_text = res.group(2)
                        except Exception as e:
                            print(e)
                            my_text = ''
                            col = textColor
                else:
                    col = textColor


            offscreen_canvas.Clear()
            len = graphics.DrawText(offscreen_canvas, font, pos, 9, col, my_text)
            pos -= 1
            if (pos + len < 0):
                pos = offscreen_canvas.width

            time.sleep(0.05)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.print_help()
