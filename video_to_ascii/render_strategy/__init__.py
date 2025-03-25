from . import ascii_bw_strategy as bw
from . import ascii_color_strategy as color
from . import ascii_color_filled_strategy as filled
from . import adaptive_ascii_strategy as adaptive
from . import cinematic_ascii_strategy as cinematic

STRATEGIES = {
    "default": color.AsciiColorStrategy(),
    "ascii-color": color.AsciiColorStrategy(),
    "just-ascii": bw.AsciiBWStrategy(),
    "filled-ascii": filled.AsciiColorFilledStrategy(),
    "adaptive": adaptive.AdaptiveAsciiStrategy(),
    "cinematic": cinematic.CinematicAsciiStrategy()
}