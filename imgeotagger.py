from img_list import Img_List
from image_control import Image_Control
from browser import *

class Wnd(gtk.Window):
    def __init__(self):
        super(Wnd, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_size_request(width=1200, height=768)
        self.set_title('IMGeotagger revived')
        self.realize()

        self.current_pos = gtk.Label()
        self.current_pos.set_use_markup(gtk.TRUE)

        self.img_list = Img_List('/home/laptus/Fotos/00to_tag/Gato/')
        self.img_list.get_selection().connect('changed', self.on_image_selection)

        self.img_ctrl = Image_Control(self.callback_set_gps_pos_requested,
                                      self.callback_open_new_path)

        img_select_layout = gtk.VBox(False, 0)
        img_select_layout.set_size_request(width=self.get_pane_width(), height=0)
        img_select_layout.pack_start(self.current_pos, False, False, 2)
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

    def get_pane_width(self):
        return 250

    def register_browser(self, browser):
        self.browser = browser

    def callback_open_new_path(self, path):
        self.img_list.set_path(path)

    def callback_set_gps_pos_requested(self):
        coords = Wnd.hack_coords_from_gmaps(self.browser.get_url())
        if coords is None:
            print "Fatal error: the URL format for Google maps has changed and " + \
                  "this program can't understand it. Unknown URL: {0}".format(map_path)
            exit(1)

        print "Setting selection to " + str(coords)
        for img in self.img_list.get_current_selection():
             img.set_position(coords)
        self.img_list.notify_elements_updated()

    def maybe_update_coords(self, url):
        if url:
            coords = Wnd.hack_coords_from_gmaps(url)
            if coords:
                self.current_pos.set_markup('Position: ' + str(coords))
                return
        self.current_pos.set_markup('Position: ???')

    def on_image_selection(self, widget, data=None):
        self.img_ctrl.on_images_selected(self.img_list.get_current_selection())

    @staticmethod
    def hack_coords_from_gmaps(map_path):
        """ Tries to get the map coords from the url of a Google maps page """
        #Expected URL format: https://www.google.nl/maps/@37.2870888,22.3544721,4z
        start_tok = 'maps/@'
        lat_pos = map_path.find(start_tok) + len(start_tok)
        lat_end = map_path.find(',', lat_pos)
        lon_pos = lat_end + 1
        lon_end = map_path.find(',', lon_pos)
        
        if (lat_pos < 0) or (lat_end < 0) or (lon_pos < 0) or (lon_end < 0):
            return None

        return (float(map_path[lat_pos:lat_end]), float(map_path[lon_pos:lon_end]))


if __name__ == '__main__':
    wnd = Wnd()
    cefgtk_main(wnd, "https://www.google.com/maps")

