# File based on CEF Python wxample with PyGTK (GTK 2).

from cefpython3 import cefpython as cef
import pygtk
import gtk
import gobject
import os
import platform
import sys

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

# In CEF you can run message loop in two ways (see API ref for more details):
# 1. By calling cef.MessageLoopWork() in a timer - each call performs
#    a single iteration of CEF message loop processing.
# 2. By calling cef.MessageLoop() instead of an application-provided
#    message loop to get the best balance between performance and CPU
#    usage. This function will block until a quit message is received by
#    the system. This seem to work only on Linux in GTK example.
# NOTE: On Mac message loop timer doesn't work, so using CEF message
#       loop by default.
MESSAGE_LOOP_TIMER = 1
MESSAGE_LOOP_CEF = 2  # Pass --message-loop-cef flag to script on Linux
g_message_loop = None

class CEFBrowser(object):
    def __init__(self, parent_window, start_url):
        self.browser = None
        self.exiting = False
        self.window = parent_window

        self.window.connect('focus-in-event', self._on_focus_in)
        self.window.connect('configure-event', self._on_configure)
        self.window.connect('destroy', self._on_exit)
        self.window.layout.connect('size-allocate', self._on_layout_size_allocate)

        self.window.show()
        self._embed_browser(start_url)
        self.window.show()
        self.window.register_browser(self)
        if g_message_loop == MESSAGE_LOOP_TIMER:
            gobject.timeout_add(10, self._on_timer)

    def _embed_browser(self, start_url):
        windowInfo = cef.WindowInfo()
        size = self.window.window.get_size()
        rect = [0, 0, size[0], size[1]]
        windowInfo.SetAsChild(self._get_window_handle(), rect)
        self.browser = cef.CreateBrowserSync(windowInfo, settings={}, url=start_url)
        self.browser.SetClientHandler(LoadHandler())

    def _on_layout_size_allocate(self, _, data):
        if self.browser:
            x = data.x + 300
            y = data.y + 0
            width = data.width
            height = data.height - 0
            if WINDOWS:
                # Fix for PyCharm hints warnings when using static methods
                WindowUtils = cef.WindowUtils()
                WindowUtils.OnSize(self._get_window_handle(), 0, 0, 0)
            elif LINUX:
                self.browser.SetBounds(x, y, width, height)

    def _on_timer(self):
        if self.exiting:
            return False
        cef.MessageLoopWork()
        return True

    def _on_focus_in(self, *_):
        if self.browser:
            self.browser.SetFocus(True)
            return True
        return False

    def _on_configure(self, *_):
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()
        return False

    def _on_exit(self, *_):
        if self.exiting:
            print("[gtk2.py] on_exit() called, but already exiting")
            return
        self.exiting = True
        self.browser.CloseBrowser(True)
        self.clear_browser_references()
        if g_message_loop == MESSAGE_LOOP_CEF:
            cef.QuitMessageLoop()
        else:
            gtk.main_quit()

    def _get_window_handle(self):
        if WINDOWS:
            return self.window.window.handle
        elif LINUX:
            return self.window.window.xid
        elif MAC:
            return self.window.window.nsview

    def get_url(self):
        return self.browser.GetUrl()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class LoadHandler(object):
    def __init__(self):
        self.initial_app_loading = True

    def OnLoadStart(self, browser, **_):
        if self.initial_app_loading:
            # Temporary fix for focus issue during initial loading
            # on Linux (Issue #284).
            if LINUX:
                print("[gtk2.py] LoadHandler.OnLoadStart:"
                      " keyboard focus fix (Issue #284)")
                browser.SetFocus(True)
            self.initial_app_loading = False



def check_versions():
    print("[gtk2.py] CEF Python {ver}".format(ver=cef.__version__))
    print("[gtk2.py] Python {ver} {arch}".format(
            ver=platform.python_version(), arch=platform.architecture()[0]))
    print("[gtk2.py] GTK {ver}".format(ver='.'.join(
                                           map(str, list(gtk.gtk_version)))))
    assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"
    pygtk.require('2.0')

def configure_message_loop():
    global g_message_loop
    if MAC and "--message-loop-cef" not in sys.argv:
        print("[gtk2.py] Force --message-loop-cef flag on Mac")
        sys.argv.append("--message-loop-cef")
    if "--message-loop-cef" in sys.argv:
        print("[gtk2.py] Message loop mode: CEF (best performance)")
        g_message_loop = MESSAGE_LOOP_CEF
        sys.argv.remove("--message-loop-cef")
    else:
        print("[gtk2.py] Message loop mode: TIMER")
        g_message_loop = MESSAGE_LOOP_TIMER

def cefgtk_main(main_window, start_url):
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    configure_message_loop()
    cef.Initialize()
    gobject.threads_init()
    CEFBrowser(main_window, start_url)
    if g_message_loop == MESSAGE_LOOP_CEF:
        cef.MessageLoop()
    else:
        gtk.main()
    cef.Shutdown()





from img_list import Img_List
from image_control import Image_Control

class Wnd(gtk.Window):
    def __init__(self):
        super(Wnd, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_size_request(width=800, height=600)
        self.set_title('GTK 2 example (PyGTK)')
        self.realize()

        self.img_list = Img_List('/home/laptus/Pictures/Fotos/00to_tag/nexus_save/')
        self.img_list.get_selection().connect('changed', self.on_image_selection)

        self.img_ctrl = Image_Control(self.callback_set_gps_pos_requested,
                                      self.callback_open_new_path)

        img_select_layout = gtk.VBox(False, 0)
        img_select_layout.pack_start(self.img_ctrl, False, False, 2)
        img_select_layout.pack_start(self.img_list.get_ui_element(), True, True, 0)

        self.layout = gtk.HBox(False, 5)
        self.layout.pack_start(img_select_layout, False, False, 0)

        self.add(self.layout)

        self.show()

    def show(self):
        self.layout.get_window().focus()
        self.get_window().focus()
        self.show_all()

    def register_browser(self, browser):
        self.browser = browser

    def _foo(self, widget, data=None):
        print self.browser.get_url()

    def callback_open_new_path(self, path):
        self.img_list.set_path(path)

    def callback_set_gps_pos_requested(self):
        # coords = Wnd.hack_coords_from_gmaps(self.browser.get_url())
        # for img in self.img_list.get_current_selection():
        #     img.set_position(coords)
        print "CHAU"

    def on_image_selection(self, widget, data=None):
        # self.img_ctrl.on_images_selected(self.img_list.get_current_selection())
        print "ASD"


if __name__ == '__main__':
    wnd = Wnd()
    cefgtk_main(wnd, "https://www.reddit.com")

