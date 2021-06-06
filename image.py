import pyexiv2
import math

class Image(object):
    def __init__(self, fullpath, fname):
        self._fullpath = fullpath
        self._fname = fname

        self._metadata = pyexiv2.ImageMetadata(self._fullpath)
        self._metadata.read()

    def get_fullpath(self):
        return self._fullpath

    def get_fname(self):
        return self._fname

    def get_date(self):
        try:
            return self._metadata['Exif.Photo.DateTimeOriginal'].value.strftime('%d %B %Y, %H:%M:%S')
        except KeyError:
            return ''

    def get_position(self):
        try:
            lat_key_ref = 'Exif.GPSInfo.GPSLatitudeRef' # S/N
            lat_key = 'Exif.GPSInfo.GPSLatitude'
            lat = "{:.4f}{}".format(
                                Image._sex_to_dec(self._metadata[lat_key].value),
                                self._metadata[lat_key_ref].raw_value)

            lon_key_ref = 'Exif.GPSInfo.GPSLongitudeRef' # West/East
            lon_key = 'Exif.GPSInfo.GPSLongitude'
            lon = "{:.4f}{}".format(
                                Image._sex_to_dec(self._metadata[lon_key].value),
                                self._metadata[lon_key_ref].raw_value)
        except KeyError:
            return None

        return lat + ' ' + lon

    def set_position(self, coords):
        lat, lon = coords
        frac_lat = Image._dec_to_sex(abs(float(lat)))
        sign_lat = 'S' if lat < 0 else 'N'
        frac_lon = Image._dec_to_sex(abs(float(lon)))
        sign_lon = 'W' if lon < 0 else 'E'

        k = 'Exif.GPSInfo.GPSLatitudeRef'
        self._metadata[k] = pyexiv2.ExifTag(k, sign_lat)
        k = 'Exif.GPSInfo.GPSLatitude'
        self._metadata[k] = pyexiv2.ExifTag(k, frac_lat)

        k = 'Exif.GPSInfo.GPSLongitudeRef'
        self._metadata[k] = pyexiv2.ExifTag(k, sign_lon)
        k = 'Exif.GPSInfo.GPSLongitude'
        self._metadata[k] = pyexiv2.ExifTag(k, frac_lon)

        # Commit
        self._metadata.write()

        print 'Position of {} is now {} - {}'.format( \
                        self._fullpath, coords[0], coords[1])

    @staticmethod
    def _dec_to_sex(x):
        degrees = int(math.floor(x))
        minutes = int(math.floor(60 * (x - degrees)))
        seconds = int(math.floor(6000 * (60 * (x - degrees) - minutes)))
        return (pyexiv2.utils.make_fraction(degrees, 1), pyexiv2.utils.make_fraction(minutes, 1), pyexiv2.utils.make_fraction(seconds, 100))

    @staticmethod
    def _sex_to_dec(fractions):
        degrees = float(fractions[0])
        minutes = float(fractions[1])
        seconds = float(fractions[2])    
        minutes = minutes + (seconds/60)
        degrees = degrees + (minutes/60)
        return degrees
