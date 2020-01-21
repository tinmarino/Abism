"""
    Show fits header
"""

import tkinter as tk

from abism.front.util_front import skin

find_num = [0]
find_list = []
# Previous string
s_old = ''

def _find(text, edit):
    """Find string in header
    text tk.Frame with text
    edit tk.Entry
    """
    global s_old  # pylint: disable=global-statement
    text.tag_remove('found', '1.0', tk.END)
    s_to_find = edit.get()
    if s_to_find:
        if s_to_find != s_old:  # reset
            find_num[0] = 0
            s_old = s_to_find
        idx = '1.0'
        while 1:
            idx = text.search(s_to_find, idx, nocase=1, stopindex=tk.END)
            if not idx:
                break
            lastidx = '%s+%dc' % (idx, len(s_to_find))
            text.tag_add('found', idx, lastidx)
            find_list.append(idx)
            idx = lastidx
        text.tag_config('found', foreground='blue')
    edit.focus_set()

    return s_to_find


def Scroll(text, edit, side):
    """AutoScroll when user click + or -"""
    # Get
    s_to_find = _find(text, edit)

    # Check in
    if len(find_list) == 0:
        print("FitsHeaderWindow: Pattern '",
              s_to_find, "' not found in header")
        return
    if find_num[0] != 0:
        if side == "+":
            find_num[0] += 1
        if side == "-":
            find_num[0] -= 1
    lastidx = find_list[find_num[0]]
    idx = '%s+%dc' % (lastidx, len(s_to_find))
    text.see(lastidx)
    try:
        text.tag_remove('on', '1.0', tk.END)
    except:
        pass
    text.tag_add("on", lastidx, idx)
    text.tag_config("on", foreground="red")
    if find_num[0] == 0:
        find_num[0] += 1
    return


def spawn_header_window(image_name, s_text, save=None):
    """Pop Window to display the header (helper)"""

    # Parent
    root = tk.Tk()
    if save is not None: save.append(root)
    root.title('header('+image_name+')')
    root.geometry("1000x1000+0+0")

    # Head
    head_frame = tk.Frame(root, **skin().frame_dic)
    head_frame.pack(side=tk.TOP, fill=tk.X)
    for i in range(4):
        head_frame.columnconfigure(i, weight=1)

    # tk.Scrollbar
    scroll = tk.Scrollbar(root, bg=skin().color.bu)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # tk.Text
    text = tk.Text(root, **skin().fg_and_bg)
    text.insert(tk.END, s_text)
    text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    text.configure(yscrollcommand=scroll.set)
    scroll.config(command=text.yview)

    # tk.Label Find
    label_find = tk.Label(
        head_frame, text='Find expression: ', **skin().fg_and_bg)
    label_find.grid(row=0, column=0, sticky='nsew')

    # tk.Texttk.Entry search
    edit = tk.Entry(head_frame, **skin().fg_and_bg)
    edit.bind("<Return>", lambda event: Scroll(text, exit, "+"))
    edit.grid(row=0, column=1, sticky="nsew")
    edit.focus_set()

    # - Previous
    tk.Button(
        head_frame, text='<-', **skin().button_dic,
        command=lambda: Scroll(text, edit, "-")
        ).grid(row=0, column=2, sticky="nsew")

    # + Next
    tk.Button(
        head_frame, text='->', **skin().button_dic,
        command=lambda: Scroll(text, edit, "+")
        ).grid(row=0, column=3, sticky="nsew")


    root.mainloop()