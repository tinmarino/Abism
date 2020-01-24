"""
    The Tkinter Frame For text / butto ninterface (left)

    Label
    Option
    Answer

"""
import re

import tkinter as tk

from abism.front.util_front import photo_up, photo_down, skin, \
    TitleLabel, open_backgroud_and_substract

from abism.util import log, get_root, quit_process, restart, get_state

# TODO remove
import abism.front.util_front as G


class LeftFrame(tk.Frame):
    """Full Container"""
    def __init__(self, root, parent):
        # Append self -> parent
        super().__init__(parent, **skin().frame_dic)

        # Create Paned && Save
        text_paned = tk.PanedWindow(self, orient=tk.VERTICAL, **skin().paned_dic)
        root.paned_text = text_paned

        # Add LabelFrame
        root.frame_label = LabelFrame(text_paned, index=0, label_text='Info')

        # Add LabelFrame
        root.frame_option = OptionFrame(text_paned, index=1, label_text='Option')

        # Add AnswerFrame
        root.frame_answser = AnswerFrame(text_paned, label_text='Result')

        # Create Buttons with callback to preceding
        root.frame_button = ButtonFrame(self)

        # Pack buttons and pane
        root.frame_button.pack(side=tk.TOP, expand=0, fill=tk.X)
        text_paned.pack(side=tk.TOP, expand=1, fill=tk.BOTH)


class TextFrame(tk.Frame):
    """TextScrollable frame
    parent <- must be vertical pane
    children <- are grided
    """
    def __init__(self, parent, label_text='Frame', index=0):
        super().__init__(parent, skin().frame_dic)

        # Prepare grid attributes
        self.columnconfigure(0, weight=1)

        # Add to parent paned
        parent.add(self, minsize=22, pady=0, sticky='nsew')

        self._parent = parent  # for sash positioning
        self._arrow = None  # Button
        # TODO can I impoorve that trick ?
        self._last = None  # To get the normal size
        self._see_me = True  # Bool do you see me
        self._label_text = label_text
        self._index = index  # for sash

    def init_after(self, add_title=True):
        """Place a last widget"""
        # Place button to resize
        self._arrow = tk.Button(
            self, command=self.toogle, image=photo_up(), **skin().button_dic)
        self._arrow.place(relx=1., rely=0., anchor="ne")

        # Place a label for the eye
        if add_title:
            TitleLabel(self, text=self._label_text).place(x=0, y=0)

        # Last widget
        if self._last is not None:
            self._last.destroy()
        self._last = tk.Label(self, height=0, width=0, **skin().frame_dic)
        self._last.grid()

    def toogle(self, visible=None):
        """Toggle visibility: Hide and show"""
        # Check: not work if last
        if self._index is None:
            log(3, 'Warning: cannot hide last sash')
            return

        if visible is not None:
            self._see_me = visible
        else:
            self._see_me = not self._see_me

        # Log before move
        log(3, 'Toggle sash: nb=', self._index,
            ',visible=', self._see_me,
            ',base_y=', self.winfo_y(),
            ',son=', self._last.winfo_y(),
            ',more=', self._last.winfo_y() - self._last.winfo_height()
            )

        # Toogle sash
        i_height = self.winfo_y() + 22
        if self._see_me:
            self._arrow.configure(image=photo_up())
            i_height += max(0, self._last.winfo_y() - self._last.winfo_height())
        else:
            self._arrow.configure(image=photo_down())
        self._parent.sash_place(self._index, 0, i_height)

        # Log after
        log(3, 'New sash pos: height=', i_height)

    def init_will_toogle(self, visible=True, add_title=True):
        """Place last and togfle later.
        Usually called to set visible when some widget added
        This trick is due to the fact widget will be updated at next tk loop
        """
        self.init_after(add_title=add_title)
        def will_refresh():
            self.update()
            self.toogle(visible=visible)
        self.after_idle(will_refresh)

    def clear(self):
        """Destroy all children, take care !"""
        log(3, 'Clearing ' + self._label_text)
        # Destroy children
        children = self.grid_slaves()
        for child in children:
            child.destroy()

        # Restore default
        self.init_after()


class LabelFrame(TextFrame):
    """Some conf"""
    def __init__(self, parent, **args):
        super().__init__(parent, **args)

    def update_label(self):
        """Called later, display what I retrived from header
        warning: expand not working well
        ESO /  not ESO
        NAco/vlt
        Reduced/raw
        Nx x Ny x Nz
        WCS detected or not
        """
        # Declare list of label (text, properties)
        text_and_props = []

        # Get company
        company = 'ESO' if get_root().header.company == "ESO" else 'NOT ESO'

        # Get instrument
        if get_root().header.instrument == "NAOS+CONICA":
            instrument = "NaCo"
        else:
            instrument = get_root().header.instrument
        telescope = re.sub("-U.", "",
                           get_root().header.telescope.replace("ESO-", ""))
        text_and_props.append((company + " / " + telescope + " / " + instrument, {}))

        # Get is_reduced
        if "reduced_type" in vars(get_root().header):
            lbl = get_root().header.reduced_type + ': '
        else:
            lbl = ''

        # Get Size : Nx * Ny * Nz
        shape = list(get_root().image.im0.shape[::-1])
        if "NAXIS3" in get_root().header.header.keys():
            shape.append(get_root().header.header["NAXIS3"])
            lbl += "%i x %i x %i" % (shape[0], shape[1], shape[2])
        else:
            lbl += "%i x %i " % (shape[0], shape[1])
        text_and_props.append((lbl, {}))

        # WCS
        if get_root().header.wcs is not None:
            lbl = "WCS detected"
        else:
            lbl = "WCS NOT detected"
        text_and_props.append((lbl, {}))

        # Header reads Strehl variables ?
        bolt = get_root().header.diameter == 99.
        bolt = bolt or get_root().header.wavelength == 99.
        bolt = bolt or get_root().header.obstruction == 99.
        bolt = bolt or get_root().header.pixel_scale == 99.

        if bolt:
            lbl = "WARNING: some parameters not found"
            text_and_props.append((lbl, {"fg": "red"}))
        else:
            lbl = "Parameters read from header"
            text_and_props.append((lbl, {"fg": "blue"}))

        # UNDERSAMPLED
        bol1 = get_root().header.wavelength * 1e-6
        bol1 /= get_root().header.diameter * (get_root().header.pixel_scale / 206265)
        bol1 = bol1 < 2
        bol2 = "sinf_pixel_scale" in vars(get_root().header)
        # if bol2 sinf_pixel_scane is not in get_root().header, we dont call the next line
        bol3 = bol2 and get_root().header.sinf_pixel_scale == 0.025
        bol3 = bol3 or (bol2 and (get_root().header.sinf_pixel_scale == 0.01))

        bolt = bol1 or bol2
        if bolt:
            lbl = "!!! SPATIALLY UNDERSAMPLED !!!"
            text_and_props.append((lbl, {"fg": "red"}))

        # Grid labels
        row = 0
        for i in text_and_props:
            arg = skin().fg_and_bg.copy()
            arg.update({"justify": tk.CENTER})
            if isinstance(i, (list, tuple)):
                arg.update(i[1])
            i = i[0]
            tk.Label(self, text=i, **arg).grid(
                row=row, column=0, sticky="nsew")
            row += 1

        # Create what it takes
        self.init_after()


class OptionFrame(TextFrame):
    """Some conf"""
    def __init__(self, parent, **args):
        super().__init__(parent, **args)
        # Image parameter
        self.see_image_parameter = False
        self.frame_image_parameter = None
        self.image_parameter_entry_dic = {}
        self.image_parameter_tkvar_dic = {}

        # Manual cut image
        self.see_manual_cut = False
        self.frame_manual_cut = None

        # More analysis
        self.see_more_analysis = False
        self.frame_more_analysis = None
        self.parent_more_analysis = None

        # Manual Bacground
        self.see_manual_background = False
        self.frame_manual_background = None

        self.init_after()

    @staticmethod
    def get_image_parameter_list():
        return [
            [u'Wavelength* [\u03BCm]:', 'wavelength', float('nan')],
            ["Pixel scale* [''/pix]: ", 'pixel_scale', float('nan')],
            ["Diameter* [m]:", 'diameter', float('nan')],
            ["Obstruction (d2/d1)* [%]:", 'obstruction', float('nan')],
            ["Zero point [mag]: ", 'zpt', float('nan')],
            ["Exposure time [sec]: ", 'exptime', float('nan')],
            ]

    def toogle_image_parameters(self):
        self.see_image_parameter = not self.see_image_parameter
        if self.see_image_parameter:
            self.open_image_parameter()
            get_root().frame_button.config_button_image_less()
        else:
            self.close_image_parameter()
            get_root().frame_button.config_button_image_more()

    def open_image_parameter(self):
        # Grid new frame
        self.frame_image_parameter = tk.Frame(self, **skin().frame_dic)
        self.frame_image_parameter.grid(sticky='nsew')

        # Pack title
        tl = TitleLabel(self.frame_image_parameter, text='Parameters')
        tl.pack(side=tk.TOP, anchor="w")

        # Pack grid frame
        frame_manual_grid = tk.Frame(self.frame_image_parameter)
        frame_manual_grid.pack(expand=0, fill=tk.BOTH, side=tk.TOP)
        frame_manual_grid.columnconfigure(0, weight=1)
        frame_manual_grid.columnconfigure(1, weight=1)

        # Loop for all needed variable
        # And grid their (label, entry)
        for row, (text, key, value) in enumerate(self.get_image_parameter_list()):
            # Init variable (may cut it)
            string_var = tk.StringVar()
            s_from_header = vars(get_root().header)[key]
            if len(str(s_from_header)) > 6:
                string_var.set("%.5f" % float(s_from_header))
            else:
                string_var.set(s_from_header)

            # Grid label
            label = tk.Label(
                frame_manual_grid, text=text, font=skin().font.answer,
                justify=tk.LEFT, anchor="nw", **skin().fg_and_bg)
            label.grid(row=row, column=0, sticky="NSEW")

            # Create entry <- string_var
            entry = tk.Entry(
                frame_manual_grid, width=10, font=skin().font.answer,
                bd=0, **skin().fg_and_bg,
                textvariable=string_var)
            # Color entry
            if vars(get_root().header)[key] == value:
                entry["bg"] = "#ff9090"
            # Bind entry Return
            entry.bind(
                '<Return>', lambda _: self.set_image_parameters())

            # Grid entry && Save
            entry.grid(row=row, column=1, sticky="NSEW")
            self.image_parameter_tkvar_dic[key] = string_var
            self.image_parameter_entry_dic[key] = entry

        # Show me
        self.init_will_toogle(visible=True, add_title=False)


    def close_image_parameter(self):
        self.frame_image_parameter.destroy()
        self.toogle(visible=False)


    def init_image_parameters(self):
        """Read from header dictionary"""
        for text, key in self.get_image_parameter_list():
            self.image_parameter_tkvar_dic[key].set(vars(get_root().image.header)[key])
        self.set_image_parameters()


    def set_image_parameters(self):
        """Set imageparameter, labels"""
        log(0, "New image parameters:")
        for label, key, badvalue in self.get_image_parameter_list():
            value = float(self.image_parameter_entry_dic[key].get())
            # Change header field
            vars(get_root().header)[key] = value

            # Log (this is important)
            log(0, f'{value:10.4f}  <-  {label}')
            # COLOR
            if vars(get_root().header)[key] == badvalue:
                self.image_parameter_entry_dic[key]["bg"] = "#ff9090"
            else:
                self.image_parameter_entry_dic[key]["bg"] = "#ffffff"

        # Show
        get_root().frame_label.update_label()


    def toogle_manual_cut(self):
        """Stupid switch"""
        self.see_manual_cut = not self.see_manual_cut
        log(5, "Manual Cut see me ?", self.see_manual_cut)
        if self.see_manual_cut:
            self.open_manual_cut()
        elif self.frame_manual_cut:
            self.close_manual_cut()


    def close_manual_cut(self):
        self.frame_manual_cut.destroy()


    def open_manual_cut(self):
        # Grid main
        self.frame_manual_cut = tk.Frame(self, bg=skin().color.bg)
        self.frame_manual_cut.grid(sticky='nsew')

        # Pack title
        lt = TitleLabel(self.frame_manual_cut, text="Cut image scale")
        lt.pack(side=tk.TOP, anchor="w")

        # Pack rest
        parent = tk.Frame(self.frame_manual_cut, bg=skin().color.bg)
        parent.pack(side=tk.TOP, expand=0, fill=tk.X)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        # Keep ref to string_vars
        string_vars = []

        # Define callback
        def set_cuts(_):
            get_state().i_image_max_cut = float(string_vars[0].get())
            get_state().i_image_min_cut = float(string_vars[1].get())
            get_root().frame_image.CutImageScale()

        # Grid them both
        lst = [["Max cut", get_state().i_image_max_cut],
               ["Min cut", get_state().i_image_min_cut]]
        for text, value in lst:
            # Label
            l = tk.Label(
                parent, text=text,
                font=skin().font.answer, **skin().fg_and_bg)
            l.grid(column=0, sticky="snew")

            # Entry
            string_var = tk.StringVar()
            string_var.set("%.1f" % value)
            string_vars.append(string_var)
            e = tk.Entry(
                parent, width=10, bd=0, **skin().fg_and_bg, font=skin().font.answer,
                textvariable=string_var)
            e.grid(column=1, sticky="nsew")
            e.bind('<Return>', set_cuts)

        # Grid close
        bu_close = tk.Button(
            parent, text=u'\u25b4 ' + 'Close',
            command=self.close_manual_cut, **skin().button_dic)
        bu_close.grid(column=0, columnspan=2)

        # Redraw
        self.init_will_toogle(visible=True, add_title=False)


    def toogle_more_analysis(self, parent=None):
        self.see_more_analysis = not self.see_more_analysis

        # Keep ref to change label
        if parent is not None:
            self.parent_more_analysis = parent

        # Toogle menu
        self.parent_more_analysis.toogle_more_options()

        # Discriminate show / hide
        if self.see_more_analysis:
            self.open_more_analysis()
        else:
            self.close_more_analysis()


    @staticmethod
    def grid_more_checkbuttons(frame):
        # Define callback
        def on_change_aniso(int_var):
            get_state().b_aniso = int_var.get()
            # Aniso
            if get_state().b_aniso:
                msg = "Anisomorphism: angular dimension are fitted separately"
            else:
                msg = "Isomorphism: angular dimension are fitted together"
            log(0, msg)

        def on_change_psf(int_var):
            get_state().b_same_psf = int_var.get()
            if get_state().b_same_psf:
                msg = "Not same psf: Each star is fitted with independant psf"
            else:
                msg = "Same psf: Both stars are fitted with same psf"
            log(0, msg)

        def on_change_center(int_var):
            get_state().b_same_center = int_var.get()
            if get_state().b_same_center:
                msg = ("Same center: Assuming the saturation "
                       "is centered at the center of the object")
            else:
                msg = ("Not same center: Assuming the saturation"
                       "isn't centered at the center of th object")
            log(0, msg)


        # Declare label and associated variable
        text_n_var_n_fct = (
            ('Anisomorphism', get_state().b_aniso, on_change_aniso),
            ('Binary_same_psf', get_state().b_same_psf, on_change_psf),
            ('Saturated_same_center', get_state().b_same_center, on_change_center),
        )

        # Create && Grid all
        for (text, var, fct) in text_n_var_n_fct:
            int_var = tk.IntVar(value=var)
            check = tk.Checkbutton(
                frame, text=text, variable=int_var, **skin().checkbutton_dic,
                command=lambda fct=fct, int_var=int_var: fct(int_var))
            check.grid(column=0, columnspan=2, sticky='nwse')


    def open_more_analysis(self):
        """Create More Frame"""
        # Grid root
        self.frame_more_analysis = tk.Frame(
            get_root().frame_option, **skin().frame_dic)
        self.frame_more_analysis.grid(sticky='nsew')

        # Pack title
        label_more = TitleLabel(self.frame_more_analysis, text="More Options")
        label_more.pack(side=tk.TOP, anchor="w")

        # Pack rest
        frame_more_grid = tk.Frame(
            self.frame_more_analysis, **skin().frame_dic)
        frame_more_grid.pack(side=tk.TOP, expand=0, fill=tk.X)
        frame_more_grid.columnconfigure(0, weight=1)
        frame_more_grid.columnconfigure(1, weight=1)

        # Grid button: substract background
        bu_subtract_bg = tk.Button(
            frame_more_grid, text='SubstractBackground',
            command=open_backgroud_and_substract, **skin().button_dic)
        bu_subtract_bg.grid(row=0, column=0, columnspan=2, sticky="nswe")

        # Grid Menu: set photometric type
        def create_phot_menu(frame):
            menu_phot = tk.Menubutton(
                frame, text=u'\u25be '+'Photometry',
                relief=tk.RAISED, **skin().button_dic)
            menu_phot.menu = tk.Menu(menu_phot)
            menu_phot['menu'] = menu_phot.menu

            lst = [
                ['Elliptical Aperture', 'elliptical_aperture'],
                ['Fit', 'fit'],
                ['Rectangle Aperture', 'encircled_energy'],
                ['Manual', 'manual'],
            ]

            def set_phot(i):
                get_state().phot_type = i

            # Add radio buttons:
            string_var = tk.StringVar()
            string_var.set(get_state().phot_type)
            for text, tag in lst:
                menu_phot.menu.add_radiobutton(
                    label=text, command=lambda tag=tag: set_phot(tag),
                    variable=string_var, value=tag)

            return menu_phot

        create_phot_menu(frame_more_grid).grid(row=1, column=1, sticky="nswe")

        # Grid menu: set noise type (or background estimation)
        def create_noise_menu(frame):
            # Root
            menu = tk.Menubutton(
                frame, text=u'\u25be '+'Background',
                relief=tk.RAISED, **skin().button_dic)
            menu.menu = tk.Menu(menu)
            menu['menu'] = menu.menu


            lst = [
                ["Annulus", "elliptical_annulus"],
                ['Fit', 'fit'],
                ["8Rects", "8rects"],
                ['Manual', "manual"],
                ["None", "None"],
            ]

            def set_noise(i):
                get_state().noise_type = i

            string_var = tk.StringVar()
            string_var.set(get_state().noise_type)
            for text, tag in lst:
                if text == "Manual":
                    menu.menu.add_radiobutton(
                        label=text, command=self.toogle_manual_background,
                        variable=string_var, value=tag)
                else:
                    menu.menu.add_radiobutton(
                        label=text, command=lambda tag=tag: set_noise(tag),
                        variable=string_var, value=tag)

            return menu

        menu_noise = create_noise_menu(frame_more_grid)
        menu_noise.grid(row=1, column=0, sticky="nswe")

        # Grid check buttons: for conf
        self.__class__.grid_more_checkbuttons(frame_more_grid)

        bu_close = tk.Button(
            frame_more_grid, text=u'\u25b4 '+'Close',
            command=self.toogle_more_analysis, **skin().button_dic)
        bu_close.grid(column=0, columnspan=2)

        # Redraw
        get_root().frame_option.init_will_toogle(visible=True, add_title=False)


    def close_more_analysis(self):
        """Close the Frame"""
        if not self.frame_more_analysis: return

        # Close sub frame
        self.close_manual_background()

        self.frame_more_analysis.destroy()


    def is_more_analysis_visible(self):
        return self.see_more_analysis


    def toogle_manual_background(self):
        """Create manual background frame"""
        self.see_manual_background = not self.see_manual_background
        if self.see_manual_background:
            self.open_manual_background()
        else:
            self.close_manual_background()


    def open_manual_background(self):
        get_state().noise_type = "manual"

        # Grid root
        self.frame_manual_background = tk.Frame(
            get_root().frame_option, bg=skin().color.bg)
        self.frame_manual_background.grid(sticky='nsew')
        self.frame_manual_background.columnconfigure(0, weight=1)
        self.frame_manual_background.columnconfigure(1, weight=1)

        def on_enter(string_var):
            i_in = float(string_var.get())
            get_state().i_manual_background = i_in
            log(0, "ManualBackground setted to:", i_in)

        # Grid label
        label = tk.Label(
            self.frame_manual_background,
            font=skin().font.param, **skin().fg_and_bg,
            text="Background value:")
        label.grid(row=0, column=0, sticky="snew")

        # Grid entry
        string_var = tk.StringVar()
        string_var.set(get_state().i_background)
        entry = tk.Entry(
            self.frame_manual_background,
            font=skin().font.param, width=10, bd=0, **skin().fg_and_bg,
            textvariable=string_var)
        entry.grid(row=0, column=1, sticky="nsew")
        entry.bind('<Return>', lambda event: on_enter(string_var))

        # Grid close button
        button = tk.Button(
            self.frame_manual_background, **skin().button_dic,
            text=u'\u25b4 ' + 'Close',
            command=self.close_manual_background)
        button.grid(row=1, column=0, columnspan=2)


    def close_manual_background(self):
        if not self.see_manual_background: return
        self.frame_manual_background.destroy()



class AnswerFrame(TextFrame):
    """Some conf"""
    def __init__(self, parent, **args):
        super().__init__(parent, **args)

        self.init_after()

    def init_after(self, add_title=False):
        """Add fit type label"""
        self._fit_type_label = tk.Label(
            self, justify=tk.CENTER, **skin().fg_and_bg,
            text=get_state().fit_type)
        self._fit_type_label.grid(sticky='nsew')
        # Add also standard above
        super().init_after(add_title=add_title)

    def set_fit_type_text(self, s_text):
        """Change fit type label text"""
        self._fit_type_label.configure(text=s_text)


class ButtonFrame(tk.Frame):
    """Frame 1 with quit, restart"""
    def __init__(self, parent, **args):
        super().__init__(parent, **args)

        # Define button option
        opts = skin().button_dic.copy()

        # Create Quit
        opts.update({'background':skin().color.quit})
        bu_quit = tk.Button(
            self, text='QUIT',
            command=quit_process, **opts)

        # Create Restart
        opts.update({'background':skin().color.restart})
        bu_restart = tk.Button(
            self, text='RESTART',
            command=restart, **opts)

        # Create Expand Image Parameter
        opts.update({'background':skin().color.parameter1})
        self.bu_manual = tk.Button(
            self, text=u'\u25be ' + 'ImageParameters',
            command=get_root().frame_option.toogle_image_parameters, **opts)

        # Grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        bu_quit.grid(row=0, column=0, sticky="nsew")
        bu_restart.grid(row=0, column=1, sticky="nsew")
        self.bu_manual.grid(row=1, column=0, columnspan=2, sticky="nsew")

    def config_button_image_less(self):
        self.bu_manual['background'] =  skin().color.parameter2
        self.bu_manual['text'] = u'\u25b4 ImageParameters'

    def config_button_image_more(self):
        self.bu_manual['background'] =  skin().color.parameter1
        self.bu_manual['text'] = u'\u25be ImageParameters'
