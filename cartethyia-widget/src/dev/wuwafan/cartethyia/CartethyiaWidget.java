package dev.wuwafan.cartethyia;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;

/** Cartethyia clock: the TextClocks tick on their own, so updates only wire up the tap action. */
public class CartethyiaWidget extends AppWidgetProvider {
    static final String GAME_PACKAGE = "com.kurogame.wutheringwaves.global";

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_cartethyia);
        Intent game = context.getPackageManager().getLaunchIntentForPackage(GAME_PACKAGE);
        if (game != null) {
            game.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            PendingIntent tap = PendingIntent.getActivity(context, 0, game,
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
            views.setOnClickPendingIntent(R.id.root, tap);
        }
        manager.updateAppWidget(ids, views);
    }
}
