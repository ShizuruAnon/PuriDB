# -*- coding: utf-8 -*-

import sys
import urllib
import urllib2
from bs4 import BeautifulSoup

import puriDataStructures

import pdb


def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def encode_search_tags(tags):
    searchString = ''
    for tag in tags:
        if not tag.startswith("%"):
            # Encode the tags
            tag = tag.encode('utf-8')
            tag = urllib.quote_plus(tag)
        searchString += '%20' + tag
    return searchString

def decode_search_tags(tags):
    # decode tags.
    try:
        if tags.startswith("%"):
            tags = to_unicode(urllib.unquote_plus(tags))
        else:
            tags = to_unicode(tags)
    except UnicodeDecodeError:
        # From command prompt
        tags = tags.decode(sys.stdout.encoding).encode("utf8")
        tags = to_unicode(tags)
    return search_tags


def generate_search_tag_url(page, searchInfo):
    tags = encode_search_tags(searchInfo.tags)
    url = ""
    dateParam = ""
    if searchInfo.startDate is not u'':
        dateParam = dateParam + "&scd=" + searchInfo.startDate
    if searchInfo.endDate is not u'':
        dateParam = dateParam + "&ecd=" + searchInfo.endDate

    if not searchInfo.memberId is u'':
        url = 'http://www.pixiv.net/member_illust.php?id=' + str(searchInfo.memberId) + '&tag=' + tags + '&p=' + str(page)
    else:
        if searchInfo.titleCaption:
            url = 'http://www.pixiv.net/search.php?s_mode=s_tc&p=' + str(page) + '&word=' + tags + dateParam
            print u"Using Title Match (s_tc)"
        else:
            if searchInfo.wildCard:
                url = 'http://www.pixiv.net/search.php?s_mode=s_tag&p=' + str(page) + '&word=' + tags + dateParam
                print u"Using Partial Match (s_tag)"
            else:
                url = 'http://www.pixiv.net/search.php?s_mode=s_tag_full&word=' + tags + '&p=' + str(page) + dateParam
                print u"Using Full Match (s_tag_full)"
                import pdb
                pdb.set_trace()

    if searchInfo.r18Mode:
        url = url + '&r18=1'

    if searchInfo.oldestFirst:
        url = url + '&order=date'
    else:
        url = url + '&order=date_d'

    # encode to ascii
    url = unicode(url).encode('iso_8859_1')

    return url

def parseImageHtml(imageHtml):
    imageInfo = puriDataStructures.puriImageInfo()

    classInfo = imageHtml.a['class']
    if classInfo == ['work', '_work', '']:
        imageType = 'pixiv_image'
    elif classInfo == ['work', '_work', 'multiple', '']:
        imageType = 'pixiv_manga'
    elif classInfo == ['work', '_work', 'ugoku-illust', '']:
        imageType = 'pixiv_ugoira'
    imageInfo.add_tag('image_type', imageType)

    imageInfo.add_tag('image_id', imageHtml.img['data-id'])
    imageInfo.add_tag('artist_id', imageHtml.img['data-user-id'])
    imageInfo.add_tag('image_name', imageHtml.h1['title'])
    artistName = imageHtml.find('a', {'class':['user', 'ui-profile-popup']})['data-user_name']
    imageInfo.add_tag('artist_name', artistName)

    bookmarkHtml = imageHtml.find('a', {'class':['bookmark-count', 'ui-tooltip']})
    if bookmarkHtml != None:
        bookmarkString = bookmarkHtml['data-tooltip']
        bookmarkString = bookmarkString[0:bookmarkString.find(u'件')]
        bookmarkString = bookmarkString.replace(',', '')
        numBookmarks = int(bookmarkString)
    else:
        numBookmarks = 0
    imageInfo.add_tag('num_bookmarks', numBookmarks)
    
    tags = imageHtml.img['data-tags'].split()
    for tag in tags:
        imageInfo.add_tag('tag', tag)

    return imageInfo


def parse_tags(responce, searchInfo):

    page = BeautifulSoup(responce, 'html.parser')

    pageImageInfo = []
    allImagesInPageHtml = page.findAll('li', {'class':'image-item'})
    for imageHtml in allImagesInPageHtml:
        pageImageInfo.append(parseImageHtml(imageHtml))

    page.decompose()
    del page
    return pageImageInfo

def create_custom_request(url, referer = 'http://www.pixiv.net', head = False):
    req = urllib2.Request(url)

    req.add_header('Referer', referer)
    #printAndLog('info', u"Using Referer: " + str(referer))

    if head:
        req.get_method = lambda : 'HEAD'
    else:
        req.get_method = lambda : 'GET'

    return req
##def



'''
fName = picsFolder + str(imageInfo.imageId) + '.zip'
f = file(fName, 'wb+')
f.write(res.read())
f.close()
'''
'''
tempUgoiraFolder = picsFolder + 'tempUgoira/'
if not os.path.exists(tempUgoiraFolder):
    os.makedirs(tempUgoiraFolder)

z = zipfile.ZipFile(fName)
z.extractall(tempUgoiraFolder)


durations = []
images = []
fns = []
json_ugoira_data = json.loads(imageInfo.ugoira_data)
for info in json_ugoira_data['frames']:
    fns.append(tempUgoiraFolder +info['file'])
    img = imageio.imread(tempUgoiraFolder + info['file'])
    images.append(img)
    durations.append(float(info['delay'])/1000.0)

print len(images)
print len(durations)


from myImages2gif import writeGif
from PIL import Image
kargs = { 'duration': durations }
tmpName = tempUgoiraFolder + 'temp.gif'
tmpName2 = tempUgoiraFolder + 'temp2.gif'

images2 = [Image.open(fn) for fn in fns]
writeGif(tmpName2, images2, duration=0.3, dither=0)
#imageio.mimwrite(tmpName, images, 'GIF', **kargs)
#imageio.mimsave(tmpName, images, 'GIF')
#shutil.move(tmpName, picsFolder + str(imageInfo.imageId) + '.gif')

#shutil.rmtree(tempUgoiraFolder)
'''

