import os
import pickle
import time
import pandas as pd
from openpyxl import Workbook
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from typing import List, Dict, Optional
import logging # Добавлен импорт logging

# --- КОНФИГУРАЦИЯ ЛОГГИРОВАНИЯ (для этого файла) ---
# Можно использовать тот же логгер, что и в api_fastapi_backend.py,
# или настроить отдельно, если нужно.
# Для простоты, используем базовую конфигурацию, которая будет писать в консоль.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_credentials():
    """
    Получает учетные данные Google API.
    Использует сохраненный токен или выполняет аутентификацию.
    """
    creds = None
    # Проверяем, есть ли сохраненный токен
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # Если учетные данные недействительны или отсутствуют, обновляем/получаем их
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request()) # Обновляем токен, если он истек
        else:
            # Запускаем локальный сервер для аутентификации
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
            )
            creds = flow.run_local_server(port=0)
            # Сохраняем токен для будущих использований
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

    return creds

def upload_table_to_sheets(table_data: List[Dict], original_order: Optional[List[str]] = None, project: str = "Unknown", geo: str = "Unknown", env: str = "prod"):
    """
    Загружает табличные данные в новую Google Sheet.
    Поддерживает сортировку данных по original_order, если он предоставлен.

    Args:
        table_data (list[dict]): Список словарей, где каждый словарь - это строка данных.
        original_order (list[str], optional): Список названий платежных методов
                                              в желаемом порядке. Если предоставлен,
                                              данные будут отсортированы по этому порядку.
        project (str): Название проекта для включения в имя файла.
        geo (str): GEO для включения в имя файла.
        env (str): Окружение (prod/stage) для включения в имя файла.
    Returns:
        str: ID созданной Google Sheet.
    """
    import tempfile

    # ✅ Сортировка данных по original_order, если он предоставлен
    if original_order:
        # Создаем маппинг Paymethod -> row_data для быстрого доступа
        title_to_row = {row.get("Paymethod"): row for row in table_data}
        # Пересобираем table_data в соответствии с original_order
        # Исключаем методы, которых нет в title_to_row (т.е. не было в исходных данных)
        table_data = [title_to_row[title] for title in original_order if title in title_to_row]

    # Преобразуем список словарей в DataFrame
    df = pd.DataFrame(table_data)
    
    # Создаем временный файл Excel
    temp_xlsx = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")

    # Записываем DataFrame во временный файл Excel
    with pd.ExcelWriter(temp_xlsx.name, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="merged", index=False) # sheet_name "merged" по умолчанию

    creds = get_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    # Метаданные для нового файла Google Sheet
    # Формируем название файла с проектом в конце
    file_name = f"Geo Methods Export {geo} {env} - {project}"
    file_metadata = {
        "name": file_name, # Имя файла в Google Drive с названием проекта
        "mimeType": "application/vnd.google-apps.spreadsheet" # Тип файла: Google Sheet
    }

    # Загружаем временный Excel файл как Google Sheet
    media = MediaFileUpload(temp_xlsx.name, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id" # Запрашиваем только ID загруженного файла
    ).execute()

    # Удаляем временный файл
    os.unlink(temp_xlsx.name)

    # Применяем стили, сортировку и заморозку
    finalize_google_sheet_formatting(uploaded_file.get("id"))
    
    # Устанавливаем права доступа
    set_sheet_permissions(uploaded_file.get("id"))

    return uploaded_file.get("id")

def set_sheet_permissions(file_id):
    """
    Устанавливает права доступа для Google Sheets файла.
    Дает права на редактирование для группы "Ramtinar Techconsult Limited".
    """
    try:
        creds = get_credentials()
        drive_service = build("drive", "v3", credentials=creds)
        
        # Устанавливаем права для группы
        permission_body = {
            'type': 'domain',
            'role': 'writer',
            'domain': 'gbl-factory.com'  # Домен группы
        }
        
        drive_service.permissions().create(
            fileId=file_id,
            body=permission_body,
            fields='id'
        ).execute()
        
        logging.info(f"✅ Права доступа установлены для файла {file_id}")
        
    except Exception as e:
        logging.error(f"❌ Ошибка установки прав доступа для файла {file_id}: {e}")

def create_google_file(output_filename):
    """
    Загружает локальный файл Excel в Google Drive как Google Sheet.
    """
    creds = get_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    file_path = output_filename
    file_name = os.path.basename(output_filename)
    # ID папки на Google Drive, куда будет загружен файл
    folder_id = "1zsYxeJvCuVH8-07O-a48Ys50NwNiqY3e"

    file_metadata = {
        "name": file_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id], # Указываем родительскую папку
    }

    # Загружаем файл
    media = MediaFileUpload(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = uploaded_file.get("id")

    print(f"📄 Загружен файл: {file_id}, мультилист — пропускаем стилизацию 'merged'")
    return file_id

def finalize_google_sheet_formatting(file_id: str, delete_columns_by_header: Optional[List[str]] = None):
    """
    Применяет сортировку, заморозку заголовка, автостили и минимальную ширину колонки "Recommended"
    к указанной Google Sheet.
    """
    creds = get_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)

    # Даем Google Sheets API время на обработку пакетного обновления данных
    time.sleep(1.5)

    # Получаем информацию обо всех листах в таблице, включая их данные (для заголовков)
    spreadsheet_metadata = sheets_service.spreadsheets().get(
        spreadsheetId=file_id,
        fields='sheets.properties' # Нужны только свойства для получения sheetId и title
    ).execute()
    sheets_props = spreadsheet_metadata.get("sheets", [])

    all_requests = [] # Список для всех запросов на обновление

    for sheet_prop in sheets_props:
        sheet_id = sheet_prop["properties"]["sheetId"]
        sheet_title = sheet_prop["properties"]["title"]

        # Получаем актуальные заголовки для конкретного листа
        try:
            header_response = sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id,
                range=f"'{sheet_title}'!1:1"
            ).execute()
            current_headers = header_response.get("values", [[]])[0]
        except Exception as e:
            logging.warning(f"Не удалось получить заголовки для листа '{sheet_title}': {e}. Пропускаем форматирование для этого листа.")
            continue # Пропускаем к следующему листу, если заголовки не могут быть получены

        if not current_headers:
            logging.info(f"Лист '{sheet_title}' пуст или не содержит заголовков. Пропускаем форматирование.")
            continue

        # Запросы на установку ширины столбцов
        # Эти значения основаны на ожидаемом порядке столбцов до удаления
        column_widths_config = [
            (0, 25 * 6),   # Колонка A (Paymethod)
            (1, 60 * 6),       # Колонка B (Recommended) - Увеличена до 70px
            (2, 50 * 6),   # Колонка C (Payment Name) - Возвращена к исходной ширине
            (3, 18 * 6),   # Колонка D (Currency)
            (4, 18 * 6),   # Колонка E (Deposit)
            (5, 18 * 6),   # Колонка F (Withdraw)
            (6, 25 * 6)    # Колонка G (Status)
            # RecommendedSort будет добавлен как последняя колонка и затем удален
        ]
        for idx, size in column_widths_config:
            if idx < len(current_headers): # Убеждаемся, что индекс находится в пределах существующих заголовков
                all_requests.append({
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": idx,
                            "endIndex": idx + 1
                        },
                        "properties": {"pixelSize": size},
                        "fields": "pixelSize"
                    }
                })

        # Запросы на стилизацию ячеек
        # Убеждаемся, что endColumnIndex всегда корректен (>= startColumnIndex)
        end_col_for_styles = len(current_headers) # Используем фактическое количество колонок

        style_requests = [
            # Жирный шрифт для первой строки (заголовков)
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            },
            # Жирный шрифт для первого столбца (названий Paymethod)
            {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            },
            # Выравнивание по центру для столбцов с данными (со 2-й строки, с 3-го столбца)
            # Убеждаемся, что endColumnIndex >= startColumnIndex + 1
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1, # Начинаем со 2-й строки (индекс 1)
                        "startColumnIndex": 2, # Начинаем с 3-го столбца (индекс 2)
                        "endColumnIndex": max(2 + 1, end_col_for_styles) # Убеждаемся, что конец как минимум 3
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat.horizontalAlignment, userEnteredFormat.verticalAlignment"
                }
            },
            # Толстая нижняя граница для заголовков
            {
                "updateBorders": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "endColumnIndex": end_col_for_styles # До последней колонки
                    },
                    "bottom": {"style": "SOLID_THICK", "color": {"red": 0.2, "green": 0.2, "blue": 0.8}}
                }
            },
            # Условное форматирование для "PROD" (зеленый фон)
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sheet_id,
                            "startRowIndex": 1, # Начинаем со 2-й строки
                            "startColumnIndex": current_headers.index("Status") if "Status" in current_headers else 0, # Динамический поиск столбца "Status"
                            "endColumnIndex": (current_headers.index("Status") + 1) if "Status" in current_headers else 1
                        }],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "PROD"}]},
                            "format": {"backgroundColor": {"red": 0.85, "green": 0.95, "blue": 0.85}}
                        }
                    },
                    "index": 0 # Индекс правила
                }
            },
            # Условное форматирование для "STAGE" (желтый фон)
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": current_headers.index("Status") if "Status" in current_headers else 0,
                            "endColumnIndex": (current_headers.index("Status") + 1) if "Status" in current_headers else 1
                        }],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "STAGE"}]},
                            "format": {"backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.75}}
                        }
                    },
                    "index": 1
                }
            },
            # Условное форматирование для "YES" (зеленый текст)
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 2, # Начинаем со столбца "Payment Name"
                            "endColumnIndex": end_col_for_styles # До конца колонок
                        }],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "YES"}]},
                            "format": {"textFormat": {"foregroundColor": {"red": 0.0, "green": 0.5, "blue": 0.0}}} # Более темный зеленый для читаемости
                        }
                    },
                    "index": 2
                }
            },
            # Условное форматирование для "NO" (красный текст)
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": 2, # Начинаем со столбца "Payment Name"
                            "endColumnIndex": end_col_for_styles # До конца колонок
                        }],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "NO"}]},
                            "format": {"textFormat": {"foregroundColor": {"red": 0.8, "green": 0.0, "blue": 0.0}}} # Более темный красный для читаемости
                        }
                    },
                    "index": 3
                }
            }
        ]
        all_requests.extend(style_requests)

        # Заморозить заголовок
        all_requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        })

        # --- Сортировка: Сначала по RecommendedSort (DESC), затем по Deposit (DESC) ---
        sort_specs = []
        recommended_sort_index = -1
        deposit_index = -1

        try:
            recommended_sort_index = current_headers.index("RecommendedSort")
        except ValueError:
            logging.warning(f"Колонка 'RecommendedSort' не найдена на листе '{sheet_title}'. Пропускаем сортировку по RecommendedSort для этого листа.")
        
        try:
            deposit_index = current_headers.index("Deposit")
        except ValueError:
            logging.warning(f"Колонка 'Deposit' не найдена на листе '{sheet_title}'. Пропускаем сортировку по Deposit для этого листа.")

        if recommended_sort_index != -1:
            sort_specs.append({
                "dimensionIndex": recommended_sort_index,
                "sortOrder": "DESCENDING"
            })
        if deposit_index != -1:
            sort_specs.append({
                "dimensionIndex": deposit_index,
                "sortOrder": "DESCENDING"
            })
        
        if sort_specs:
            all_requests.append({
                "sortRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,  # пропускаем заголовок
                        "startColumnIndex": 0,
                        "endColumnIndex": len(current_headers) # Сортируем до последней колонки
                    },
                    "sortSpecs": sort_specs
                }
            })

    # Выполняем все запросы одним пакетом
    try:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=file_id,
            body={"requests": all_requests}
        ).execute()
        logging.info(f"✅ Стили, сортировка и заморозка применены ко всем {len(sheets_props)} листам.")
    except Exception as e:
        logging.error(f"Ошибка при применении пакетного обновления стилей и сортировки: {e}")
        raise # Перевыбрасываем исключение, если нужно указать на сбой

    # --- Удаление колонок по названию (после сортировки) ---
    if delete_columns_by_header:
        delete_requests = []
        # Повторно получаем метаданные, чтобы получить актуальные свойства листа и заголовки столбцов
        # Это важно, так как сортировка могла изменить порядок столбцов
        time.sleep(1.5) # Даем время на применение сортировки перед получением метаданных для удаления
        updated_spreadsheet_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=file_id,
            fields='sheets.properties,sheets.data.rowData.values.formattedValue'
        ).execute()
        updated_sheets = updated_spreadsheet_metadata.get("sheets", [])

        for sheet in updated_sheets:
            sheet_id = sheet["properties"]["sheetId"]
            sheet_title = sheet["properties"]["title"]
            
            current_headers = []
            if sheet.get("data") and sheet["data"] and sheet["data"][0].get("rowData") and sheet["data"][0]["rowData"][0].get("values"):
                current_headers = [
                    cell.get("formattedValue", "")
                    for cell in sheet["data"][0]["rowData"][0]["values"]
                ]

            # Собираем индексы столбцов для удаления (справа налево, чтобы избежать смещения индексов)
            indices_to_delete = sorted([
                idx for idx, header_value in enumerate(current_headers)
                if header_value in delete_columns_by_header
            ], reverse=True) # Удаляем справа налево

            for idx in indices_to_delete:
                delete_requests.append({
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": idx,
                            "endIndex": idx + 1
                        }
                    }
                })
        
        if delete_requests:
            try:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=file_id,
                    body={"requests": delete_requests}
                ).execute()
                logging.info(f"✅ Колонки {delete_columns_by_header} удалены со всех листов.")
            except Exception as e:
                logging.warning(f"⚠️ Не удалось удалить колонки {delete_columns_by_header}: {e}")
    
    # ⏱ Подождать конвертацию (если вдруг не применилось сразу)
    time.sleep(1.5) # Сохраняем эту задержку, так как она может быть необходима для обработки изменений Google Sheets API

    # 🔚 Удаление пустых листов (если остались после удаления колонок)
    try:
        # Получаем метаданные с данными ячеек, чтобы проверить, есть ли строки данных (кроме заголовков)
        spreadsheet_content = sheets_service.spreadsheets().get(spreadsheetId=file_id, includeGridData=True).execute()
        for sheet_item in spreadsheet_content.get("sheets", []):
            sheet_id = sheet_item["properties"]["sheetId"]
            sheet_title = sheet_item["properties"]["title"]
            
            # Проверяем, есть ли данные в листе (кроме заголовка)
            # sheet_item.get("data") может быть пустым, если лист абсолютно пуст
            # rowData[0] - это заголовок
            row_data = sheet_item.get("data", [{}])[0].get("rowData", [])
            
            # Если только заголовок или вообще пусто (0 или 1 строка)
            if len(row_data) <= 1:
                logging.info(f"🗑 Удаляем пустой лист: {sheet_title} (ID: {sheet_id})")
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=file_id,
                    body={
                        "requests": [{"deleteSheet": {"sheetId": sheet_id}}]
                    }
                ).execute()
    except Exception as e:
        logging.warning(f"⚠️ Не удалось удалить пустые листы: {e}")

    logging.info(f"✅ Финализация стилей и сортировки для {file_id} завершена.")

# Старые функции apply_styles_to_sheet и apply_sorting_and_freeze удалены,
# так как их функциональность теперь включена в finalize_google_sheet_formatting.
