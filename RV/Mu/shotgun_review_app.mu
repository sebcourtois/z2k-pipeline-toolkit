
module: shotgun_review_app {

use commands;
use rvtypes;
use extra_commands;
use export_utils;
use external_qprocess;
use mode_manager;
use qt;
use io;

require shotgun_mode;
require shotgun_fields;
require shotgun_stringMap;
require shotgun_upload;
require rvui;
require system;
require math;
require runtime;

StringMap := shotgun_stringMap.StringMap;

global bool SGR_DEBUG = false;

global bool SGR_PLAY = true;

global string[] ADDED_SEQ_GRPS;
global let DEFAULT_SEQ_NODE = "reviewAppSequenceGroup";
global let CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;


////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// The following 3 globals are there to allow the asynchronous execution of launchTimeline and launchSubmitTool
//
// Explanation:
// When an RVLINK is called, it fires two methods sequentially, setServer and launchWhatever.  Before,
// setServer was a blocking function that had finished switching the server when it exited.  Now that we
// authenticate with shotgun server creds, the method is asynchronous and returns immediately.
// When that happens, launchWhatever is called even if the server change didn't go through yet.
// So we needed a way to handle that race condition.
//
// Here's how it works:
// When you set ASYNC_LICENSE_SWITCH_IN_PROGRESS to false, the general case is processed and method code is
// executed as they are called.
// When you set ASYNC_LICENSE_SWITCH_IN_PROGRESS to true, it means that the next call to launchWhatever
// should be done only when the previous call was completed.  NEXT_CALL_AFTER_LICENSE_SWITCH contains the
// function pointer to launchWhatever, and NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM contains the parameter
// that's passed to NEXT_CALL_AFTER_LICENSE_SWITCH.
//
global bool ASYNC_LICENSE_SWITCH_IN_PROGRESS = false;
global (void; [(string, string)]) NEXT_CALL_AFTER_LICENSE_SWITCH = nil;
global [(string, string)] NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM = nil;

\: deb(void; string s) { if (SGR_DEBUG) print("screening room: " +s); }

// This class is a proxy for the SLUtils library
class: SLUtils
{
    ((string,string,string,string); string) getSessionParamsFromUrl;
    ((string, string, string, string, string, string, string);) getCurrentSessionParams;
    (bool; string) isUrlInLastSession;
    (void; string, string, string, string, string, (void; bool)) changeLoginToUrlAndUName;

    method: SLUtils (SLUtils;)
    {
        if (runtime.load_module("slutils")) {
            runtime.name name;

            try {
                name = runtime.intern_name("slutils.getSessionParamsFromUrl");
                this.getSessionParamsFromUrl = runtime.lookup_function(name);    

                name = runtime.intern_name("slutils.getCurrentSessionParams");
                this.getCurrentSessionParams = runtime.lookup_function(name);

                name = runtime.intern_name("slutils.isUrlInLastSession");
                this.isUrlInLastSession = runtime.lookup_function(name);

                name = runtime.intern_name("slutils.changeLoginToUrlAndUName");
                this.changeLoginToUrlAndUName = runtime.lookup_function(name);
            }
            catch (...) {;}

        } else {
            print("ERROR: SLUtils proxy not initialized in shotgun_review_app.mu\n");
        }
    }
}

// Global pointer for the SLUtils proxy
global SLUtils _slUtils = nil;

\: getSLUtils (SLUtils;)
{
    if (_slUtils eq nil) {
        _slUtils = SLUtils();
    }

    return _slUtils;
}

// This retrieves connection parameters associated with an URL
\: getSessionParamFromSLUtils((string, string, string, string); string url)
{
    return getSLUtils().getSessionParamsFromUrl(url);
}

// This retrieves the connection parameters associated with the default session
\: getDefaultSessionFromSLUtils((string, string, string, string, string, string, string);)
{
    return getSLUtils().getCurrentSessionParams();
}

\: isUrlInLastSessionFromSLUtils(bool; string url)
{
    return getSLUtils().isUrlInLastSession(url);
}


// Custom cookie management for the QWebViews. By default, QtWebKit only stores
// cookies in memory, so they're lost when you quit the app. Here, we store the
// cookies to and read them from a QSettings file.
class: CookieJar : QNetworkCookieJar
{
    // All of the cookies will be stored in this list of tuples. The first
    // component of the tuple is the host name and the second component is a
    // list of all cookies for that host.
    [(string, QNetworkCookie[])] _allCookies;
    
    // Load all of our saved cookies from a QSettings file, disregarding any
    // cookies that might have expired
    method: loadSettings(void; QUrl url)
    {
        deb("INFO: Loading Cookies\n");

        QNetworkCookie[] cookieList;

        // Read the cookies from RV settings. They'll be an array of strings
        // The strings are organized into chunks of three where the first
        // element is the name of the cookie, the second is its value and
        // the third is its expiration time as a unix timestamp
        let SettingsValue.StringArray cookies = readSetting("ReviewApp", url.host(), SettingsValue.StringArray(string[]{}) );

        // Try to reach the SLModule registry to get the last session cookie
        (string, string, string, string, string, string, string) slSessionParam = ("", "", "", "", "", "", "");
        bool isRVDefaultSessionActive = isUrlInLastSessionFromSLUtils(url.host());

        if (isRVDefaultSessionActive) {
            slSessionParam = getDefaultSessionFromSLUtils();

            deb("INFO: We are starting a session based on RV session data...\n");
            deb("INFO: The startup session data is: %s %s %s %s %s %s %s\n" % (slSessionParam._0, slSessionParam._1, slSessionParam._2, 
                                                                                slSessionParam._3, slSessionParam._4, slSessionParam._5, slSessionParam._6));
        }

        bool isPatchedSID = false;     // Did we patched any session id in the existing cookies?
        bool isPatchedCSRF = false;    // Did we patch any csrf-related tokens in the existing cookies?

        // Iterate over each chunk of three strings
        int i;
        for (i = 0; i < cookies.size(); i+=3) {
            // If any of the cookies fail to be read then we abort and return
            // an empty cookie list. This might happen if the way the cookies
            // are stored changes.
            try {
                // Get the expiration date of this cookie
                let x = QDateTime.fromTime_t( int(cookies[i+2]) );

                // If it's earlier than the current time then we move on to the
                // next chunk
                if ( x < QDateTime.currentDateTime() ) {
                    continue;
                }

                if (isRVDefaultSessionActive) {
                    deb("INFO: Patching existing cookies!\n");
                    // If there's a session cookie in there, patch its value to the current session value
                    if ((cookies[i] == "_session_id") && (slSessionParam._2 != "")) {
                        cookies[i+1] = slSessionParam._2;
                        isPatchedSID = true;
                    }

                    // If there's a csrf token in there, patch its value into the current session value
                    if (cookies[i] == slSessionParam._4 && slSessionParam._5 != "") {
                        cookies[i+1] = slSessionParam._5;
                        isPatchedCSRF = true;
                    }

                    // Add a week to the said initial date
                    x = QDateTime.fromTime_t( int(slSessionParam._6) + 604800);
                }

                // Create a QNetworkCookie with the same name, value and
                // expiration time as this cookie
                let n = QByteArray().append(cookies[i]);
                let v = QByteArray().append(cookies[i+1]);
                let c = QNetworkCookie(n, v);
                c.setExpirationDate(x);

                // Append it to our cookie list
                cookieList.push_back(c);
            }
            catch(...)
            {
                cookieList = QNetworkCookie[]{};
                break;
            }
        }

        if (isRVDefaultSessionActive) {
            let x = QDateTime.fromTime_t((QDateTime.currentMSecsSinceEpoch() / 1000) + 172800); // Assume RV timestamp is unavailable by default, give two day

            if (slSessionParam._6 != "") {
                deb("INFO: Init date setup from RV\n");
                x = QDateTime.fromTime_t( int(slSessionParam._6) + 604800);                     // RV drives the date, give one week!
            } else {
                deb("INFO: Init date setup from now, plus two days\n");  
            }

            // If we didn't patch the session id cookie and we have a current session, add the cookie now
            if (!isPatchedSID && slSessionParam._2 != "") {
                deb("INFO: Adding new session id cookie\n");

                let n = QByteArray().append("_session_id");
                let v = QByteArray().append(slSessionParam._2);
                let c = QNetworkCookie(n, v);
                c.setExpirationDate(x);

                // Append it to our cookie list
                cookieList.push_back(c);
            }

            // If we didn't patch the csrf cookie and we have a current session, add the cookie now
            if (!isPatchedCSRF && slSessionParam._4 != "") {
                deb("INFO: Adding new csrf cookie\n");

                let n = QByteArray().append(slSessionParam._4);
                let v = QByteArray().append(slSessionParam._5);
                let c = QNetworkCookie(n, v);
                c.setExpirationDate(x);

                // Append it to our cookie list
                cookieList.push_back(c);
            }
        }

        // Append the cookies for this host to our cookies table
        _allCookies = (url.host(), cookieList) : _allCookies;
    }

    // Store the current set of cookies to a Settings file
    method: saveSettings(void; QNetworkCookie[] cookieList, QUrl url)
    {
        // Instantiate a new string array to be stored in the settings file
        let SettingsValue.StringArray cookies = SettingsValue.StringArray(string[]{});

        // Iterate over the given list of cookies
        for_each(cookie; cookieList) {
            let expiryDate = cookie.expirationDate();

            // Create a string from each of the byte arrays
            let n = osstream(),
                v = osstream();
            n.write( cookie.name().constData() );
            v.write( cookie.value().constData() );

            if ( cookie.isSessionCookie() ) {
                // Intercept the _session_id and csrf_tokens and let them
                // persist for 1 day
                if ( string(n) == "_session_id" ||
                     regex.match( "^csrf_token_u[0-9]+$", string(n) ) ) {
                    expiryDate = QDateTime.currentDateTime().addDays(1);
                } else {
                    // Do not store any other session cookies to file
                    continue;
                }
            }

            // Store the cookie name, value as strings. We convert the expiry
            // date to a unix timestamp and store it as a string, too.
            cookies.push_back( string(n) );
            cookies.push_back( string(v) );
            cookies.push_back( "%d" % expiryDate.toTime_t() );
        }

        // Write out the cookies for this host to file
        writeSetting("ReviewApp", url.host(), SettingsValue.StringArray(cookies) );
    }

    // Return all of the cookies for the given url
    method: cookiesForUrl(QNetworkCookie[]; QUrl url)
    {
        // If we've already loaded the cookies for this site then we can look
        // for the host name in our cookie table and return whatever we
        // find there
        for_each(cookiesTuple; _allCookies) {
            if ( cookiesTuple._0 == url.host() ) {
                return cookiesTuple._1;
            }
        }

        // If we didn't see it then we attempt to load the cookies for this url
        loadSettings(url);

        // Look for it in the cookies table once again
        for_each(cookiesTuple; _allCookies) {
            if ( cookiesTuple._0 == url.host() ) {
                return cookiesTuple._1;
            }
        }

        // If all else fails we return an empty cookie list
        return QNetworkCookie[]{};
    }

    // Add the given cookies for the given url
    method: setCookiesFromUrl(bool; QNetworkCookie[] cookieList, QUrl url)
    {
        // Check whether the cookies from the QSettings file have already been
        // read in for this host
        bool settingsLoaded = false;
        for_each(cookiesTuple; _allCookies) {
            if ( cookiesTuple._0 == url.host() ) {
                settingsLoaded = true;
                break;
            }
        }

        // If not, load them
        if ( !settingsLoaded ) {
            loadSettings(url);
        }

        // Now grab the cookies for this host from the cookies table
        QNetworkCookie[] cookies;
        for_each(cookiesTuple; _allCookies) {
            if ( cookiesTuple._0 == url.host() ) {
                cookies = cookiesTuple._1;
                break;
            }
        }

        // Iterate over the given list of cookies
        for_each(cookie; cookieList) {
            // Check if a cookie with this name exists already in the current
            // set of cookies. If so, we'll overwrite it
            bool cookieFound = false;
            int i;
            for (i = 0; i < cookies.size(); i++) {
                let n = osstream(),
                v = osstream();
                n.write( cookies[i].name().constData() );
                v.write( cookies[i].value().constData() );
                // deb("INFO:                      type(%s) key(%s) value(%s)\n" % (cookies[i].name(), string(n), string(v)));
                // A cookie with this name was found! Update its value and
                // expiration date
                if ( cookies[i].name() == cookie.name() ) {
                    cookies[i].setValue(cookie.value());
                    cookies[i].setExpirationDate( cookie.expirationDate() );
                    cookieFound = true;
                    break;
                }
            }

            // If not, we'll append it to the list of cookies
            if ( !cookieFound ) {
                cookies.push_back(cookie);
            }
        }

        // Save all of these cookies to a QSettings file
        saveSettings(cookies, url);
        return true;
    }

    // Empty out the settings for every site we're tracking
    method: clearAllCookies(void;) {
        deb("INFO: Clearing all cookies\n");
        // Iterate over each site stored in the cookie list and clear the cookies
        // that are stored to file
        int i;
        for_each(cookieTuple; _allCookies) {
            let url = QUrl("http://%s" % cookieTuple._0);
            let cookies = QNetworkCookie[]{};

            deb("Saving settings for url: %s" % url.toString(QUrl.None));
            saveSettings(cookies, url);
        }

        // Next clear all the cookies in memory
        // I can't figure out how to declare an empty Mu list on the RHS, so
        // I'll just declare a new list and assign it to _allCookies
        [(string, QNetworkCookie[])] empty;
        _allCookies = empty;
    }

    method: CookieJar (CookieJar; QObject parent=nil)
    {
        QNetworkCookieJar.QNetworkCookieJar(this, parent);
    }
}

class: ReviewAppMinorMode : MinorMode
{
    QDockWidget[]  _dockWidgets;
    QWidget[]      _baseWidgets;
    QWebView[]     _webViews;
    QProgressBar[] _progressBars;
    QWidget[]      _titleBarWidgets;
    QNetworkAccessManager _networkAccessManager;
    string _sessionUrl;

    // Storage for version info
    (string, int, QDateTime, StringMap)[] _infoCache;
    (string, int, string, QDateTime, int[])[] _entityVersionsCache;
    int _infoCacheMaxItems;
    int _sourceCacheMaxSize;
    int _maxCacheAgeSecs;

    // Keep track of the last frame that the use was on so that we can detect if
    // the source at that frame differs from the current frame
    int _lastVersionId;
    bool _sessionIsLoading;
    bool _fetching;

    string[] _allShotgunSourceNames;
    int[] _allShotgunSourceIds;

    // We'll use these to inform the Review App UI that it shouldn't be doing any
    // more updating
    int _updateFrequency;
    bool _detailPanePinnedWhenPlaying;
    string _mystate;
    QTimer _playStopTimer;
    QTimer _propertyChangedTimer;
    QTimer _inputsChangedTimer;
    bool _frameChangeUpdatesDisabled;

    // When using the previousFlaggedVersion and nextFlaggedVersion keyboard
    // shortcuts, this member attribute stores the initial non-flagged version
    // so that it will be cycled through along with other flagged versions in
    // the same entity
    StringMap _activeVersion;

    // Stored pane position information
    int[] _floating;
    int[] _sizes;
    int[] _positions;
    int[] _hidden;
    QByteArray _mainWindowGeometry;
    bool _geometryRestored;
    bool _allHidden;

    StringMap[] _postProgLoadInfos;
    string[] _preProgLoadSources;
    bool _postProgLoadTurnOnWipes;
    (void; string[]) _postProgLoadCallback;

    // Whether to allow directories to be loaded
    bool _allowDirectories;

    // Convert from the name of a pane quadrant to an index into the widgets arrays
    method: nameToIndex (int; string name)
    {
        if (name == "Left")   return 0;
        if (name == "Right")  return 1;
        if (name == "Top")    return 2;
        if (name == "Bottom") return 3;
        return 0;
    }

    // Convert from an index into the widgets array to the name of a pane quadrant
    method: indexToName (string; int index)
    {
        if (index == 0) return "Left";
        if (index == 1) return "Right";
        if (index == 2) return "Top";
        if (index == 3) return "Bottom";
        return "Left";
    }

    // Reset the progress bar that displays when loading content from a site
    method: progressReset (void; int index, bool ok)
    {
        _progressBars[index].reset();
        _baseWidgets[index].setMaximumSize( QSize(16777215, 16777215) );
        _baseWidgets[index].setMinimumSize( QSize(0, 0) );
    }

    // Set the progress for a pane
    method: progress (void; int index, int value)
    {
        _progressBars[index].setValue(value);
    }

    // Dynamically hide and show a title bar for a pane based on whether the pane
    // is floating or docked. This is hooked up to a Qt event that informs us of
    // a change to the widget's floating state
    method: showTitleBar(void; int index, bool floating) {
        QWidget w;

        // If the pane is now floating, then we restore its original title bar
        if (floating) {
            w = _titleBarWidgets[index];

        // Otherwise we remove the title bar
        } else {
            w = QWidget(mainWindowWidget(), 0);
        }

        _dockWidgets[index].setTitleBarWidget(w);

        // We emit an event that we can listen for on the javascript side so that
        // we know when to change the undock icon to a dock icon and vice versa
        string contents = "%s;%d" % (indexToName(index), if (floating) then 1 else 0);
        sendInternalEvent("sg-pane-top-level-changed", contents);
    }

    // Initialise a new webview
    method: initView (void; int index, string url, int startSize=0)
    {
        SGR_PLAY = true;

        // The UI file contains the definition for how our pane is layed out
        let uiFilePath = path.join(supportPath("shotgun_review_app", "screening_room"),
            "webview_panel.ui");

        // Create the component widgets of our pane
        _dockWidgets[index]  = QDockWidget("Screening Room", mainWindowWidget(), 0);
        _baseWidgets[index]  = loadUIFile(uiFilePath, mainWindowWidget());
        _webViews[index]     = _baseWidgets[index].findChild("webView");
        _progressBars[index] = _baseWidgets[index].findChild("progressBar");

        // Keep track of the title bar widget for the pane. We'll be dynamically
        // adding and removing it based on whether the pane is docked. We can't
        // just hide() the title bar widget (for reasons unknown). We must remove
        // it from the pane. So we need to store it somewhere so that it can be
        // restored at a later time.
        _titleBarWidgets[index] = _dockWidgets[index].titleBarWidget();

        // Update our progress widget as necessary
        connect(_webViews[index], QWebView.loadProgress, progress(index,));
        connect(_webViews[index], QWebView.loadFinished, progressReset(index,));

        // Dynamically show the title bar when this pane is docked/broken off
        connect(_dockWidgets[index], QDockWidget.topLevelChanged, showTitleBar(index,));

        // Remove the title bar since this will be docked by default
        _dockWidgets[index].setTitleBarWidget(QWidget(mainWindowWidget(), 0));

        // This pane can be docked, floated and moved
        _dockWidgets[index].setFeatures(
                QDockWidget.DockWidgetClosable |
                QDockWidget.DockWidgetFloatable);

        // Make sure all of the panes share a common network access manager,
        // which means they'll have a common set of cookies
        _webViews[index].page().setNetworkAccessManager(_networkAccessManager);

        // Load up the desired page in the web view
        _openWebViewAtIndexToUrl(index, url);

        // Enable Mu communication with javascript in this pane
        javascriptMuExport(_webViews[index].page().mainFrame());

        // Place the webview etc widgets inside the dockable pane
        _dockWidgets[index].setWidget(_baseWidgets[index]);

        // Determine which quadrant the dock widget should be placed in
        int pos;
        if (index == 0) pos = Qt.LeftDockWidgetArea;
        if (index == 1) pos = Qt.RightDockWidgetArea;
        if (index == 2) pos = Qt.TopDockWidgetArea;
        if (index == 3) pos = Qt.BottomDockWidgetArea;

        // Restrict where the dock widgets can be placed
        if ( index == 0 || index == 1 ) {
            _dockWidgets[index].setAllowedAreas(Qt.LeftDockWidgetArea |
                                                Qt.RightDockWidgetArea);
        } else if ( index == 2 ) {
            _dockWidgets[index].setAllowedAreas(Qt.TopDockWidgetArea);
        } else {
            _dockWidgets[index].setAllowedAreas(Qt.BottomDockWidgetArea);
        }
        mainWindowWidget().addDockWidget(pos, _dockWidgets[index]);

        // Restore the main window's geometry that was saved in the last
        // session
        if ( !_geometryRestored ) {
            restoreGeometry();
            _geometryRestored = true;
        }

        // Size the base widget according to the user's preference
        int i = index;
        if ( _sizes[2 * i] != -1 && _sizes[2 * i + 1] != -1 )
        {
            // If the panes are docked, then we want the horizontally oriented
            // panes to have a fixed height but maintain the current width, and
            // the vertically oriented panes to have a fixed width but maintain
            // their current height.

            // If the pane is *not* docked (i.e. floating) then we set both the
            // height and width from the previous session
            let mainRect = mainWindowWidget().centralWidget().frameGeometry(),
                minWidth = mainRect.width(),
                maxWidth = mainRect.width(),
                minHeight = mainRect.height(),
                maxHeight = mainRect.height();

            if ( i == 0 || i == 1 || _floating[i] == 1 ) {
                minWidth = _sizes[2 * i];
                maxWidth = _sizes[2 * i];

                if ( _floating[i] != 1 ) {
                    minHeight = 0;
                    maxHeight = 16777215;
                }
            }

            if ( i == 2 || i == 3 || _floating[i] == 1 ) {
                minHeight = _sizes[2 * i + 1];
                maxHeight = _sizes[2 * i + 1];

                if ( _floating[i] != 1 ) {
                    minWidth = 0;
                    maxWidth = 16777215;
                }
            }

            _baseWidgets[i].setMaximumSize( QSize(maxWidth, maxHeight) );
            _baseWidgets[i].setMinimumSize( QSize(minWidth, minHeight) );
        }
        else if (i == 0 || i == 1)
        {
            _baseWidgets[i].setMaximumSize( QSize(startSize, 16777215) );
            _baseWidgets[i].setMinimumSize( QSize(startSize, 0) );
        }
        else if (i == 2 || i == 3)
        {
            _baseWidgets[i].setMaximumSize( QSize(16777215, startSize) );
            _baseWidgets[i].setMinimumSize( QSize(0, startSize) );
        }

        if ( _floating[i] == 1 ) {
            _dockWidgets[i].setFloating(true);
        }

        if ( _positions[2 * i] != -1 && _positions[2 * i + 1] != -1 ) {
            _dockWidgets[i].setPos( QPoint( _positions[2 * i], _positions[2 * i + 1] ) );
        }

        // Show the widget
        _dockWidgets[index].show();
    }

    // Restore the saved main window geometry (position and dimensions) from a
    // previous review app session
    method: restoreGeometry(void;)
    {
        // No main window geometry was stored in the last session
        if ( _mainWindowGeometry eq nil ) {
            return;
        }

        let mainWin = mainWindowWidget();

        // Restore the geometry exactly as it was -- this might cause the window
        // to overflow the dimensions of the screen
        mainWin.restoreGeometry(_mainWindowGeometry);

        // Determine if we need to reposition the window so that it will fit on
        // screen
        let mainRect = mainWin.frameGeometry(),
            usedRect = QApplication.desktop().availableGeometry(mainWin);

        let outRight = usedRect.width() + usedRect.x() - mainWin.x() - mainRect.width(),
            outBelow = usedRect.height() + usedRect.y() - mainWin.y() - mainRect.height(),
            outLeft  = mainWin.x() - usedRect.x(),
            outAbove = mainWin.y() - usedRect.y();

        let deltaX = math.min(outRight, outLeft),
            deltaY = math.min(outBelow, outAbove);
        if (deltaX > 0) deltaX = 0;
        if (deltaX == outLeft) deltaX = -1 * deltaX;
        if (deltaY > 0) deltaY = 0;
        if (deltaY == outAbove) deltaY = -1 * deltaY;

        // Intersect the main window with the screen rectangle, so that the
        // main window cannot extend beyond the edges of the screen
        let newPos = qt.QPoint(mainWin.x() + deltaX, mainWin.y() + deltaY),
            newRect = QRect( newPos, QSize( mainRect.width(), mainRect.height() ) ),
            iRect = newRect.intersected(usedRect);

        mainWin.setGeometry(iRect);
        redraw();
    }

    // Reset the min/max sizes of the panes
    method: resetMinMaxSizes(void;)
    {
        for (int i = 0; i < 4; ++i) {
            if ( _dockWidgets[i] eq nil ) {
                continue;
            }

            _baseWidgets[i].setMaximumSize( QSize(16777215, 16777215) );
            _baseWidgets[i].setMinimumSize( QSize(0, 0) );
        }
    }

    // Reset the sizes of the panes and dock them
    method: resetPanes(void; Event event)
    {
        for (int i = 0; i < 4; ++i) {
            if ( _dockWidgets[i] eq nil ) {
                continue;
            }

            _floating[i] = 0;
            _hidden[i] = 0;

            if ( i == 0 || i == 1 ) {
                _baseWidgets[i].setMinimumWidth(400);
                _baseWidgets[i].setMaximumWidth(400);
            } else if ( i == 2 || i == 3 ) {
                _baseWidgets[i].setMinimumHeight(300);
                _baseWidgets[i].setMaximumHeight(300);
            }

            int pos;
            if (i == 0) pos = Qt.LeftDockWidgetArea;
            if (i == 1) pos = Qt.RightDockWidgetArea;
            if (i == 2) pos = Qt.TopDockWidgetArea;
            if (i == 3) pos = Qt.BottomDockWidgetArea;

            mainWindowWidget().addDockWidget(pos, _dockWidgets[i]);
            _dockWidgets[i].setFloating(false);
            _dockWidgets[i].show();
        }

        // We have to reset the min/max sizes after a brief timeout or else they
        // don't get saved
        let timer = QTimer( mainWindowWidget() );
        timer.setSingleShot(true);
        connect(timer, QTimer.timeout, resetMinMaxSizes);
        timer.start(1);
    }

    // This should be called whenever a review app pane is opened. It
    // ensures that we bind to the correct events so that the UI updates as
    // expected
    method: onPaneOpened(void;)
    {
        if ( !_allHidden ) {
            // A pane is already open. We don't need to re-bind the events
            return;
        }

        _allHidden = false;
        _bindCoreEvents();

        // This method will determine if we should re-bind the frame-change events
        _updateIfStateChanged(true);

        // Ensure the UI is up-to-date when reopened
        emitSourceFrameChanged(nil);
    }

    // This should be called whenver a review app pane is hidden. Once all panes
    // are hidden, we'll unbind the events so that the mode doesn't respond to
    // any changes in RV while it's not visible.
    method: onPaneClosed(void;)
    {
        if ( _allHidden ) {
            return;
        }

        for_each(w; _dockWidgets) {
            if ( w neq nil && !w.isHidden() ) {
                return;
            }
        }

        _allHidden = true;
        _unbindCoreEvents();
        _unbindFrameEvents();
    }

    // Open the pane in the given pos to the given URL. This pane might have
    // already been opened and initialised. This pane might also already be
    // open to the given tool. If it is, we do nothing.
    method: openPaneToUrl(void; string url, string pos, int startSize=0)
    {
        deb("openPaneToUrl: pane = %s, url = %s\n" % (pos,url) );

        // Get the index associated with the given position
        let i = nameToIndex(pos);

        // A web view has already been defined in this quadrant
        if (_webViews[i] neq nil) {
            deb("openPaneToUrl: calling _openWebViewAtIndexToUrl\n" );

            if ( _dockWidgets[i] neq nil ) {
                deb("openPaneToUrl: _dockWidgets[i] not nil\n" );
            }
            if ( _baseWidgets[i] neq nil ) {
                deb("openPaneToUrl: _baseWidgets[i] not nil\n" );
            }
            if ( _progressBars[i] neq nil ) {
                deb("openPaneToUrl: _progressBars[i] not nil\n" );
            }
            if ( _titleBarWidgets[i] neq nil ) {
                deb("openPaneToUrl: _titleBarWidgets[i] not nil\n" );
            }

            _openWebViewAtIndexToUrl(i, url);

            // If the user hasn't explicitly hidden this pane, then show it
            if ( _dockWidgets[i].isHidden() && _hidden[i] == 0 ) {
                deb("openPaneToUrl: unhiding dock widget\n" );
                _dockWidgets[i].show();
                onPaneOpened();
            } else { 
                deb("openPaneToUrl: dock widget is not hidden so nothing to do\n" );
            }
        } else {       // No dock widget exists, so initialise one
            deb("openPaneToUrl: calling initView\n" );
            initView(i, url, startSize);
            onPaneOpened();
        }
    }

    method: _openWebViewAtIndexToUrl(void; int index, string url)
    {
        // We need to determine if the url has changed
        QUrl currentUrl = _webViews[index].url();
        QUrl newUrl = QUrl(url);

        // If the current url is empty, or differs from the new url then
        // we redirect the page to the new url
        if ( currentUrl.isEmpty() || currentUrl != newUrl ) {
            if ( newUrl.isRelative() ) {
                let serverName = getDefaultServerName();
                newUrl = QUrl("%s%s" % (serverName, url));
            }

            _webViews[index].load(newUrl);
        }
    }

    // Close (hide) the pane in the given position
    method: closePane(void; string pos, bool storePref=true)
    {
        let i = nameToIndex(pos);

        if (_dockWidgets[i] neq nil && !_dockWidgets[i].isHidden()) {
            _dockWidgets[i].hide();
            onPaneClosed();
        }

        if (storePref) {
            _hidden[i] = 1;
        }
    }

    method: openPane(void; string pos, bool storePref=true)
    {
        let i = nameToIndex(pos);
        if (_dockWidgets[i] neq nil && _dockWidgets[i].isHidden()) {
            _dockWidgets[i].show();
            onPaneOpened();
        }

        if (storePref) {
            _hidden[i] = 0;
        }
    }

    method: paneIsOpen(bool; string pos)
    {
        let i = nameToIndex(pos);
        return _dockWidgets[i] neq nil && !_dockWidgets[i].isHidden();
    }

    method: submitToolIsOpen(bool;)
    {
        if (!paneIsOpen("Bottom")) return false;

        let i = nameToIndex("Bottom");
        if (_webViews[i].url().path() == "/page/review_app_submit") {
            return true;
        }

        return false;
    }

    method: reviewAppBrowserIsOpen(bool;)
    {
        if (!paneIsOpen("Bottom")) return false;

        let i = nameToIndex("Bottom");
        if (_webViews[i].url().path() == "/page/review_app_browser") {
            return true;
        }

        return false;
    }

    method: paneIsAvailable(bool; string pos)
    {
        let i = nameToIndex(pos);
        return _dockWidgets[i] neq nil;
    }

    method: disabledFunc (int;) { return DisabledMenuState; }
    method: neutralFunc (int; ) { return NeutralMenuState; }
    method: checkedFunc (int; ) { return CheckedMenuState; }
    method: uncheckedFunc (int; ) { return UncheckedMenuState; }

    method: doNothingEvent (void; Event e)
    {
        ;
    }

    method: masterPaneMenuState(int;)
    {
        if (!paneIsAvailable("Bottom")) {
            return DisabledMenuState;
        }

        if paneIsOpen("Bottom") then CheckedMenuState else UncheckedMenuState;
    }

    method: masterPaneIsOpenMenuState(int;)
    {
        if paneIsOpen("Bottom") then UncheckedMenuState else DisabledMenuState;
    }

    method: detailPaneMenuState(int;)
    {
        if (!paneIsAvailable("Bottom") || submitToolIsOpen()) {
            return DisabledMenuState;
        }

        if paneIsOpen("Right") then CheckedMenuState else UncheckedMenuState;
    }

    method: toggleMasterPane(void; Event event)
    {
        deb("INFO: toggleMasterPane()\n");
        if (!paneIsAvailable("Bottom")) {
            internalLaunchTimeline();
        } else {
            let i = nameToIndex("Bottom");
            if (paneIsOpen("Bottom")) {
                closePane("Bottom");
            } else {
                openPane("Bottom");
            }
        }
    }

    method: toggleDetailsPane(void; Event event)
    {
        deb("INFO: toggleDetailsPane()\n");

        if (!paneIsAvailable("Right")) {
            openPaneToUrl("/page/review_app_details", "Right", 400);
            return;
        }

        let i = nameToIndex("Right");
        if (paneIsOpen("Right")) {
            closePane("Right");
        } else {
            openPane("Right");
        }
    }

    // Return whether the pane the given position is docked or torn off
    // A true value means that the pane is torn off
    method: paneIsFloating(bool; string pos)
    {
        let i = nameToIndex(pos);
        if (_dockWidgets[i] neq nil && !_dockWidgets[i].isHidden()) {
            return _dockWidgets[i].floating();
        }

        return false;
    }

    // Dock or tear off the pane in the given position
    // A true value means that the pane is torn off
    method: setFloating(void; string pos, bool floating)
    {
        let i = nameToIndex(pos);
        int size;
        if (_dockWidgets[i] neq nil && !_dockWidgets[i].isHidden()) {
            _floating[i] = if ( floating ) then 1 else 0;
            _dockWidgets[i].setFloating(floating);
        }
    }

    // Update the update frequency of the current session. If -1, updates will
    // always occur on frame change or when a new source is viewed. If -2,
    // updates will *never* occur. Any other positive integer will be the
    // maximum resolution, in any dimension, below which updates to the
    // Review App UI will occur while playing media in RV. This is to preserve
    // playback performance
    method: setUpdateFrequency(void; int freq, Event e) {
        _updateFrequency = freq;
        writeSetting("ReviewApp", "updateFrequency", SettingsValue.Int(freq));
        _updateIfStateChanged(true);
    }

    // Update the number of sources that can be stored in the "Screening Room
    // Cached Sources" folder during a session
    method: setSourceCacheMaxSize(void; int maxSize, Event e) {
        _sourceCacheMaxSize = maxSize;
        writeSetting("ReviewApp", "sourceCacheMaxSize", SettingsValue.Int(maxSize));
        pruneCachedSourcesGroup(maxSize, e);
    }

    // This toggles on/off the setting that controls whether detail pane updates
    // are always disabled when playing media in RV. If false, detail pane
    // updates are dictated by the update frequency setting above.
    method: toggleDetailPanePinnedWhenPlaying(void; Event e) {
        _detailPanePinnedWhenPlaying = !_detailPanePinnedWhenPlaying;
        writeSetting("ReviewApp", "detailPanePinnedWhenPlaying",
            SettingsValue.Bool(_detailPanePinnedWhenPlaying));
        _updateIfStateChanged(true);
    }

    method: toggleDebugInfo(void; Event e) {
        SGR_DEBUG = !SGR_DEBUG;
        writeSetting("ReviewApp", "debugInfoEnabled",
            SettingsValue.Bool(SGR_DEBUG));
    }

    method: toggleDirectoriesAllowed(void; Event e) {
        _allowDirectories = !_allowDirectories;
        writeSetting("ReviewApp", "allowDirectories",
            SettingsValue.Bool(_allowDirectories));
        _reload(e);
    }

    // Get the current update frequency
    method: getUpdateFrequency(int;) {
        return _updateFrequency;
    }

    // Get the names of the servers that are configured in the RV-Shotgun
    // integration package
    method: getServerNames(string[];)
    {
        string[] serverNames;

        string serverMap;
        try
        {
            serverMap = shotgun_fields.serverMap();
        }
        catch(object obj)
        {
            return serverNames;
        }

        if (serverMap eq nil) {
            return serverNames;
        }

        // Split the server map string
        let parts = serverMap.split(" ");

        // They should be pairs of entries. If there's an odd number of entries
        // then something is wrong
        if (parts.size() == 0 || parts.size() % 2 != 0) {
            return serverNames;
        }

        // Only return the even numbers pieces. These are the server names
        for_index(i; parts) {
            if (i % 2 == 0) {
                serverNames.push_back(parts[i]);
            }
        }

        return serverNames;
    }

    // Return the default site that's stored in the RV prefs. If there is none,
    // then just return the first site in the list
    method: getDefaultServerName (string;)
    {
        string defaultServerName;
        try {
            let defSession = getDefaultSessionFromSLUtils();
            if (defSession._0 != "") {
                deb("INFO: Default server name highjack succeeded with '%s' !\n" % defSession._0);
                defaultServerName = defSession._0;
            } else {
                deb("INFO: Default server name taken from the old prefs: '%s'...\n" % shotgun.theMode()._prefs.serverURL);
                defaultServerName = shotgun.theMode()._prefs.serverURL;
            }
        } catch(...) {
            deb("ERROR: Catched an exception, default server name is nil\n");
            defaultServerName = nil;
        }

        if (defaultServerName eq nil || defaultServerName == "") {
            deb("WARNING: No server names has been decided, so pick the first one!\n");
            let serverNames = getServerNames();
            if (serverNames.size() > 0) {
                return getServerNames()[0];
            } else {
                return nil;
            }
        }

        return defaultServerName;
    }

    // This method is called when changeLoginToUrlAndUName() completes its task.
    method: completedLicenseSwitch(void; ) 
    {
        if ( ASYNC_LICENSE_SWITCH_IN_PROGRESS ) {
            deb("INFO: License switch is completed\n");
    
            ASYNC_LICENSE_SWITCH_IN_PROGRESS = false;

            // If there's a differed call to execute
            if (NEXT_CALL_AFTER_LICENSE_SWITCH neq nil) {
                deb("INFO: Calling next step!\n");
                // Call it!
                NEXT_CALL_AFTER_LICENSE_SWITCH(NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM);

                // Cleanup for the next one
                NEXT_CALL_AFTER_LICENSE_SWITCH = nil;
                NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM = nil;
            }
        }
    }

    // Set the name of the server used for the Shotgun-RV integration
    method: setServer (void; string serverName )
    {
        deb("Logging into srv '%s'\n" % serverName);

        shotgun.theMode().setServerURLValue(serverName);


        if (_sessionUrl eq nil || serverName != _sessionUrl) {
            ASYNC_LICENSE_SWITCH_IN_PROGRESS = true;

            // clearing any leak from previous time...
            NEXT_CALL_AFTER_LICENSE_SWITCH = nil;
            NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM = nil;

            getSLUtils().changeLoginToUrlAndUName(serverName, "", "", "", "", nil );
        }
    }    

    // Return the absolute file path associated with the source with the given
    // name
    method: getFilePathForSource(string; string sourceName) {
        let filePath = sourceMedia(sourceName)._0;

        if ( filePath eq nil ) {
            return nil;
        }

        let absFilePath = QFileInfo(filePath).absoluteFilePath();
        deb( "File path for source '%s' is %s\n" % (sourceName, absFilePath) );
        return absFilePath;
    }

    // Return a tuple representing the frame range for the source with the given
    // node name
    method: getFrameRangeForSource((int, int); string sourceName) {
        let mediaInfo = sourceMediaInfo(sourceName);
        return (mediaInfo.startFrame, mediaInfo.endFrame);
    }

    // Return a tuple representing the frame range for the Shotgun source with
    // the given node name. If the frame range cannot be retrieved because the
    // source has no Shotgun data available, return the tuple (-1, -1)
    method: getFrameRangeForShotgunSource((int, int); string sourceName)
    {
        // Check if we can get Shotgun data for the node with this name
        let sgInfo = shotgun_fields.infoFromSource(sourceName),
            rangePref = shotgun.theMode()._prefs.loadRange;

        // If not, abort
        if (sgInfo eq nil) {
            return (-1, -1);
        }

        // Get the frame range for the source
        let filePath = sourceMedia(sourceName)._0,
            frameRange = getFrameRangeForSource(sourceName),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1,
            in = getIntProperty("%s.cut.in" % sourceName).front(),
            out = getIntProperty("%s.cut.out" % sourceName).front();

        // If there's edl info we use that
        if ( in != -int.max || out != int.max ) {
            localStartFrame = in;
            localEndFrame = out;
        }

        return (localStartFrame, localEndFrame);
    }

    // Returns the duration of a clip given a node name
    method: getDurationForShotgunSource(int; string sourceName)
    {
        let frameRange = getFrameRangeForShotgunSource(sourceName),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1;

        if ( localStartFrame == -1 && localEndFrame == -1 ) {
            return -1;
        }

        return (localEndFrame - localStartFrame + 1);
    }

    // Locate the StrinMap info for the Version with the given id on the given
    // server in the _infoCache. The info isn't present, return nil
    method: _findVersionInCache(StringMap; string server, int id)
    {
        // If there are no entries in our _infoCache, return nil
        if ( _infoCache.size() == 0 ) {
            return nil;
        }

        // Iterate over the _infoCache entries in reverse order. The end of the
        // cache list will have the most recent items, and it's more likely that
        // someone will be request recent items than older items
        int i;
        for(i = _infoCache.size() - 1; i >= 0; i--) {
            let cacheTuple = _infoCache[i];

            // Check that the server and id match
            if ( cacheTuple._0 != server || cacheTuple._1 != id ) {
                continue;
            }

            // Grab the time that this entry was put in the cache
            let cachedOn = cacheTuple._2;

            // Test if the entry is still fresh
            if ( cachedOn.addSecs(_maxCacheAgeSecs) < QDateTime.currentDateTime() ) {
                // Oldest will always be later in the list so we know there's
                // nothing newer
                return nil;
            }

            // It's fresh!
            return cacheTuple._3;
        }

        // Didn't find anything
        return nil;
    }

    // Find entries in the cache for the given version ids and invalidate them
    method: invalidateVersionsInCache(void; string server, int[] ids)
    {
        // If there are no entries in our _infoCache, return nil
        if ( _infoCache.size() == 0 ) {
            return;
        }

        // Iterate over all of the rows of the cache
        int i, j;
        for(i = _infoCache.size() - 1; i >= 0; i--) {
            let cacheTuple = _infoCache[i];

            // Iterate over all of the version ids checking if the row in the
            // cache is a match for one of them
            for(j = 0; j < ids.size(); j++) {
                // Check that the server and id match
                if ( cacheTuple._0 != server || cacheTuple._1 != ids[j] ) {
                    continue;
                }

                // Grab the time that this entry was put in the cache
                let cachedOn = cacheTuple._2;

                // Test if the entry is still fresh
                if ( cachedOn.addSecs(_maxCacheAgeSecs) > QDateTime.currentDateTime() ) {
                    // Oldest will always be later in the list so we know there's
                    // nothing newer
                    deb("Invalidating record with id %d\n" % ids[j]);
                    cacheTuple._2 = QDateTime.currentDateTime().addSecs(-_maxCacheAgeSecs);
                }

                // We found a match, so there's no sense checking that this
                // entry works for other version ids
                break;
            }
        }
    }

    // Add the Version data for the versions with the given ids on the given
    // server to the _infoCache
    method: _addInfosToCache(void; string server, int[] ids, StringMap[] infos)
    {
        // Get rid of as many items as necessary so that the final size of our
        // cache is below the threshhold
        int numToRemove = _infoCache.size() + ids.size() - _infoCacheMaxItems;

        if ( numToRemove > 0 ) {
            let temp = (string, int, QDateTime, StringMap)[]();
            int i;
            for(i = numToRemove; i < _infoCache.size(); i++) {
                temp.push_back( _infoCache[i] );
            }

            _infoCache = temp;
        }

        // Append the new items to the cache
        let currentTime = QDateTime.currentDateTime();
        int i;
        for(i = 0; i < ids.size(); i++) {
            let cacheTuple = (server, ids[i], currentTime, infos[i]);
            _infoCache.push_back(cacheTuple);
        }
    }

    // Called after the Version data is retrieved for the first time
    method: _afterVersionInfoCollected(void; string server, int[] allIds, int[] uncachedIds, (int, StringMap)[] cachedInfos, (void; StringMap[]) afterFunc, StringMap[] uncachedInfos)
    {
        // Insert the info for these versions in the cache
        _addInfosToCache(server, uncachedIds, uncachedInfos);

        // Now we need to reassemble the cached and uncached items in the
        // right order
        StringMap[] finalInfos;

        // Iterate over each id in the original list
        for (int j = 0; j < allIds.size(); ++j) {
            let id = allIds[j],
                infoFound = false;

            // Check if the info for this id was just retrieved
            int i;
            for(i = 0; i < uncachedIds.size(); i++) {
                if ( uncachedIds[i] == id ) {
                    finalInfos.push_back(uncachedInfos[i]);
                    infoFound = true;
                }
            }

            // Otherwise look for it in the items we retrieved from the cache
            if ( !infoFound ) {
                for (int k = 0; k < cachedInfos.size(); ++k) {
                    let cacheTuple = cachedInfos[k];
                    if ( cacheTuple._0 == id ) {
                        finalInfos.push_back(cacheTuple._1);
                        infoFound = true;
                    }
                }
            }

            // If all else fails, add a nil entry
            if ( !infoFound ) {
                finalInfos.push_back(nil);
            }

        }

        _fetching = false;

        // Execute the callback on the final list
        afterFunc(finalInfos);
    }

    // An alternative to shotgun_state.collectVersionInfo that first checks an
    // internal cache
    method: collectVersionInfo(void; int[] ids, (void; StringMap[]) afterFunc)
    {
        // The items will be keyed in the cache by server and version id
        let server = getDefaultServerName();

        // Keep track of the Version info that we find in the cache and their
        // associated ids
        let cachedInfos = (int, StringMap)[]();

        // Track all of ids that aren't found in the cache
        int[] uncachedIds;

        // Iterate over all of the requested ids
        for_each(id; ids) {
            // Check if the _infoCache for an entry for this id
            let cachedInfo = _findVersionInCache(server, id);

            if ( cachedInfo eq nil ) {
                // No cached entry was found
                uncachedIds.push_back(id);
            } else {
                // It exists in the cache!
                cachedInfos.push_back((id, cachedInfo));
            }
        }

        // If all the ids were found in the cache then we can run the callback
        // straight away and return
        if ( uncachedIds.size() == 0 ) {
            StringMap[] finalInfos;

            for_each(cacheTuple; cachedInfos) {
                finalInfos.push_back(cacheTuple._1);
            }

            _fetching = false;
            afterFunc(finalInfos);
            return;
        }

        deb("Fetching version info for ids: %s\n" % uncachedIds);
        State state = data();
        state.emptySessionStr = "Loading From Shotgun ...";
        redraw();

        // Otherwise we need to fetch the remaining uncached Version info
        shotgun.theMode()._shotgunState.collectVersionInfo(uncachedIds,
            _afterVersionInfoCollected(server, ids, uncachedIds, cachedInfos, afterFunc,));
    }

    // Find the Versions associated with the entity with the given id and type in the cache
    // Return nil if it cannot be found
    method: _findEntityVersionsInCache(int[]; string server, int id, string eType)
    {
        // If the entity version cache is empty then return nil
        if ( _entityVersionsCache.size() == 0 ) {
            return nil;
        }

        // Iterate backwards throug the entity version cache
        int i;
        for(i = _entityVersionsCache.size() - 1; i >= 0; i--) {
            let cacheTuple = _entityVersionsCache[i];

            // Check that the server and id match
            if ( cacheTuple._0 != server ||
                 cacheTuple._1 != id ||
                 cacheTuple._2 != eType ) {
                continue;
            }

            // Grab the time that this entry was put in the cache
            let cachedOn = cacheTuple._3;

            // Test if the entry is still fresh
            if ( cachedOn.addSecs(_maxCacheAgeSecs) < QDateTime.currentDateTime() ) {
                // Oldest will always be later in the list so we know there's
                // nothing newer
                return nil;
            }

            // It's fresh!
            return cacheTuple._4;
        }

        // Didn't find anything
        return nil;
    }

    // Add the entity with the given id, type and version id list to the cache
    method: _addEntityVersionsToCache(void; string server, int id, string eType, int[] versionIds)
    {
        // Get rid of as many items as necessary so that the final size of our
        // cache is below the threshhold
        int numToRemove = _entityVersionsCache.size() + 1 - _infoCacheMaxItems;
        if ( numToRemove > 0 ) {
            let temp = (string, int, string, QDateTime, int[])[]();

            int i;
            for(i = numToRemove; i < _entityVersionsCache.size(); i++) {
                temp.push_back( _entityVersionsCache[i] );
            }

            _entityVersionsCache = temp;
        }

        // Append these items to the cache
        let currentTime = QDateTime.currentDateTime();
        let cacheTuple = (server, id, eType, currentTime, versionIds);
        _entityVersionsCache.push_back(cacheTuple);
    }

    // Called after the uncached entity versions are retrieved
    method: _afterEntityVersionsCollected(void; string server, int id, string eType, (void; StringMap[]) afterFunc, StringMap[] infos)
    {
        // Cache the entity's version ids
        int[] ids;

        for_each(info; infos) {
            ids.push_back( info.findInt("id") );
        }

        _addEntityVersionsToCache(server, id, eType, ids);

        // Retrieve the info for these ids, which might be in the cache or they
        // might need to be fetched from Shotgun
        collectVersionInfo(ids, afterFunc);
    }

    // An alternative implementation of _shotgunState.collectAllVersionsOfEntity
    // that makes use of a cache
    method: collectAllVersionsOfEntity(void; int id, string eType, (void; StringMap[]) afterFunc)
    {
        if ( _fetching ) {
            return;
        }

        let server = getDefaultServerName();

        // Check the cache for the ids for the entity with the given id and entity type
        let ids = _findEntityVersionsInCache(server, id, eType);

        // If the returned list of ids isn't nil then they were found in the cache!
        // We can collect the info for the Versions with these ids
        if ( ids neq nil ) {
            collectVersionInfo(ids, afterFunc);
            return;
        }

        _fetching = true;

        // It's not cached so fetch it
        shotgun.theMode()._shotgunState.collectAllVersionsOfEntity(-1, id, "entity", eType,
            _afterEntityVersionsCollected(server, id, eType, afterFunc,), true);
    }

    method: playCurrent(void;) {
        // If RV was opened with start playback (-play) option, and media is not currently playing,
        // then start playback. 
        if ( 1 == optionsPlay() && !isPlaying() ) extra_commands.togglePlay();
    }    

    // Called when the new sources (that have not been cached) are finished loading but
    // *before* their shotgun data is available
    method: onSequenceSourcesCreated(void; StringMap[] infos, string[] existingSources,
        string[] newSources) {

        string[] viewNodes = string[] {"defaultStack", "defaultSequence", "defaultLayout",
            getSequenceNode(), getLayoutNode(), getStackNode()};

        string[] disconnectFromNodes = string[] {"defaultStack", "defaultSequence", "defaultLayout",
            getSequenceNode(), getLayoutNode(), getStackNode()};

        if ( _sourceCacheMaxSize > 0 ) {
            disconnectFromNodes.push_back(getCachedSourcesGroup());
        }
        string[] allSources = string[]();

        // Turn off caching while we mess with the connections of these nodes
        let mode = cacheMode();
        setCacheMode(CacheOff);

        let existingSourceIndex = 0,
            newSourceIndex = 0;

        // Prep for fastSourceForInfo
        //
        // Since we will need to get the source for info repeatedly during this method,
        // we optimize with a local function instead of calling sourceForInfo().  What we avoid
        // this way is repeated calls to infoFromSource() for the same source nodes -
        // that was a bottleneck in this method.

        let fastSourceForInfoArray = (int,string)[]();

        for_each(s; nodesOfType("RVFileSource")) {
            // Attempt to get the Shotgun metadata for the source
            let statusProp = s + ".tracking.infoStatus";
            if (! propertyExists(statusProp)) continue;
            if (getStringProperty(statusProp)[0] != "    good") continue;

            let sgInfo = shotgun_fields.infoFromSource(s);

            if ( sgInfo eq nil ) continue;

            fastSourceForInfoArray.push_back((sgInfo.findInt("id"), s));
        }

        function: fastSourceForInfo(string; int id) {
            for_each(pair; fastSourceForInfoArray) {
                if (pair._0 == id) return pair._1;
            }
            return nil;
        }

        // Create an ordered list of all sources by iterating over the info
        // hashes.

        for_each(inf; infos) {
            // Check if a cached source for this info is the next item in the
            // existingSources list
            let id = inf.findInt("id");
            if ( existingSources.size() > existingSourceIndex &&
                 fastSourceForInfo(id) neq nil &&
                 fastSourceForInfo(id) == existingSources[existingSourceIndex] ) {

                allSources.push_back( existingSources[existingSourceIndex] );
                existingSourceIndex++;
            } else if ( newSources.size() > newSourceIndex ) {
                // If a cached source cannot be found it must be the next item
                // in the newSources list
                allSources.push_back( newSources[newSourceIndex] );
                newSourceIndex++;
            }
        }

        // Disconnect our sources from all the view nodes so that they get
        // connected in the correct order
        for (int j = 0; j < disconnectFromNodes.size(); ++j) {
            let v = disconnectFromNodes[j],
                inputs = nodeConnections(v, false)._0,
                newInputs = string []();

            for (int k = 0; k < inputs.size(); ++k) {
                let i = inputs[k],
                    found = false;
                for (int l = 0; l < allSources.size(); ++l) {
                    let a = allSources[l];
                    if ( i == nodeGroup(a) ) {
                        found = true;
                        break;
                    }
                }

                if ( !found )
                    newInputs.push_back(i);
            }

            setNodeInputs(v, newInputs);
        }

        // Connect all of the sources to our view nodes
        for (int i = 0; i < viewNodes.size(); ++i) {
            let v = viewNodes[i],
                inputs = nodeConnections(v, false)._0;
            for (int j = 0; j < allSources.size(); ++j) {
                inputs.push_back( nodeGroup(allSources[j]) );
            }

            setNodeInputs(v, inputs);
        }

        // Reenable caching
        setCacheMode(mode);
        redraw();

        playCurrent();
    }

    // Create a sequence in RV from the given list of info hashes, making use of the source cache
    // where possible
    method: sequenceFromInfos (void; bool doCompare, StringMap[] infos)
    {
        if ( infos.size() == 0 ) {
            return;
        }

        let needCreation = StringMap[](),
            existingSources = string[](),
            oldSources = string[]();

        // Iterate over each metadata item
        for_index(i; infos) {
            // Find the source for this metadata, if there is one
            let s = sourceForInfo( infos[i] );
            if ( s neq nil ) {
                // There is a source!
                deb("Source exists for Version with id: %d (%s)\n" % (infos[i].findInt("id"), s) );
                existingSources.push_back(s);
            } else {
                // A source needs to be created
                deb("Source does not exist for Version with id: %d\n" % infos[i].findInt("id") );
                needCreation.push_back( infos[i] );
            }
        }

        if (CURRENT_SEQ_NODE == DEFAULT_SEQ_NODE){
    
            // Remove any existing sources from the sources cache, so they don't get deleted
            // completely before we can display them, if the sources cache overflows when caching
            // unused sources below. #25444
            for_each(s; existingSources) {
                let group = nodeGroup(s);
                takeSourceOutOfCache( group );
            }
    
            // Determine the sources that are now no longer used - i.e. they are loaded
            // but not in our list of the ones we are about to display - and not already in the
            // sources cache.
            // We will then unlink them and put them in the sources cache.
            let unusedSources = string[]();
            let allSources = nodesOfType("RVFileSource");
            if ( allSources.size() > 0 ) {
                // Find the currently cached sources - we do not need to process and cache these again.
                let cachedSourceGroup = getCachedSourcesGroup(),
                    cached_sources1 = nodeConnections(cachedSourceGroup, false)._0;
    
                //  XXX WTF! cached_sources ref is messed up somehow, have to make
                //  a secondary reference to get it to work!
                string[] cached_sources = cached_sources1;
                for (int i = 0; i < allSources.size(); ++i) {
                    // First skip any unused sources that are already in the sources cache.
                    let s = allSources[i],
                        isCached = false;
                    for (int j = 0; j < cached_sources.size(); ++j) {
                        let s2 = cached_sources[j];
                        if ( s == s2 + "_source" ) {
                            isCached = true;
                            break;
                        }
                    }
                    if ( ! isCached ) {
                        // Now identify the remaining ones that are not displayed.
                        let hasSource = false;
                        for (int j = 0; j < existingSources.size(); ++j) {
                            let s2 = existingSources[j];
                            if ( s == s2 ) {
                                hasSource = true;
                                break;
                            }
                        }
    
                        if ( !hasSource )
                            unusedSources.push_back(s);
                    }
                }
            }
    
            if ( unusedSources.size() > 0 ) {
                let unusedSourcesAsGroups = string[]();
                for (int j = 0; j < unusedSources.size(); ++j) {
                    // Remove any existing connections to the new source
                    let s = unusedSources[j],
                        group = nodeGroup(s);
                    if ( group eq nil ) {
                        continue;
                    }
                    unusedSourcesAsGroups.push_back( group );
    
                    let outputs = nodeConnections(group, false)._1;
                    // Iterate over all of the outputs
                    for (int k = 0; k < outputs.size(); ++k) {
                        let o = outputs[k],
                            inputs = nodeConnections(o, false)._0,
                            newInputs = string[]();
    
                        // Remove the new node from the inputs of this output
                        for (int l = 0; l < inputs.size(); ++l) {
                            let i = inputs[l];
                            if ( i != group ) {
                                newInputs.push_back(i);
                            }
                        }
    
                        // Update this output's connections
                        setNodeInputs(o, newInputs);
                    }
                }
                // Cache the sources
                cacheSources( unusedSourcesAsGroups );
            }
        }

        if ( needCreation.size() > 0 ) {
            _postProgLoadInfos = infos;
            _preProgLoadSources = nodesOfType("RVFileSource");

            createSourcesForInfos(needCreation, onSequenceSourcesCreated(infos, existingSources,));
        } else {
            deb("All sources already loaded\n");
            onSequenceSourcesCreated(infos, existingSources, string[] {});
            _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
        }

        if (doCompare)
        {
            let p = shotgun.theMode()._prefs.compareOp;
            deb ("    doCompare mode %s" % p);
            if (p == 0)
            {
                setViewNodeAndResetInOutPoints( getLayoutNode() );
                setStringProperty("#RVLayoutGroup.layout.mode", string[]{"packed"});
            }
            else if (p == 1)
            {
                setViewNodeAndResetInOutPoints( getStackNode() );
                setStringProperty("#RVStack.composite.type", string[]{"over"});
                _postProgLoadTurnOnWipes = true;
            }
            else if (p == 2)
            {
                setViewNodeAndResetInOutPoints( getStackNode() );
                setStringProperty("#RVStack.composite.type", string[]{"difference"});
            }
            else print ("ERROR: bad compareOp pref %s\n" % p);
        } else if ( viewNode() != getSequenceNode() ) {
            setViewNodeAndResetInOutPoints( getSequenceNode() );
        }
    }

    // Set the current view node and reset the global in and out points
    method: setViewNodeAndResetInOutPoints(void; string node)
    {
        // Don't do anything if this is already the view node
        if ( viewNode() == node ) {
            return;
        }
        setViewNode(node);
        setInPoint(frameStart());
        setOutPoint(frameEnd());
    }

    // Just a method to transfer the context switch from the canvas timeline/browser
    // to the details panel
    method: versionContextChanged(void; int ctxt_id, string ctxt_type, string ctxt_name, int ctxt_project_id, string ctxt_valid)
    {
        if (ctxt_id < 0) {
            let result = "-1||||";
            sendInternalEvent("sg-version-context-changed", result);
        } else {
            let result = "%d|%s|%s|%d|%s" %  (ctxt_id, ctxt_type, ctxt_name, ctxt_project_id, ctxt_valid);
            sendInternalEvent("sg-version-context-changed", result);
        }
    }

    // An alternative to shotgun.sessionFromVersionIDs that takes advantage of
    // a cache
    method: sessionFromVersionIds(void; int[] ids)
    {
        if ( _sessionIsLoading ) {
            return;
        }

        _sessionIsLoading = true;
        try {
            if ( ids.size() > 0 ) {
            
                if ( nodeExists(DEFAULT_SEQ_NODE) ){
            
                    int choice = alertPanel(true,
                                            InfoAlert,
                                            "Do you want to play in a",
                                            "new Viewable Sequence ?",
                                            "Yes",
                                            "No",
                                            nil);
                
                    if (choice == 0){
                        print("NEW SEQUENCE YEAH !\n");
                        
                        int numSeqGrps = ADDED_SEQ_GRPS.size() + 1;
                        
                        let newSeqNode = newNode("RVSequenceGroup", "reviewAppSequenceGroup");
                        setUIName(newSeqNode, "Screening Room Sequence %s" % numSeqGrps);
                        ADDED_SEQ_GRPS.push_back(newSeqNode);
                        CURRENT_SEQ_NODE = newSeqNode;
                    }
                    else {
                        for_each(seqGrp; ADDED_SEQ_GRPS){
                            deleteNode(seqGrp);
                        }
                        ADDED_SEQ_GRPS.clear();
                    }
                }
                collectVersionInfo(ids, sequenceFromInfos(false,));                
                
            } else {
                _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
            }
        } catch (object o) {
            _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
            throw o;
        }
    }

    // An alternative to shotgun.compareFromVersionIDs that takes advantage of
    // a cache
    method: compareFromVersionIds(void; int[] ids)
    {
        if ( _sessionIsLoading ) return;

        _sessionIsLoading = true;
        try {
            if ( ids.size() > 0 ) {
                collectVersionInfo(ids, sequenceFromInfos(true,));
            } else {
                _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
            }
        } catch (object o) {
            _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
            throw o;
        }
    }

    // Get the first source that is associated with the entity of the given type
    // with the given id. If there is no such source, return nil.
    method: sourceFromEntity(string; string entity_type, int entity_id)
    {
        // Get all of the file sources
        let sourceNames = allShotgunSourceNames();

        // Iterate over them
        for_each(s; sourceNames) {
            // Attempt to get the Shotgun metadata for the source
            let sgInfo = shotgun_fields.infoFromSource(s);

            // If there is none, move on to the next source
            if ( sgInfo eq nil ) {
                continue;
            }

            // If there is metadata, get the link info.
            string link = sgInfo.find("link");

            // If there is no link, move on to the next source
            if ( link eq nil ) {
                continue;
            }

            // If there is a link, parse the encoded string and find the link id
            let id = shotgun_fields.extractEntityValueParts(link)._2;

            // If the link id matches the given entity id then we've found our
            // source. Return the source name
            if ( id == entity_id ) {
                return s;
            }
        }

        return nil;
    }

    // Create new source nodes that correspond to the given list of Shotgun Version
    // metadata
    method: createSourcesForInfos(void; StringMap[] infos, (void; string[]) afterFunc)
    {
        // Assemble the args for the creation command in this array
        let args = string[](),
            hasDirectory = false;

        // Keep track of the metadata thats being added. The order of the metadata
        // in this list should match the order in which the corresponding args are
        // added to the command
        _postProgLoadInfos = StringMap[]();

        for_each(inf; infos) {
            let frameMin = inf.findInt("frameMin"),
                frameMax = inf.findInt("frameMax");
            int rangePref = shotgun.theMode()._prefs.loadRange;

            //
            //  Only build rangeOffset, media, pixelAspect arrays if
            //  we are actually adding sources.
            //
            deb ("    _prefs.loadMedia %s\n" % shotgun.theMode()._prefs.loadMedia);
            let edlMediaType = shotgun.theMode().mediaTypeFallback (shotgun.theMode()._prefs.loadMedia, inf);

            let edlMedia = shotgun_fields.mediaTypePath (edlMediaType, inf),
                edlPA = shotgun_fields.mediaTypePixelAspect (edlMediaType, inf),
                hasSlate = shotgun_fields.mediaTypeHasSlate (edlMediaType, inf);

            if ( filePathIsDirectory(edlMedia) ) {
                // Versions whose file paths are directories cannot be viewed
                hasDirectory = true;
                deb("Cannot load path %s. Directories are not supported!\n" % edlMedia);
                continue;
            }

            //  Save mediaType for use by post progressive load code.
            //
            inf.add ("internalMediaType", edlMediaType);

            deb ("    new media for mediaType %s is %s\n" % (edlMediaType, edlMedia));
            int edlRS = int.max;
            if (shotgun.theMode().mediaIsMovie (edlMedia) && frameMin != -int.max)
            {
                edlRS = frameMin - (if (hasSlate) then 1 else 0);
            }

            int edlIn;
            int edlOut;
            if (rangePref == 3)
            {
                deb ("    keeping same edl info\n");

                edlIn = int.max-1;
                edlOut = int.max-1;
            }
            else if (rangePref == 0)
            {
                deb ("    loading full range\n");

                edlIn = -int.max;
                edlOut = int.max;
            }
            else if (rangePref == 1)
            {
                deb ("    loading full range without slate\n");

                edlIn = frameMin;
                edlOut = frameMax;
            }
            else if (rangePref == 2)
            {
                deb ("    loading cut length\n");

                edlIn = inf.findInt("frameIn");
                edlOut = inf.findInt("frameOut");
            }

            _postProgLoadInfos.push_back(inf);

            args.push_back ("[");
            args.push_back (shotgun_fields.extractLocalPathValue(edlMedia));
            if (edlRS != int.max)
            {
                args.push_back ("+rs");
                args.push_back ("%s" % edlRS);
            }
            args.push_back ("+pa");
            args.push_back ("%s" % edlPA);
            args.push_back ("+in");
            args.push_back ("%s" % edlIn);
            args.push_back ("+out");
            args.push_back ("%s" % edlOut);
            args.push_back ("]");
        }

        if ( args.size() == 0 ) {
            _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
            afterFunc( string[]() );
            return;
        }

        // Store the current set of sources -- we'll compare this list with the
        // current set of sources after progressive loading has completed to
        // determine which sources were created
        _preProgLoadSources = nodesOfType("RVFileSource");

        // Keep track of our callback
        _postProgLoadCallback = afterFunc;

        //
        //  XXX Not sure why we'd want to call runtime.eval to do this work.
        //  That will incure the expense of parsing, etc, and we can just call
        //  addSources directly.
        //

        deb ("    addSources args %s\n" % args);
        addSources(args, true);
        /*
        let mode = cacheMode();
        setCacheMode(CacheOff);

        // Execute the command
        let evalString = """
            commands.addSources(%s, "", true);
            """ % args;

        deb ("    addSources evalString %s\n" % evalString);
        runtime.eval (evalString);

        deb ("    sources added\n");

        setCacheMode(mode);
        */
    }

    method: filePathIsDirectory(bool; string filePath) {
        if ( _allowDirectories ) {
            return false;
        }

        return QFileInfo(filePath).isDir();
    }

    // Called after new sources are added
    method: afterProgressiveLoading (void; Event event)
    {
        deb ("afterProgressiveLoading\n");
        event.reject();

        // If we don't have any Shotgun metadata in our array, there's nothing
        // to be processed, but we still want to emitSourceFrameChanged, since
        // that was disabled during progressive loading.  If there _is_ stuff
        // to process it'll happen in response to property changes from
        // updateSourceInfo().
        if ( _postProgLoadInfos eq nil || _postProgLoadInfos.size() == 0 )
        {
            emitSourceFrameChanged(nil);
            return;
        }

        // Get the current list of RV sources
        let currentSources = nodesOfType("RVFileSource"),
            sourceNames = string[]();

        // Look for any newly created sources
        for (int i = 0; i < currentSources.size(); ++i) {
            let cs = currentSources[i],
                found = false;
            for (int j = 0; j < _preProgLoadSources.size(); ++j) {
                let s = _preProgLoadSources[j];
                if ( s == cs ) {
                    found = true;
                    break;
                }
            }
            if ( found ) {
                // This source existed before, so we ignore it
                continue;
            }

            // This is a new source
            sourceNames.push_back(cs);
        }

        // Execute our after load callback *before* we update the Shotgun source
        // info
        if ( _postProgLoadCallback neq nil ) {
            deb("    executing callback %s\n" % _postProgLoadCallback);
            deb("        sources: %s\n" % sourceNames);
            _postProgLoadCallback(sourceNames);
            deb("    executing callback finished\n");
        } else {
            deb("    callback is nil\n");
        }

        // Update the shotgun info
        shotgun_fields.updateSourceInfo (sourceNames, _postProgLoadInfos);
        deb ("    updating mediaType\n");

        for_index(i; _postProgLoadInfos) {
            try
            {
                let t = _postProgLoadInfos[i].find ("internalMediaType", true);

                shotgun.theMode()._setMediaType (if (t neq nil) then t else shotgun.theMode()._prefs.loadMedia, sourceNames[i]);
            }
            catch (...) { ; }
        }
        if ( _postProgLoadTurnOnWipes )
        {
            rvui.toggleWipe();
            _postProgLoadTurnOnWipes = false;
        }

        _preProgLoadSources = string[]();
        _postProgLoadInfos = StringMap[]();
        _postProgLoadCallback = nil;
    }

    // Find the name of the source node that corresponds to the given Shotgun
    // metadata
    method: sourceForInfo(string; StringMap inf) {
        // Get all of the file sources
        let sourceNames = nodesOfType("RVFileSource");

        // Iterate over them
        for_each(s; sourceNames) {
            // Attempt to get the Shotgun metadata for the source
            let sgInfo = shotgun_fields.infoFromSource(s);

            // If there is none, move on to the next source
            if ( sgInfo eq nil ) {
                continue;
            }

            if ( sgInfo.findInt("id") == inf.findInt("id") )
                return s;
        }

        return nil;
    }

    // Return the name of the Review App Caches Sources folder. If it doesn't
    // exist, create it
    method: getCachedSourcesGroup(string;)
    {
        let cachedSourceGroup = "reviewAppCachedSources";

        if ( !nodeExists(cachedSourceGroup) ) {
            let node = newNode("RVFolderGroup", cachedSourceGroup);
            setUIName(node, "Screening Room Cached Sources");
            return node;
        }

        return cachedSourceGroup;
    }

    method: getSequenceNode(string;)
    {
        let node = CURRENT_SEQ_NODE;
        if ( !nodeExists(node) ) {
            node = newNode("RVSequenceGroup", node);
            setUIName(node, "Screening Room Sequence");
        }

        return node;
    }

    method: getLayoutNode(string;)
    {
        let node = "reviewAppLayoutGroup";
        if ( !nodeExists(node) ) {
            node = newNode("RVLayoutGroup", node);
            setUIName(node, "Screening Room Layout");
        }

        return node;
    }

    method: getStackNode(string;)
    {
        let node = "reviewAppStackGroup";
        if ( !nodeExists(node) ) {
            node = newNode("RVStackGroup", node);
            setUIName(node, "Screening Room Stack");
        }

        return node;
    }

    // Cache a bunch of nodes into the Review App Cached Sources folder.
    // This ensures that if you ask to cache more nodes than fit into the cache,
    // the extra nodes are just discarded.
    method: cacheSources(void; string[] nodeNames) {
        if ( _sourceCacheMaxSize == 0 ) {
            deb("Source caching is disabled.\n");
            for ( int i = 0; i < nodeNames.size(); i++ ) {
                deleteNode(nodeNames[i]);
            }
            return;
        }

        if ( _sourceCacheMaxSize >= nodeNames.size() ) {
            // Since we are caching less than the max, we can just cache them all.
            for_each( n; nodeNames) {
                cacheSource( n );
            }
        } else {
            // There are too many to actually fit in the cache, so we will only cache the
            // amount that fits - this avoids caching things initially that we will then remove
            // from the cache immediately after when it overflows.
            // We must also properly delete the ones we are not caching.
            for ( int i = 0; i < nodeNames.size(); i++ ) {
                if ( i < nodeNames.size() - _sourceCacheMaxSize ) {
                    // Properly discard the ones we can't fit in the cache
                    deleteNode( nodeNames[i] );
                } else {
                    // Cache the ones that fit
                    cacheSource( nodeNames[i] );
                }
            }
        }
    }

    // Cache the given node into the Review App Cached Sources folder
    method: cacheSource(void; string nodeName) {
        if ( _sourceCacheMaxSize == 0 ) {
            deb("Source caching is disabled.\n");
            deleteNode(nodeName);
            return;
        }

        // Get the current list of nodes that are included in this folder
        let cachedSourceGroup = getCachedSourcesGroup(),
            sources = nodeConnections(cachedSourceGroup, false)._0;

        // If the cache is over the max cache size then we'll need to remove
        // some nodes
        string[] newSources;
        if ( sources.size() > _sourceCacheMaxSize ) {
            deb("Cache size exceded. Will remove nodes.\n");
        }
        int i;
        for ( i = 0; i < sources.size(); i++ ) {
            if ( sources[i] == nodeName + "_source" ) {
                deb("Source %s is already cached!\n" % nodeName);
                return;
            }

            if ( i < sources.size() - _sourceCacheMaxSize + 1 ) {
                deb("Removing node from cache: %s\n" % sources[i]);
                deleteNode( sources[i] );
            } else {
                newSources.push_back( sources[i] );
            }
        }

        // Add this node to the list of inputs and update the Folder's connections
        newSources.push_back(nodeName);
        setNodeInputs(cachedSourceGroup, newSources);
    }

    // When we reuse a cached node, take it out of the cache (or else it will get
    // pruned out from under us when more things are cached)!
    method: takeSourceOutOfCache(void; string nodeName) {
        deb( "Removing source from cache: %s\n" % nodeName );

        // Caching is turned off - do nothing.
        if ( _sourceCacheMaxSize == 0 ) {
            return;
        }

        // Get the current list of nodes that are included in this folder
        let cachedSourceGroup = getCachedSourcesGroup(),
            sources = nodeConnections(cachedSourceGroup, false)._0;

        string[] newSources;
        int i;
        // Copy all but the given node over to the new list
        for ( i = 0; i < sources.size(); i++ ) {
            if ( sources[i] != nodeName ) {
                newSources.push_back( sources[i] );
            }
        }

        // Add this node to the list of inputs and update the Folder's connections
        setNodeInputs(cachedSourceGroup, newSources);
    }

    method: pruneCachedSourceGroupNoEvent(void; int maxSize)
    {
        // Get the current list of nodes that are included in this folder
        let cachedSourceGroup = getCachedSourcesGroup(),
            sources = nodeConnections(cachedSourceGroup, false)._0;

        // If the cache is over the max cache size then we'll need to remove
        // some nodes
        if ( sources.size() > maxSize ) {
            deb("Cache size exceded. Will remove nodes.\n");
        }
        int i;
        for ( i = 0; i < sources.size() - maxSize; i++ ) {
            deb("Removing node from cache: %s\n" % sources[i]);
            deleteNode( sources[i] );
        }

        if ( maxSize == 0 ) {
            deleteNode(cachedSourceGroup);
        }    
    }

    method: pruneCachedSourcesGroup(void; int maxSize, Event e)
    {
        pruneCachedSourceGroupNoEvent(maxSize);
    }

    // Get the outputs of the given originalSourceGroup and transfer them to the given
    // newSourceGroup
    method: swapSourceGroupConnections(void; string originalSourceGroup, string newSourceGroup)
    {
        deb("Swapping connections from node %s to node %s\n" % (originalSourceGroup, newSourceGroup));
        // Get the connections of the original
        let cxns = nodeConnections(originalSourceGroup, false),
            outputs = cxns._1;

        // Disable caching while we fiddle with the connections
        let mode = cacheMode();
        setCacheMode(CacheOff);

        // Iterate over the outputs
        for (int j = 0; j < outputs.size(); ++j) {
            // Get the input connections of the output
            let o = outputs[j],
                inputs = nodeConnections(o, false)._0,
                newInputs = string[]();

            // Iterate over the inputs
            for (int k = 0; k < inputs.size(); ++k) {
                let i = inputs[k];
                if ( i != originalSourceGroup ) {
                    newInputs.push_back(i);
                } else {
                    // Found the original source. Replace it with the new source
                    deb("   Connecting %s to %s\n" % (newSourceGroup, o));
                    newInputs.push_back(newSourceGroup);
                }
            }

            // Update this output's inputs
            setNodeInputs(o, newInputs);
        }

        // Restore caching
        setCacheMode(mode);
    }

    // Return the callback that should be executed when the new sources are finished
    // being created
    method: getAfterCreateSourceFunc((void; string[]); string[] originalSourceNames)
    {
        \: (void; string[] sourceNames)
        {
            // Iterate over all of the new source names
            for_index(i; sourceNames) {
                // Find the group of the new source and the corresponding original
                // source
                let sourceName = sourceNames[i],
                    originalSourceName = originalSourceNames[i],
                    group = nodeGroup(sourceName),
                    originalSourceGroup = nodeGroup(originalSourceName);

                // Remove any existing connections to the new source
                let outputs = nodeConnections(group, false)._1;

                // Iterate over all of the outputs
                for (int j = 0; j < outputs.size(); ++j) {
                    let o = outputs[j],
                        inputs = nodeConnections(o, false)._0,
                        newInputs = string[]();

                    // Remove the new node from the inputs of this output
                    for (int k = 0; k < inputs.size(); ++k) {
                        let i = inputs[k];
                        if ( i != group ) {
                            newInputs.push_back(i);
                        }
                    }

                    // Update this output's connections
                    setNodeInputs(o, newInputs);
                }

                // Swap the connections from the original source to this source
                this.swapSourceGroupConnections(originalSourceGroup, group);

                // Cache the original source
                this.cacheSource(originalSourceGroup);
            }
        };
    }

    // Replace the given set of sources with a source that corresponds to the metadata
    // in the matching index of the given infos array. Some of the new sources might
    // already exist and some might need to be created.
    method: replaceSourcesWithInfos(void; string[] sourceNames, StringMap[] infos)
    {
        // Prime some lists to collect the names of the sources that already exist
        // and the metadata for those that don't
        let needCreation = StringMap[](),
            needCreationOriginalSources = string[](),
            existingSources = string[](),
            existingOriginalSources = string[]();

        // Iterate over each metadata item
        for_index(i; infos) {
            // Find the source for this metadata, if there is one
            let s = sourceForInfo( infos[i] );
            if ( s neq nil ) {
                // There is a source!
                deb("Source exists for Version with id: %d (%s)\n" % (infos[i].findInt("id"), s) );
                existingSources.push_back(s);
                existingOriginalSources.push_back( sourceNames[i] );
            } else {
                // A source needs to be created
                deb("Source does not exist for Version with id: %d\n" % infos[i].findInt("id") );
                needCreation.push_back( infos[i] );
                needCreationOriginalSources.push_back( sourceNames[i] );
            }
        }

        // Execute the after create callback for the existing sources
        if ( existingSources.size() > 0 ) {
            let callback = getAfterCreateSourceFunc(existingOriginalSources);
            callback(existingSources);
        }

        if ( needCreation.size() > 0 ) {
            // Create the new sources
            createSourcesForInfos(needCreation, getAfterCreateSourceFunc(needCreationOriginalSources));
        } else {
            deb("All sources already exist!\n");
            // If there were no sources needing creation, emit our frame changed
            // event
            emitSourceFrameChanged(nil);
        }
    }

    // Return a callback that's executed once the Shotgun metadata has been
    // fetched for the Versions to replace the content of the given list of
    // sources
    method: getSwapAfterLoadFunc((void; StringMap[]); string[] sourceNames)
    {
        \: (void; StringMap[] infos) {
            this.replaceSourcesWithInfos(sourceNames, infos);
        };
    }

    // Replace the contents of the source with the given name with the version
    // with the given id
    method: swapVersionsForSources(void; string[] sourceNames, int[] versionIds)
    {
        // Fetch the metadata for this version
        collectVersionInfo(int[] {versionIds}, getSwapAfterLoadFunc(sourceNames));
    }

    // Get the entity type and id for the source being currently viewed
    method: entityForCurrentSource((string, int);) {
        // Get the first source
        let sourceName = shotgun.theMode().singleSourceName();
        string nilString;

        if ( sourceName eq nil ) {
            return (nilString, -1);
        }

        // Attempt to get the Shotgun metadata for this source. If there is none
        // return
        let sgInfo = shotgun_fields.infoFromSource(sourceName);

        if ( sgInfo eq nil ) {
            return (nilString, -1);
        }

        // Determine the link associated with this source. It could be either an
        // Asset or a Shot
        string link = sgInfo.find("link");

        // If there is no link, return
        if ( link eq nil ) {
            return (nilString, -1);
        }

        // Get the version id of the current source
        let versionId = sgInfo.findInt("id");

        // If there is none, return
        if ( versionId == -int.max ) {
            return (nilString, -1);
        }

        // Get the type and id of the associated entity
        let (_, t, id) = shotgun_fields.extractEntityValueParts(link);

        // and return them
        return (t, id);
    }

    // Get all of the version ids associated with the current source being
    // viewed in RV
    method: _collectAllVersionsOfCurrentSource(void; (void; string, string, int, int, StringMap[]) afterFunc)
    {
        let sourceName = shotgun.theMode().singleSourceName();

        if ( sourceName eq nil ) {
            return;
        }

        // Attempt to get the Shotgun metadata for this source. If there is none
        // return
        let sgInfo = shotgun_fields.infoFromSource(sourceName);

        if ( sgInfo eq nil ) {
            return;
        }

        // Get the version id of the current source
        let versionId = sgInfo.findInt("id");

        if ( versionId == -int.max ) {
            return;
        }

        // Get the type and id of the associated entity
        let (t, id) = entityForCurrentSource();

        if ( t eq nil || id == -1 ) {
            return;
        }

        // We pass the source name and current version id in so that they can
        // be modified
        function: postFunc(void; StringMap[] infos) {
            afterFunc(sourceName, t, id, versionId, infos);
        }

        // Collect the version info and, when finished, execute the completion
        // callback
        collectAllVersionsOfEntity(id, t, postFunc);
    }

    // Return a callback that's executed after the metadata for the previous version
    // is finished loading
    method: getPreviousVersionAfterLoadFunc((void; string, string, int, int, StringMap[]);)
    {
        \: (void; string sourceName, string entityType, int entityId, int versionId, StringMap[] infos) {
            if ( infos.size() == 0 ) {
                return;
            }

            int i = -1;

            // Iterate over all of the info entries and find the index of the
            // one whose version id matches our original version id
            int j;
            for_index(j; infos) {
                string id = infos[j].find("id");

                if ( id eq nil ) {
                    continue;
                }

                if ( int(id) == versionId ) {
                    i = j;
                    break;
                }
            }

            if ( i < 1 ) {
                displayFeedback("Earliest Version reached", 3.0);
                return;
            }

            string vName = infos[i - 1].find("name");
            if ( vName neq nil ) {
                displayFeedback("Displaying previous Version: %s" % vName, 3.0);
            } else {
                displayFeedback("Displaying previous Version", 3.0);
            }


            this.replaceSourcesWithInfos(string[] {sourceName}, StringMap[] {infos[i - 1]});
        };

    }

    // Switch from the version currently being viewed to its predecessor without
    // affecting the rest of the sequence or session
    method: previousVersion(void; Event e) {
        deb("previousVersion called\n");

        if ( e neq nil ) {
            e.reject();
        }

        // Make sure that we clear the _activeVersion member attribute
        clearActiveVersion();
        _collectAllVersionsOfCurrentSource(getPreviousVersionAfterLoadFunc());
    }

    // Return a callback that's executed after the metadata for the next version
    // is finished loading
    method: getNextVersionAfterLoadFunc((void; string, string, int, int, StringMap[]);)
    {
        \: (void; string sourceName, string entityType, int entityId, int versionId, StringMap[] infos) {
            if ( infos.size() == 0 ) {
                return;
            }

            int i = -1;

            // Iterate over all of the info entries and find the index of the
            // one whose version id matches our original version id
            int j;
            for_index(j; infos) {
                string id = infos[j].find("id");

                if ( id eq nil ) {
                    continue;
                }

                if ( int(id) == versionId ) {
                    i = j;
                    break;
                }
            }

            if ( i < 0 || i >= infos.size() - 1 ) {
                displayFeedback("Latest Version reached", 3.0);
                return;
            }

            string vName = infos[i + 1].find("name");
            if ( vName neq nil ) {
                displayFeedback("Displaying next Version: %s" % vName, 3.0);
            } else {
                displayFeedback("Displaying next Version", 3.0);
            }

            this.replaceSourcesWithInfos(string[] {sourceName}, StringMap[] {infos[i + 1]});
        };

    }

    // Switch from the version currently being viewed to its successor without
    // affecting the rest of the sequence or session
    method: nextVersion(void; Event e) {
        deb("nextVersion called\n");
        if ( e neq nil ) {
            e.reject();
        }

        clearActiveVersion();
        _collectAllVersionsOfCurrentSource(getNextVersionAfterLoadFunc());
    }

    // Return whether flagged data is available for Versions
    method: flaggedFieldExists(bool;) {
        // Ensure that the "flagged" field is available for Versions
        let fields = shotgun_fields.fieldListByEntityType("Version");

        for_each(field; fields) {
            if ( field == "flagged" ) {
                return true;
            }
        }

        return false;
    }

    // Set the _activeVersion member attribute to the given StringMap
    // The _activeVersion is used to track what the original version was when
    // nextFlaggedVersion and previousFlaggedVersion were initially triggered.
    method: setActiveVersion(void; StringMap info) {
        _activeVersion = info;
    }

    // Clear the _activeVersion
    // The _activeVersion is used to track what the original version was when
    // nextFlaggedVersion and previousFlaggedVersion were initially triggered.
    // It should be cleared whenever a different operation is triggered (like
    // previousVersion/nextVersion) or when the session is rewritten, or the
    // entity changes
    method: clearActiveVersion(void;) {
        _activeVersion = nil;
    }

    // Like the above, but only clears the active version if the session has
    // changed
    method: clearActiveVersionIfCurrentEntityDiffers(void;) {
        // There is no current active version, so nothing to do
        if ( _activeVersion eq nil ) {
            return;
        }

        // Determine the entity type and id for the current source
        let (t, id) = entityForCurrentSource();

        // Couldn't be determined, so clear anyway
        if ( t eq nil && id == -1 ) {
            clearActiveVersion();
            return;
        }

        // Get the link for the active version
        let link = _activeVersion.find("link");

        // If it's nil then we clear the active version anyway
        if ( link eq nil ) {
            clearActiveVersion();
            return;
        }

        // Get the entity type and id of the active version's link
        let (_, et, eid) = shotgun_fields.extractEntityValueParts(link);

        // They're the same, so don't clear the active version
        if ( t == et && id == eid ) {
            return;
        }

        // They're different, so clear the active version
        clearActiveVersion();
    }

    // Called by previousFlaggedVersion after all of the versions for the current entity have
    // been collected. Returns a callback function
    method: getPreviousAfterLoadFunc((void; string, string, int, int, StringMap[]);) {
        \: (void; string sourceName, string entityType, int entityId, int versionId, StringMap[] infos) {
            if ( infos.size() == 0 ) {
                return;
            }

            int i = -1;

            deb("Finding previous flagged version\n");
            // Walk backwards through the list of Versions looking for for the current
            // Version. Then pick the next flagged Version that we encounter, or the
            // active Version.
            bool pickNext = false;
            int j;
            for(j = infos.size() - 1; j >= 0; j--) {
                // Only enter this logic if we've found our currently viewed version in the
                // list
                if ( pickNext ) {
                    if ( infos[j].findBool("flagged") ) {
                        // The previous version is flagged
                        i = j;
                        break;
                    } else if ( this._activeVersion neq nil &&
                                this._activeVersion.findInt("id") == infos[j].findInt("id") ) {
                        // The previous version is the active version
                        i = j;
                        break;
                    }
                }

                if ( infos[j].findInt("id") == versionId ) {
                    // We've found the currently viewed version in the list. We want to pick the
                    // next version that we come across that is flagged or active
                    pickNext = true;
                } else if ( j == 0 ) {
                    i = 0;
                }
            }

            if ( i < 0 ) {
                displayFeedback("Earliest version reached");
                return;
            }

            let inf = infos[i];

            // Flash the name of the version we're moving to
            string vName = inf.find("name");
            if ( vName neq nil ) {
                displayFeedback("Displaying Version: %s" % vName, 3.0);
            }

            this.replaceSourcesWithInfos(string[] {sourceName}, StringMap[] {inf});
        };
    }

    // Move to the previous flagged version in the history for this entity
    method: previousFlaggedVersion(void; Event e) {
        if ( e neq nil ) {
            e.reject();
        }

        // Ensure that the "flagged" field is available for Versions
        if ( !flaggedFieldExists() ) {
            // It's not, so exit
            print("ERROR: Unable to find flagged field in RV-Shotgun integration config");
            return;
        }

        // If there is no active version then we'll want to set one
        if ( _activeVersion eq nil ) {
            // Determine the name for the currently viewed source
            let sourceName = shotgun.theMode().singleSourceName();

            if ( sourceName neq nil ) {
                // Get the shotgun metadata for this source
                let sgInfo = shotgun_fields.infoFromSource(sourceName);

                if ( sgInfo neq nil && !sgInfo.findBool("flagged") ) {
                    // Only set the active version if there is shotgun metadata
                    // and the version is not flagged
                    setActiveVersion(sgInfo);
                }
            }
        }

        deb("Finding all versions for the current entity\n");
        _collectAllVersionsOfCurrentSource( getPreviousAfterLoadFunc() );
    }

    // Called by nextFlaggedVersion after all of the versions for the current entity have
    // been collected. Returns a callback function
    method: getNextAfterLoadFunc((void; string, string, int, int, StringMap[]);) {
        \: (void; string sourceName, string entityType, int entityId, int versionId, StringMap[] infos) {
            if ( infos.size() == 0 ) {
                return;
            }

            int i = -1;

            deb("Finding next flagged version\n");
            // Walk through the list of Versions looking for for the current
            // Version. Then pick the next flagged Version that we encounter, or the
            // active Version.
            bool pickNext = false;
            int j;
            for(j = 0; j < infos.size(); j++) {
                // Only enter this logic if we've found our currently viewed version in the
                // list
                if ( pickNext ) {
                    if ( infos[j].findBool("flagged") ) {
                        // The next version is flagged
                        i = j;
                        break;
                    } else if ( this._activeVersion neq nil &&
                                this._activeVersion.findInt("id") == infos[j].findInt("id") ) {
                        // The next version is the active version
                        i = j;
                        break;
                    }
                }

                if ( infos[j].findInt("id") == versionId ) {
                    // We've found the currently viewed version in the list. We want to pick the
                    // next version that we come across that is flagged or active
                    pickNext = true;
                } else if ( j == infos.size() - 1 ) {
                    i = infos.size() - 1;
                }
            }

            if ( i < 0 ) {
                displayFeedback("Latest version reached");
                return;
            }

            let inf = infos[i];

            // Flash the name of the version we're moving to
            string vName = inf.find("name");
            if ( vName neq nil ) {
                displayFeedback("Displaying Version: %s" % vName, 3.0);
            }

            this.replaceSourcesWithInfos(string[] {sourceName}, StringMap[] {inf});
        };
    }

    // Move to the next flagged version in the history for this entity
    method: nextFlaggedVersion(void; Event e) {
        if ( e neq nil ) {
            e.reject();
        }

        // Ensure that the "flagged" field is available for Versions
        if ( !flaggedFieldExists() ) {
            // It's not, so exit
            print("ERROR: Unable to find flagged field in RV-Shotgun integration config");
            return;
        }

        if ( _activeVersion eq nil ) {
            let sourceName = shotgun.theMode().singleSourceName();

            if ( sourceName neq nil ) {
                let sgInfo = shotgun_fields.infoFromSource(sourceName);

                if ( sgInfo neq nil && !sgInfo.findBool("flagged") ) {
                    setActiveVersion(sgInfo);
                }
            }
        }

        deb("Finding all versions for the current entity\n");
        _collectAllVersionsOfCurrentSource( getNextAfterLoadFunc() );
    }

    // Return the names of the Shotgun sources that are connected to the current
    // view node and visible at the current frame
    method: currentShotgunSourceNames(string[];)
    {
        let f = frame(),
            shotgunSourceNames = string[](),
            sourceNames = sourcesAtFrame(f);

        if (sourceNames.size() < 1) {
            return shotgunSourceNames;
        }

        let vnode = viewNode(),
            vnodeInputs = nodeConnections(vnode, false)._0;

        // Look for shotgun data for each source
        for (int j = 0; j < sourceNames.size(); ++j) {
            let sourceName = sourceNames[j],
                found = false;
            for (int k = 0; k < vnodeInputs.size(); ++k) {
                let i = vnodeInputs[k];
                if ( i == nodeGroup(sourceName) ) {
                    found = true;
                    break;
                }
            }

            if ( !found ) {
                continue;
            }

            let sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                shotgunSourceNames.push_back(sourceName);
            }
        }

        return shotgunSourceNames;
    }

    // Get the list of ids of Versions associated with the sources that are
    // connected to the current view node and visible at the current frame
    method: currentShotgunSources(int[];) {
        int[] versionIds;

        let sourceNames = currentShotgunSourceNames();

        if (sourceNames.size() < 1) {
            return versionIds;
        }

        // Look for shotgun data for each source
        for (int i = 0; i < sourceNames.size(); ++i) {
            let sourceName = sourceNames[i],
                sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                string id = sgInfo.find("id");

                if (id neq nil) {
                    let found = false;
                    for (int j = 0; j < versionIds.size(); ++j) {
                        let vid = versionIds[j];
                        if ( vid == int(id) ) {
                            found = true;
                            break;
                        }
                    }

                    if ( !found ) {
                        versionIds.push_back(int(id));
                    }
                }
            }
        }

        return versionIds;
    }

    method: allShotgunSourceNames(string[];)
    {
        if ( _allShotgunSourceNames neq nil )
            return _allShotgunSourceNames;

        let sourceNames = nodesOfType("RVFileSource"),
            shotgunSourceNames = string[]();

        if (sourceNames.size() < 1) {
            return shotgunSourceNames;
        }

        let vnode = viewNode(),
            vnodeInputs = nodeConnections(vnode, false)._0;

        // Look for shotgun data for each source
        for (int j = 0; j < sourceNames.size(); ++j) {
            let sourceName = sourceNames[j],
                found = false;
            for (int k = 0; k < vnodeInputs.size(); ++k) {
                let i = vnodeInputs[k];
                if ( i == nodeGroup(sourceName) ) {
                    found = true;
                    break;
                }
            }

            if ( !found ) {
                continue;
            }

            let sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                shotgunSourceNames.push_back(sourceName);
            }
        }

        _allShotgunSourceNames = shotgunSourceNames;
        return shotgunSourceNames;
    }

    // Return a list of version ids for all shotgun sources that are connected to
    // the current view node (not just the ones on the current frame)
    method: allShotgunSources(int[];) {
        if ( _allShotgunSourceIds neq nil )
            return _allShotgunSourceIds;

        int[] versionIds;

        let sourceNames = allShotgunSourceNames();

        if (sourceNames.size() < 1) {
            return versionIds;
        }

        // Look for shotgun data for each source
        for (int i = 0; i < sourceNames.size(); ++i) {
            let sourceName = sourceNames[i],
                sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                string id = sgInfo.find("id");

                if (id neq nil) {
                    let found = false;
                    for (int j = 0; j < versionIds.size(); ++j) {
                        let vid = versionIds[j];
                        if ( vid == int(id) ) {
                            found = true;
                            break;
                        }
                    }

                    if ( !found ) {
                        versionIds.push_back(int(id));
                    }
                }
            }
        }

        _allShotgunSourceIds = versionIds;
        return versionIds;
    }

    // Return the project id of the first source that we come across
    method: currentProjectId(int;) {
        let f = frame(),
            sourceNames = currentShotgunSourceNames();

        if (sourceNames.size() < 1) {
            return -1;
        }

        // Look for shotgun data for each source
        for_each(sourceName; sourceNames) {
            let sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                let (pId, pName) = shotgun.theMode().projectIDFromSource(sourceName);
                return pId;
            }
        }

        return -1;
    }

    // Find the Version with the given Id in Shotgun, attempt to locate a media
    // format that we're congfigured to view and then open that path in the
    // Finder on a Mac.
    method: viewVersionInFileSystemFromId(void; int versionId) {
        collectVersionInfo(int[] {versionId}, openInFileSystem);
    }

    method: openInFileSystem(void; StringMap[] infos) {
        if (infos.size() < 1) {
            return;
        }

        let inf = infos[0];

        // Prioritise our preferred media, and fallback on others if we can't
        // find that media for this
        let mediaPref = shotgun.theMode()._prefs.loadMedia;
        string mediaType = shotgun.theMode().mediaTypeFallback(mediaPref, inf);
        let media = shotgun_fields.mediaTypePath(mediaType, inf);

        if (media eq nil || media == "") {
            return;
        }

        if (shotgun.theMode().mediaIsMovie(media)) {
            system.system("open --reveal %s" % media);
        } else {
            system.system("open --reveal %s" % path.dirname(media));
        }
    }

    method: currentMediaIsMovie(bool;) {
        let f = frame(),
            sourceNames = currentShotgunSourceNames();

        if (sourceNames.size() < 1) {
            return false;
        }

        // Look for shotgun data for each source
        string filePath;
        for_each(sourceName; sourceNames) {
            let sgInfo = shotgun_fields.infoFromSource(sourceName);

            if (sgInfo neq nil) {
                string id = sgInfo.find("id");

                if (id neq nil) {
                    filePath = sourceMedia(sourceName)._0;
                    break;
                }
            }
        }

        return shotgun.theMode().mediaIsMovie(filePath);
    }

    // Return the id of the version currently being viewed and its completion
    // ratio for progress indicators
    method: playheadPosition ((int, float); )
    {
        // Get the current frame and all of the sources that exist at that
        // frame
        let f = frame(),
            sourceNames = currentShotgunSourceNames();

        (int, float) nilValue = (-1, 0.0);

        // If there are no sources at that frame, return a nil(ish) tuple
        if (sourceNames.size() < 1) {
            return nilValue;
        }

        // Get a bunch of info about the current source
        let sourceName = sourceNames.front(),
            frameRange = getFrameRangeForShotgunSource(sourceName),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1;

        if ( localStartFrame == -1 && localEndFrame == -1 ) {
            return nilValue;
        }

        let sgInfo = shotgun_fields.infoFromSource(sourceName);
        if (sgInfo eq nil) {
            return nilValue;
        }

        string id = sgInfo.find("id");
        if (id eq nil) {
            return nilValue;
        }

        let localFrame = sourceFrame(f);
        float completion = 0.0;
        if ( localFrame >= localStartFrame && localFrame <= localEndFrame ) {
            completion = float(localFrame - localStartFrame) / (localEndFrame - localStartFrame);
        }

        return (int(id), completion);
    }

    // Upload a thumbnail generated from the center frame of the current source
    // being viewed in RV and upload it to the Version with the given id
    method: uploadThumbnailForCurrentSource(ExternalProcess; int versionId) {

        // Get the current frame and all of the sources that exist at that frame
        let f = frame(),
            sourceNames = sourcesAtFrame(f);

        // If there are no sources at the current frame then abort
        string error;
        if (sourceNames.size() < 1) {
            error = "No media is currently loaded";
            sendInternalEvent("sg-thumbnail-upload-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        let sourceName = sourceNames.front(),
            frameRange = getFrameRangeForSource(sourceName),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1;

        if (localStartFrame == -1 && localEndFrame == -1) {
            error = "Could not locate a source at the current frame with Shotgun info";
            sendInternalEvent("sg-thumbnail-upload-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        let localFrame = sourceFrame(f);

        int middleFrame = f;
        if ( localStartFrame != localEndFrame ) {
            int middleFrameOffset = (localEndFrame - localStartFrame + 1) / 2;
            middleFrame = f - (localFrame - localStartFrame) + middleFrameOffset;
        }

        let filePath = sourceMedia(sourceName)._0;

        // Create a directory into which we can generate the thumbnail
        let dirName = path.join(QDir.tempPath(), "%d-%d/thumb" % (system.getpid(), system.time()));
        if (runtime.build_os() == "WINDOWS") {
            system.system("mkdir %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("mkdir -p %s" % dirName);
        }

        // Use the name of the source as the basename of the thumbnail
        string filepat = "%s/%s.#.jpg" % (dirName, path.basename(filePath));

        string[] args = {
            makeTempSession(),
            "-o", filepat,
            "-t", "%d" % middleFrame
        };

        // We'll perform the upload in a post process
        function: finishedFunc(void;) {
            thumbnailExportCompleted(versionId, dirName);
        }

        deb("Exporting thumbnail\n");
        rvio("Export Thumbnail", args, finishedFunc);
    }

    // Once the export has completed, upload it to the Version with the given id
    method: thumbnailExportCompleted(void; int versionId, string dirName) {
        // Get the file contents of the temp directory
        deb("Locating exported thumbnails\n");
        let contents = QDir(dirName).entryInfoList(QDir.Files, 0);

        // Look for the thumbnail in this directory. It should be the only file
        string error;
        if (contents.size() > 0) {
            let filePath = contents[0].absoluteFilePath();

            deb("Uploading thumbnail\n");

            // When the upload finishes we'll do some cleanup of the temp files
            function: finishedFunc(void; Event event) {
                deb("Thumbnail upload finished\n");
                event.reject();
                removeTempSession();
                if (runtime.build_os() == "WINDOWS") {
                    system.system("rmdir /s /q %s" % regex.replace("/", dirName, "\\\\"));
                } else {
                    system.system("rm -rf %s" % dirName);
                }
            }
            app_utils.bind("sg-thumbnail-upload-finished", finishedFunc);

            // Upload the jpeg
            error = shotgun_upload.theMode().uploadJPEGthumbnail(filePath, versionId, "Version", "thumb_image", "sg-thumbnail-upload-finished");
            if (error == "") {
                return;
            }
        } else {
            // If the file wasn't found there must have been an error in the
            // export process
            error = "The thumbnail export failed";
        }

        // Something went wrong. Inform javascript that there was an error
        sendInternalEvent("sg-thumbnail-upload-error", error);
        sendInternalEvent("sg-submission-error", error);

        // Do some clean up
        removeTempSession();
        if (runtime.build_os() == "WINDOWS") {
            system.system("rmdir /s /q %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("rm -rf %s" % dirName);
        }
    }

    // Return whether RV for the current operating system supports quicktime encoding
    // Not currently supported for win64 OS where the RV version is less than 4.0
    method: supportsQuicktimeEncoding(bool;) {
        let os = runtime.build_os(),
            arch = runtime.build_architecture(),
            isWin64 = os == "WINDOWS" && arch == "IA32_64",
            verParts = system.getenv("TWK_APP_VERSION").split(".");
            return !isWin64 || ( verParts.size() > 0 && int(verParts[0]) >= 4 );
    }

    // Create a quicktime from the current source at the given path.
    method: exportQuicktimeForCurrentSource(void; string outputPath, string[] metadata) {
        // Get the current frame and all of the sources that exist at that frame
        let f = frame(),
            sourceNames = sourcesAtFrame(f);

        // If there are no sources at the current frame then abort
        string error;
        if (sourceNames.size() < 1) {
            error = "No media is loaded at the current frame";
            sendInternalEvent("sg-quicktime-export-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        let sourceName = sourceNames.front(),
            frameRange = getFrameRangeForSource(sourceName),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1;

        if ( localStartFrame == -1 && localEndFrame == -1 ) {
            error = "Could not find a Shotgun source at the current frame";
            sendInternalEvent("sg-quicktime-export-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        let localFrame = sourceFrame(f);

        // Find the start and end frames of the current source
        int startFrame = f - localFrame + localStartFrame;
        int endFrame = f - localFrame + localEndFrame;

        // Ensure that outputPath is an absolute path
        outputPath = QFileInfo(outputPath).absoluteFilePath();

        // Create a directory into which we can generate the thumbnail
        let dirName = path.join( path.join(QDir.tempPath(), "%d-%d" % ( system.getpid(), system.time() ) ), "mov");
        if ( !QDir(dirName).exists() ) {
            QDir("").mkpath(dirName);
        }

        string tempFilePath = path.join(dirName, QFileInfo(outputPath).fileName());

        // Add some slate and overlay stuff
        string[] args = {
            makeTempSession(),
            "-o", tempFilePath,
            "-t", "%d-%d" % (startFrame, endFrame),
            "-v",
            "-overlay", "sg_frameburn", "0.5", "1.0", "30", "%d-%d=%d" % (startFrame, endFrame, localStartFrame - 1),
            "-leader", "simpleslate", "Screening Room"
        };

        for_each(item; metadata) {
            args.push_back(item);
        }

        app_utils.bind("sg-quicktime-export-finished", makeExportCompleteFunc(dirName, outputPath, "quicktime"));

        error = shotgun.runRVIO(args, "sg-quicktime-export-finished");
    }


    // Create a quicktime from the current source at the given path.
    method: exportPngForCurrentSource(void; string outputPath) {
        // Get the current frame and all of the sources that exist at that frame
        let f = frame(),
            sourceNames = sourcesAtFrame(f);

        // If there are no sources at the current frame then abort
        string error;
        if (sourceNames.size() < 1) {
            error = "No media is loaded at the current frame";
            sendInternalEvent("sg-png-export-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        // Ensure that outputPath is an absolute path
        outputPath = QFileInfo(outputPath).absoluteFilePath();

        // Create a directory into which we can generate the thumbnail
        let dirName = path.join( path.join(QDir.tempPath(), "%d-%d" % ( system.getpid(), system.time() ) ), "png");
        if ( !QDir(dirName).exists() ) {
            QDir("").mkpath(dirName);
        }

        string tempFilePath = path.join(dirName, QFileInfo(outputPath).fileName());

        // Add some slate and overlay stuff
        string[] args = {
            makeTempSession(),
            "-o", tempFilePath,
            "-v"
        };

        app_utils.bind("sg-png-export-finished", makeExportCompleteFunc(dirName, outputPath, "png"));

        error = shotgun.runRVIO(args, "sg-png-export-finished");
    }

    method: onExportComplete(void; Event e, string dirName, string outputPath, string eventName) {
        e.reject();
        removeTempSession();
        let tempDir = QDir(dirName);

        if (e.contents() == "") {
            outputPath = QFileInfo(outputPath).absoluteFilePath();

            let outputFile = QFile(outputPath);
            if ( outputFile.exists() ) {
                outputFile.remove();
            }

            let contents = tempDir.entryInfoList(QDir.Files, 0);
            int i;
            for ( i = 0; i < contents.size(); i++ ) {
                let tempFileName = contents[i].absoluteFilePath(),
                    tempFile = QFile(tempFileName);

                tempFile.copy(outputPath);
                tempFile.remove();
            }
        }

        // Remove the entire directory structure that was created earlier
        let parentDir = QFileInfo(dirName).dir().absolutePath();
        if (runtime.build_os() == "WINDOWS") {
            system.system("rmdir /s /q %s" % regex.replace("/", parentDir, "\\\\"));
        } else {
            system.system("rm -rf %s" % parentDir);
        }
        if ( e.contents() == "" ) {
            sendInternalEvent("sg-" + eventName + "-export-complete");
            return;
        }

        sendInternalEvent("sg-" + eventName + "-export-error", e.contents());
        sendInternalEvent("sg-submission-error", e.contents());
    }


    // Do cleanup and error detection when we're informed that the export has
    // has completed
    method: makeExportCompleteFunc((void; Event); string dirName, string outputPath, string eventName) {
        \: (void; Event e) {
            this.onExportComplete(e, dirName, outputPath, eventName);
        };
    }

    // Generate a filmstrip thumbnail from the source being submitted
    method: uploadFilmstripForCurrentSource(ExternalProcess; int versionId) {
        deb("Exporting filmstrip thumbnail\n");
        // Get the current frame and all of the sources that exist at that frame
        let f = frame(),
            sourceNames = sourcesAtFrame(f);

        // If there are no sources at the current frame then abort
        string error;
        if (sourceNames.size() < 1) {
            error = "No media is loaded at the current frame";
            sendInternalEvent("sg-filmstrip-export-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        let sourceName = sourceNames.front(),
            frameRange = getFrameRangeForSource(sourceName),
            startFrame = frameRange._0,
            endFrame = frameRange._1,
            smi = sourceMediaInfo(sourceName),
            width = smi.width,
            height = smi.height;

        if ( startFrame == -1 && endFrame == -1 ) {
            error = "Could not determine frame range of source";
            sendInternalEvent("sg-filmstrip-export-error", error);
            sendInternalEvent("sg-submission-error", error);
            return;
        }

        // The frame count
        int nFrames = endFrame - startFrame + 1;

        // If there are fewer than 25 frames in the sequence then all of them
        // will appear in the filmstrip thumbnail. If there are more than 25 then
        // we'll choose 25 frames that are roughly equally spaced throughout the
        // sequence
        int[] frames;
        int i;
        if ( nFrames < 25 ) {
            for ( i = startFrame; i <= endFrame; i++ ) {
                frames.push_back(i);
            }
        } else {
            let incr = (nFrames - 1) / 24.0;
            for ( i = 0; i <= 24; i++ ) {
                frames.push_back( math.floor( startFrame + i * incr ) );
            }
        }

        // Get the file associated with this source
        let sourceFilePath = getFilePathForSource(sourceName);

        // Create a directory into which we can generate the thumbnail
        let dirName = path.join(QDir.tempPath(), "%d-%d/filmstrip" % (system.getpid(), system.time()));
        if (runtime.build_os() == "WINDOWS") {
            system.system("mkdir %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("mkdir -p %s" % dirName);
        }

        string fileName = "filmstrip_session.rv";
        string filmstripFileName = "filmstrip.jpg";

        let sessionFilePath = QDir(dirName).filePath(fileName);
        let filmstripFilePath = QDir(dirName).filePath(filmstripFileName);
        let sessionStream = ofstream(sessionFilePath);

        // Determine the width and height of the filmstrip that will be exported
        float ar = float(height) / (frames.size() * width);

        // Each individual frame needs to be 240px in width
        int frameWidth = 240;

        // So the total width is 240 * the number of frames being exported
        int outputWidth = frameWidth * frames.size();
        int outputHeight = math.floor(outputWidth * ar);

        // Now we generate the rv session file
        // Write out the header
        print(sessionStream, """GTOa (3)

rv : RVSession (2)
{
    session
    {
        string viewNode = "defaultLayout"
        int marks = [ ]
        int[2] range = [ [ 1 4 ] ]
        int[2] region = [ [ 1 4 ] ]
        float fps = 24
        int realtime = 0
        int inc = 1
        int currentFrame = 1
        int version = 1
        int background = 0
    }
}
""");

        // Write out the list of connections
        print(sessionStream, """
connections : connection (1)
{
    evaluation
    {
        string lhs = [ """);

        // Print out a source name for each frame
        for_each(f; frames) {
            print(sessionStream, "\"sourceGroup%06d\" " % f);
        }

        print(sessionStream, """ ]
        string rhs = [ """);

        for_each(f; frames) {
            print(sessionStream, "\"defaultLayout\" ");
        }

        print(sessionStream, """ ]
    }

    top
    {
        string nodes = [ "defaultLayout" """);

        // Print out a source name for each frame
        for_each(f; frames) {
            print(sessionStream, "\"sourceGroup%06d\" " % f);
        }

        // Print the layout, which organises the individual frames into a row
        // And the default stack which has attributes that set the dimensions of
        // the output
        print(sessionStream, """ ]
    }
}

defaultLayout : RVLayoutGroup (1)
{
    ui
    {
        string name = "Default Layout"
    }

    layout
    {
        string mode = "row"
    }

    timing
    {
        int retimeInputs = 1
    }

    session
    {
        float fps = 24
        int marks = [ ]
        int frame = 1
    }
}

defaultLayout_stack : RVStack (1)
{
    output
    {
        float fps = 24
        int size = [ %d %d ]
        int autoSize = 0
        string chosenAudioInput = ".all."
    }

    mode
    {
        int useCutInfo = 1
        int alignStartFrames = 0
        int strictFrameRanges = 0
    }

    composite
    {
        string type = "over"
    }
}
""" % (outputWidth, outputHeight));

        // Now add one source for each frame
        for_each(f; frames) {
            print(sessionStream, """
sourceGroup%06d : RVSourceGroup (1)
{
    ui
    {
        string name = "%d"
    }
}
""" % (f, f));

            print(sessionStream, """
sourceGroup%06d_source : RVFileSource (1)
{
    media
    {
        string movie = "%s"
    }

    group
    {
        float fps = 24
        float volume = 1
        float audioOffset = 0
        int rangeOffset = 0
        int noMovieAudio = 0
        float balance = 0
        float crossover = 0
    }

    cut
    {
        int in = %d
        int out = %d
    }
}
""" % (f, sourceFilePath, f, f));
        }

        // Close the file
        deb("Writing session to %s\n" % sessionFilePath);
        sessionStream.close();

        string[] args = {
            sessionFilePath,
            "-resize", frameWidth, outputHeight,
            "-outres", outputWidth, outputHeight,
            "-o", filmstripFilePath
        };

        // After the file has been exported, we'll do the upload in a post
        // process
        function: finishedFunc(void;) {
            filmstripThumbnailExportCompleted(versionId, dirName);
        }

        deb("Generating thumbnail to %s\n" % filmstripFilePath);
        rvio("Export filmstrip thumbnail", args, finishedFunc);
    }

    method: filmstripThumbnailExportCompleted(void; int versionId, string dirName) {
        // Get the file contents of the temp directory
        let contents = QDir(dirName).entryInfoList(QDir.Files, 0);

        // Look for the thumbnail in this directory. It should be the only file
        string error;
        if (contents.size() > 0) {
            int i;
            for ( i = 0; i < contents.size(); i++ ) {
                if ( contents[i].suffix() != "jpg" ) {
                    continue;
                }

                let filePath = contents[i].absoluteFilePath();

                // When the upload finishes do some cleanup
                \: finishedFunc(void; Event event) {
                    event.reject();
                    deb("Filmstrip thumbnail upload finished.\n");
                    let parentDir = path.dirname(dirName);
                    deb("Removing %s\n" % parentDir);
                    if (runtime.build_os() == "WINDOWS") {
                        system.system("rmdir /s /q %s" % regex.replace("/", parentDir, "\\\\"));
                    } else {
                        system.system("rm -rf %s" % parentDir);
                    }
                }

                app_utils.bind("sg-filmstrip-upload-finished", finishedFunc);

                // Upload the filmstrip
                deb("Uploading filmstrip thumbnail: %s\n" % filePath);
                error = shotgun_upload.theMode().uploadJPEGthumbnail(filePath, versionId, "Version", "filmstrip_thumb_image", "sg-filmstrip-upload-finished");

                if (error == "") {
                    return;
                }
            }
        } else {
            // If the file wasn't found there must have been an error in the
            // export process
            error = "The filmstrip thumbnail export failed";
        }

        // Something went wrong. Inform javascript that there was an error
        sendInternalEvent("sg-filmstrip-upload-error", error);
        sendInternalEvent("sg-submission-error", error);

        // Do some clean up
        if (runtime.build_os() == "WINDOWS") {
            system.system("rmdir /s /q %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("rm -rf %s" % dirName);
        }
    }

    method: submissionComplete(void;) {
        sendInternalEvent("sg-submission-complete");
        deb("Emitted sg-submission-complete\n");
    }

    method: onSubmissionError(void; Event e) {
        e.reject();
        deb("Emitted sg-submission-error");
    }

    // Return whether annotation mode is currently active
    method: annotationModeIsEnabled(bool;) {
        require annotate_mode;

        State state = data();
        ModeManagerMode manager = state.modeManager;
        ModeManagerMode.ModeEntry entry = manager.findModeEntry ("annotate_mode");

        if (entry eq nil) {
            print ("ERROR: annotate mode unknown ?\n");
            return false;
        }

        if (entry.mode eq nil || !entry.mode._active)
            return false;

        return true;
    }

    method: toggleAnnotationTools(void;) {
        require annotate_mode;

        State state = data();
        ModeManagerMode manager = state.modeManager;
        ModeManagerMode.ModeEntry entry = manager.findModeEntry ("annotate_mode");

        if (entry eq nil) {
            print ("ERROR: annotate mode unknown ?\n");
            return;
        }

        if (entry.mode eq nil || !entry.mode._active) {
            manager.activateEntry (entry, true);
            if (entry.mode eq nil || !entry.mode._active) {
                print ("ERROR: activation of annotate mode failed\n");
                return;
            }
        } else {
            manager.activateEntry(entry, false);
        }
    }

    // Get a list of the frame numbers which contain annotations for the
    // currently viewed source that should be uploaded
    method: getAnnotatedFramesForCurrentSource(int[];) {

        int[] framesToExport;

        // Find all of the annotated frames and the current sources
        let frames = findAnnotatedFrames(),
            currentFrame = frame(),
            sourceNames = sourcesAtFrame(currentFrame);

        // If there are no frames or no current sources, return an empty list
        if (frames.empty() || sourceNames.size() < 1) {
            return framesToExport;
        }

        // Find a bunch of metadata about the current source
        let sourceName = sourceNames.front(),
            frameRange = getFrameRangeForShotgunSource(sourceName),
            localCurrentFrame = sourceFrame(currentFrame),
            localStartFrame = frameRange._0,
            localEndFrame = frameRange._1;

        // If the annotated frame falls within the frame range of the currently
        // viewed source, then add it to the list of frames to export
        for_each(f; frames) {
            // determine this frame number relative to the start of the current
            // source
            int localFrame = localCurrentFrame - currentFrame + f;
            if ( localFrame >= localStartFrame && localFrame <= localEndFrame ) {
                framesToExport.push_back(f);
            }
        }

        return framesToExport;
    }

    // Determine whether the currently viewed source has annotated frames
    method: hasAnnotatedFramesToUpload(bool;) {
        // Check if our upload status for this source is dirty
        let frames = findAnnotatedFrames(),
            currentFrame = frame(),
            sourceNames = sourcesAtFrame(frame());

        // If there are no frames or no current sources, return an empty list
        if (frames.empty() || sourceNames.size() < 1) {
            return false;
        }

        // Identify the sourceName
        let sourceName = sourceNames.front();

        let newAnn = sourceName + ".screeningRoom.newAnnotation";

        // The property should exist at that point, but for defensive coding purposes, add it now
        // and set it as dirty (
        if (!propertyExists(newAnn))
        {
            newProperty(newAnn, IntType, 1);
            setIntProperty(newAnn, int[]{1}, true);
        }

        if (getIntProperty(newAnn).front() == 0) {
            deb(">>> Upload flag? Clear!\n");
            return false;
        }

        deb(">>> Upload flag? Set!\n");

        let framesToExport = getAnnotatedFramesForCurrentSource();
        return framesToExport.size() > 0;
    }

    // Find the annotated frames for the current source and upload them to
    // the note with the given id
    method: uploadAnnotatedFramesToNote(ExternalProcess; int noteId) {
        use export_utils;

        osstream timestr;

        // Get the annotated frames for the currently viewed source
        let framesToExport = getAnnotatedFramesForCurrentSource(),
            currentFrame = frame(),
            sourceNames = sourcesAtFrame(currentFrame);

        // If there are none, return
        if (framesToExport.size() < 1 || sourceNames.size() < 1) {
            return;
        }

        // In the srcs list we'll keep track of all of the sources that we come
        // across
        // For each source, in the corresponding index of the ranges list we'll
        // store a mapping of the frame range for that source to the value needed
        // to offset the current global frame number
        string[] srcs = {};
        string[] ranges = {};

        // Iterate over all of the frames that have annotations
        for_index(i; framesToExport) {
            // Add the frame to the frame spec
            let f = framesToExport[i];
            if (i > 0) print(timestr, ",");
            print(timestr, "%d" % f);

            // Find the first source at this frame
            let sourceNames = currentShotgunSourceNames(),
                sourceName = sourceNames[0];

            // Determine if this source is already in our srcs and ranges lists
            int i = -1;
            for_index(j; srcs) {
                if ( srcs[j] == sourceName ) {
                    i = j;
                    break;
                }
            }

            // If the i index is -1 that means we haven't come across this source
            // before
            if ( i == -1 ) {
                // Determine the local frame number for this source
                int localFrame = sourceFrame(f);

                // Get the start and end frame numbers of the current source in
                // local frame numbers
                let localFrameRange = getFrameRangeForShotgunSource(sourceName),
                    localStartFrame = localFrameRange._0,
                    localEndFrame = localFrameRange._1;

                if ( localStartFrame == -1 && localEndFrame == -1 ) {
                    continue;
                }

                // Determine the global start and end frames for the current
                // source
                int rangeStart = f - (localFrame - localStartFrame);
                int rangeEnd = rangeStart + (localEndFrame - localStartFrame);

                // The offset value calculated here will be used to transform
                // any global frame between rangeStart and rangeEnd to local
                // frame numbers in the sg_frameburn overlay script.
                int offset = f - localFrame;

                deb("offset: %d\n" % offset);

                // Map the frame range to the offset value and push it onto the
                // back of our lists
                string rangeSpec = "%d-%d=%d" % (rangeStart, rangeEnd, offset);

                deb("rangeSpec: %s\n" % rangeSpec);

                srcs.push_back(sourceName);
                ranges.push_back(rangeSpec);

                // Does the newAnnotation flag already exists on the source?  If not, create it.
                let newAnn = sourceName + ".screeningRoom.newAnnotation";
                if (!propertyExists(newAnn))
                {
                    newProperty(newAnn, IntType, 1);
                }

                // Clear the newAnnotation flag for this source
                setIntProperty(newAnn, int[]{0}, true);
                deb(">>> Clear upload flag.\n");
            }
        }

        // Create a temp directory to which these frames should be exported
        let dirName = path.join(QDir.tempPath(), "%d-%d" % (system.getpid(), system.time()));
        if (runtime.build_os() == "WINDOWS") {
            system.system("mkdir %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("mkdir -p %s" % dirName);
        }

        // Find the version_id of the current media, cancel if it doesn't exist
        let sgInfo = shotgun_fields.infoFromSource(sourceNames[0]);
        if (sgInfo eq nil) {
            deb("\nSource infos are nil\n");
            return;
        }
        let versionId = sgInfo.findInt("id");

        // Add an "annot" prefix so that we can identify the image as an
        // annotation just by analysing the file path
        string filepat = "%s/annot_version_%s.#.jpg" % (dirName, versionId);

        // Assemble the args to the RV command
        string[] args = {
            makeTempSession(),
            "-o", filepat,
            "-t", string(timestr),
            "-overlay", "sg_frameburn", "0.5", "1.0", "30"
        };

        // Add the frame range offset map values
        for_each(range; ranges) {
            args.push_back(range);
        }

        function: cleanUpFunc(void;) {
            annotationExportCompleted(noteId, dirName);
        }

        // Run RV. When the export has successfully completed, we emit a signal
        // that we can pick up on from the javascript side
        rvio("Export Annotated Frames", args, cleanUpFunc);
    }

    // Called once the rvio process for exporting frames has completed, indicating
    // that the frames are ready for upload.
    method: annotationExportCompleted(void; int noteId, string dirName) {
        // Get the file contents of the temp directory
        let contents = QDir(dirName).entryInfoList(QDir.Files, 0);

        // Iterate over all of the files in the directory
        string[] filePaths;
        string[] displayNames;
        for_each(fileInfo; contents) {
            // Get the file name of the current file
            let fileName = fileInfo.fileName();

            // Track down the frame number in the file name
            let parts = regex.smatch("([0-9]+)\\.jpg$", fileName);
            if ( parts neq nil ) {
                // The frame number will be the last group in the matches list
                int frame = int( parts.back() );

                // rename the file to remove trailing zeros in the annotation
                string newFileName = regex.replace("[0-9]+\\.jpg$", fileName, "%d.jpg" % frame);
                fileInfo.dir().rename(fileName, newFileName);

                // Set the file info to point to this file
                fileInfo.setFile(fileInfo.dir(), newFileName);
            }

            filePaths.push_back(fileInfo.absoluteFilePath());
            displayNames.push_back(fileName);
        }

        function: progressFunc(void; Event event) {
            attachmentUploadProgress(noteId, event);
        }

        function: finishedFunc(void; Event event) {
            attachmentUploadComplete(noteId, dirName, event);
        }

        app_utils.bind("sg-attachment-upload-progress", progressFunc);
        app_utils.bind("sg-attachment-upload-finished", finishedFunc);

        let result = shotgun_upload.theMode().uploadJPEGattachments(filePaths, displayNames, noteId, "Note", "sg-attachment-upload-progress", "sg-attachment-upload-finished");

        if (result == "") return;

        sendInternalEvent("sg-note-attachment-upload-error", result);
        sendInternalEvent("sg-submission-error", result);

        // There was an error so we should clean this stuff up
        removeTempSession();
        if (runtime.build_os() == "WINDOWS") {
            system.system("rmdir /s /q %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("rm -rf %s" % dirName);
        }
    }

    method: attachmentUploadProgress(void; int noteId, Event event)
    {
        let contents = "%d;%s" % (noteId, event.contents());
        deb("Emitting sg-note-attachment-progress-updated\n");
        sendInternalEvent("sg-note-attachment-progress-updated", contents);
    }

    method: attachmentUploadComplete(void; int noteId, string dirName, Event event)
    {
        // Remove the temp session and directory
        removeTempSession();
        if (runtime.build_os() == "WINDOWS") {
            system.system("rmdir /s /q %s" % regex.replace("/", dirName, "\\\\"));
        } else {
            system.system("rm -rf %s" % dirName);
        }

        // Emit a signal so we can pick up on the completed upload in
        // Javascript
        deb("Emitting sg-all-note-uploads-complete\n");
        sendInternalEvent("sg-all-note-uploads-complete", noteId);
    }

    // Set focus on the timeline and inform the timeline to set focus on the
    // search field (via an internal event)
    method: focusSearchField(void; Event event) {
        // If the timeline has focus, ignore this
        if ( event neq nil ) {
            event.reject();
        }

        let i = nameToIndex("Bottom");

        // The web view doesn't exist, so abort
        if ( _webViews[i] eq nil ) return;

        _webViews[i].setFocus();
        deb("Emitting sg-focus-search-field\n");
        sendInternalEvent("sg-focus-search-field");
    }

    // Show the keyboard shortcuts in the timeline
    method: showKeyboardShortcuts(void; Event event) {
        if ( event neq nil ) {
            event.reject();
        }

        let i = nameToIndex("Bottom");

        // The web view doesn't exist, so abort
        if ( _webViews[i] eq nil ) return;

        _webViews[i].setFocus();

        deb("Emitting sg-show-keyboard-shortcuts\n");
        sendInternalEvent("sg-show-keyboard-shortcuts");
    }

    // We listen for changing properties of the graph so that we can emit a
    // specialised signal when new Shotgun data is available
    method: propertyChanged(void; Event event) {
        event.reject();

        let contents = event.contents();

        if ( regex.match("\\.tracking\\.infoStatus$", contents) &&
             getStringProperty(contents)[0] == "    good") {

            _propertyChangedTimer.start();
        }

        let parts = contents.split("."),
                    node = parts[0],
                    prop = parts[2];

        if (nodeType(node) == "RVPaint" && prop == "nextId")
        {
            let source = closestNodesOfType("RVFileSource", node)[0];

            // Does the newAnnotation flag already exists on the source?  If not, create it.
            let newAnn = source + ".screeningRoom.newAnnotation";
            if (!propertyExists(newAnn))
            {
                newProperty(newAnn, IntType, 1);
            }

            // Dirty the newAnnotation flag (assume there are new annotations)
            setIntProperty(newAnn, int[]{1}, true);

            deb(">>> Set upload flag.\n");
        }
    }

    method: propertyChangedTimeout(void; ) {

        _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;

        clearActiveVersionIfCurrentEntityDiffers();

        _allShotgunSourceNames = nil;
        _allShotgunSourceIds = nil;

        emitSourceFrameChanged(nil);
    }

    // Changes when the inputs of a Node are changed. We use it to detect when
    // the inputs to the current view node change.
    method: graphNodeInputsChanged(void; Event event) {
        event.reject();

        // If we are in the middle of a progressive load, the inputs to the
        // default views will change constantly, but we can respond once after
        // progressive loading is complete instead of to every single change.
        // See handler for after-progressive-loading.
        if (loadCount() > 0) return;

        let contents = event.contents(),
            vNode = viewNode();

        if ( contents != string(vNode) )
            return;

        _inputsChangedTimer.start();
    }

    method: inputsChangedTimeout(void; ) {
        _allShotgunSourceNames = nil;
        _allShotgunSourceIds = nil;

        emitSourceFrameChanged(nil);
    }

    // Called when the current view node is changed (changes from Sequence to
    // Stack or Layout)
    method: afterGraphViewChange(void; Event event) {
        event.reject();

        _allShotgunSourceNames = nil;
        _allShotgunSourceIds = nil;

        emitSourceFrameChanged(nil);
    }

    // Inform panes that the flagged state of a version or versions in
    // another pane has changed. We also pass the name of a sender, so that panes do
    // not have to respond to their own events
    method: flaggedStateChanged(void; int[] versionIds, string sender=nil) {
        // Invalidate the cache for all of these version ids
        let server = getDefaultServerName();

        if ( server neq nil ) {
            invalidateVersionsInCache(server, versionIds);
        }

        deb("Emitting sg-flagged-state-changed with contents: %s|%s\n" % (versionIds, sender));
        sendInternalEvent("sg-flagged-state-changed", "%s|%s" % (versionIds, sender));
    }

    // This function is called *every time* the frame changes, even when playing
    // back media. That means that it has to be *super* lightweight so that
    // playback isn't affected. We cache a few pieces of data and only perform
    // some of the more intensive calculations if that data has changed
    method: emitSourceFrameChanged(void; Event event) {
        if ( event neq nil ) {
            event.reject();
        }

        // Get all of the sources that are loaded at the current frame number
        let f = frame(),
            sourceNames = sourcesAtFrame(f);

        // If our collection of sources has *not* changed, then we assume that
        // the sources which are *Shotgun* sources (meaning they have Shotgun
        // metadata associated with them) have not changed.
        let allSources = allShotgunSourceNames(),
            allSourceIds = allShotgunSources();

        int versionId = -1;
        string contents;
        if ( !_frameChangeUpdatesDisabled ) {
            // If updates are enabled, then we emit the "frame changed" event
            // with the version id and percentage completion of that version
            let playheadPos = playheadPosition();
            versionId = playheadPos._0;

            contents = "%s|%s" % (allSourceIds, playheadPos);
            sendInternalEvent("sg-source-frame-changed", contents);

            if ( versionId > -1 && (isPlaying() || SGR_PLAY) ) {
                // Automatically play new source if -play option was used
                SGR_PLAY = false;
                playCurrent();
            }
        } else {
            // Determine if the current source (the primary source being viewed) has
            // changed
            let currentSourceChanged = false;
            string currentSourceName;
            for (int i = 0; i < sourceNames.size(); ++i) {
                let s = sourceNames[i];
                for (int j = 0; j < allSources.size(); ++j) {
                    let shotgunSource = allSources[j];
                    if ( shotgunSource == s ) {
                        currentSourceName = s;
                        break;
                    }
                }

                if ( currentSourceName neq nil )
                    break;
            }

            if ( currentSourceName neq nil ) {
                let sgInfo = shotgun_fields.infoFromSource(currentSourceName);
                if ( sgInfo neq nil )
                    versionId = sgInfo.findInt("id");
            }

            if ( versionId != _lastVersionId ) {
                // Frame-dependent updates are disabled by the user for performance
                // reasons. We only emit this event when the version id has changed,
                // or when the collection of Shotgun sources has changed
                contents = "%s|%d" % (allSourceIds, versionId);
                sendInternalEvent("sg-source-changed", contents);
                deb("Emitting sg-source-changed with contents %s\n" % contents);
            }
        }

        _lastVersionId = versionId;
    }

    method: playChanged(void; Event event) {
        event.reject();

        // Start the timer if it isn't active. Once the timer has reached 100ms
        // it will execute updateIfStateChanged
        if ( !_playStopTimer.active() ) _playStopTimer.start();
    }

    // Enable or disable updates to the Review App UI. If we are starting to play
    // a sequence of images whose longest dimension is greater than a maximum
    // threshhold then we will disable updates of the Review App UI as we play
    // to maintain playback performance.
    method: _updateIfStateChanged(void; bool force) {

        bool disableUpdates = false;
        bool enableUpdates = false;

        // If updateFrequency is -1 that means we *always* want updates to
        // occur regardless of the image dimensions of what's playing
        if ( _updateFrequency == -1 ) {
            enableUpdates = true;
        } else if ( isPlaying() && (force || _mystate != "playing") ) {
            _mystate = "playing";

            // If updateFrquency is -2 that means we never want updates to the
            // Review App UI to occur while we're playing media in RV
            if ( _updateFrequency == -2 ) { // Never update
                disableUpdates = true;
            } else if ( _updateFrequency > 0 ) {
                // Get the current RV view node
                let vNode = viewNode();

                if (vNode eq nil) {
                    return;
                }

                // Get its inputs. These will be the sources that correspond to
                // individual shots in a sequence, for example
                let inputs = nodeConnections(vNode, false)._0;

                // The maximum resolution for which live updates are still
                // permitted
                int maxRes = _updateFrequency;

                // Iterate over all sources and ensure that they fall below the
                // maxRes threshhold
                for_index (i; inputs)
                {
                    // Get the image geometry info for this source
                    let smi = sourceMediaInfo(inputs[i] + "_source");
                    if (smi.width > maxRes || smi.height > maxRes) {
                        disableUpdates = true;
                        break;
                    }
                }

                // Otherwise we reenable updates
                if ( !disableUpdates ) {
                    enableUpdates = true;
                }
            }
        } else if ( !isPlaying() && (force || _mystate != "stopped") ) {
            // If playing stops then we want to reenable updates
            _mystate = "stopped";
            enableUpdates = true;
        }

        // Disable updates and unbind the frame events
        if ( disableUpdates ) {
            _frameChangeUpdatesDisabled = true;
            _unbindFrameEvents();
            sendInternalEvent("sg-updates-disabled");
        }

        if ( disableUpdates || (isPlaying() && _detailPanePinnedWhenPlaying) ) {
            sendInternalEvent("sg-detail-pane-updates-disabled");
        }

        // Enable updates and re-bind frame events
        if ( enableUpdates ) {
            _frameChangeUpdatesDisabled = false;
            _bindFrameEvents();
            sendInternalEvent("sg-updates-enabled");
        }

        if ( !isPlaying() || ( enableUpdates && !_detailPanePinnedWhenPlaying ) ) {
            sendInternalEvent("sg-detail-pane-updates-enabled");
        }

    }

    method: updateIfStateChanged (void;) {
        // Okay, here's something weird. There needs to be some statement, either
        // this if (true) business or a print statement or whatever, before the
        // call to _updateIfStateChanged or it won't work. No idea what's going
        // on there.
        if (true) _updateIfStateChanged(false);
    }

    // Generate a url that will use the "redirect_with_local_fallback" controller
    // to attempt to access the given desiredUrl and, if authentication fails,
    // will redirect the user to the Review App login page. The login page url
    // must have an escaped version of the desiredUrl passed in via the "return_to"
    // url query item so that once authenticated the user can be eventaully taken
    // to the original desiredUrl.
    method: _generateUrl(QUrl; QUrl desiredUrl)
    {
        let serverName = getDefaultServerName();

        // Assemble a path to the local login page
        string filePath = path.join(supportPath("shotgun_review_app", "screening_room"),
            "login.html");

        // The path will use a different separator if we're on Windows
        if (rvui.globalConfig.os == "WINDOWS")
        {
            filePath = regex.replace("/", filePath, "\\\\");
        }

        QUrl url;
        if ( serverName neq nil ) {
            // We need an escaped version of the desiredUrl to add as a query item
            // to our local login page
            // We need to make the ampersands and question marks gets encoded
            QByteArray include = QByteArray();
            include.append("&?");
            QByteArray exclude = QByteArray();

            // Percent encode this puppy. This will return a QByteArray that we then
            // need to convert into a string via some heroic measures
            let returnToEncodedBytes = QUrl.toPercentEncoding(desiredUrl.toString(QUrl.None), exclude, include);
            // Write the byte array to a string stream, which we can then cast to
            // a proper string.
            let returnToEncoded = osstream();
            returnToEncoded.write(returnToEncodedBytes.constData());

            // Create the url for our local login page and add the encoded desiredUrl
            // as a query item
            QUrl fallbackUrl = QUrl.fromLocalFile(filePath);
            fallbackUrl.addQueryItem("return_to", string(returnToEncoded));

            // The redirect_with_local_fallback controller takes two query items,
            // the first is "url", which is the desired url, and the second is
            // "fallback" which is the local file we'll be taken to if authentication
            // fails. Both of these are base 64 encoded to avoid the nightmare of
            // escaping

            // Base64 encode the desired url
            // Create a new byte array and populate it with our desiredUrl
            let encodedUrlBytes1 = QByteArray();
            encodedUrlBytes1.append(desiredUrl.toString(QUrl.None));

            // Base64 encode it and write the byte array to a string stream
            encodedUrlBytes1 = encodedUrlBytes1.toBase64();
            let encodedDesiredUrl = osstream();
            encodedDesiredUrl.write(encodedUrlBytes1.constData());

            // Do the same with the fallback url
            let encodedUrlBytes2 = QByteArray();
            encodedUrlBytes2.append(fallbackUrl.toString(QUrl.None));
            encodedUrlBytes2 = encodedUrlBytes2.toBase64();
            let encodedFallbackUrl = osstream();
            encodedFallbackUrl.write(encodedUrlBytes2.constData());

            // Create the url for the controller and add the two query items
            url = QUrl("/user/redirect_with_local_fallback");
            url.addQueryItem("url", string(encodedDesiredUrl));
            url.addQueryItem("fallback", string(encodedFallbackUrl));
        } else {
            url = QUrl.fromLocalFile(filePath);
        }

        // Return the final, messy url
        return url;
    }

    // Open the timeline. The given list of urlArgs contains pairs that define
    // query items that should be passed via the url to the page. This allows
    // the timeline to be opened with a given context.
    method: internalLaunchTimeline(void; [(string, string)] urlArgs = nil)
    {
        // We can proceed to the normal launchTimeline
        deb("INFO: internalLaunchTimeline()\n");

        let defSession = getDefaultSessionFromSLUtils();
        _sessionUrl = if (defSession._0 eq nil) then "" else defSession._0;

        if ( _sessionUrl != "") {
            // this is an old function that changes the prefs
            shotgun.theMode().setServerURLValue(_sessionUrl);
        }   

        // The url for the timeline
        QUrl desiredUrl = QUrl("/page/review_app_browser");

        // Add the context, if there is any
        for_each(urlArg; urlArgs) {
            deb( "internalLaunchTimeline: arg = (%s,%s)\n" % urlArg );
            desiredUrl.addQueryItem(urlArg._0, urlArg._1);
        }

        // Generate the correct url so that we are bounced back to the Review App
        // login page if we aren't already authenticated
        let url = _generateUrl(desiredUrl);

        // Open the bottom pane if it isn't already and navigate to this page
        openPaneToUrl(url.toString(QUrl.None), "Bottom", 300);

        let i = nameToIndex("Bottom");
        _webViews[i].setFocus();
        _dockWidgets[i].show();
    }

    // Method called by the rvlink. An asynch-enabled wrapper for internalLaunchTimeline.
    method: launchTimeline(void; [(string, string)] urlArgs = nil)
    {
        deb("INFO: launchTimeline()\n");

        if (ASYNC_LICENSE_SWITCH_IN_PROGRESS) {
            // Just setup the differed call

            NEXT_CALL_AFTER_LICENSE_SWITCH = internalLaunchTimeline;
            NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM = urlArgs;
        } else {
            // Call immediately
            internalLaunchTimeline(urlArgs);
        }
    }

    // Open the submit tool. The given list of urlArgs contains pairs that define
    // query items that should be passed via the url to the page. This allows
    // the submit tool to be opened with a given context (to prepopulate form
    // fields, etc).
    method: internalLaunchSubmitTool(void; [(string, string)] urlArgs = nil)
    {
        deb("INFO: internalLaunchSubmitTool()\n");

        let defSession = getDefaultSessionFromSLUtils();
        _sessionUrl = if (defSession._0 eq nil) then "" else defSession._0;

        if ( _sessionUrl != "") {
            // this is an old function that changes the prefs
            shotgun.theMode().setServerURLValue(_sessionUrl);
        }   

        // The url for the submit tool
        QUrl desiredUrl = QUrl("/page/review_app_submit");

        // Add the context query items to the url
        for_each(urlArg; urlArgs) {
            desiredUrl.addQueryItem(urlArg._0, urlArg._1);
        }

        // Generate the correct url so that we are bounced back to the Review App
        // login page if we aren't already authenticated
        let url = _generateUrl(desiredUrl);

        // Open the bottom pane if it isn't already and navigate to this page
        openPaneToUrl(url.toString(QUrl.None), "Bottom", 300);

        let i = nameToIndex("Bottom");
        _webViews[i].setFocus();
        _dockWidgets[i].show();

        // Make sure the detail pane is closed
        closePane("Right", false);
    }

    // Method called by the rvlink.  An asynch-enabled wrapper for internalLaunchSubmitTool.
    method: launchSubmitTool(void; [(string, string)] urlArgs = nil)
    {
        deb("INFO: launchSubmitTool()\n");
        if (ASYNC_LICENSE_SWITCH_IN_PROGRESS) {
            // Just setup the differed call
            NEXT_CALL_AFTER_LICENSE_SWITCH = internalLaunchSubmitTool;
            NEXT_CALL_AFTER_LICENSE_SWITCH_PARAM = urlArgs;
        } else {
            // Call immediately
            internalLaunchSubmitTool(urlArgs);
        }
    }

    // OBSOLETE: I need to keep this method to avoid an error
    // Shotgun v < 6.0.2 is calling this method after handling the sg-clear-local-storage event
    // that I send in _clearCookies...
    // Shotgun v >= 6.0.2 is now calling reload directly
    method: logOut(void;)
    {
        reload();
    }

    method: reload(void;)
    {
        closePane("Bottom", false);
        internalLaunchTimeline();
    }

    method: saveDockWidgetSettings(void; Event event) {
        event.reject();
        deb("Saving dock widget settings\n");

        bool paneOpen = false;
        for ( int i = 0; i < 4; i++ ) {
            if ( _dockWidgets[i] neq nil && _baseWidgets[i] neq nil ) {
                _floating[i] = if ( _dockWidgets[i].floating() ) then 1 else 0;
                _sizes[2 * i] = _dockWidgets[i].width();
                _sizes[2 * i + 1] = _dockWidgets[i].height();
                _positions[2 * i] = _dockWidgets[i].x();
                _positions[2 * i + 1] = _dockWidgets[i].y();
                paneOpen = true;
            }
        }

        // We only need to save this stuff if the Review App was opened, e.g. at least
        // one dock widget was created
        if ( paneOpen ) {
            writeSetting("ReviewApp", "floating", SettingsValue.IntArray(_floating) );
            writeSetting("ReviewApp", "sizes", SettingsValue.IntArray(_sizes) );
            writeSetting("ReviewApp", "positions", SettingsValue.IntArray(_positions) );
            writeSetting("ReviewApp", "hidden", SettingsValue.IntArray(_hidden) );

            // Save the main window's geometry
            let g = osstream();
            g.write( mainWindowWidget().saveGeometry().toBase64().constData() );
            writeSetting("ReviewApp", "mainWindowGeom", SettingsValue.String( string(g) ) );
        }
    }

    method: restoreDockWidgetSettings(void;) {
        let SettingsValue.IntArray floatingVals = readSetting("ReviewApp", "floating",
            SettingsValue.IntArray(int[] {0, 0, 0, 0}) );

        let SettingsValue.IntArray sizeVals = readSetting("ReviewApp", "sizes",
            SettingsValue.IntArray(int[] {-1, -1, -1, -1, -1, -1, -1, -1}) );

        let SettingsValue.IntArray posVals = readSetting("ReviewApp", "positions",
            SettingsValue.IntArray(int[] {-1, -1, -1, -1, -1, -1, -1, -1}) );

        let SettingsValue.IntArray hiddenVals = readSetting("ReviewApp", "hidden",
            SettingsValue.IntArray(int[] {0, 0, 0, 0}) );

        let SettingsValue.String mainWindowGeomVal = readSetting("ReviewApp", "mainWindowGeom",
            SettingsValue.String("") );

        _floating = int[]();
        _floating.resize(4);
        _floating = floatingVals;

        _sizes = int[]();
        _sizes.resize(8);
        _sizes = sizeVals;

        _positions = int[]();
        _positions.resize(8);
        _positions = posVals;

        _hidden = int[]();
        _hidden.resize(4);
        _hidden = hiddenVals;

        if ( mainWindowGeomVal.size() > 0 ) {
            _mainWindowGeometry = QByteArray().append(mainWindowGeomVal).fromBase64();
        }
        _geometryRestored = false;
    }

    method: _showTimeline (void; Event event)
    {
        deb("INFO: _showTimeline()\n");
        internalLaunchTimeline();
    }

    method: _showSubmitTool(void; Event event)
    {
        internalLaunchSubmitTool();
    }

    method: _reload(void; Event event)
    {
        // Empty the source cache
        pruneCachedSourcesGroup(0, event);

        reload();
    }

    method: _clearCookies(void; Event e)
    {
        // Empty the source cache
        pruneCachedSourcesGroup(0, e);

        // Logout needs to happen *before* the cookies are cleared or the user will
        // be redirected to the login page twice
        CookieJar cj = _networkAccessManager.cookieJar();
        cj.clearAllCookies();
        sendInternalEvent("sg-clear-local-storage");
        deb("emitting sg-clear-local-storage");

        reload();
    }

    method: _emailSupport(void; Event e)
    {
        openUrl("mailto:support@shotgunsoftware.com");
    }

    method: _visitHelpSite(void; Event e)
    {
        openUrl("https://support.shotgunsoftware.com/entries/24062067");
    }

    method: _bindCoreEvents(void;)
    {
        _unbindCoreEvents();
        bind(_modeName, "global", "play-start", playChanged, "");
        bind(_modeName, "global", "play-stop", playChanged, "");
        bind(_modeName, "global", "before-session-deletion", saveDockWidgetSettings, "");
        bind(_modeName, "global", "after-progressive-loading", afterProgressiveLoading, "Update Infos After Load");
        bind(_modeName, "global", "after-graph-view-change", afterGraphViewChange, "");
        bind(_modeName, "global", "graph-node-inputs-changed", graphNodeInputsChanged, "");
        bind(_modeName, "global", "sg-submission-error", onSubmissionError, "");

        deb("Core events bound\n");
    }

    method: _unbindCoreEvents(void;)
    {
        try
        {
            unbind(_modeName, "global", "play-start");
            unbind(_modeName, "global", "play-stop");
            unbind(_modeName, "global", "before-session-deletion");
            unbind(_modeName, "global", "after-progressive-loading");
            unbind(_modeName, "global", "after-graph-view-change");
            unbind(_modeName, "global", "graph-node-inputs-changed");
            unbind(_modeName, "global", "sg-submission-error");

            deb("Core events unbound\n");
        }
        catch(...) { ; }
    }

    method: _bindFrameEvents(void;)
    {
        // Make sure these are unbound before trying to bind them
        _unbindFrameEvents();
        bind(_modeName, "global", "frame-changed", emitSourceFrameChanged, "");
        bind(_modeName, "global", "graph-state-change", propertyChanged, "");

        deb("Frame events bound\n");
    }

    method: _unbindFrameEvents(void;)
    {
        unbind(_modeName, "global", "frame-changed");
        unbind(_modeName, "global", "graph-state-change");

        deb("Frame events unbound\n");
    }

    method: _buildMenu(Menu; shotgun_mode.ShotgunMinorMode shotgunMode, Menu connectionDetailsSubMenu )
    {
        Menu m1 = Menu {
            {"Shotgun Connection Details", connectionDetailsSubMenu },
            {"_", nil},
            {"Screening Room", nil, nil, disabledFunc},
            {"    Launch Browser", _showTimeline, "control b"},
            {"    Launch Submit Tool", _showSubmitTool, "control t"},
            {"    View", Menu {
                {"Browser/Submit Pane", toggleMasterPane, "alt b", masterPaneMenuState},
                {"Details Pane", toggleDetailsPane, "alt d", detailPaneMenuState},
                {"Reset Panes", resetPanes},
            }},
            {"    Clear Cookies and Reload", _clearCookies},
            {"    Reload", _reload},
            {"_", nil},
            {"Playback", nil, nil, disabledFunc},
            {"    Shotgun Info Overlay", shotgunMode.toggleInfoWidget, "shift I", shotgunMode.infoWidgetState},
        };

        let SwapMediaMenu = Menu();

        if ( shotgun_fields.initialized ) {
            let types = shotgun_fields.mediaTypes();
            for_each (t; types)
            {
                SwapMediaMenu.push_back (MenuItem {"Play " + t, shotgunMode.swapMedia("all", t, ), nil, neutralFunc});
            }

            if (types.size() > 0) {
                m1.push_back( MenuItem {"    Swap Media", SwapMediaMenu } );
            }
        }

        int PrefLoadRangeFull = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeFull;
        int PrefLoadRangeNoSlate = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeNoSlate;
        int PrefLoadRangeCut = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeCut;

        Menu m2 = Menu {
            {"    Frame Range", Menu {
                {"Full Length", shotgunMode.changeEdit("all", PrefLoadRangeFull,), nil, neutralFunc},
                {"Full Without Slate", shotgunMode.changeEdit("all", PrefLoadRangeNoSlate,), nil, neutralFunc},
                {"Cut Length", shotgunMode.changeEdit("all", PrefLoadRangeCut,), nil, neutralFunc}
            }},
            {"    Current Source Prefs", shotgunMode._buildCurrentSourceMenu(/*old ?*/false) },
            {"    Session Prefs", _buildPrefsMenu(shotgunMode) },

            {"_", nil},
            {"Help", doNothingEvent, nil, disabledFunc},
            {"    Keyboard Shortcuts", showKeyboardShortcuts, nil, masterPaneIsOpenMenuState},
            {"    Email us...", _emailSupport},
            {"    Visit our Help Site...", _visitHelpSite},
        };

        return shotgun._combineMenus( m1, m2 );
    }

    method: isUpdateFrequency((int;); int freq)
    {
        \: (int;)
        {
            if (this._updateFrequency == freq) then CheckedMenuState else UncheckedMenuState;
        };
    }

    method: isSourceCacheMaxSize((int;); int maxSize)
    {
        \: (int;)
        {
            if (this._sourceCacheMaxSize == maxSize) then CheckedMenuState else UncheckedMenuState;
        };
    }

    method: isSourceCacheMaxSizeNonZero((int;);)
    {
        \: (int;)
        {
            if (this._sourceCacheMaxSize != 0) then UncheckedMenuState else DisabledMenuState;
        };
    }

    method: isDetailPanePinnedWhenPlaying((int;);)
    {
        \: (int;)
        {
            if (this._detailPanePinnedWhenPlaying) then CheckedMenuState else UncheckedMenuState;
        };
    }

    method: isDebugInfoEnabled((int;);)
    {
        \: (int;)
        {
            if ( SGR_DEBUG ) then CheckedMenuState else UncheckedMenuState;
        };
    }

    method: directoriesAreAllowed((int;);)
    {
        \: (int;)
        {
            if ( this._allowDirectories ) then CheckedMenuState else UncheckedMenuState;
        };
    }

    method: openEncodedUrl(void; string url)
    {
        QByteArray qba = QByteArray();
        qba.append(url);
        openUrl(QUrl.fromPercentEncoding(qba));
    }

    method: _buildPrefsMenu(Menu; shotgun_mode.ShotgunMinorMode shotgunMode )
    {
        int PrefLoadRangeFull = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeFull;
        int PrefLoadRangeNoSlate = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeNoSlate;
        int PrefLoadRangeCut = shotgun_mode.ShotgunMinorMode.Prefs.PrefLoadRangeCut;
        int PrefCompareOpTiled = shotgun_mode.ShotgunMinorMode.Prefs.PrefCompareOpTiled;
        int PrefCompareOpOverWipe = shotgun_mode.ShotgunMinorMode.Prefs.PrefCompareOpOverWipe;
        int PrefCompareOpDiff = shotgun_mode.ShotgunMinorMode.Prefs.PrefCompareOpDiff;

        Menu m1 = Menu();

        if ( shotgun_fields.initialized ) {
            let types = shotgun_fields.mediaTypes();
            if ( types.size() > 0 ) {
                m1.push_back( MenuItem { "Swap Media", nil, nil, disabledFunc } );
                for_each (t; types)
                {
                    m1.push_back (MenuItem {"    Play " + t, shotgunMode.setLoadMedia(t,), nil, shotgunMode.isLoadMedia(t)});
                }
                m1.push_back( MenuItem {"_", nil} );
            }
        }

        Menu m2 = Menu {
            { "Frame Range", nil, nil, disabledFunc },
            { "    Full Length", shotgunMode.setLoadRange(PrefLoadRangeFull,), nil, shotgunMode.isLoadRange(PrefLoadRangeFull)},
            { "    Full Without Slate", shotgunMode.setLoadRange(PrefLoadRangeNoSlate,), nil, shotgunMode.isLoadRange(PrefLoadRangeNoSlate)},
            { "    Cut Length", shotgunMode.setLoadRange(PrefLoadRangeCut,), nil, shotgunMode.isLoadRange(PrefLoadRangeCut)},

            {"_", nil},
            { "Compare Options", doNothingEvent, nil, disabledFunc },
            { "    Tiled", shotgunMode.setCompareOp(PrefCompareOpTiled,), nil, shotgunMode.isCompareOp(PrefCompareOpTiled) },
            { "    Over, With Wipes", shotgunMode.setCompareOp(PrefCompareOpOverWipe,), nil, shotgunMode.isCompareOp(PrefCompareOpOverWipe) },
            { "    Difference", shotgunMode.setCompareOp(PrefCompareOpDiff,), nil, shotgunMode.isCompareOp(PrefCompareOpDiff) },

            {"_", nil},
            {"Update", nil, nil, disabledFunc},
            {"    Shotgun Info", shotgunMode.updateTrackingInfo("one",), nil, shotgunMode.enableIfSingleSourceHasInfo},
            {"    To Latest Version", shotgunMode.swapLatestVersions("one",), nil, shotgunMode.enableIfSingleSourceHasInfo},

            {"_", nil},
            {"Screening Room UI Update Frequency During Playback", doNothingEvent, nil, disabledFunc},
            {"    Always", setUpdateFrequency(-1,), nil, isUpdateFrequency(-1)},
            {"    Sources Under 2K", setUpdateFrequency(2048,), nil, isUpdateFrequency(2048)},
            {"    Sources Under 1K", setUpdateFrequency(1024,), nil, isUpdateFrequency(1024)},
            {"    Never", setUpdateFrequency(-2,), nil, isUpdateFrequency(-2)},

            {"_", nil},
            {"Always Pin Detail Pane When Playing", toggleDetailPanePinnedWhenPlaying, nil, isDetailPanePinnedWhenPlaying()},

            {"_", nil},
            {"Source Caching", doNothingEvent, nil, disabledFunc},
            {"    Cache 10 Versions", setSourceCacheMaxSize(10,), nil, isSourceCacheMaxSize(10)},
            {"    Cache 20 Versions", setSourceCacheMaxSize(20,), nil, isSourceCacheMaxSize(20)},
            {"    Cache 50 Versions", setSourceCacheMaxSize(50,), nil, isSourceCacheMaxSize(50)},
            {"    Disable", setSourceCacheMaxSize(0,), nil, isSourceCacheMaxSize(0)},
            {"    Empty Cache", pruneCachedSourcesGroup(0,), nil, isSourceCacheMaxSizeNonZero()},

            {"_", nil},
            {"Copy Shotgun-Aware RVLINK", nil, nil, disabledFunc},
            {"    Session URL", shotgunMode.copyUrl("session",), nil, neutralFunc},
            {"    Current Version URL", shotgunMode.copyUrl("version",), nil, shotgunMode.enableIfSingleSourceHasInfo},

            {"_", nil},
            {"Advanced", doNothingEvent, nil, disabledFunc},
            {"    Allow Directories (Not Advised, Requires Reload)", toggleDirectoriesAllowed, nil, directoriesAreAllowed()},
            {"    Draw Info Widget on Presentation Device", shotgunMode.toggleDrawInfoOnPresentation, nil, shotgunMode.drawingInfoOnPresentation},
            {"    Print debug info", toggleDebugInfo, nil, isDebugInfoEnabled()},
            {"    Set Preferred Department", shotgunMode.setDepartment, nil, uncheckedFunc},
            {"    Set Shotgun Config Style", shotgunMode.setShotgunConfigStyle, nil, uncheckedFunc},
            {"    Show Feedback", shotgunMode.toggleShowInFlight, nil, shotgunMode.showingInFlight},
            {"    Redirect URLs", shotgunMode.toggleRedirectUrls, nil, shotgunMode.redirectingUrls},
        };

        return shotgun._combineMenus( m1, m2 );
    }

    method: activate(void;)
    {
        deb("Activating mode\n");
        for_each (w; _dockWidgets) if (w neq nil) w.show();
    }

    method: deactivate(void;)
    {
        deb("Deactivating mode\n");
        for_each (w; _webViews)    if (w neq nil) w.page().mainFrame().setHtml("", QUrl());
        for_each (w; _dockWidgets) if (w neq nil) w.hide();
    }

    method: ReviewAppMinorMode (ReviewAppMinorMode;)
    {
        deb("INFO: ReviewAppMinorMode()\n");

        // We bind the shortcut keys at initialization and we keep them bound
        // even when the panes are hidden so that they keep working.
        init( "Screening Room", nil,
              [("key-down--alt--b", toggleMasterPane, ""),
               ("key-down--alt--d", toggleDetailsPane, ""),
               ("key-down--shift--up", nextVersion, ""),
               ("key-down--shift--down", previousVersion, ""),
               ("key-down--alt-shift--up", nextFlaggedVersion, ""),
               ("key-down--alt-shift--down", previousFlaggedVersion, ""),
               ("key-down--s", focusSearchField, ""),
               ("key-down--?", showKeyboardShortcuts, ""),
               ("key-down--/", showKeyboardShortcuts, "")]);

        // Initialise all the widgets
        _dockWidgets  = QDockWidget[]();  _dockWidgets.resize(4);
        _baseWidgets  = QWidget[]();      _baseWidgets.resize(4);
        _webViews     = QWebView[]();     _webViews.resize(4);
        _progressBars = QProgressBar[](); _progressBars.resize(4);
        _titleBarWidgets = QWidget[]();   _titleBarWidgets.resize(4);
        _networkAccessManager = QNetworkAccessManager(mainWindowWidget());

        // Only keep 500 items in the cache and expire each item after 5 mins
        _infoCache = (string, int, QDateTime, StringMap)[]();
        _entityVersionsCache = (string, int, string, QDateTime, int[])[]();
        _infoCacheMaxItems = 500;

        let SettingsValue.Int maxSize = readSetting("ReviewApp", "sourceCacheMaxSize", SettingsValue.Int(20));
        _sourceCacheMaxSize = maxSize;

        _maxCacheAgeSecs = 300;

        _preProgLoadSources = string[]();
        _postProgLoadInfos = StringMap[]();
        _postProgLoadTurnOnWipes = false;

        _fetching = false;

        // We've implemented our own QNetworkCookieJar so that we can save
        // cookies across sessions. The default implementation only stores
        // cookies in memory.
        _networkAccessManager.setCookieJar( CookieJar() );

        let SettingsValue.Bool debugInfo = readSetting("ReviewApp", "debugInfoEnabled",
            SettingsValue.Bool(false));
        SGR_DEBUG = debugInfo;

        let s = QWebSettings.globalSettings();
        s.setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, true);
        s.setAttribute(QWebSettings.PluginsEnabled, false);
        s.setAttribute(QWebSettings.DeveloperExtrasEnabled, SGR_DEBUG);
        s.setAttribute(QWebSettings.LocalStorageEnabled, true);

        let storageDir = path.join( cacheDir(), "local_storage" );
        if ( ! QDir(storageDir).exists() ) {
            QDir("").mkdir(storageDir);
        }
        s.setLocalStoragePath( QDir.toNativeSeparators(storageDir) );

        deb("Local storage path is: %s\n" % s.localStoragePath());

        restoreDockWidgetSettings();

        _lastVersionId = -1;
        _sessionIsLoading = false;CURRENT_SEQ_NODE = DEFAULT_SEQ_NODE;
        _allHidden = true;
        _frameChangeUpdatesDisabled = false;

        // Parse any command line flags that might have been sent in
        for (int i = 0; i < 4; ++i)
        {
            _dockWidgets[i]  = nil;
            _baseWidgets[i]  = nil;
            _webViews[i]     = nil;
            _progressBars[i] = nil;
            _titleBarWidgets[i] = nil;

            let url = commandLineFlag("reviewAppUrl" + indexToName(i), nil);
            if (url neq nil)
            {
                url = regex.replace ("EQUALS", url, "=");

                let startSize = int (commandLineFlag("reviewAppSize" + indexToName(i), "300"));

                openPaneToUrl(url, indexToName(i), startSize);
            }
        }

        // Initial state for how updates should be handled when playing media
        // in RV to preserve playback performance
        _mystate = "unknown";
        let SettingsValue.Int freq = readSetting("ReviewApp", "updateFrequency", SettingsValue.Int(-1));
        _updateFrequency = freq;
        let SettingsValue.Bool pinned = readSetting("ReviewApp", "detailPanePinnedWhenPlaying", SettingsValue.Bool(false));
        _detailPanePinnedWhenPlaying = pinned;

        let SettingsValue.Bool allowDirs = readSetting("ReviewApp", "allowDirectories", SettingsValue.Bool(false));
        _allowDirectories = allowDirs;

        // Create a timer that will be started whenever playback starts or stops.
        // After a short interval (100ms) it will potentially inform the
        // Review App UI in the browser that it should stop updating itself on
        // frame events or when the shotgun source changes.
        _playStopTimer = QTimer(mainWindowWidget());
        _playStopTimer.setSingleShot(true);
        _playStopTimer.setInterval(100);

        connect(_playStopTimer, QTimer.timeout, updateIfStateChanged);

        _propertyChangedTimer = QTimer(mainWindowWidget());
        _propertyChangedTimer.setSingleShot(true);
        _propertyChangedTimer.setInterval(100);

        connect(_propertyChangedTimer, QTimer.timeout, propertyChangedTimeout);

        _inputsChangedTimer = QTimer(mainWindowWidget());
        _inputsChangedTimer.setSingleShot(true);
        _inputsChangedTimer.setInterval(100);

        connect(_inputsChangedTimer, QTimer.timeout, inputsChangedTimeout);

        mainWindowWidget().show();
    }

    method: resetViewNode(void;)
    {
        rvui.clearEverything();
        // setNodeInputs(getSequenceNode(), string []() );
    }

    method: destroyAllQtWidgets(void;)
    {
        int i;
        for(i = 0; i < _webViews.size(); ++i ) {
            let webView = _webViews[i];
            if ( webView neq nil ) {
                qt.QObject obj = webView;
                obj.deleteLater();
                _webViews[i] = nil;
            }
        }
        for(i = 0; i < _dockWidgets.size(); ++i ) {
            let dockWidget = _dockWidgets[i];
            if ( dockWidget neq nil ) {
                qt.QObject obj = dockWidget;
                obj.deleteLater();
                _dockWidgets[i] = nil;
            }
        }
        for(i = 0; i < _baseWidgets.size(); ++i ) {
            let baseWidget = _baseWidgets[i];
            if ( baseWidget neq nil ) {
                qt.QObject obj = baseWidget;
                obj.deleteLater();
                _baseWidgets[i] = nil;
            }
        }
        for(i = 0; i < _progressBars.size(); ++i ) {
            let progressBar = _progressBars[i];
            if ( progressBar neq nil ) {
                qt.QObject obj = progressBar;
                obj.deleteLater();
                _progressBars[i] = nil;
            }
        }
        for(i = 0; i < _titleBarWidgets.size(); ++i ) {
            let titleBar = _titleBarWidgets[i];
            if ( titleBar neq nil ) {
                qt.QObject obj = titleBar;
                obj.deleteLater();
                _titleBarWidgets[i] = nil;
            }
        }
    }
}

\: createMode (Mode;)
{
    return ReviewAppMinorMode();
}

\: theMode (ReviewAppMinorMode;)
{
    ReviewAppMinorMode m = rvui.minorModeFromName("Screening Room");
    return m;
}

\: externalBuildMenu(Menu; shotgun_mode.ShotgunMinorMode shotgunMode, Menu submenu)
{
    ReviewAppMinorMode m = theMode();

    Menu ret = nil;
    if (m neq nil) ret = m._buildMenu(shotgunMode, submenu);

    return ret;
}

\: externalCompletedLicenseSwitch(void;) 
{
    ReviewAppMinorMode m = theMode();
    m.completedLicenseSwitch(); 
}

\: externalLaunchTimeline(void;) 
{
    ReviewAppMinorMode m = theMode();
    m.internalLaunchTimeline(); 
}

\: resetScreeningRoom(void;bool force, bool resetPlayer)
{
    ReviewAppMinorMode m = rvui.minorModeFromName("Screening Room");

    let defSession = getDefaultSessionFromSLUtils(),
        defUrl = if (defSession._0 eq nil) then "" else defSession._0;

    if ( force || m._sessionUrl eq nil || m._sessionUrl != defUrl ) {
        m._sessionUrl = defUrl;

        if ( m.reviewAppBrowserIsOpen() ) {
            m.pruneCachedSourceGroupNoEvent(0);

            if (m.paneIsAvailable("Bottom")) {
                m.closePane("Bottom", false);
            }
            
            if (m.paneIsAvailable("Right")) {
                m.closePane("Right", false);
            }

            m.destroyAllQtWidgets();
            if ( resetPlayer ) {
                let playerURL = shotgun.theMode()._shotgunState._serverURL;

                // because of #29253 we only reset the player if the URL has changed
                // and here we ignore 
                if ( playerURL eq nil || playerURL != defUrl ) {
                    m.resetViewNode();
                }
            }

            m.internalLaunchTimeline();
        } else if (m.submitToolIsOpen()) {
            m.pruneCachedSourceGroupNoEvent(0);

            if (m.paneIsAvailable("Bottom")) {
                m.closePane("Bottom", false);
            }
            
            if (m.paneIsAvailable("Right")) {
                m.closePane("Right", false);
            }

            m.destroyAllQtWidgets();
            if ( resetPlayer ) {
                m.resetViewNode();
            }

            m.internalLaunchSubmitTool();
        }
    }
}

\: willSRRestart(bool;(string, string, string, string, string, string, string) session)
{
    ReviewAppMinorMode m = rvui.minorModeFromName("Screening Room");

    if ( ! m.reviewAppBrowserIsOpen() ) {
        return false;
    }

    if ( session eq nil ) {
        // we don't know what the new session is
        // so let's not take any change
        return true;
    }

    if ( session._0 eq nil || m._sessionUrl != session._0 ) {
        return true;
    }
    return false;
}

\: packageVersion((int, int);)
{
    State state = data();
    ModeManagerMode mm = state.modeManager;
    let pkg = mm.findPackageByBase("screening_room");

    if ( pkg neq nil ) {
        return (pkg.major, pkg.minor);
    }

    return (-1, -1);
}

\: mediaFieldNames(string[];)
{
    let re = regex("^mt_([^_]*)$"),
        fields = string[]();

    for_each(f; shotgun_fields.fields) {
        if ( re.match(f.name) ) {
            fields.push_back(f.fieldName);
        }
    }

    return fields;
}

}

