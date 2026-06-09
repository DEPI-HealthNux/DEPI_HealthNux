from nicegui import ui
import pandas as pd
import sys
sys.path.append("..")
from google.cloud import bigquery
from google.oauth2 import service_account
from Components.Navigation import navigation_bar
from Pages.Visits_Page.Available_Visits_Tab import render_available_visits_tab
#from Pages.Settings_Page.Booked_Visits_Tab import render_timetable_tab
import Cache


@ui.page('/visits')
def visits_page():
    navigation_bar(
    active='visits'
    )
    with ui.column().classes(
    'w-full p-4 gap-4'
    ):
        tabs = ui.tabs().classes(
            'w-full'
        )

    with tabs:

        tab_ava_visits = ui.tab(
            '🕒 Available Visits'
        )

        tab_book_visits = ui.tab(
            '📅 Booked Visits'
        )


    with ui.tab_panels(
        tabs,
        value=tab_ava_visits
    ).classes(
        'w-full'
    ):

        with ui.tab_panel(tab_ava_visits):

                render_available_visits_tab()


        with ui.tab_panel(tab_book_visits):

            with ui.card().classes(
                'w-full p-8 rounded-2xl'
            ):

                ui.label(
                    '📅 Booked Visits'
                ).classes(
                    'text-3xl font-bold'
                )

                ui.separator()

                ui.label(
                    'Coming Soon'
                ).classes(
                    'text-xl text-gray-500'
                )

    # =========================================
    # SCROLL TO TOP
    # =========================================

    ui.button(
        icon='keyboard_arrow_up',
        on_click=lambda:
        ui.run_javascript(
            '''
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
            '''
        )
    ).props(
        'round color=primary'
    ).style(
        '''
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 9999;
        '''
    )