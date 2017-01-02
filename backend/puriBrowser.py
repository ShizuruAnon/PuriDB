# -*- coding: utf-8 -*-
# pylint: disable=I0011, C, C0302

import mechanize
from bs4 import BeautifulSoup
import cookielib
import socket
import socks
import urlparse
import urllib
import urllib2
import httplib
import time
import sys
import json
import threading
#import puriEvents
import puriCommunication

#import PixivHelper
#from PixivException import PixivException
#import PixivModelWhiteCube
#import PixivModel

defaultCookieJar = None
defaultConfig = None
_browser = None
_browser_manager = None
def start_browser_manager(browserOptions):
    global _browser_manager
    if _browser_manager == None:
        _browser_manager = puriBrowserManager(browserOptions)
        _browser_manager.start()

class puriBrowserManager(threading.Thread):
    def __init__(self, browserOptions):
        #self.parent = parent
        threading.Thread.__init__(self)
        self.comm = puriCommunication.get_communications()
        self.browserOptions = browserOptions
        self.loggedIn = False

    def run(self):
        self.browser = getBrowser(self.browserOptions)
        while True:
            (sender, messageType, message) = self.get_next_command()
            if sender == '':
                pass
            elif messageType == 'browser-doLogin':
                res = self.browser.doLogin()
                self.loggedIn = res
            elif messageType == 'browser-open':
                responce = self.browser.open(message).read()
                self.sendResponse(sender, messageType, responce)
            elif messageType == 'browser-open_novisit':
                responce = self.browser.open_novisit(message)
                self.sendResponse(sender, messageType, responce)


    def get_next_command(self):
        sender = ''
        while sender == '':
            import pdb
            #pdb.set_trace()
            downloaderTime = self.comm.downloaderToBrowser.get_send_time()
            databaseTime = self.comm.databaseToBrowser.get_send_time()
            guiTime = self.comm.guiToBrowser.get_send_time()
            if (downloaderTime < databaseTime) and (downloaderTime < guiTime):
                (messageType, message) = self.comm.downloaderToBrowser.rec_message()
                sender = 'downloader'
            elif (databaseTime < guiTime):
                (messageType, message) = self.comm.databaseToBrowser.rec_message()
                sender = 'database'
            elif (guiTime != sys.float_info.max):
                (messageType, message) = self.comm.guiToBrowser.rec_message()
                sender = 'gui'
        return (sender, messageType, message)


    def sendResponse(self, dest, messageType, message):
        if dest == 'downloader':
            self.comm.browserToDownloader.send_message(messageType, message)
        elif dest == 'database':
            self.comm.browserToDatabase.send_message(messageType, message)
        elif dest == 'gui':
            self.comm.browserToGui.send_message(messageType, message)

# pylint: disable=E1101
class PixivBrowser(mechanize.Browser):
    _browserOptions = None
    #_isWhitecube = False
    #_whitecubeToken = ""
    #_cache = dict()

    def __init__(self, browserOptions, cookieJar):
        mechanize.Browser.__init__(self, factory=mechanize.RobustFactory())
        self._configureBrowser(browserOptions)
        self._configureCookie(cookieJar)


    def _configureBrowser(self, browserOptions):
        if browserOptions == None:
            #PixivHelper.GetLogger().info("No config given")
            return

        global defaultConfig
        if defaultConfig == None:
            defaultConfig = browserOptions

        self._browserOptions = browserOptions
        if browserOptions.useProxy:
            if browserOptions.proxyAddress.startswith('socks'):
                parseResult = urlparse.urlparse(browserOptions.proxyAddress)
                assert parseResult.scheme and parseResult.hostname and parseResult.port
                socksType = socks.PROXY_TYPE_SOCKS5 if parseResult.scheme == 'socks5' else socks.PROXY_TYPE_SOCKS4

                socks.setdefaultproxy(socksType, parseResult.hostname, parseResult.port)
                socks.wrapmodule(urllib)
                socks.wrapmodule(urllib2)
                socks.wrapmodule(httplib)

                #PixivHelper.GetLogger().info("Using SOCKS Proxy: " + browserOptions.proxyAddress)
            else:
                self.set_proxies(browserOptions.proxy)
                #PixivHelper.GetLogger().info("Using Proxy: " + browserOptions.proxyAddress)

        #self.set_handle_equiv(True)
        #self.set_handle_gzip(True)
        self.set_handle_redirect(True)
        self.set_handle_referer(True)
        self.set_handle_robots(False)

        self.set_debug_http(browserOptions.debugHttp)
        #if browserOptions.debugHttp :
            #PixivHelper.GetLogger().info('Debug HTTP enabled.')

        # self.visit_response
        self.addheaders = [('User-agent', browserOptions.useragent)]

        socket.setdefaulttimeout(browserOptions.timeout)


    def _configureCookie(self, cookieJar):
        if cookieJar != None:
            self.set_cookiejar(cookieJar)

            global defaultCookieJar
            if defaultCookieJar == None:
                defaultCookieJar = cookieJar


    def addCookie(self, cookie):
        global defaultCookieJar
        if defaultCookieJar == None:
            defaultCookieJar = cookielib.LWPCookieJar()
        defaultCookieJar.set_cookie(cookie)


    def getPixivPage(self, url, referer="http://www.pixiv.net"):
        ''' get page from pixiv and return as parsed BeautifulSoup object

            throw PixivException as server error
        '''
        url = self.fixUrl(url)
        retry_count = 0
        while True:
            req = urllib2.Request(url)
            req.add_header('Referer', referer)
            try:
                page = self.open(req)
                parsedPage = BeautifulSoup(page.read(), 'html.parser')
                return parsedPage
            except Exception as ex:
                if isinstance(ex, urllib2.HTTPError):
                    if ex.code in [403, 404, 503]:
                        return BeautifulSoup(ex.read(), 'html.parser')

                if retry_count < self._browserOptions.retry:
                    for t in range(1, self._browserOptions.retryWait):
                        print t,
                        time.sleep(1)
                    print ''
                    retry_count = retry_count + 1
                else:
                    raise PixivException("Failed to get page: " + ex.message, errorCode = PixivException.SERVER_ERROR)


    def fixUrl(self, url, useHttps=False):
        ## url = str(url)
        if not url.startswith("http"):
            if not url.startswith("/"):
                url = "/" + url
            if useHttps:
                return "https://www.pixiv.net" + url
            else:
                return "http://www.pixiv.net" + url
        return url

    def _loadCookie(self, cookie_value):
        """ Load cookie to the Browser instance """
        ck = cookielib.Cookie(version=0, name='PHPSESSID', value=cookie_value, port=None,
                             port_specified=False, domain='pixiv.net', domain_specified=False,
                             domain_initial_dot=False, path='/', path_specified=True,
                             secure=False, expires=None, discard=True, comment=None,
                             comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.addCookie(ck)


    def _getInitConfig(self, page):
        init_config = page.find('input', attrs={'id':'init-config'})
        js_init_config = json.loads(init_config['value'])
        return js_init_config

    def loginWithCookie(self):
        """  Log in to Pixiv using saved cookie, return True if success """

        loginCookie = self._browserOptions.loginCookie

        if len(loginCookie) > 0:
            #PixivHelper.printAndLog('info', 'Trying to log with saved cookie')
            self._loadCookie(loginCookie)
            res = self.open('http://www.pixiv.net/mypage.php')
            resData = res.read()

            parsed = BeautifulSoup(resData, 'html.parser')
            self.detectWhiteCube(parsed, res.geturl())

            if "logout.php" in resData:
                #PixivHelper.printAndLog('info', 'Login successfull.')
                #PixivHelper.GetLogger().info('Logged in using cookie')
                return True
            #else:
                #PixivHelper.GetLogger().info('Failed to login using cookie')
                #PixivHelper.printAndLog('info', 'Cookie already expired/invalid.')
        return False


    # TODO: this doesn't work for some reason
    def doLogin(self):

        result = self.loginWithCookie()
        if not result:
            result = self.loginWithoutCookie()

        return result

    def loginWithoutCookie(self):
    	username = self._browserOptions.username
    	password = self._browserOptions.password
        #try:
        #PixivHelper.printAndLog('info', 'Logging in...')
        url = "https://accounts.pixiv.net/login"
        page = self.open(url)

        # get the post key
        parsed = BeautifulSoup(page, 'html.parser')
        js_init_config = self._getInitConfig(parsed)

        data = {}
        data['pixiv_id'] = username
        data['password'] = password
        data['return_to'] = 'http://www.pixiv.net'
        data['lang'] = 'en'
        data['post_key'] = js_init_config["pixivAccount.postKey"]
        data['source'] = "pc"

        request = urllib2.Request("https://accounts.pixiv.net/api/login?lang=en", urllib.urlencode(data))
        response = self.open(request)

        return self.processLoginResult(response)
        #except:
        #PixivHelper.printAndLog('error', 'Error at login(): ' + str(sys.exc_info()))
        #    raise

    def processLoginResult(self, response):
        #PixivHelper.GetLogger().info('Logging in, return url: ' + response.geturl())

        # check the returned json
        js = response.read()
        #PixivHelper.GetLogger().info(str(js))
        result = json.loads(js)
        if result["body"] is not None and result["body"].has_key("successed"):
            for cookie in self._ua_handlers['_cookies'].cookiejar:
                if cookie.name == 'PHPSESSID':
                    #PixivHelper.printAndLog('info', 'new cookie value: ' + str(cookie.value))
                    self._browserOptions.loginCookie = cookie.value
                    #self._browserOptions.writeConfig(path=self._browserOptions.configFileLocation)
                    break

            # check whitecube
            page = self.open(result["body"]["successed"]["return_to"])
            parsed = BeautifulSoup(page, 'html.parser')
            self.detectWhiteCube(parsed, page.geturl())

            return True
        else :
            #if result["body"] is not None and result["body"].has_key("validation_errors"):
            #    PixivHelper.printAndLog('info', "Server reply: " + str(result["body"]["validation_errors"]))
            #else:
            #    PixivHelper.printAndLog('info', 'Unknown login issue, please use cookie login method.')
            return False

    def detectWhiteCube(self, page, url):
        if url.find("pixiv.net/whitecube") > 0:
            print "*******************************************"
            print "* Pixiv whitecube UI mode.                *"
            print "* Some feature might not working properly *"
            print "*******************************************"
            js_init = self._getInitConfig(page)
            self._whitecubeToken = js_init["pixiv.context.token"]
            print "whitecube token:", self._whitecubeToken
            self._isWhitecube = True

    def parseLoginError(self, res):
        page = BeautifulSoup(res.read(), 'html.parser')
        r = page.findAll('span', attrs={'class': 'error'})
        return r

    def getImagePage(self, imageId, parent=None, fromBookmark=False,
                     bookmark_count=-1, image_response_count=-1):
        image = None
        response = None
        PixivHelper.GetLogger().debug("Getting image page: {0}".format(imageId))
        if self._isWhitecube:
            url = "https://www.pixiv.net/rpc/whitecube/index.php?mode=work_details_modal_whitecube&id={0}&tt={1}".format(imageId, self._whitecubeToken)
            response = self.open(url).read()
            PixivHelper.GetLogger().debug(response)
            image = PixivModelWhiteCube.PixivImage(imageId,
                                                   response,
                                                   parent,
                                                   fromBookmark,
                                                   bookmark_count,
                                                   image_response_count,
                                                   dateFormat=self._browserOptions.dateFormat)
            # overwrite artist info
            if fromBookmark:
                self.getMemberInfoWhitecube(image.originalArtist.artistId, image.originalArtist)
            else:
                self.getMemberInfoWhitecube(image.artist.artistId, image.artist)
        else:
            url = "http://www.pixiv.net/member_illust.php?mode=medium&illust_id={0}".format(imageId)
            response = self.open(url).read()
            parsed = BeautifulSoup(response, 'html.parser')
            image = PixivModel.PixivImage(imageId,
                                          parsed,
                                          parent,
                                          fromBookmark,
                                          bookmark_count,
                                          image_response_count,
                                          dateFormat=self._browserOptions.dateFormat)
            if image.imageMode == "ugoira_view" or image.imageMode == "bigNew":
                image.ParseImages(parsed)
            parsed.decompose()

        return (image, response)


    def getMemberInfoWhitecube(self, member_id, artist, bookmark=False):
        ''' get artist information using AppAPI '''
        url = 'https://app-api.pixiv.net/v1/user/detail?user_id={0}'.format(member_id)
        if self._cache.has_key(url):
            info = self._cache[url]
        else:
            PixivHelper.GetLogger().debug("Getting member information: {0}".format(member_id))
            infoStr = self.open(url).read()
            info = json.loads(infoStr)
            self._cache[url] = info
        artist.ParseInfo(info, False, bookmark=bookmark)


    def getMemberBookmarkWhiteCube(self, member_id, page, limit, tag):
        response = None
        PixivHelper.printAndLog('info', 'Getting Bookmark Url for page {0}...'.format(page))
        # iterate to get next page url
        start = 1
        last_member_bookmark_next_url = None
        while start <= page:
            if start == 1:
                url = 'https://www.pixiv.net/rpc/whitecube/index.php?mode=user_collection_unified&id={0}&bookmark_restrict={1}&limit={2}&is_profile_page={3}&is_first_request={4}&max_illust_bookmark_id={5}&max_novel_bookmark_id={6}&tt={7}&tag={8}'
                url = url.format(member_id, 0, limit, 1, 1, 0, 0, self._whitecubeToken, tag)
            else:
                url = last_member_bookmark_next_url

            # PixivHelper.printAndLog('info', 'Member Bookmark Page {0} Url: {1}'.format(start, url))
            if self._cache.has_key(url):
                response = self._cache[url]
            else:
                response = self.open(url).read()
                self._cache[url] = response

            payload = json.loads(response)
            last_member_bookmark_next_url = payload["body"]["next_url"]
            if last_member_bookmark_next_url is None and start  < page:
                PixivHelper.printAndLog('info', 'No more images for {0} bookmarks'.format(member_id))
                url = None
                break

            start = start + 1
        PixivHelper.printAndLog('info', 'Member Bookmark Page {0} Url: {1}'.format(page, url))
        return (url, response)


    def getMemberPage(self, member_id, page=1, bookmark=False, tags=None):
        artist = None
        response = None
        if tags is not None:
            tags = PixivHelper.encode_tags(tags)

        if self._isWhitecube:
            limit = 50
            if bookmark:
                (url, response) = self.getMemberBookmarkWhiteCube(member_id, page, limit, tags)
            else:
                offset = (page - 1) * limit
                url = 'https://www.pixiv.net/rpc/whitecube/index.php?mode=user_new_unified&id={0}&offset_illusts={1}&offset_novels={2}&limit={3}&tt={4}'.format(member_id, offset, 0, limit, self._whitecubeToken)
                if tags is not None:
                    url = url + '&tag={0}'.format(tags)
                elif self._browserOptions.r18Mode:
                    url = url + '&tag=R-18'
                PixivHelper.printAndLog('info', 'Member Url: ' + url)

            if url is not None:
                response = self.open(url).read()
                PixivHelper.GetLogger().debug(response)
                artist = PixivModelWhiteCube.PixivArtist(member_id, response, False)
                self.getMemberInfoWhitecube(member_id, artist, bookmark)

        else:
            if bookmark:
                member_url = 'http://www.pixiv.net/bookmark.php?id=' + str(member_id) + '&p=' + str(page)
            else:
                member_url = 'http://www.pixiv.net/member_illust.php?id=' + str(member_id) + '&p=' + str(page)

            if tags is not None:
                member_url = member_url + "&tag=" + tags
            elif self._browserOptions.r18Mode and not bookmark:
                member_url = member_url + '&tag=R-18'
                PixivHelper.printAndLog('info', 'R-18 Mode only.')
            PixivHelper.printAndLog('info', 'Member Url: ' + member_url)
            response = self.getPixivPage(member_url)
            artist = PixivModel.PixivArtist(mid=member_id, page=response)

        return (artist, response)


    def getSearchTagPage(self, tags, i,
                         wild_card=True,
                         title_caption=False,
                         start_date=None,
                         end_date=None,
                         member_id=None,
                         oldest_first=False,
                         start_page=1):
        response = None
        result = None

        if self._isWhitecube:
            if member_id is None:
                # from search page:
                # https://www.pixiv.net/rpc/whitecube/index.php?order=date&adult_mode=include&q=vocaloid&p=0&type=&mode=whitecube_search&s_mode=s_tag&scd=&size=&ratio=&like=&tools=&tt=4e2cdee233f1156231ee99da1e51a83c
                url = "https://www.pixiv.net/rpc/whitecube/index.php?q={0}".format(tags)
                url = url + "&adult_mode={0}".format("include")
                url = url + "&mode={0}".format("whitecube_search")

                # date ordering
                order = "date_d"
                if oldest_first:
                    order = "date"
                url = url + "&order={0}".format(order)

                # search mode
                s_mode = "s_tag_full"
                if wild_card:
                    s_mode = "s_tag"
                elif title_caption:
                    s_mode ="s_tc"
                url = url + "&s_mode={0}".format(s_mode)

                # start/end date
                if start_date is not None:
                    url = url + "&scd={0}".format(start_date)
                if end_date is not None:
                    url = url + "&ecd={0}".format(end_date)

                url = url + "&p={0}".format(i)
                url = url + "&start_page={0}".format(start_page)
                url = url + "&tt={0}".format(self._whitecubeToken)

                PixivHelper.printAndLog('info', 'Looping for {0} ...'.format(url))
                response = self.open(url).read()
                PixivHelper.GetLogger().debug(response)
                result = PixivModelWhiteCube.PixivTags()
                result.parseTags(response, tags)
            else:
                # from member id search by tags
                (artist, response) = self.getMemberPage(member_id, i, False, tags)
                # convert to PixivTags
                result = PixivModelWhiteCube.PixivTags()
                result.parseMemberTags(artist, member_id, tags)
        else:
            url = PixivHelper.generateSearchTagUrl(tags, i,
                                                   title_caption,
                                                   wild_card,
                                                   oldest_first,
                                                   start_date,
                                                   end_date,
                                                   member_id,
                                                   self._browserOptions.r18Mode)

            PixivHelper.printAndLog('info', 'Looping... for ' + url)
            response = self.open(url).read()
            parse_search_page = BeautifulSoup(response, 'html.parser')

            if self._browserOptions.dumpTagSearchPage and self._browserOptions.enableDump:
                dump_filename = PixivHelper.dumpHtml(url + ".html", parse_search_page)
                PixivHelper.printAndLog('info', "Dump tag search page to: " + dump_filename)

            result = PixivModel.PixivTags()
            if not member_id is None:
                result.parseMemberTags(parse_search_page, member_id, tags)
            else:
                try:
                    result.parseTags(parse_search_page, tags)
                except:
                    PixivHelper.dumpHtml("Dump for SearchTags " + tags + ".html", response)
                    raise

            parse_search_page.decompose()
            del parse_search_page

        return (result, response)


def getBrowser(config = None, cookieJar = None):
    global defaultCookieJar
    global defaultConfig
    global _browser

    if _browser is None:
        if config != None:
            defaultConfig = config
        if cookieJar != None:
            defaultCookieJar = cookieJar
        if defaultCookieJar == None:
            #PixivHelper.GetLogger().info("No default cookie jar available, creating... ")
            defaultCookieJar = cookielib.LWPCookieJar()
        _browser = PixivBrowser(defaultConfig, defaultCookieJar)

    return _browser


def getExistingBrowser():
    global _browser
    if _browser is None:
        raise PixivException("Browser is not initialized yet!", errorCode = PixivException.NOT_LOGGED_IN)
    return _browser


# pylint: disable=W0612
def test():
    from PixivConfig import PixivConfig
    cfg = PixivConfig()
    cfg.loadConfig("./config.ini")
    b = getBrowser(cfg, None)
    success = False
    if cfg.cookie is not None and len(cfg.cookie) > 0:
        success = b.loginUsingCookie(cfg.cookie)
    elif not success:
        success = b.login(cfg.username, cfg.password)

    if success:
        def testSearchTags():
            print "test search tags"
            tags = "VOCALOID"
            p = 1
            wild_card=True
            title_caption=False
            start_date="2016-11-06"
            end_date="2016-11-07"
            member_id=None
            oldest_first=True
            start_page=1
            (resultS, page) = b.getSearchTagPage(tags, p,
                                                wild_card,
                                                title_caption,
                                                start_date,
                                                end_date,
                                                member_id,
                                                oldest_first,
                                                start_page)
            resultS.PrintInfo()
            assert(len(resultS.itemList) > 0)

        def testImage():
            print "test image mode"
            print ">>"
            (result, page) = b.getImagePage(60040975)
            print result.PrintInfo()
            assert(len(result.imageTitle) > 0)
            print result.artist.PrintInfo()
            assert(len(result.artist.artistToken) > 0)
            assert(not("R-18" in result.imageTags))
            assert(result.worksTools.find("CLIP STUDIO PAINT") > -1)

            print ">>"
            (result2, page2) = b.getImagePage(59628358)
            print result2.PrintInfo()
            assert(len(result2.imageTitle) > 0)
            print result2.artist.PrintInfo()
            assert(len(result2.artist.artistToken) > 0)
            assert("R-18" in result2.imageTags)

            print ">> ugoira"
            (result3, page3) = b.getImagePage(60070169)
            print result3.PrintInfo()
            assert(len(result3.imageTitle) > 0)
            print result3.artist.PrintInfo()
            print result3.ugoira_data
            assert(len(result3.artist.artistToken) > 0)
            assert(result3.imageMode == 'ugoira_view')


        def testMember():
            print "Test member mode"
            print ">>"
            (result3, page3) = b.getMemberPage(1227869, page=1, bookmark=False, tags=None)
            print result3.PrintInfo()
            assert(len(result3.artistToken) > 0)
            assert(len(result3.imageList) > 0)
            print ">>"
            (result4, page4) = b.getMemberPage(1227869, page=2, bookmark=False, tags=None)
            print result4.PrintInfo()
            assert(len(result4.artistToken) > 0)
            assert(len(result4.imageList) > 0)
            print ">>"
            (result5, page5) = b.getMemberPage(4894, page=1, bookmark=False, tags=None)
            print result5.PrintInfo()
            assert(len(result5.artistToken) > 0)
            assert(len(result5.imageList) > 0)
            print ">>"
            (result6, page6) = b.getMemberPage(4894, page=3, bookmark=False, tags=None)
            print result6.PrintInfo()
            assert(len(result6.artistToken) > 0)
            assert(len(result6.imageList) > 0)

        def testMemberBookmark():
            print "Test member bookmarks mode"
            print ">>"
            (result5, page5) = b.getMemberPage(1227869, page=1, bookmark=True, tags=None)
            print result5.PrintInfo()
            assert(len(result5.artistToken) > 0)
            assert(len(result5.imageList) > 0)
            print ">>"
            (result6, page6) = b.getMemberPage(1227869, page=2, bookmark=True, tags=None)
            print result6.PrintInfo()
            assert(len(result6.artistToken) > 0)
            assert(len(result6.imageList) > 0)
            print ">>"
            (result6, page6) = b.getMemberPage(1227869, page=10, bookmark=True, tags=None)
            if result6 is not None:
                print result6.PrintInfo()
            (result6, page6) = b.getMemberPage(1227869, page=12, bookmark=True, tags=None)
            if result6 is not None:
                print result6.PrintInfo()
                assert(len(result6.artistToken) > 0)
                assert(len(result6.imageList) == 0)

        ## testSearchTags()
        testImage()
        ## testMember()
        ## testMemberBookmark()

    else:
        print "Invalid username or password"

if __name__ == '__main__':
    test()
    print "done"