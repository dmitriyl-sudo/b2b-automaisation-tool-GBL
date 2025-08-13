from googleapiclient.discovery import build
from utils.google_drive import get_credentials  # если у тебя get_credentials отдельно — импорт скорректируй

def delete_column_b_from_all_sheets(spreadsheet_id: str):
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_ids = [sheet["properties"]["sheetId"] for sheet in spreadsheet["sheets"]]

    requests = []
    for sheet_id in sheet_ids:
        requests.append({
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 1,  # B = index 1
                    "endIndex": 2
                }
            }
        })

    body = {"requests": requests}
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"✅ Столбец B удалён из {len(sheet_ids)} листов таблицы.")

# Вызов
delete_column_b_from_all_sheets("1raoZjkWdOoCEwzw5W9aaW3EbpUU9lj5b0lev0dmNaxI")
