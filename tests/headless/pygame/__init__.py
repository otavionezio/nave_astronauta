"""Pygame mínimo (Pillow) só para testes headless. Ver ../README.md."""
from PIL import Image, ImageDraw, ImageFont

SRCALPHA = 0x00010000
QUIT = KEYDOWN = KEYUP = MOUSEBUTTONDOWN = MOUSEBUTTONUP = MOUSEMOTION = MOUSEWHEEL = 0


class Surface(object):
    def __init__(self, size, flags=0):
        self.image = Image.new("RGBA", (int(size[0]), int(size[1])), (0, 0, 0, 255))

    def get_width(self):
        return self.image.width

    def get_height(self):
        return self.image.height

    def get_size(self):
        return self.image.size

    def fill(self, color):
        c = tuple(color) if len(color) == 4 else tuple(color) + (255,)
        self.image.paste(c, (0, 0, self.image.width, self.image.height))

    def blit(self, other, pos):
        self.image.alpha_composite(other.image, (int(pos[0]), int(pos[1])))


class _ImageModule(object):
    @staticmethod
    def load(path):
        s = Surface((1, 1))
        s.image = Image.open(path).convert("RGBA")
        return s

    @staticmethod
    def tobytes(surface, fmt="RGBA", flipped=False):
        img = surface.image.transpose(Image.FLIP_TOP_BOTTOM) if flipped else surface.image
        return img.convert("RGBA").tobytes()

    tostring = tobytes


class _Font(object):
    def __init__(self, name, size):
        try:
            self.font = ImageFont.load_default(size)
        except TypeError:
            self.font = ImageFont.load_default()

    def render(self, text, antialias, color, background=None):
        box = self.font.getbbox(text or " ")
        w, h = max(box[2] + 2, 1), max(box[3] + 2, 1)
        s = Surface((w, h))
        s.image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(s.image).text((0, 0), text, font=self.font, fill=tuple(color)[:3] + (255,))
        return s

    def size(self, text):
        box = self.font.getbbox(text or " ")
        return (box[2] + 2, box[3] + 2)

    def get_linesize(self):
        return self.font.getbbox("Ag")[3] + 2


class _FontModule(object):
    Font = _Font

    @staticmethod
    def init():
        pass


image = _ImageModule()
font = _FontModule()


class _Draw(object):
    @staticmethod
    def rect(surface, color, rect):
        x, y, w, h = [int(v) for v in rect]
        c = tuple(color) if len(color) == 4 else tuple(color) + (255,)
        surface.image.paste(c, (x, y, x + w, y + h))


draw = _Draw()
