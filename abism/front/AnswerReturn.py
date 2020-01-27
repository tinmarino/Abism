"""
    To pretty print the answer, may go to FrameText
    C'est le bordel !
"""

from threading import Thread, currentThread

from tkinter import *
from tkinter import font as tkFont
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas

# Front
from abism.front.util_front import skin
import abism.front.util_front as G

# Back
from abism.back import ImageFunction as IF
import abism.back.fit_template_function as BF
from abism.back.image import get_array_stat
import abism.back.util_back as W

# Plugin
from abism.util import log, get_root, get_state, abism_val, EA

# new
from abism.back.Strehl import get_equivalent_strehl_ratio


def tktext_insert_answer(self, answer, error=None, tags=None):
    """Insert an answer in a tktext"""
    # Get name
    stg = answer.text + ":\t"

    # Convert unit && Convert tag
    if not isinstance(answer.unit, (list, tuple)):
        answer.unit = answer.unit, answer.unit
    if not tags: tags = []

    # Get value and error
    if get_state().s_answer_unit == 'detector':
        stg += answer.str_detector()
        if error:
            stg += ' +/- ' + error.str_detector()
        stg += answer.unit[0]
    else:
        stg += answer.str_sky()
        if error:
            stg += ' +/- ' + error.str_sky()
        stg += answer.unit[1]

    # Add new line
    stg += "\n"

    # Insert
    self.insert(END, stg, tags)
Text.insert_answer = tktext_insert_answer


def tktext_insert_warnings(self):
    """Insert all warning from analyse in tk text widget"""
    stg = ''

    # Saturated
    if 'intensity' not in W.strehl:  # binary
        intensity = W.strehl["intensity0"] + W.strehl["intensity1"]
    else:
        intensity = W.strehl["intensity"]

    if intensity > get_root().header.non_linearity_level:
        if intensity > 1.0 * get_root().header.saturation_level:
            stg += "!!! SATURATED !!!  Strehl is UNRELIABLE\n"
        else:
            stg += "!!! NON-LINEAR Strehl may be  unreliable\n"

    # Undersampled
    is_undersampled = "sinf_pixel_scale" in vars(get_root().header)
    is_undersampled = is_undersampled and get_root().header.sinf_pixel_scale <= 0.01
    if is_undersampled:
        stg += "!!! UNDER-SAMPLED !!! Use FWHM\n (SR under-estimated)\n"

    # Binary too far
    if get_state().pick_type == "binary":
        max_dist = max(W.strehl["fwhm_x0"] + W.strehl["fwhm_x1"],
                       W.strehl["fwhm_y0"] + W.strehl["fwhm_y1"])
        sep = (W.strehl["x0"] - W.strehl["x1"])**2
        sep += (W.strehl["y0"] - W.strehl["y1"])**2
        sep = np.sqrt(sep)

        if max_dist*15 < sep:  # means too high separation
            stg += "Wide Binary\npick objects individually\n"

        if max_dist*3 > sep:  # means too high separation
            stg += "Tight Binary\nmay be unreliable\n"

    # Insert
    self.insert(END, stg, ['tag-important', 'tag-center'])
Text.insert_warnings = tktext_insert_warnings


def show_answer():  # CALLER
    """Draw && Print answer i.e. Image and Text"""
    plot_result()


def plot_result():
    """Discirminate according to pick"""
    pick = get_state().pick_type

    if pick == 'one':
        print_one(); return

    if pick in ('binary', 'tightbinary'):
        print_binary(); return

    if pick == 'ellipse':
        PlotEllipse(); return

    if pick == "stat":
        print_statistic(); return


def grid_button_change_coord():
    # Declare button info
    if get_state().s_answer_unit == "detector":
        s_button = u"\u21aa"+'To sky     '
        s_label = "In detector units"
    else:
        s_button = u"\u21aa"+'To detector'
        s_label = "In sky units"

    def callback():
        if get_state().s_answer_unit == 'detector':
            get_state().s_answer_unit = 'sky'
        else:
            get_state().s_answer_unit = 'detector'
        show_answer()

    button = Button(
        get_root().frame_answer, background='Khaki', borderwidth=1,
        text=s_button, **skin().button_dic,
        command=callback)

    label = Label(
        get_root().frame_answer,
        justify=LEFT, anchor="nw", **skin().fg_and_bg,
        text=s_label)

    # Grid Buttons
    button.grid(column=1, sticky="wnse")
    label.grid(column=0, sticky="wnse")


def print_one():
    # Pack fit type in Frame
    get_root().frame_answer.set_fit_type_text(get_state().fit_type)
    get_root().frame_answer.clear()

    # Button to change cord
    grid_button_change_coord()

    # <- Calculate Equivalent strehl2.2 and error
    strehl = get_state().get_answer(EA.STREHL) / 100
    wavelength = get_root().header.wavelength

    # Get equivalent Strehl ratio
    strehl_eq = get_equivalent_strehl_ratio(strehl, wavelength)

    # Save it
    get_state().add_answer(EA.STREHL_EQ, strehl_eq, unit=' %')

    # Get Error on equivalent strehl
    strehl_eq_err = get_state().get_answer(EA.ERR_STREHL)
    strehl_eq_err *= strehl_eq / (strehl * 100)

    # Save it
    get_state().add_answer(EA.ERR_STREHL_EQ, strehl_eq_err, unit=' %')


    # TODO move all preceding in back

    text = grid_text_answer()

    # Strehl
    text.insert_answer(
        get_state().get_answer_obj(EA.STREHL),
        error=get_state().get_answer_obj(EA.ERR_STREHL),
        tags=['tag-important'])

    # Equivalent Strehl Ratio
    text.insert_answer(
        get_state().get_answer_obj(EA.STREHL_EQ),
        error=get_state().get_answer_obj(EA.ERR_STREHL_EQ))


    # # Center (need to inverse)
    # line = AnswerImageSky(
    #     "Center x,y: ",
    #     (W.strehl["center_y"], W.strehl["center_x"]),
    #     MyFormat(W.strehl["center_y"], 3, "f") + " , " + MyFormat(W.strehl['center_x'], 3, "f"),
    #     "%s , %s" % (format_sky(W.strehl['center_ra'], W.strehl['center_dec']))
    #     )
    # W.tmp.lst.append(line)

    # FWHM
    text.insert_answer(get_state().get_answer_obj(EA.FWHM_ABE))


    # Photometry
    text.insert_answer(get_state().get_answer_obj(EA.PHOTOMETRY))

    # Background
    text.insert_answer(
        get_state().get_answer_obj(EA.BACKGROUND),
        error=get_state().get_answer_obj(EA.NOISE))

    # Signal / Noise ratio
    text.insert_answer(get_state().get_answer_obj(EA.SN))

    # Peak of detection
    text.insert_answer(get_state().get_answer_obj(EA.INTENSITY))

    # text.insert_answer(
    # W.tmp.lst.extend(answer_warning())

    # Warnings
    text.insert_warnings()

    # Disable edit
    text.configure(state=DISABLED)



def on_resize_text(event):
    log(5, 'Answer, Resize text:', event)
    event.widget.configure(tabs=(event.width/2, LEFT))


def grid_text_answer():
    """Grid formatted text answered
    Nobody can edit text, when it is disabled
    """
    # Create text
    text = Text(get_root().frame_answer, **skin().text_dic)

    # Configure Text
    text.bind("<Configure>", on_resize_text)
    text.tag_configure('tag-important', foreground=skin().color.important)
    text.tag_configure('tag-center', justify=CENTER)

    # Grid text
    text.grid(columnspan=2, sticky='nsew')

    return text



def PlotEllipse():
    """TODO clean + not working anymore due to W.tmp.lst"""
    rms = get_root().header.wavelength / 2/np.pi * \
        np.sqrt(-np.log(get_state().get_answer(EA.STREHL)/100))
    W.strehl["strehl2_2"] = 100 * np.exp(-(rms*2*np.pi/2.17)**2)
    # <- CAlculate Equivalent strehl2.2

    ########
    # BUTTON
    # to fill th ecolumn on th epossible space
    get_root().frame_answer.columnconfigure(0, weight=1)
    G.bu_answer_type = Button(
        get_root().frame_answer, text='useless', background='Khaki', borderwidth=1, width=9)
    G.lb_answer_type = Label(
        get_root().frame_answer, text="useless", justify=LEFT, anchor="nw", **skin().fg_and_bg)

    ############
    # IMAGE COORD
    if get_state().s_answer_unit == "detector":
        G.bu_answer_type["text"] = u"\u21aa"+'To sky     '
        G.bu_answer_type["command"] = lambda: PlotAnswer(unit="sky")
        G.lb_answer_type["text"] = "In detector units"

        W.tmp.lst = [
            ["Strehl: ", get_state().get_answer(EA.STREHL), MyFormat(
                get_state().get_answer(EA.STREHL), 1, "f") + " +/- " + MyFormat(get_state().get_answer(EA.ERR_STREHL), 1, "f") + " %"],
            ["Intensity: ", W.strehl["intensity"], MyFormat(
                W.strehl["intensity"], 1, "f") + " [adu]"],
            ["Background: ", get_state().get_answer(EA.BACKGROUND), MyFormat(
                get_state().get_answer(EA.BACKGROUND), 1, "f") + ' +/- ' + MyFormat(W.strehl['rms'], 1, "f") + "[adu]"],
            ["Photometry: ", W.strehl["my_photometry"], MyFormat(
                W.strehl["my_photometry"], 1, "f") + " [adu]"],
            #["S/N: "           , W.strehl["snr"]    ,MyFormat(W.strehl["snr"],1,"f") ],
            ["Eq. SR(2.17"+u"\u03bc" + "m): ", W.strehl["strehl2_2"],
                MyFormat(W.strehl["strehl2_2"], 1, "f") + " %"],
            ["Center x,y: ", (W.strehl["center_y"], W.strehl["center_x"]), MyFormat(
                W.strehl["center_y"], 3, "f") + " , " + MyFormat(W.strehl['center_x'], 3, "f")],  # need to inverse
        ]

    ##################
    # SKY COORD
    # including unit = sky :    not =  detector  get_state().s_answer_unit=="sky":
    else:
        G.bu_answer_type["text"] = u"\u21aa"+'To detector'
        G.bu_answer_type["command"] = lambda: PlotAnswer(unit="detector")
        G.lb_answer_type["text"] = "In sky units"

        ###
        # WCS
        try:
            # if len( W.hdulist[0].data.shape ) == 3: # if cube,  just cut the WCS object, see antoine
            #   my_wcs = ProjectWcs(get_root().header.wcs).all_pix2world( np.array([[ W.strehl["center_y"],W.strehl["center_x"] ]]), 0 )
            # else : # not cube
            my_wcs = get_root().header.wcs.all_pix2world(
                np.array([[W.strehl["center_y"], W.strehl["center_x"]]]), 0)
        except:
            import traceback
            traceback.print_exc()
            print("WARNING I did not manage to get WCS")
            my_wcs = np.array([[99, 99], [99, 99]])
        W.strehl["center_ra"], W.strehl["center_dec"] = my_wcs[0, 0], my_wcs[0, 1]

        W.tmp.lst = [
            ["Strehl: ", get_state().get_answer(EA.STREHL), "%.1f" %
                (get_state().get_answer(EA.STREHL)) + " +/- "+"%.1f" % get_state().get_answer(EA.ERR_STREHL)+" %"],
            ["Intensity: ", W.strehl["intensity"],  "%.1f" % (
                get_root().header.zpt-2.5*np.log10(W.strehl["intensity"]/get_root().header.exptime)) + " [mag]"],
            ["Background: ", get_state().get_answer(EA.BACKGROUND), "%.2f" % (get_root().header.zpt-2.5*np.log10(
                get_state().get_answer(EA.BACKGROUND)/get_root().header.exptime)) + '| rms: ' + "%.2f" % (get_root().header.zpt-2.5*np.log10(W.strehl['rms'])) + " [mag]"],
            ["Photometry: ", W.strehl["my_photometry"], "%.2f" % (
                get_root().header.zpt-2.5*np.log10(W.strehl["my_photometry"]/get_root().header.exptime)) + " [mag]"],
            #["S/N: "           , W.strehl["snr"]    ,MyFormat(W.strehl["snr"],1,"f")  ],
            ["Eq. SR 2.17"+u"\u03bc" + "m: ", W.strehl["strehl2_2"], "%.1f" %
                W.strehl["strehl2_2"] + "%"],
            ["Center RA,Dec: ", (W.strehl["center_ra"], W.strehl["center_dec"]),
             "%.8f" % W.strehl["center_ra"]+","+"%.8f" % W.strehl['center_dec']],
        ]  # label , variable, value as string


def print_binary():
    # Pack fit type in Frame
    get_root().frame_answer.set_fit_type_text(get_state().fit_type)
    get_root().frame_answer.clear()

    # Button to change cord
    grid_button_change_coord()

    # Some lookup due to move
    x0, x1, y0, y1 = W.strehl["x0"], W.strehl["x1"], W.strehl["y0"], W.strehl["y1"]
    dx0, dx1 = W.psf_fit[1]["x0"], W.psf_fit[1]["x1"]
    dy0, dy1 = W.psf_fit[1]["y0"], W.psf_fit[1]["y1"]

    # Get separation
    separation_dic = Separation(point=((x0, x1), (y0, y1)), err=((dx0, dx1), (dy0, dy1)))
    separation = separation_dic["dist"]
    sep_err = separation_dic["dist_err"]
    im_angle = separation_dic["im_angle"]
    sky_angle = separation_dic["sky_angle"]

    # STREHL
    # Some math TODO move
    phot0, phot1 = W.strehl["my_photometry0"], W.strehl["my_photometry1"]
    bessel_integer = get_root().header.wavelength * \
        10**(-6.) / np.pi / (get_root().header.pixel_scale/206265) / get_root().header.diameter
    bessel_integer = bessel_integer**2 * 4 * \
        np.pi / (1-(get_root().header.obstruction/100)**2)
    Ith0, Ith1 = phot0/bessel_integer, phot1/bessel_integer
    strehl0 = W.strehl["intensity0"] / Ith0 * 100
    strehl1 = W.strehl["intensity1"] / Ith1 * 100

    ##############
    # IMAGE COORD
    # TODO move that math to back

    text = grid_text_answer()

    # Fit type
    answer = get_state().add_answer(EA.BINARY, get_state().fit_type)
    text.insert_answer(answer)

    # Star 1
    answer = get_state().add_answer(EA.STAR1, (y0, x0))
    text.insert_answer(answer)

    # Star 2
    answer = get_state().add_answer(EA.STAR2, (y1, x1))
    text.insert_answer(answer)

    # Separation
    o_answer_separation = get_state().add_answer(EA.SEPARATION, separation)
    o_answer_err_separation = get_state().add_answer(EA.ERR_SEPARATION, sep_err)
    text.insert_answer(
        o_answer_separation,
        error=o_answer_err_separation)

    # Photometry 1
    answer = get_state().add_answer(EA.PHOTOMETRY1, phot0)
    text.insert_answer(answer)

    # Photometry 2
    answer = get_state().add_answer(EA.PHOTOMETRY2, phot1)
    text.insert_answer(answer)

    # Flux ratio
    answer = get_state().add_answer(EA.FLUX_RATIO, phot0 / phot1)
    text.insert_answer(answer)

    # TODO
    # ["Orientation: ", im_angle, "%.2f" % im_angle + u'\xb0'],

    # Strehl 1
    answer = get_state().add_answer(EA.STREHL1, strehl0, unit=' %')
    text.insert_answer(answer)

    # Strehl 2
    answer = get_state().add_answer(EA.STREHL2, strehl1, unit=' %')
    text.insert_answer(answer)

    # Warnings
    text.insert_warnings()

    # Disable edit
    text.configure(state=DISABLED)


def print_statistic():
    """Print statistics from a rectangle selection
    Also get them
    """
    # Get stat <- subarray
    W.r = IF.Order4(W.r)
    sub_array = get_root().image.im0[W.r[0]:W.r[1], W.r[2]:W.r[3]]
    dicr = get_array_stat(sub_array)

    # Clear answer frame
    get_root().frame_answer.clear()

    # Create text
    text = grid_text_answer()

    lst = [
        ["DIM X*DIM Y:\t", "%.1f x %.1f" %
         (abs(W.r[0]-W.r[1]), abs(W.r[2]-W.r[3]))],
        ["MIN:\t", "%.1f" % dicr["min"]],
        ["MAX:\t", "%.1f" % dicr["max"]],
        ["SUM:\t", "%.1f" % dicr["sum"]],
        ["MEAN:\t", "%.1f" % dicr["mean"]],
        ["MEDIAN:\t", "%.1f" % dicr["median"]],
        ["RMS:\t", "%.1f" % dicr["rms"]],
    ]

    stg = ''
    for name, value in lst:
        log(0, name, value)
        stg += name + value + "\n"

    text.insert(END, stg)

    # Disable edit
    text.configure(state=DISABLED)


# "
#   1D 1D 1D
###############





def PlotStar():
    # Binary plot profile
    if (get_state().pick_type == "binary") or (get_state().pick_type == "tightbinary"):
        PlotBinaryStar1D()
    else:  # including only one star  (ie : not binary)
        PlotOneStar1D()
        PlotStar2()


def PlotOneStar1D():
    center = (W.strehl['center_x'], W.strehl['center_y'])
    #################
    # PLOT radius profile
    params = W.strehl
    log(3, 'center=', center)

    # Get ax
    ax = get_root().frame_fit.reset_figure_ax(
        xlabel='Pixel', ylabel='Intensity')

    # Plot x, y
    # we need to give the center (of course)
    x, y = IF.XProfile(get_root().image.im0, center)
    # we get a smaller bin for the fitted curve.
    a = np.arange(min(x), max(x), 0.1)
    # RAW  DATA in X
    # x+0.5 to recenter the bar
    ax.plot(x+0.5, y, color='black', drawstyle='steps', linestyle='--',
            linewidth=1, label='Data')

    # Plot encircle line
    r99 = (W.strehl['r99x']+W.strehl['r99y'])/2
    x0cut, x1cut = center[0]-r99, center[0]+r99
    ax.axvline(x=x0cut, color='black', linestyle='-.', label='99% EE')
    ax.axvline(x=x1cut, color='black', linestyle='-.')
    ax.axhline(y=get_state().get_answer(EA.BACKGROUND), color='black', linestyle='-.')

    # Plot Fit
    if not get_state().fit_type == 'None':
        I_theory = vars(BF)[get_state().fit_type]((a, params['center_y']), params)
        ax.plot(a, I_theory, color='purple', linewidth=2, label='Fit')

    # Plot perfect diffraction pattern
    if not get_root().header.wavelength*1e-6/get_root().header.diameter/(get_root().header.pixel_scale/206265) < 2:
        params2 = {'diameter': get_root().header.diameter,
                   'lambda': get_root().header.wavelength,
                   'center_x': params['center_x'],
                   'center_y': params['center_y'],
                   'pixelscale': get_root().header.pixel_scale,
                   'phot': abism_val(EA.PHOTOMETRY),
                   'obstruction': get_root().header.obstruction/100,
                   }
        bessel = BF.DiffractionPatern((a, params['center_y']), params2)
        ax.plot(a, bessel+params['my_background'],
                color='blue', linewidth=2, label='Ideal PSF')

    # Draw Legend
    ax.legend(loc=1, prop={'size': 8})

   #  def Percentage(y):  # y is the intensity
   #      res = 100*(max(MyBessel)-get_state().get_answer(EA.BACKGROUND))*y
    ax.set_xlim(center[0]-r99-5, center[0] + r99 + 5)

    # Update skin && Draw
    get_root().frame_fit.update_skin()
    get_root().frame_fit.get_canvas().draw()


def PlotBinaryStar1D():
    """Draw 1D of binary system"""
    x0, y0 = W.strehl["x0"], W.strehl["y0"]
    x1, y1 = W.strehl["x1"], W.strehl["y1"]
    fwhm0, fwhm1 = W.strehl["fwhm_x0"], W.strehl["fwhm_x1"]

    #######
    # EXTREMITIES OF PROFILE LINE ...
    # following the line x0,x1
    # Do not by pass the image borders
    line_len = np.sqrt((x1-x0)**2 + (y1-y0)**2)
    dx0 = (x0-x1) / line_len * 5 * fwhm0
    dy0 = (y0-y1) / line_len * 5 * fwhm0
    dx1 = (x1-x0) / line_len * 5 * fwhm1
    dy1 = (y1-y0) / line_len * 5 * fwhm1

    extremity0 = IF.DoNotPassBorder(get_root().image.im0, (int(x0+dx0), int(y0+dy0)))
    extremity1 = IF.DoNotPassBorder(get_root().image.im0, (int(x1+dx1), int(y1+dy1)))

    ab, od, points = IF.RadialLine(
        get_root().image.im0, (extremity0, extremity1), return_point=1)

    if "Moffat" in get_state().fit_type:
        fit_type = "Moffat2pt"
    else:
        fit_type = "Gaussian2pt"
    ab_range = ab[0], ab[-1]
    x_range = points[0][1], points[0][-1]
    y_range = points[1][1], points[1][-1]

    ab_th = np.arange(ab_range[0], ab_range[1], 0.1)
    x_theory = np.interp(ab_th, ab_range, x_range)
    y_theory = np.interp(ab_th, ab_range, y_range)
    if get_state().fit_type is not None:
        I_theory = vars(BF)[fit_type](
            (x_theory, y_theory), W.strehl["fit_dic"])
    else:
        I_theory = 0*x_theory

    ################
    # PLOT
    ax = get_root().frame_fit.reset_figure_ax()
    ax.plot(ab_th+0.5, I_theory, color='purple',
            linewidth=2, label='Fitted PSF')
    #G.ax2.plot(ab_th,I_theory,color='purple',linewidth=2,label='Fitted PSF')
    ax.plot(ab, od, color='black', linestyle='steps', linewidth=1,
            label='Real Profile')  # x+0.5 to recenter the bar
    ax.legend(loc=1, prop={'size': 8})      # Legend
    get_root().frame_fit.redraw()



def show_profile(point1, point2):
    """Callback for Profile Pick: 1 and 2D"""
    # Get data to plot
    ab, od, points = IF.RadialLine(
        get_root().image.im0, (point1, point2), return_point=1)

    # FIT
    # if ( get_state().fit_type != "None" ) & ( "strehl" in vars(W) ):
    #  I_theory = vars(BF) [get_state().fit_type ](points,W.strehl["fit_dic"],get_state().fit_type)
    #  G.ax2.plot(ab,I_theory,color='purple',linewidth=2,label='Fitted PSF')

    # Plot <- Reset
    ax = get_root().frame_fit.reset_figure_ax()
    ax.plot(ab, od, '-', linewidth=1, label="Data")
    ax.legend(loc=1, prop={'size': 8})
    get_root().frame_fit.redraw()

    log(8, "ProfileAnswer :", zip(points, get_root().image.im0[tuple(points)]))

    # Get stat
    ps = get_array_stat(get_root().image.im0[tuple(points)])
    # LEN
    tlen = np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    lst = [
        ["LENGTH: ", tlen],
        ["MIN: ", ps.min],
        ["MAX: ", ps.max],
        ["MEAN: ", ps.mean],
        ["RMS: ", ps.rms],
    ]

    # Plot <- Reset
    ax = get_root().frame_result.reset_figure_ax()
    # like profile_stat points[0] is x and points[1] is y
    for num, (label, value) in enumerate(lst):
        ax.text(0.3, 1.0 - num / (len(lst) + 1), label + "%.1f" % value)
    get_root().frame_result.redraw()


####################
#   2D 2D 2D
####################


def PlotStar2():   # the two images colormesh
    if (get_state().pick_type == "one") or (get_state().pick_type[0] == "many"):
        PlotOneStar2D()
    elif get_state().pick_type == "binary":
        PlotBinaryStar2D()


def PlotOneStar2D():
    x0, y0 = W.strehl["center_x"], W.strehl["center_y"]
    r99x, r99y = W.strehl["r99x"], W.strehl["r99y"]
    dx1, dx2 = int(max(x0-4*r99x, 0)), int(min(x0+4*r99x,
                                               len(get_root().image.im0) + 1))  # d like display
    dy1, dy2 = int(max(y0-4*r99y, 0)), int(min(y0+4*r99y,
                                               len(get_root().image.im0) + 1))  # c like cut If borders
    r = (dx1, dx2, dy1, dy2)  # Teh local cut applied to the image. To show it

    x, y = np.arange(r[0], r[1]), np.arange(r[2], r[3])
    Y, X = np.meshgrid(y, x)

    def Data(ax):
        ax.imshow(
            get_root().image.im0[r[0]:r[1], r[2]:r[3]],
            vmin=get_state().i_image_min_cut, vmax=get_state().i_image_max_cut,
            cmap=G.cbar.mappable.get_cmap().name, origin='lower')
        # extent=[r[2],r[3],r[0],r[1]])#,aspect="auto")
        #G.ax31.format_coord=lambda x,y: "%.1f"%get_root().image.im0[r[2]+y,r[0]+x]
        ax.format_coord = lambda x, y: ""

    def Fit(ax):
        fit_type = get_state().fit_type
        if "Gaussian_hole" in fit_type:
            fit_type = "Gaussian_hole"
        ax.imshow(
            vars(BF)[fit_type]((X, Y), W.strehl),
            vmin=get_state().i_image_min_cut, vmax=get_state().i_image_max_cut,
            cmap=G.cbar.mappable.get_cmap().name, origin='lower',
                                          # extent=[r[2],r[3],r[0],r[1]])#,aspect="auto")
                                          )  # need to comment the extent other wise too crowded and need to change rect position
        #G.ax32.format_coord= lambda x,y:'%.1f'% vars(BF)[fit_type]((r[2]+y,r[0]+x),W.strehl)
        ax.format_coord = lambda x, y: ""

    # Get && Reset figure
    figure = get_root().frame_result.get_figure()
    figure.clf()
    ax1 = figure.add_subplot(121)
    ax2 = figure.add_subplot(122)
    get_root().frame_result.update_skin()

    # Plot first image (data)
    Data(ax1)

    # Plot second image (fit)
    if get_state().fit_type != "None":
        Fit(ax2)
    else:
        Data(ax2)

    # APERTTURES
    params = W.strehl
    #   s   (te center of the rect is in fact the bottm left corner)

    # NOISE 8 RECT
    if (get_state().noise_type == "8rects"):
        rect = (x0 - params['r99x'], x0 + params['r99x'],
                y0 - params['r99y'], y0 + params['r99y'])
        var = IF.EightRectangleNoise(get_root().image.im0, rect, return_rectangle=1)[2]
        for p in var:
            center_tmp = (p[0][0]-r[0]-p[1]/2, p[0][1]-r[2]-p[2]/2)
            a = matplotlib.patches.Rectangle(
                (center_tmp[1], center_tmp[0]), p[2], p[1], facecolor='orange', edgecolor='black')
            ax2.add_patch(a)
        center = x0 - r[0], y0-r[2]

    # NOISE ANNULUS
    elif (get_state().noise_type == "elliptical_annulus"):
        # INNER
        tmpmin, tmpmax = W.ell_inner_ratio,  W.ell_outer_ratio
        tmpstep = (tmpmax-tmpmin)/3
        lst = np.arange(tmpmin, tmpmax + tmpstep, tmpstep)
        for rt in lst:
            width = 2*params["r99v"]*rt  # invert
            height = 2*params["r99u"]*rt
            angle = params["theta"] * 180./np.pi
            x = params["center_y"] - r[2]
            y = params["center_x"] - r[0]
            a = matplotlib.patches.Ellipse(
                (x, y), width, height, angle, fc="none", ec="yellow", linestyle="solid", alpha=0.6)
            ax2.add_patch(a)

    # PHOT RECT
    if get_state().phot_type == "encircled_energy":
        tx = params["center_x"] - r[0]
        ty = params["center_y"] - r[2]
        a = matplotlib.patches.Rectangle(
            (ty-params['r99y'], tx-params['r99x']), 2*params['r99y'], 2*params['r99x'], facecolor='none', edgecolor='black')
        ax2.add_patch(a)

    # PHOT ELL
    elif get_state().phot_type == "elliptical_aperture":
        width = 2*params["r99v"]
        height = 2*params["r99u"]
        angle = params["theta"] * 180./np.pi
        x = params["center_y"] - r[2]
        y = params["center_x"] - r[0]
        a = matplotlib.patches.Ellipse(
            (x, y), width, height, angle, fc="none", ec="black")
        ax2.add_patch(a)

    #####
    # LABEL
    ax1.set_title("True Image")
    ax2.set_title("Fit")

    ax2.set_yticks((0, r[1]-r[0]))
    ax2.set_yticklabels((str(int(r[0])), str(int(r[1]))))
    ax2.set_xticks((0, r[3]-r[2]))
    ax2.set_xticklabels((str(int(r[2])), str(int(r[3]))))
    #plt.xticks( (r[0],r[1] ) )
    #plt.xticks( (r[2],r[3] ) )
    ax1.set_xticks(())
    ax1.set_yticks(())

    get_root().frame_result.redraw()
    return


def PlotBinaryStar2D():
    x0, y0 = W.strehl["x0"], W.strehl["y0"]
    x1, y1 = W.strehl["x1"], W.strehl["y1"]
    xr, yr = 3*abs(x0-x1), 3*abs(y0-y1)  # ditances
    side = max(xr, yr)  # side of the displayed square
    rx1, rx2 = int(min(x0, x1) - side / 2),  int(max(x0, x1) + side / 2)
    ry1, ry2 = int(min(y0, y1) - side / 2),  int(max(y0, y1) + side / 2)
    r = (rx1, rx2, ry1, ry2)

    # define coord for the fitted function display
    x, y = np.arange(r[0], r[1]), np.arange(r[2], r[3])
    Y, X = np.meshgrid(y, x)

    ###########
    # IMAGES draw
    # TRUE
    get_root().frame_result.get_figure().clf()
    ax1 = get_root().frame_result.get_figure().add_subplot(121)
    ax1.imshow(
        get_root().image.im0[r[0]:r[1], r[2]:r[3]],
        vmin=get_state().i_image_min_cut, vmax=get_state().i_image_max_cut,
        cmap=G.cbar.mappable.get_cmap().name, origin='lower')

    # extent=[r[2],r[3],r[0],r[1]])#,aspect="auto")
    ax1.format_coord = lambda x, y: "%.1f" % get_root().image.im0[y, x]
    ax1.format_coord = lambda x, y: ""
    # FIT
    if "Moffat" in get_state().fit_type:
        stg = "Moffat2pt"
    elif "Gaussian" in get_state().fit_type:
        stg = "Gaussian2pt"
    ax2 = get_root().frame_result.get_figure().add_subplot(122)
    ax2.imshow(
        vars(BF)[stg]((X, Y), W.strehl),
        vmin=get_state().i_image_min_cut, vmax=get_state().i_image_max_cut,
        cmap=G.cbar.mappable.get_cmap().name, origin='lower',
        # extent=[r[2],r[3],r[0],r[1]])#,aspect="auto")
        )  # need to comment the extent other wise too crowded and need to change rect positio
    #ax2.format_coord= lambda x,y:'%.1f'% vars(BF)[stg]((y,x),W.strehl)
    ax2.format_coord = lambda x, y: ""
    get_root().frame_result.redraw()
    return

    ############
    # OTHERS
    ############


def CallContrastMap():
    """Not called"""
    G.contrast_fig = matplotlib.figure.Figure()
    ax = G.contrast_fig.add_subplot(111)

    ax.text(0.1, 0.7, 'Calculating\nContrast\nPlease Wait\n.....',
            verticalalignment='top', horizontalalignment='left',
            transform=ax.transAxes,
            color='green', fontsize=40)

    G.ContrastWindow = Tk()
    G.ContrastWindow.title("Contrast Map")
    G.ContrastCanvas = FigureCanvas(G.contrast_fig, master=G.ContrastWindow)
    G.ContrastCanvas.get_tk_widget().pack(side=TOP, expand=0, fill=BOTH)
    G.contrast_fig.canvas.draw()

    G.ContrastButtonFrame = Frame(G.ContrastWindow, bg="black")
    G.ContrastButtonFrame.pack(side=TOP, expand=0, fill=X)

    G.ContrastButton1Frame = Frame(G.ContrastWindow, bg="black")
    G.ContrastButton1Frame.pack(side=TOP, expand=0, fill=X)

    W.strehl["contrast_max"] = W.strehl["intensity"]

    Label(G.ContrastButton1Frame, text="Peak Intensity",
          **skin().fg_and_bg).grid(row=0, column=0, sticky="snew")

    G.TEXT = Text(G.ContrastButton1Frame, height=1)
    G.TEXT.bind()

    #G.v1= [ ]
    #v =  StringVar()
    #G.PeakContrast1Entry = Entry(G.ContrastButton1Frame, width=10,textvariable=v,font=skin().font.param )
    # G.PeakContrast1Entry.grid(row=0,column=1,sticky="snew")
    #G.PeakContrast1Entry.bind('<Return>',Get )
    # v.set("%.2f"%W.strehl["contrast_max"])
    # G.v1.append(v)

    def Get(event):
        log(1, G.v.get())

    def Worker():
        import ImageFunction as IF
        x, y, tdic = IF.ContrastMap(get_root().image.im0, (W.strehl["center_x"], W.strehl["center_y"]), interp=True, xmin=0.5, xmax=20, step=2, dic={
                                    "theta": 0, "ru": 1, "rv": 1}, background=0)  # get_state().get_answer(EA.BACKGROUND))

        FigurePlot(x, y, dic=tdic)


    G.contrast_thread = Thread(target=Worker)
    G.contrast_thread.daemon = True  # can close the program without closing this thread
    G.contrast_thread.start()

    G.ContrastWindow.mainloop()


def FigurePlot(x, y, dic={}):
    """ x and y can be simple list
    or also its can be list of list for a multiple axes
    dic : title:"string", logx:bol, logy:bol, xlabel:"" , ylabel:""
    """
    log(3, "MG.FigurePlotCalled")
    default_dic = {"warning": 0, "title": "no-title"}
    default_dic.update(dic)
    dic = default_dic

    def SubPlot(x, y):
        nx, ny = 7, 5
        if "logx" in dic:
            ax.set_xscale("log")
        if "logy" in dic:
            ax.set_yscale("log")
        if "xlabel" in dic:
            ax.set_xlabel(dic["xlabel"])
        if "ylabel" in dic:
            ax.set_ylabel(dic["ylabel"])

        ax.plot(x, y)

        ax2 = ax.twiny()
        ax2.set_xticks(np.arange(nx))
        xlist = np.linspace(0, x[-1] * get_root().header.pixel_scale, nx)
        xlist = [int(1000 * u) for u in xlist]
        ax2.set_xticklabels(xlist, rotation=45)
        ax2.set_xlabel(u"Distance [mas]")

        ax3 = ax.twinx()
        ax3.set_yticks(np.arange(ny))
        ylist = np.linspace(0, y[0], ny)
        ylist = [int(u) for u in ylist]
        ax3.set_yticklabels(ylist)
        ax3.set_ylabel(u"number count per pixel")
        ############
        # TWIN axes

    log(3, 50 * '_', "\n", currentThread().getName(),
        "Starting------------------\n")

    global ax
    G.contrast_fig.clf()
    # tfig.canvas.set_window_title(dic["title"])

    if not isinstance(x[0], list):  # otherwise multiple axes
        log(3, "FigurePlot, we make a single plot")
        ax = G.contrast_fig.add_subplot(111)
        #from mpl_toolkits.axes_grid1 import host_subplot
        #ax = host_subplot(111)
        SubPlot(x, y)
        log(3, "I will show ")
        G.contrast_fig.canvas.draw()

    # Over
    log(3, '_' * 50 + "\n", currentThread().getName(),
        'Exiting' + 20 * '-' + "\n")



def MyFormat(value, number, letter):
    """This is just to put a "," between the 1,000 for more readability
    MyFormat(var, 1, 'f') -> "%.1f" % var
    TODO remove one day
    """
    try:
        float(value)  # in case
    except:
        return value
    stg = "{:,"
    stg += "." + str(number) + letter + "}"
    return stg.format(value).replace(",", " ")


def Separation(point=((0, 0), (0, 0)), err=((0, 0), (0, 0))):
    """point1i  (and 2) : list of 2 float = (x,y)= row, column
    err_point1 = 2 float = x,y )
    read north position in W
    """
    point1, point2 = point[0], point[1]
    err_point1, err_point2 = err[0], err[1]
    x0, x1, y0, y1 = point1[0],  point1[1], point2[0],  point2[1]
    dx0, dx1, dy0, dy1 = err_point1[0],  err_point1[1], err_point2[0],  err_point2[1]

    ##########
    # SEPARATION DISTANCE
    dist = np.sqrt((y1-y0)**2 + (x1-x0)**2)

    # ERR
    dist_err = np.sqrt(dx0**2 + dx1**2)
    dx0 = np.sqrt(err_point1[0]**2 + err_point1[1]**2)
    dx1 = np.sqrt(err_point2[0]**2 + err_point2[1]**2)

    #############
    # SEPARATION ANGLE
    angle = np.array([(y1-y0),   (x1-x0)])
    angle /= np.sqrt((y0-y1)**2 + (x0-x1)**2)

    im_angle = np.arccos(angle[1]) * 57.295779  # 360/2pi
    sign = np.sign(angle[0])
    im_angle = im_angle + (sign-1)*(-90)

    sky_angle = np.arccos(
        angle[1]*W.north_direction[1] + angle[0] *
        W.north_direction[0]) * 57.295779  # inverted angle and not north
    sign = np.sign(angle[0]*W.east_direction[0] + angle[1]*W.east_direction[1])
    sky_angle = sky_angle + (sign-1)*(-90)

    res = {"im_angle": im_angle,
           "sky_angle": sky_angle,
           "dist": dist, "dist_err": dist_err,
           }
    return res
