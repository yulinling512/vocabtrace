package com.vocabtrace.app;

import android.app.Activity;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView wv;
    private int statusBarHeight = 0;

    public static class JsBridge {
        private final Activity act;

        JsBridge(Activity a) {
            act = a;
        }

        @JavascriptInterface
        public void exitApp() {
            act.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    act.finish();
                }
            });
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        wv = new WebView(this);
        setContentView(wv);

        int rid = getResources().getIdentifier("status_bar_height", "dimen", "android");
        if (rid > 0) statusBarHeight = getResources().getDimensionPixelSize(rid);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            getWindow().setStatusBarColor(Color.TRANSPARENT);
            getWindow().setNavigationBarColor(Color.TRANSPARENT);
            int flags = View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            }
            getWindow().getDecorView().setSystemUiVisibility(flags);
        }

        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN) {
            s.setAllowFileAccessFromFileURLs(true);
            s.setAllowUniversalAccessFromFileURLs(true);
        }
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);

        wv.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    view.loadUrl(url);
                    return true;
                }
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                float density = getResources().getDisplayMetrics().density;
                int satDp = Math.round(statusBarHeight / density);
                /* 状态栏高度 + 顶栏真实高度都交给页面；顶栏用 DOM 实测，
                   这样换任何手机/系统，背诵页高度都能自动贴合，不再硬编码 */
                final String js =
                        "(function(){" +
                        "document.documentElement.style.setProperty('--sat','" + satDp + "px');" +
                        "function m(){var h=document.getElementById('appbar');" +
                        "var hd=h?Math.round(h.getBoundingClientRect().height):0;" +
                        "document.documentElement.style.setProperty('--hdH',hd+'px');}" +
                        "m();window.addEventListener('resize',m);" +
                        "})()";
                view.evaluateJavascript(js, null);
            }
        });
        wv.setWebChromeClient(new WebChromeClient());
        wv.addJavascriptInterface(new JsBridge(this), "Android");
        wv.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            wv.evaluateJavascript("window.vocabBack && window.vocabBack()", null);
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
