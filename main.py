"""Punto de entrada de la aplicacion Widget Dashboard."""

from widget_dashboard.app import WidgetDashboardApp


def main() -> None:
    app = WidgetDashboardApp()
    app.run()


if __name__ == "__main__":
    main()
