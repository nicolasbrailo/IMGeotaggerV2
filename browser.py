# File based on CEF Python wxample with PyGTK (GTK 2) but heavily hacked.
# If something doesn't work it's probably my fault and not cefpython's

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
    # This is used to trigger a JS hack that loads a crosshair. It's not very
    # clean, but it works. May be cleaner to replace this with an OnLoad callback
    # but I have no idea how that works in CEF...
    MAP_LOAD_TIME = 4000

    def __init__(self, parent_window, start_url):
        self.browser = None
        self.exiting = False
        self.window = parent_window

        # TODO: This breaks the focus for the treeview (so, multiple elements 
        # can't be selected). Not sure what's going on but commenting this out
        # doesn't seem to seriously break anything.
        #self.window.connect('focus-in-event', self._on_focus_in)
        self.window.connect('configure-event', self._on_configure)
        self.window.connect('destroy', self._on_exit)
        self.window.layout.connect('size-allocate', self._on_layout_size_allocate)

        self.window.show()
        self._embed_browser(start_url)
        self.window.show()
        self.window.register_browser(self)
        gobject.timeout_add(CEFBrowser.MAP_LOAD_TIME, self._hack_crosshair)
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
            x = data.x + self.window.get_pane_width()
            y = data.y + 0
            width = data.width - self.window.get_pane_width()
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

    def _hack_crosshair(self):
        """ Show a crosshair in the middle of the page """
        hack = "" + \
               "var img = document.createElement('img');" + \
               "img.src = 'https://github.com/nicolasbrailo/IMGeotaggerV2/blob/master/crosshair.png?raw=true';" + \
               "img.style.position='absolute';" + \
               "img.style.left='50%';" + \
               "img.style.marginLeft='-24px';" + \
               "img.style.top='50%';" + \
               "img.style.marginTop='-24px';" + \
               "document.body.appendChild(img);"
        self.browser.GetMainFrame().ExecuteJavascript(hack)
        # Tell gobject we don't need to trigger this callback again
        return False

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


