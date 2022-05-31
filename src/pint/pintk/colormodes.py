""" Color modes for graphed pintk TOAs. """
import numpy as np
import matplotlib

import pint.logging
from loguru import logger as log

named_colors = {
    "red": "red",
    "green": "green",  # this is any green bank obs
    "cyan": "cyan",
    "blue": "blue",
    "burnt orange": "#CC6600",  # burnt orange
    "brown": "#362511",  # brown
    "indigo": "#4B0082",  # indigo
    "purple": "#7C11AD",  # purple
    "dark blue": "#00006B",  # dark blue
    "light green": "#52E222",  # light green
    "dark green": "#006D35",  # dark green
    "light blue": "#0091AE",  # light blue
    "dark red": "#8C0000",  # dark red
    "magenta": "#E4008D",  # magenta
    "black": "black",
    "grey": "#7E7E7E",  # grey
    "light grey": "#E2E2E1",  # light grey
    "yellow-ish": "#FFF133",  # yellow-ish
    "orange": "#FFA500",
}


class ColorMode:
    """Base Class for color modes."""

    def __init__(self, application):
        self.application = application  # PLKWidget for pintk

    def displayInfo(self):
        raise NotImplementedError

    def plotColorMode(self):
        raise NotImplementedError


class DefaultMode(ColorMode):
    """
    A class to manage the Default color mode, where TOAs are colored
    blue as a default and red if jumped.
    """

    def __init__(self, application):
        super(DefaultMode, self).__init__(application)
        self.mode_name = "default"

    def displayInfo(self):
        print(
            '"Default" mode selected\n'
            + "  Blue   = default color\n"
            + "  Orange = selected TOAs\n"
            + "  Red    = jumped TOAs\n"
        )

    def plotColorMode(self):
        """
        Plots application's residuals in proper color scheme.
        """
        if self.application.yerrs is None:
            self.application.plkAxes.scatter(
                self.application.xvals[~self.application.selected],
                self.application.yvals[~self.application.selected],
                marker=".",
                color="blue",
            )
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.jumped],
                self.application.yvals[self.application.jumped],
                marker=".",
                color="red",
            )
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.selected],
                self.application.yvals[self.application.selected],
                marker=".",
                color="orange",
            )
        else:
            self.application.plotErrorbar(~self.application.selected, color="blue")
            self.application.plotErrorbar(self.application.jumped, color="red")
            self.application.plotErrorbar(self.application.selected, color="orange")


class FreqMode(ColorMode):
    """
    A class to manage the Frequency color mode, where TOAs are colored
    according to their frequency.
    """

    def __init__(self, application):
        super(FreqMode, self).__init__(application)
        self.mode_name = "freq"

    def displayInfo(self):
        print(
            '"Frequency" mode selected\n'
            + "  Dark Red <  300 MHz\n"
            + "  Red      =  300-400  MHz\n"
            + "  Orange   =  400-500  MHz\n"
            + "  Yellow   =  500-700  MHz\n"
            + "  Green    =  700-1000 MHz\n"
            + "  Blue     = 1000-1800 MHz\n"
            + "  Indigo   = 1800-3000 MHz\n"
            + "  Black    = 3000-8000 MHz\n"
            + "  Grey     > 8000 MHz\n"
            + "  Brown is for selected TOAs\n"
        )

    def plotColorMode(self):
        """
        Plots application's residuals in proper color scheme.
        """

        colorGroups = [
            named_colors["dark red"],  # dark red
            named_colors["red"],  # red
            named_colors["orange"],  # orange
            named_colors["yellow-ish"],  # yellow-ish
            named_colors["green"],  # green
            named_colors["blue"],  # blue
            named_colors["indigo"],  # indigo
            named_colors["black"],  # black
            named_colors["grey"],  # grey
        ]
        highfreqs = [300.0, 400.0, 500.0, 700.0, 1000.0, 1800.0, 3000.0, 8000.0]

        freqGroups = []
        for ii, highfreq in enumerate(highfreqs):
            if ii == 0:
                freqGroups.append(
                    self.application.psr.all_toas.get_freqs().value < highfreq
                )
            else:
                freqGroups.append(
                    (self.application.psr.all_toas.get_freqs().value < highfreq)
                    & (
                        self.application.psr.all_toas.get_freqs().value
                        >= highfreqs[ii - 1]
                    )
                )
        freqGroups.append(
            self.application.psr.all_toas.get_freqs().value >= highfreqs[-1]
        )

        for index in range(len(freqGroups)):
            if self.application.yerrs is None:
                self.application.plkAxes.scatter(
                    self.application.xvals[freqGroups[index]],
                    self.application.yvals[freqGroups[index]],
                    marker=".",
                    color=colorGroups[index],
                )
            else:
                self.application.plotErrorbar(
                    freqGroups[index], color=colorGroups[index]
                )
        # The following is for selected TOAs
        if self.application.yerrs is None:
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.selected],
                self.application.yvals[self.application.selected],
                marker=".",
                color="#362511",  # brown
            )
        else:
            self.application.plotErrorbar(self.application.selected, color="#362511")


class NameMode(ColorMode):
    """
    A class to manage the Frequency color mode, where TOAs are colored
    according to their names in the TOA lines.
    """

    def __init__(self, application):
        super(NameMode, self).__init__(application)
        self.mode_name = "name"

    def displayInfo(self):
        print('"Name" mode selected\n' + "  Orange = selected TOAs\n")

    def plotColorMode(self):
        """
        Plots application's residuals in proper color scheme.
        """

        all_names = np.array(
            [f["name"] for f in self.application.psr.all_toas.get_flags()]
        )
        single_names = list(set(all_names))
        N = len(single_names)
        cmap = matplotlib.cm.get_cmap("brg")
        colorGroups = [matplotlib.colors.rgb2hex(cmap(v)) for v in np.linspace(0, 1, N)]
        colorGroups += ["orange"]

        freqGroups = []
        index = 0
        for name in single_names:
            index += 1
            freqGroups.append(all_names == name)
            index += 1

        for index in range(N):
            if self.application.yerrs is None:
                self.application.plkAxes.scatter(
                    self.application.xvals[freqGroups[index]],
                    self.application.yvals[freqGroups[index]],
                    marker=".",
                    color=colorGroups[index],
                )
            else:
                self.application.plotErrorbar(
                    freqGroups[index], color=colorGroups[index]
                )

        if self.application.yerrs is None:
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.selected],
                self.application.yvals[self.application.selected],
                marker=".",
                color=colorGroups[N],
            )
        else:
            self.application.plotErrorbar(
                self.application.selected, color=colorGroups[N]
            )


class ObsMode(ColorMode):
    """
    A class to manage the Observatory color mode, where TOAs are colored
    according to their observatory.
    """

    def __init__(self, application):
        super(ObsMode, self).__init__(application)
        self.mode_name = "obs"

    def get_obs_mapping(self):
        "This maps the obs names in the TOAs to our local subset"
        tmp_obs = self.application.psr.all_toas.observatories
        mapping = {}
        for oo in tmp_obs:
            if "stl" in oo:
                mapping[oo] = "space"
            elif oo.startswith("gb"):
                mapping[oo] = "gb"
            elif oo.startswith("jb"):
                mapping[oo] = "jodrell"
            elif "ncy" in oo:
                mapping[oo] = "nancay"
            else:
                mapping[oo] = oo if oo in self.obs_colors else "other"
        return mapping

    obs_colors = {
        "parkes": named_colors["red"],
        "gb": named_colors["green"],  # this is any green bank obs
        "jodrell": named_colors["cyan"],
        "arecibo": named_colors["blue"],
        "chime": named_colors["burnt orange"],
        "gmrt": named_colors["brown"],
        "vla": named_colors["indigo"],
        "effelsberg": named_colors["purple"],
        "fast": named_colors["dark blue"],
        "nancay": named_colors["light green"],
        "srt": named_colors["dark green"],
        "wsrt": named_colors["light blue"],
        "lofar": named_colors["dark red"],
        "lwa": named_colors["dark red"],
        "mwa": named_colors["dark red"],
        "meerkat": named_colors["magenta"],
        "barycenter": named_colors["black"],
        "geocenter": named_colors["grey"],
        "space": named_colors["light grey"],
        "other": named_colors["yellow-ish"],
    }

    obs_text = {
        "parkes": "  Parkes = red",
        "gb": "  Green Bank = green",
        "jodrell": "  Jodrell = cyan",
        "arecibo": "  Arecibo = blue",
        "chime": "  CHIME = burnt orange",
        "gmrt": "  GMRT = brown",
        "vla": "  VLA = indigo",
        "effelsberg": "  Effelsberg = purple",
        "fast": "  FAST = dark blue",
        "nancay": "  Nancay = light green",
        "srt": "  SRT = dark green",
        "wsrt": "  WSRT = light blue",
        "lofar": "  LOFAR = dark red",
        "lwa": "  LWA = dark red",
        "mwa": "  MWA = dark red",
        "meerkat": "  MeerKAT = magenta",
        "barycenter": "  barycenter = black",
        "geocenter": "  geocenter = grey",
        "space": "  satellite = light grey",
        "other": "  other = yellow-ish",
    }

    def displayInfo(self):
        outstr = '"Observatory" mode selected\n'
        for obs in self.get_obs_mapping().values():
            outstr += self.obs_text[obs] + "\n"
        outstr += "  selected = orange\n"
        print(outstr)

    def plotColorMode(self):
        """
        Plots application's residuals in proper color scheme.
        """
        obsmap = self.get_obs_mapping()
        alltoas = self.application.psr.all_toas
        for obs, ourobs in obsmap.items():
            # group toa indices by observatory
            toas = alltoas.get_obss() == obs
            color = self.obs_colors[ourobs]
            if self.application.yerrs is None:
                self.application.plkAxes.scatter(
                    self.application.xvals[toas],
                    self.application.yvals[toas],
                    marker=".",
                    color=color,
                )
            else:
                self.application.plotErrorbar(toas, color=color)
        # Now handle the selected TOAs
        if self.application.yerrs is None:
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.selected],
                self.application.yvals[self.application.selected],
                marker=".",
                color="orange",
            )
        else:
            self.application.plotErrorbar(self.application.selected, color="orange")


class JumpMode(ColorMode):
    """
    A class to manage the Jump color mode, where TOAs are colored
    according to their jump.
    """

    def __init__(self, application):
        super(JumpMode, self).__init__(application)
        self.mode_name = "jump"

    def get_jumps(self):
        if self.application.psr.fitted:
            model = self.application.psr.postfit_model
        else:
            model = self.application.psr.prefit_model
        return model.get_jump_param_objects()

    jump_colors = named_colors

    def displayInfo(self):
        outstr = '"Jump" mode selected\n'
        for jumpnum, jump in enumerate(self.get_jumps()):
            # only use the number of colors - 1 to preserve orange for selected
            color_number = jumpnum % (len(self.jump_colors) - 1)
            color_name = list(self.jump_colors)[color_number]
            outstr += f"{jump.name}"
            if jump.key is not None:
                outstr += f" {jump.key}"
            if jump.key_value is not None:
                outstr += " " + " ".join(jump.key_value)
            outstr += f" = {color_name}\n"
        outstr += "  selected = orange\n"
        print(outstr)

    def plotColorMode(self):
        """
        Plots application's residuals in proper color scheme.
        """
        alltoas = self.application.psr.all_toas
        for jumpnum, jump in enumerate(self.get_jumps()):
            color_number = jumpnum % (len(self.jump_colors) - 1)
            color_name = list(self.jump_colors)[color_number]
            toas = jump.select_toa_mask(alltoas)
            color = self.jump_colors[color_name]
            # group toa indices by jump
            if self.application.yerrs is None:
                self.application.plkAxes.scatter(
                    self.application.xvals[toas],
                    self.application.yvals[toas],
                    marker=".",
                    color=color,
                )
            else:
                self.application.plotErrorbar(toas, color=color)
        # Now handle the selected TOAs
        if self.application.yerrs is None:
            self.application.plkAxes.scatter(
                self.application.xvals[self.application.selected],
                self.application.yvals[self.application.selected],
                marker=".",
                color="orange",
            )
        else:
            self.application.plotErrorbar(self.application.selected, color="orange")
