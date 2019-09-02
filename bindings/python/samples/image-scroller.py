#!/usr/bin/env python
import time
from samplebase import SampleBase
from PIL import Image


class ImageScroller(SampleBase):
    def __init__(self, *args, **kwargs):
        super(ImageScroller, self).__init__(*args, **kwargs)
        self.parser.add_argument("-i", "--image", help="The image to display", default="../../../examples-api-use/runtext.ppm")

    def run(self):
        if not 'image' in self.__dict__:
            self.image = Image.open(self.args.image).convert('RGB')
#        self.image.resize((self.matrix.width, self.matrix.height), Image.ANTIALIAS)
        image = self.image # .resize((self.matrix.width, self.matrix.height), Image.ANTIALIAS)

        double_buffer = self.matrix.CreateFrameCanvas()
        img_width, img_height = image.size

        # let's scroll
        xpos = 0
        while True:
            xpos += 1
            if (xpos >= 32):
                xpos = 0

            double_buffer.Clear()
            double_buffer.SetImage(image, -xpos)
            double_buffer.SetImage(image, -xpos + 32)

            double_buffer = self.matrix.SwapOnVSync(double_buffer)
            time.sleep(0.1)

# Main function
# e.g. call with
#  sudo ./image-scroller.py --chain=4
# if you have a chain of four
if __name__ == "__main__":
    image_scroller = ImageScroller()
    if (not image_scroller.process()):
        image_scroller.print_help()
