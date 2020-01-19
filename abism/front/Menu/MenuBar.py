"""
    Create Menu bar
"""
import tkinter as tk

from abism.front.Menu import FileMenu
from abism.front.Menu import AbismMenu
from abism.front.Menu import AnalysisMenu
from abism.front.Menu import ToolMenu
from abism.front.Menu import ViewMenu

from abism.front.util_front import skin
import abism.front.util_front as G


def MenuBarMaker(root):
    """Create the menu bar (autopack top)"""

    # Pack bar at top
    menu_bar = tk.Frame(root, bg=skin().color.bg)
    menu_bar.pack(side=tk.TOP, expand=0, fill=tk.X)

    # Prepare argument dic
    args = skin().fg_and_bg.copy()
    args.update({"relief": tk.FLAT, "width": G.menu_button_width})

    # For all menu button (tab)
    for col, i in enumerate([
            [AbismMenu.AbismMenu, {"text": u"\u25be "+"ABISM"}],
            [FileMenu.FileMenu, {"text": u"\u25be "+"File"}],
            [AnalysisMenu.AnalysisMenu, {"text": u'\u25be '+'Analysis'}],
            [ViewMenu.ViewMenu, {"text": u'\u25be '+'View'}],
            [ToolMenu.ToolMenu, {"text": u'\u25be '+'Tools'}],
                ]):
        # Same weight
        menu_bar.columnconfigure(col, weight=1)
        # Prepare button args
        args.update(i[1])
        # Create button
        button = i[0](root, menu_bar, args)
        # Grid it
        button.grid(row=0, column=col, sticky="nsew")