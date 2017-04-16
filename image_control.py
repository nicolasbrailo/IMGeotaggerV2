import pygtk
pygtk.require('2.0')
import gtk
from image import Image

class Image_Control(gtk.VBox):
    def __init__(self, callback_on_set_position_called, callback_on_new_path_selected):
        gtk.VBox.__init__(self, False, 0)

        self.lbl_img_info = gtk.Label()
        self.lbl_img_info.set_use_markup(gtk.TRUE)

        self.btn_set_pos = gtk.Button('Set position')
        self.btn_set_pos.connect('button-press-event', self._on_set_position_called)

        self.btn_pick_dir = gtk.Button('Pick directory')
        self.btn_pick_dir.connect('button-press-event', self._on_new_path_selected)

        self.pack_start(self.lbl_img_info, False, False, 2)
        self.pack_start(self.btn_set_pos, False, False, 0)
        self.pack_start(self.btn_pick_dir, False, False, 0)

        self.on_selection_cleared()
        self._callback_on_set_position_called = callback_on_set_position_called
        self._callback_on_new_path_selected = callback_on_new_path_selected

    def on_images_selected(self, img_list):
        if len(img_list) == 0:
            self.on_selection_cleared()
            return
        elif (len(img_list) == 1):
            self.lbl_img_info.set_markup('<b>Filename: ' + img_list[0].get_fname() + '\n' + \
                                            'Date:     ' + img_list[0].get_date() + '\n' + \
                                            'Position: ' + img_list[0].get_position() + '</b>')
        else:
            self.lbl_img_info.set_markup('<b>Filename: Multiple\n' + \
                                            'Date:     ---\n' + \
                                            'Position: ---</b>')

        self.btn_set_pos.set_sensitive(True)

    def on_selection_cleared(self):
        self.btn_set_pos.set_sensitive(False)
        self.lbl_img_info.set_markup('<b>Filename: ---\n' + \
                                        'Date:     ---\n' + \
                                        'Position: ---</b>')

    def _on_set_position_called(self, widget, data=None):
        self._callback_on_set_position_called()
    
    def _on_new_path_selected(self, widget, data=None):
        d = Image_Control._ui_pick_dir()
        if d is not None:
            self._callback_on_new_path_selected(d)

    @staticmethod
    def _ui_pick_dir():
        dialog = gtk.FileChooserDialog('Select new directory..',
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_default_size(800, 400)

        path = None
        if dialog.run() == gtk.RESPONSE_OK:
            path = dialog.get_filename()

        dialog.destroy()
        return path

