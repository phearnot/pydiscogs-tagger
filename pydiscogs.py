#!/usr/bin/python

import urllib2, gzip, cStringIO, os
from lxml import etree
from optparse import OptionParser
from mutagen.flac import FLAC

API_KEY = 'b860fc8efb'

XPATH_TRACKS = '//tracklist/track'

TAG_WRITERS = {'.flac':FLAC}

TAG_TRACK_XPATH = {'title':'title/text()', 
    'artist':'artists/artist/name/text()', 
    'tracknumber':'position/text()'}

TAG_RELEASE_XPATH = {'artist':'//release/artists/artist/name/text()',
    'producer':'//producer',
    'releasecountry':'//country/text()',
    'totaltracks':'count(//tracklist/track)',
    'albumartist':'//artists/artist/name/text()',
    'composer':'//composer',
    'catalognumber':'//labels/label/@catno',
    'date':'//released/text()',
    'label':'//labels/label/@name',
    'album':'//release/title/text()'}

release_info = {}

def get_release_info(release_id):
    request = urllib2.Request('http://www.discogs.com/release/%d?f=xml&api_key=%s' % (release_id, API_KEY))  
    request.add_header('Accept-Encoding', 'gzip')  
    data = urllib2.urlopen(request).read()
    unzipped_data = gzip.GzipFile(fileobj = cStringIO.StringIO(data)).read()
    tree = etree.parse(cStringIO.StringIO(unzipped_data))
    for key in TAG_RELEASE_XPATH:
        value = tree.xpath(TAG_RELEASE_XPATH[key])
        if isinstance(value, list) and value:
            release_info[key] = value[0]
        elif value:
            release_info[key] = str(value)
    return tree

def parse_command_line():
    parser = OptionParser(usage='Usage: %prog [options] file1 ...')
    parser.add_option('-i', '--release-id', type='int', dest='release_id', help='Discogs release id', metavar='ID')
    parser.add_option('-n', '--no-save', action='store_false', dest='save', help='Do not save changes to files', default=True)
    parser.add_option('-r', action='store_true', dest='rename', help='Rename files', default=False)
    return parser.parse_args()

def save_track_metadata(file, track_info):
    global opts, args
    print 'Processing file %s' % file
    writer = TAG_WRITERS[os.path.splitext(file)[1].lower()](file)
    for key in TAG_TRACK_XPATH.keys():
        value = track_info.xpath(TAG_TRACK_XPATH[key])
        if isinstance(value, list) and value:
            writer[key] = value[0]
        elif value:
            writer[key] = str(value)
        else:
            writer[key] = release_info[key]
    writer.pprint()
    if opts.save:
        print 'Saving file %s' % file
        writer.save()

def main():
    global opts, args
    (opts, args) = parse_command_line()
    if not len(args):
        print 'No filenames given, will exit now'
        return
    tree = get_release_info(opts.release_id)
    map(save_track_metadata, args, tree.xpath(XPATH_TRACKS)[:len(args)])

if __name__ == '__main__':
    main()
