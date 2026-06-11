from nicegui import ui
import pandas as pd
import Cache
from sqlalchemy import create_engine, text
from datetime import date, timedelta
import sys
import psycopg2
sys.path.append("..")
from Keys.PostGresKey import POSTGRES_URL
engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True
)
DAY_ORDER = {
    "Saturday": 1,
    "Sunday": 2,
    "Monday": 3,
    "Tuesday": 4,
    "Wednesday": 5,
    "Thursday": 6,
    "Friday": 7,
}
DAY_COLUMNS = [
    "Saturday",
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]
def safe_notify(client, message, color='positive'):

    try:

        with client:

            ui.notify(
                message,
                color=color
            )

    except Exception as e:

        print(f'Notification Error: {e}')

def get_icd_cache():

    if Cache.ICD_DF_CACHE is None:

        print(
            'Loading ICD Cache...'
        )

        query = """

        SELECT

            icd_main_disease_code,
            icd_main_disease_description,
            icd_chronic

        FROM icd_codes

        
        ORDER BY

            icd_main_disease_code

        """

        icd_df = pd.read_sql(

            query,

            engine

        )

        icd_options = {}

        icd_lookup = {}

        for _, row in icd_df.iterrows():

            chronic_options = {}

            display_text = (

                f'{row["icd_main_disease_code"]} | '

                f'{row["icd_main_disease_description"]}'

            )

            icd_options[

                row["icd_main_disease_code"]

            ] = display_text

            if row["icd_chronic"]:

                chronic_options[
                    row["icd_main_disease_code"]
                ] = display_text

            icd_lookup[

                row["icd_main_disease_code"]

            ] = row[

                "icd_main_disease_description"

            ]

        Cache.ICD_DF_CACHE = (
            icd_df
        )

        Cache.ICD_OPTIONS_CACHE = (
            icd_options
        )

        Cache.ICD_LOOKUP_CACHE = (
            icd_lookup
        )

        Cache.ICD_CHRONIC_OPTIONS_CACHE = (
            chronic_options
        )

    return (

        Cache.ICD_DF_CACHE,

        Cache.ICD_OPTIONS_CACHE,

        Cache.ICD_CHRONIC_OPTIONS_CACHE,

        Cache.ICD_LOOKUP_CACHE

    )

def get_labs_cache():

    if Cache.LABS_DF_CACHE is None:

        print(
            'Loading Labs Cache...'
        )

        query = """

        SELECT

            lab_code,
            lab_group,
            lab_name

        FROM labs_ref

        ORDER BY

            lab_group,
            lab_name

        """

        labs_df = pd.read_sql(
            query,
            engine
        )

        labs_options = {}

        labs_lookup = {}

        for _, row in labs_df.iterrows():

            display_text = (

                f'{row["lab_code"]} | '

                f'{row["lab_group"]} | '

                f'{row["lab_name"]}'

            )

            labs_options[
                row["lab_code"]
            ] = display_text

            labs_lookup[
                row["lab_code"]
            ] = row["lab_name"]

        Cache.LABS_DF_CACHE = labs_df

        Cache.LABS_OPTIONS_CACHE = labs_options

        Cache.LABS_LOOKUP_CACHE = labs_lookup

    return (

        Cache.LABS_DF_CACHE,

        Cache.LABS_OPTIONS_CACHE,

        Cache.LABS_LOOKUP_CACHE

    )

def get_scans_cache():

    if Cache.SCANS_DF_CACHE is None:

        print(
            'Loading Scans Cache...'
        )

        query = """

        SELECT

            scan_code,
            scan_group,
            scan_name

        FROM scans_ref

        ORDER BY

            scan_group,
            scan_name

        """

        scans_df = pd.read_sql(
            query,
            engine
        )

        scans_options = {}

        scans_lookup = {}

        for _, row in scans_df.iterrows():

            display_text = (

                f'{row["scan_code"]} | '

                f'{row["scan_group"]} | '

                f'{row["scan_name"]}'

            )

            scans_options[
                row["scan_code"]
            ] = display_text

            scans_lookup[
                row["scan_code"]
            ] = row["scan_name"]

        Cache.SCANS_DF_CACHE = scans_df

        Cache.SCANS_OPTIONS_CACHE = scans_options

        Cache.SCANS_LOOKUP_CACHE = scans_lookup

    return (

        Cache.SCANS_DF_CACHE,

        Cache.SCANS_OPTIONS_CACHE,

        Cache.SCANS_LOOKUP_CACHE

    )

def format_requested_labs(codes):

    if not codes:
        return "-"

    return "\n".join(

        Cache.LABS_LOOKUP_CACHE.get(
            code,
            code
        )

        for code in codes

    )

def format_requested_scans(codes):

    if not codes:
        return "-"

    return "\n".join(

        Cache.SCANS_LOOKUP_CACHE.get(
            code,
            code
        )

        for code in codes

    )

def format_diagnosis_codes(codes):

    if not codes:
        return "-"

    return "\n".join(

        f"{code} - {Cache.ICD_LOOKUP_CACHE.get(code, code)}"

        for code in codes
    )

def format_time(value):

    try:

        return pd.to_datetime(

            str(value)

        ).strftime(

            "%I:%M %p"

        )

    except:

        return str(value)
    
opened_visits = []
selected_visit = None
visit_tabs_container = None
visit_details_container = None

def get_booked_visits():

    if Cache.BOOKED_VISITS_CACHE is None:

        query = """

        SELECT

            bv.booking_key,
            bv.visit_key,

            bv.status,

            bv.creation_time_stamp,

            bv.chief_complaint,

            bv.consultation_timestamp,

            p.patient_u_id,
            p.patient_name,
            p.phone_number,

            dl.dr_code,
            dl.dr_name,
            dl.speciality,

            av.scheduled_date,

            COALESCE(

                av.start_time_override,

                tt.scheduled_start_time

            ) AS start_time,

            COALESCE(

                av.end_time_override,

                tt.scheduled_end_time

            ) AS end_time,

            CONCAT(

                dl.dr_name,

                ' - ',

                TO_CHAR(

                    COALESCE(

                        av.start_time_override,

                        tt.scheduled_start_time

                    ),

                    'HH12:MI AM'

                )

            ) AS shift_name

        FROM booked_visits bv

        LEFT JOIN patients_list p

            ON bv.patient_u_id =
            p.patient_u_id

        LEFT JOIN available_visits av

            ON bv.visit_key =
            av.visit_key

        LEFT JOIN dr_time_table tt

            ON av.time_table_key =
            tt.time_table_key

        LEFT JOIN dr_list dl

            ON tt.dr_code =
            dl.dr_code

        ORDER BY

            av.scheduled_date,
            start_time

        """

        Cache.BOOKED_VISITS_CACHE = pd.read_sql(
            query,
            engine
        )

    return Cache.BOOKED_VISITS_CACHE

def reload_booked_visits_cache():

    Cache.BOOKED_VISITS_CACHE = None

    return get_booked_visits()

def get_previous_visits(

    patient_u_id,current_booking_key

):

    query = """

    SELECT

        bv.booking_key,

        bv.visit_key,

        bv.status,

        bv.chief_complaint,

        bv.diagnosis_codes,

        bv.requested_labs,

        bv.requested_scans,

        bv.doctor_notes,

        bv.consultation_timestamp,

        av.scheduled_date,

        dl.dr_name,

        dl.speciality

    FROM booked_visits bv

    LEFT JOIN available_visits av

        ON bv.visit_key =
        av.visit_key

    LEFT JOIN dr_time_table dtt

        ON av.time_table_key =
        dtt.time_table_key

    LEFT JOIN dr_list dl

        ON dtt.dr_code =
        dl.dr_code

    WHERE

        bv.patient_u_id = :patient_u_id

        AND

        bv.booking_key <> :booking_key

        AND

        bv.status = 'Completed'

    ORDER BY

        av.scheduled_date DESC

    """

    return pd.read_sql(

        text(query),

        engine,

        params={

        "patient_u_id":

        patient_u_id,

        "booking_key":

        current_booking_key

    }

    )

def render_doctor_card(row):

    card = ui.card().classes(

        '''
        w-full
        cursor-pointer
        hover:bg-blue-50
        '''

    )

    with card:

        ui.label(

            row["patient_name"]

        ).classes(

            'font-bold text-lg'

        )

        ui.label(

            row["status"]

        ).classes(

            'text-gray-500'

        )

    card.on(

        'click',

        lambda v=row.to_dict():

        open_visit(v)

    )

def update_visit_status(
    booking_key,
    new_status
):

    with engine.connect() as conn:

        conn.execute(

            text("""

            UPDATE booked_visits

            SET

                status = :status

            WHERE

                booking_key = :booking_key

            """),

            {

                "status":
                    new_status,

                "booking_key":
                    booking_key

            }

        )

        conn.commit()

    reload_booked_visits_cache()

    ui.notify(
        f'Visit Updated To {new_status}'
    )

def get_visit_medications(

    booking_key

):

    query = """

    SELECT

        medication_name,

        medictaion_dose,

        medictaion_dose_unit,

        frequency,

        frequency_unit

    FROM rx_medications

    WHERE

        booking_key = :booking_key

    ORDER BY

        md_line_key

    """

    return pd.read_sql(

        text(query),

        engine,

        params={

            "booking_key":
                booking_key

        }

    )

def render_admin_card(row):

    card = ui.card().classes(

        '''
        w-full
        cursor-pointer
        hover:bg-blue-50
        '''

    )

    with card:
        with ui.row().classes(
            'w-full justify-between items-center'
        ):
            ui.label(

                row["patient_name"]

            ).classes(

                'font-bold'

            )

            ui.label(

                row["dr_name"]

            )

        with ui.row().classes(
            'gap-1'
        ):

            ui.button(
                icon='visibility'
            ).props(
                'flat round'
            ).on(
                'click',
                lambda v=row.to_dict():
                open_visit(v)
            )

            if row["status"] == "Booked":

                ui.button(
                    icon='login'
                ).props(
                    'flat round'
                ).on(

                'click',

                lambda bk=row["booking_key"]:

                update_visit_status(

                    bk,

                    "Checked In"

                )

            )
            ui.button(
                icon='cancel'
            ).props(
                'flat round'
            ).on(

                    'click',

                    lambda bk=row["booking_key"]:

                    update_visit_status(

                        bk,

                        "Cancelled"

                    )

                )

def render_doctor_group(

    dr_name,

    doctor_df

):

    with ui.expansion(

        f"{dr_name} ({len(doctor_df)})",

        value=False

    ).classes(

        'w-full'

    ):

        for _, row in doctor_df.iterrows():

            render_admin_card(
                row
            )

def render_section(

    title,
    df,
    is_admin,
    is_doctor

):

    with ui.expansion(

        f"{title} ({len(df)})",

        value=True

    ).classes(

        'w-full'

    ):

        if df.empty:

            ui.label(

                'No Appointments'

            ).classes(

                'text-grey'

            )

            return

        if is_doctor:

            for _, row in df.iterrows():

                render_doctor_card(
                    row
                )

        elif is_admin:

            doctors = df.groupby(
                "dr_name"
            )

            for dr_name, doctor_df in doctors:

                render_doctor_group(

                    dr_name,

                    doctor_df

                )

def empty_visit_details():

    visit_details_container.clear()

    with visit_details_container:

        with ui.column().classes(

            '''
            w-full
            h-[600px]
            items-center
            justify-center
            '''

        ):

            ui.icon(

                'event_note'

            ).classes(

                'text-8xl text-gray-400'

            )

            ui.label(

                'Select a Visit'

            ).classes(

                'text-4xl font-bold text-gray-500'

            )

def show_visit_details(visit):

    visit_details_container.clear()

    (
    _,
        ICD_OPTIONS,
        _,
        _
    ) = get_icd_cache()
    options=ICD_OPTIONS
    
    (
        _,
        LAB_OPTIONS,
        _
    ) = get_labs_cache()

    (
        _,
        SCAN_OPTIONS,
        _
    ) = get_scans_cache()
    with visit_details_container:

        # =====================================
        # VISIT CONSULTATION
        # =====================================

        with ui.expansion(

            'Visit Consultation',

            value=True

        ).classes(

            'w-full'

        ):

            with ui.column().classes(

                'w-full gap-4 p-2'

            ):

                # ==========================
                # VISIT INFORMATION
                # ==========================

                with ui.row().classes(
                    'w-full gap-8'
                ):

                    ui.label(
                        f'Booking: {visit["booking_key"]}'
                    )

                    ui.label(
                        f'Doctor: {visit["dr_name"]}'
                    )

                    ui.label(
                        f'Status: {visit["status"]}'
                    )

                with ui.row().classes(
                    'w-full gap-8'
                ):

                    ui.label(
                        f'Date: {visit["scheduled_date"]}'
                    )

                    ui.label(
                        f'Speciality: {visit["speciality"]}'
                    )

                ui.separator()

                # ==========================
                # VITALS
                # ==========================

                with ui.row().classes(
                    'gap-2'
                ):

                    ui.button(

                        'Add Vitals',

                        icon='monitor_heart'

                    )

                    ui.button(

                        'Previous Vitals',

                        icon='history'

                    )

                ui.separator()

                # ==========================
                # CHIEF COMPLAINT
                # ==========================

                chief_complaint = ui.textarea(

                    'Chief Complaint',

                    value=visit.get(
                        "chief_complaint",
                        ""
                    ) or ""

                ).classes(
                    'w-full'
                )

                # ==========================
                # DIAGNOSIS
                # ==========================

                diagnosis_codes = ui.select(

                    options=ICD_OPTIONS,

                    label='Diagnosis',

                    multiple=True,

                    value=visit.get(
                        "diagnosis_codes",
                        []
                    ) or []

                ).props(

                    'use-input use-chips fill-input'
                ).classes(
                    'w-full'
                )

                # ==========================
                # LABS
                # ==========================

                requested_labs = ui.select(

                    options=LAB_OPTIONS,
                    label='Labs to Request',
                    multiple=True,

                    value=visit.get(
                        "requested_labs"
                    ) or []

                ).props(

                    'use-input use-chips fill-input'

                ).classes(

                    'w-full'

                )

                # ==========================
                # SCANS
                # ==========================

                requested_scans = ui.select(

                    options=SCAN_OPTIONS,
                    label='Scans to Request',
                    multiple=True,

                    value=visit.get(
                        "requested_scans"
                    ) or []

                ).props(

                    'use-input use-chips fill-input'

                ).classes(

                    'w-full'

                )

                # ==========================
                # DOCTOR NOTES
                # ==========================

                doctor_notes = ui.textarea(

                    'Doctor Notes',

                    value=visit.get(
                        "doctor_notes",
                        ""
                    ) or ""

                ).classes(
                    'w-full'
                )

                ui.separator()

                # ==========================
                # ACTION BUTTONS
                # ==========================

                with ui.row().classes(
                    'w-full justify-end gap-2'
                ):

                    ui.button(

                        'Save Visit',

                        icon='save'

                    )

                    ui.button(

                        'Add Medications',

                        icon='medication'

                    )

                    ui.button(

                        'Generate Prescription',

                        icon='picture_as_pdf'

                    )

                    ui.button(

                        'Complete Visit',

                        icon='task_alt',

                        color='green'

                    )

        # =====================================
        # PATIENT PROFILE
        # =====================================

        with ui.expansion(

            'Patient Information',

            value=False

        ).classes(

            'w-full'

        ):

            with ui.tabs().classes(

                'w-full'

            ) as patient_tabs:

                profile_tab = ui.tab(
                    'Patient Profile'
                )

                previous_visits_tab = ui.tab(
                    'Previous Visits'
                )

                labs_history_tab = ui.tab(
                    'Labs History'
                )

                scans_history_tab = ui.tab(
                    'Scans History'
                )

            with ui.tab_panels(

                patient_tabs,

                value=profile_tab

            ).classes(

                'w-full'

            ):
                with ui.tab_panel(

                    profile_tab

                ):
                    ui.label(

                        'Patient Profile Will Be Rendered Here'

                    ).classes(

                        'text-h6'

                    )

                with ui.tab_panel(

                    previous_visits_tab

                ):
                    previous_visits_df = (

                        get_previous_visits(

                            visit[
                                "patient_u_id"
                            ],

                            visit[
                                "booking_key"
                            ]

                        )

                    )
                    if previous_visits_df.empty:

                        ui.label(

                            'No Previous Visits'

                        )

                    else:
                        for _, old_visit in previous_visits_df.iterrows():

                            with ui.expansion(

                                f'''

                                {old_visit["scheduled_date"]}

                                |

                                {old_visit["speciality"]}

                                |

                                {old_visit["dr_name"]}

                                
                                '''

                            ).classes(

                                'w-full'

                            ):
                                

                                ui.label(

                                    f'Speciality: '

                                    f'{old_visit["speciality"]}'

                                )

                                ui.label(

                                    f'Status: '

                                    f'{old_visit["status"]}'

                                )
                                ui.separator()

                                ui.label(

                                    'Chief Complaint'

                                ).classes(

                                    'font-bold'

                                )

                                ui.label(

                                    old_visit.get(

                                        "chief_complaint",

                                        "-"

                                    ) or "-"

                                )

                                ui.separator()
                                ui.label(

                                    'Diagnosis'

                                ).classes(

                                    'font-bold'

                                )

                                ui.label(

                                    format_diagnosis_codes(

                                        old_visit.get(
                                            "diagnosis_codes"
                                        )

                                    )

                                )

                                ui.separator()
                                ui.label(

                                    'Doctor Notes'

                                ).classes(

                                    'font-bold'

                                )

                                ui.label(

                                    old_visit.get(

                                        "doctor_notes",

                                        "-"

                                    ) or "-"

                                )

                                ui.separator()

                                ui.label(

                                    'Requested Labs'

                                ).classes(

                                    'font-bold'

                                )

                                ui.label(

                                    format_requested_labs(

                                        old_visit.get(
                                            "requested_labs"
                                        )

                                    )

                                )
                                ui.separator()

                                ui.label(

                                    'Requested Scans'

                                ).classes(

                                    'font-bold'

                                )

                                ui.label(

                                    format_requested_scans(

                                        old_visit.get(
                                            "requested_scans"
                                        )

                                    )

                                )

                                ui.separator()

                                ui.label(

                                    'Medications'

                                ).classes(

                                    'font-bold'
                                )
                                medications_df = (

                                    get_visit_medications(

                                        old_visit[
                                            "booking_key"
                                        ]

                                    )

                                )
                                if medications_df.empty:

                                    ui.label(
                                        '-'
                                    )
                                for _, med in medications_df.iterrows():

                                    ui.label(

                                        f"""

                                        {med["medication_name"]}

                                        |

                                        {med["medictaion_dose"]}

                                        {med["medictaion_dose_unit"]}

                                        |

                                        {med["frequency"]}

                                        {med["frequency_unit"]}

                                        """

                                    )


                with ui.tab_panel(

                    labs_history_tab

                ):

                    ui.label(

                        'Coming Soon'

                    )
                with ui.tab_panel(

                    scans_history_tab

                ):

                    ui.label(

                        'Coming Soon'

                    )

def open_visit(visit):

    global selected_visit

    exists = any(

        v["booking_key"]

        ==

        visit["booking_key"]

        for v in opened_visits

    )

    if not exists:

        opened_visits.append(
            visit
        )

    selected_visit = visit

    refresh_visit_tabs()

    show_visit_details(
        visit
    )

def close_visit(visit):

    global selected_visit

    opened_visits[:] = [

        v

        for v in opened_visits

        if

        v["booking_key"]

        !=

        visit["booking_key"]

    ]

    if (

        selected_visit

        and

        selected_visit["booking_key"]

        ==

        visit["booking_key"]

    ):

        if opened_visits:

            selected_visit = (

                opened_visits[0]

            )

            show_visit_details(

                selected_visit

            )

        else:

            selected_visit = None

            empty_visit_details()

    refresh_visit_tabs()

def refresh_visit_tabs():

    visit_tabs_container.clear()

    with visit_tabs_container:

        with ui.row().classes(

            'gap-2 flex-wrap'

        ):

            for visit in opened_visits:

                active = (

                    selected_visit

                    and

                    selected_visit["booking_key"]

                    ==

                    visit["booking_key"]

                )

                bg = (

                    'bg-blue-100'

                    if active

                    else 'bg-white'

                )

                tab_card = ui.card().classes(

                    f'px-4 py-2 cursor-pointer {bg}'

                )

                tab_card.on(

                    'click',

                    lambda v=visit:

                    open_visit(v)

                )

                with tab_card:

                    with ui.row().classes(

                        'items-center gap-2'

                    ):
                        status_color = {

                            "Checked In":
                                "green",

                            "Booked":
                                "orange",

                            "Completed":
                                "blue",

                            "Cancelled":
                                "red",

                            "No Show":
                                "grey"

                        }.get(
                            visit["status"],
                            "grey"
                        )

                        ui.icon(
                            'circle'
                        ).style(
                            f'color:{status_color};font-size:12px'
                        )

                        label = ui.label(
                            visit["patient_name"][:15]
                        ).classes(
                            'font-bold'
                        )

                        ui.tooltip(
                            visit["patient_name"]
                        )

                        close_btn = ui.button(
                            icon='close'
                        ).props(
                            'flat round dense'
                        )

                        close_btn.on(

                            'click.stop',

                            lambda v=visit:
                            close_visit(v)

                        )

def render_booked_visits_tab():
    bookings_df = get_booked_visits()

    today = date.today()

    tomorrow = (
        today +
        timedelta(days=1)
    )

    bookings_df[
    "scheduled_date"
        ] = pd.to_datetime(

            bookings_df[
                "scheduled_date"
            ]

        ).dt.date
    
    role = Cache.CURRENT_USER["role"]
    is_admin = role in [

    "Admin",

    "Super Admin",

    "Reception"

        ]
    is_doctor = role == "Doctor"
    if is_doctor:

        bookings_df = bookings_df[

            bookings_df["dr_code"]

            ==

            Cache.CURRENT_USER["dr_code"]

        ]
    
    today_df = bookings_df[

            bookings_df[
            "scheduled_date"
                ] == today

        ]
    
    tomorrow_df = bookings_df[

            bookings_df[
                "scheduled_date"
            ] == tomorrow

        ]
    
    upcoming_df = bookings_df[

            bookings_df[
                "scheduled_date"
            ] > tomorrow

        ]
    
    with ui.row().classes(

    'w-full gap-4 items-start'

    ):  
        # Left Section
        with ui.column().classes(

    'w-[450px] gap-2'

        ):

    

            render_section(

            "Today's Visits",

            today_df,

            is_admin,

            is_doctor

            )

            render_section(

                "Tomorrow's Visits",

                tomorrow_df,

                is_admin,

                is_doctor

            )

            render_section(

                "Upcoming Visits",

                upcoming_df,

                is_admin,

                is_doctor

            )

        # Right Section
        with ui.column().classes(
                'flex-1 gap-4'
            ):

                global visit_tabs_container
                global visit_details_container

                visit_tabs_container = ui.column()

                visit_details_container = ui.column().classes(
                    'w-full'
                )   
    empty_visit_details()