package dev.wuwafan.cartethyia;

import android.app.Activity;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.os.Bundle;

/** Asks the launcher to place the widget (shows its "Add to home screen" dialog), then closes. */
public class PinActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        AppWidgetManager manager = getSystemService(AppWidgetManager.class);
        if (manager != null && manager.isRequestPinAppWidgetSupported()) {
            manager.requestPinAppWidget(new ComponentName(this, CartethyiaWidget.class), null, null);
        }
        finish();
    }
}
