from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'


def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('calendar', 'v3', credentials=creds)


def tambah_event(nama, deskripsi, tanggal, lokasi):
    service = get_calendar_service()

    event = {
        'summary': nama,
        'description': deskripsi,
        'location': lokasi,
        'start': {'date': tanggal, 'timeZone': 'Asia/Jakarta'},
        'end': {'date': tanggal, 'timeZone': 'Asia/Jakarta'}
    }

    created_event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    return created_event['id']


def update_event(event_id, nama, deskripsi, tanggal, lokasi):
    service = get_calendar_service()
    event = service.events().get(
        calendarId='primary',
        eventId=event_id
    ).execute()

    event.update({
        'summary': nama,
        'description': deskripsi,
        'location': lokasi,
        'start': {'date': tanggal, 'timeZone': 'Asia/Jakarta'},
        'end': {'date': tanggal, 'timeZone': 'Asia/Jakarta'}
    })

    service.events().update(
        calendarId='primary',
        eventId=event_id,
        body=event
    ).execute()


def hapus_event(event_id):
    service = get_calendar_service()
    service.events().delete(
        calendarId='primary',
        eventId=event_id
    ).execute()


def ambil_event_kalender():
    service = get_calendar_service()
    events = service.events().list(
        calendarId='primary',
        singleEvents=True
    ).execute()

    return events.get('items', [])
