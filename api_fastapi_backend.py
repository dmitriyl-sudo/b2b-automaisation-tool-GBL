# --- ОБЯЗАТЕЛЬНЫЕ ИМПОРТЫ ДЛЯ ВСЕГО ФАЙЛА ---
# Убедитесь, что все эти библиотеки установлены (pip install ...)

# Стандартные и сторонние библиотеки
import logging
import os
import pickle
import time
import json
import sys
import re
from datetime import timedelta, datetime
from typing import Literal, List, Dict, Optional

import pandas as pd
import openpyxl
from openpyxl import Workbook
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

# Импорты для работы с Google API
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- ВАЖНО: Импорты из вашего проекта ---
from main import geo_groups, password_data, site_list
from utils.excel_utils import save_payment_data_to_excel, merge_payment_data
from utils.google_drive import create_google_file, upload_table_to_sheets, get_credentials
from utils.google_drive import finalize_google_sheet_formatting # Added this import

# --- ИСПРАВЛЕНИЕ: Удален неработающий импорт ---
# from auth_and_fetch import run_login_check, get_methods_only

from extractors.ritzo_extractor import RitzoExtractor
from extractors.rolling_extractor import RollingExtractor
from extractors.nfs_extractor import NeedForSpinExtractor
from extractors.wld_extractor import WildTokyoExtractor
from extractors.godofwins_extractor import GodofwinsExtractor
from extractors.hugo_extractor import HugoExtractor
from extractors.winshark_extractor import WinsharkExtractor
from extractors.spinlander_extractor import SpinlanderExtractor
from extractors.slota_extractor import SlotaExtractor
from extractors.spinline_extractor import SpinlineExtractor
from extractors.glitchspin_extractor import GlitchSpinExtractor

from test_runner import run_payment_method_tests


# --- КОНФИГУРАЦИЯ ЛОГГИРОВАНИЯ ---
LOG_FILE = os.path.join(os.path.dirname(__file__), "export_debug.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# --- БЕЗОПАСНОСТЬ И АУТЕНТИФИКАЦИЯ ---
SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

users_db = {
    "admin": {"password": "123", "role": "admin"},
    "qa": {"password": "qa123", "role": "qa"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in users_db:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": users_db[username]["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def extract_tags(name):
    tags = []
    dep_match = None
    for i in range(10):
        if f"{i}dep" in name.lower():
            dep_match = f"{i}DEP"
            break
    if dep_match:
        tags.append(dep_match)
    if "aff" in name.lower():
        tags.append("AFF")
    if "mob" in name.lower():
        tags.append("MOB")
    return tags

def extract_conditions_from_name(name: str) -> str:
    if not isinstance(name, str):
        return "ALL"
    tags = set()
    name_lower = name.lower()
    dep_match = re.search(r'(\d+)dep', name_lower)
    if dep_match:
        tags.add(f"{dep_match.group(1)}DEP")
    if "aff" in name_lower:
        tags.add("AFF")
    if "mob" in name_lower:
        tags.add("MOB")
    if not tags:
        return "ALL"
    return "\n".join(sorted(list(tags)))


# --- ИНИЦИАЛИЗАЦИЯ FastAPI ---
app = FastAPI()


# --- PYDANTIC МОДЕЛИ ДЛЯ ЗАПРОСОВ ---
class LoginTestRequest(BaseModel):
    project: str
    login: str
    geo: str
    env: Literal["stage", "prod"]

class MethodTestRequest(BaseModel):
    project: str
    geo: str
    login: str
    mode: str
    env: Literal["stage", "prod"]

class FullProjectExportRequest(BaseModel):
    project: str
    env: Literal["stage", "prod"]


# --- ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ---
EXTRACTORS = {
    site["name"]: (site["extractor_class"], site["stage_url"], site["prod_url"])
    for site in site_list
}

# --- ИСПРАВЛЕНИЕ: Логика вынесена в отдельные функции ---

def get_methods_only(project: str, geo: str, env: str, login: str):
    if project not in EXTRACTORS:
        raise HTTPException(status_code=400, detail="Unknown project")
    extractor_class, stage_url, prod_url = EXTRACTORS[project]
    url = stage_url if env == "stage" else prod_url
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        if "mobi" in login
        else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    )
    extractor = extractor_class(login, password_data, user_agent=user_agent, base_url=url)
    if not extractor.authenticate():
        return {"success": False, "error": "Authentication failed"}
    try:
        deposit, withdraw, dep_names, wd_names, currency, dep_count, recommended = extractor.get_payment_and_withdraw_systems(geo)
        deposit_pairs = list(zip(deposit, dep_names))
        withdraw_pairs = list(zip(withdraw, wd_names))
        recommended_pairs = [
            (title, name)
            for title, name in deposit_pairs + withdraw_pairs
            if (title, name) in recommended
        ]
        return {
            "success": True,
            "deposit_methods": deposit_pairs,
            "withdraw_methods": withdraw_pairs,
            "recommended_methods": recommended_pairs,
            "debug": {
                "recommended_pairs": list(recommended),
                "deposit_raw": deposit,
                "withdraw_raw": withdraw
            }
        }
    except Exception as e:
        logging.error(f"Error in get_methods_only for {project}/{geo}/{login}: {e}")
        return {"success": False, "error": str(e)}

def run_login_check(project: str, geo: str, env: str, login: str):
    if project not in EXTRACTORS:
        raise HTTPException(status_code=400, detail="Unknown project")
    extractor_class, stage_url, prod_url = EXTRACTORS[project]
    url = stage_url if env == "stage" else prod_url
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        if "mobi" in login
        else "Mozilla/5.5 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    )
    extractor = extractor_class(login, password_data, user_agent=user_agent, base_url=url)
    if not extractor.authenticate():
        raise HTTPException(status_code=401, detail="Authentication failed")
    return {
        "success": True,
        "currency": extractor.currency,
        "deposit_count": extractor.deposit_count
    }

# --- API ЭНДПОИНТЫ ---

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def read_me(user: dict = Depends(get_current_user)):
    return user

@app.get("/list-projects")
def list_projects():
    return [
        {"name": site["name"], "stage_url": site["stage_url"], "prod_url": site["prod_url"]}
        for site in site_list
    ]

@app.get("/geo-groups")
def list_geo_groups():
    return geo_groups

@app.post("/get-methods-only")
def get_methods_only_endpoint(request: LoginTestRequest):
    return get_methods_only(project=request.project, geo=request.geo, env=request.env, login=request.login)

@app.post("/run-login-check")
def run_login_check_endpoint(request: LoginTestRequest):
    return run_login_check(project=request.project, geo=request.geo, env=request.env, login=request.login)


@app.post("/test-methods")
async def test_methods(req: MethodTestRequest):
    results = run_payment_method_tests(
        project=req.project,
        geo=req.geo,
        login=req.login,
        mode=req.mode,
        env=req.env
    )
    return JSONResponse(content={"results": results})

@app.post("/export-table-to-sheets")
def export_table_to_sheets(payload: Dict = Body(...)):
    data: List[Dict] = payload.get("data", [])
    original_order: Optional[List[str]] = payload.get("originalOrder")
    try:
        file_id = upload_table_to_sheets(data, original_order=original_order)
        return {
            "success": True,
            "message": "Таблица экспортирована в Google Sheets",
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{file_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/export-full-project")
def export_full_project(req: FullProjectExportRequest, background_tasks: BackgroundTasks):
    if req.project not in [site["name"] for site in site_list]:
        raise HTTPException(status_code=400, detail="Unknown project")

    extractor_class, stage_url, prod_url = EXTRACTORS[req.project]
    url = stage_url if req.env == "stage" else prod_url

    filename = f"merged_{req.project}_{req.env}_FULL.xlsx"
    wb = openpyxl.Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    for geo, logins in geo_groups.items():
        if not logins:
            continue

        all_payment_data = {}
        original_order = []
        method_type_map = {}
        recommended_set = set()
        seen_titles = set()
        currency = None
        conditions_raw = {} 

        for login in logins:
            user_agent = (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)"
                if "mobi" in login
                else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            )
            extractor = extractor_class(login, password_data, user_agent=user_agent, base_url=url)
            if not extractor.authenticate():
                continue

            deposit, withdraw, dep_names, wd_names, curr, _, recommended = extractor.get_payment_and_withdraw_systems(geo)
            currency = currency or curr
            deposit_pairs = list(zip(deposit, dep_names))
            withdraw_pairs = list(zip(withdraw, wd_names))
            all_pairs = deposit_pairs + withdraw_pairs

            for title, name in all_pairs:
                key = f"{title}|||{name}"
                if title not in seen_titles:
                    original_order.append(title)
                    seen_titles.add(title)

                method_type_map[key] = method_type_map.get(key, {"Deposit": "NO", "Withdraw": "NO"})
                if (title, name) in deposit_pairs:
                    method_type_map[key]["Deposit"] = "YES"
                if (title, name) in withdraw_pairs:
                    method_type_map[key]["Withdraw"] = "YES"

                all_payment_data.setdefault(login, {})[key] = {
                    "Payment Name": name,
                    "Deposit": method_type_map[key]["Deposit"],
                    "Withdraw": method_type_map[key]["Withdraw"],
                    "Status": req.env.upper()
                }

                tags = extract_tags(name)
                if tags:
                    combined = "+".join(tags)
                    if title not in conditions_raw:
                        conditions_raw[title] = set()
                    conditions_raw[title].add(combined)
                else:
                    if title not in conditions_raw:
                        conditions_raw[title] = set()
                    conditions_raw[title].add("ALL")

            recommended_set.update(recommended)

        conditions_map = {k: "\n".join(sorted(v)) if v else "ALL" for k, v in conditions_raw.items()}
        merged = merge_payment_data(
            all_payment_data,
            list(all_payment_data.keys()),
            original_order,
            currency,
            list(recommended_set),
            excel_filename=filename,
            url=url,
            conditions_map=conditions_map
        )

        sheet = wb.create_sheet(title=f"{req.project}_{geo}_{req.env}")
        headers = ["Paymethod", "Payment Name", "Currency", "Deposit", "Withdraw", "Status", "Details"]
        for col, header in enumerate(headers, start=1):
            sheet.cell(row=1, column=col, value=header)

        for i, method in enumerate(merged, start=2):
            row_data = [
                method, 
                merged[method].get("Payment Name", ""),
                merged[method].get("Currency", ""),
                merged[method].get("Deposit", ""),
                merged[method].get("Withdraw", ""),
                merged[method].get("Status", ""),
                merged[method].get("Details", "")
            ]
            for col, val in enumerate(row_data, start=1):
                sheet.cell(row=i, column=col, value=val)

    wb.save(filename)
    file_id = upload_table_to_sheets(merged, original_order=original_order) 

    return {
        "success": True,
        "message": "Проект экспортирован с несколькими GEO-листами",
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{file_id}"
    }


# ==============================================================================
# === НОВЫЙ ЭНДПОИНТ ДЛЯ ЭКСПОРТА ВСЕГО ПРОЕКТА В GOOGLE SHEETS ===
# ==============================================================================
@app.post("/export-full-project-to-google-sheet")
def export_full_project_to_google_sheet(data: FullProjectExportRequest):
    """
    Экспортирует все GEO для проекта в один Google Sheet,
    где каждый GEO находится на отдельном листе.
    """
    try:
        creds = get_credentials()
        sheets_service = build("sheets", "v4", credentials=creds)
    except Exception as e:
        logging.error(f"Google API credentials error: {e}")
        raise HTTPException(status_code=500, detail=f"Google API credentials error: {e}")

    project = data.project
    env = data.env
    all_geo = list(geo_groups.keys())

    spreadsheet_body = { "properties": {"title": f"📊 {project} ({env.upper()}) — Full Export"} }
    try:
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        file_id = spreadsheet["spreadsheetId"]
        logging.info(f"Created new Google Sheet with ID: {file_id}")
    except Exception as e:
        logging.error(f"Failed to create Google Sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create Google Sheet: {e}")

    sheets_to_add = []
    all_sheets_data = {}

    for geo in all_geo:
        logins = geo_groups.get(geo, [])
        if not logins:
            continue

        seen_methods = {}
        recommended_set = set()

        for login in logins:
            try:
                methods = get_methods_only(project=project, geo=geo, env=env, login=login)
                if not methods or not methods.get("success"):
                    continue
            except Exception as e:
                logging.warning(f"Could not fetch methods for {login} in {geo}: {e}")
                continue

            for (title, name) in methods.get("recommended_methods", []):
                recommended_set.add((title.strip(), name.strip()))

            all_methods = set(methods.get("deposit_methods", []) + methods.get("withdraw_methods", []))

            for (title, name) in all_methods:
                key = (title.strip(), name.strip())
                if key not in seen_methods:
                    seen_methods[key] = {
                        "Paymethod": title,
                        "Recommended": "",
                        "Deposit": "NO",
                        "Withdraw": "NO",
                        "Payment Name": name,
                        "Conditions": extract_conditions_from_name(name),
                        "Env": env.upper()
                    }
                if (title, name) in methods.get("deposit_methods", []):
                    seen_methods[key]["Deposit"] = "YES"
                if (title, name) in methods.get("withdraw_methods", []):
                    seen_methods[key]["Withdraw"] = "YES"
                if (title, name) in recommended_set:
                    seen_methods[key]["Recommended"] = "⭐"

        if seen_methods:
            rows = list(seen_methods.values())
            headers = list(rows[0].keys())
            values = [headers] + [[r.get(h, "") for h in headers] for r in rows]
            
            sheet_title = geo[:100]
            sheets_to_add.append({"addSheet": {"properties": {"title": sheet_title}}})
            all_sheets_data[sheet_title] = values

    if not sheets_to_add:
        try:
            drive_service = build('drive', 'v3', credentials=creds)
            drive_service.files().delete(fileId=file_id).execute()
        except Exception as e:
            logging.error(f"Could not delete empty spreadsheet {file_id}: {e}")
        return {"success": False, "message": "No data found for any GEO in this project."}
        
    try:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=file_id,
            body={"requests": sheets_to_add}
        ).execute()

        data_to_update = []
        for sheet_title, values in all_sheets_data.items():
            data_to_update.append({
                "range": f"'{sheet_title}'!A1",
                "values": values
            })
        
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=file_id,
            body={
                "valueInputOption": "RAW",
                "data": data_to_update
            }
        ).execute()
        
    except Exception as e:
        logging.error(f"Failed to update sheets in batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update sheets: {e}")

    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        default_sheet_id = next((s['properties']['sheetId'] for s in sheets if s['properties']['title'] == 'Sheet1'), None)

        if default_sheet_id is not None:
             sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=file_id,
                body={"requests": [{"deleteSheet": {"sheetId": default_sheet_id}}]}
            ).execute()
    except Exception:
        logging.warning("Could not delete default 'Sheet1'. It may not have existed.")

    return {"success": True, "sheet_url": f"https://docs.google.com/spreadsheets/d/{file_id}"}


# ==============================================================================
# === НОВЫЙ ЭНДПОИНТ ДЛЯ ЭКСПОРТА НЕСКОЛЬКИХ ТАБЛИЦ В GOOGLE SHEETS (ПО ФРОНТУ) ===
# ==============================================================================
@app.post("/export-table-to-sheets-multi")
def export_table_to_sheets_multi(payload: Dict = Body(...)):
    """
    Принимает несколько таблиц по GEO и выгружает их в один Google Sheet (по фронту).
    """
    try:
        sheets = payload.get("sheets", [])
        if not sheets or not isinstance(sheets, list):
            raise HTTPException(status_code=400, detail="Invalid or missing 'sheets'")

        creds = get_credentials()
        sheets_service = build("sheets", "v4", credentials=creds)

        spreadsheet_body = {
            "properties": {
                "title": f"📊 Multi-GEO Export {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        file_id = spreadsheet["spreadsheetId"]
        logging.info(f"Created new spreadsheet: {file_id}")

        # 1. Создать листы и заполнить данными
        requests = []
        data_to_update = [] # Переименовано для ясности

        for sheet_data_item in sheets: # Переименовано для ясности
            title = sheet_data_item.get("geo", "Sheet")[:100]
            rows = sheet_data_item.get("rows", [])
            if not rows:
                continue

            requests.append({"addSheet": {"properties": {"title": title}}})
            headers = list(rows[0].keys())
            values = [headers] + [[r.get(h, "") for h in headers] for r in rows]
            
            data_to_update.append({
                "range": f"'{title}'!A1",
                "values": values
            })

        if not requests:
            return {"success": False, "message": "No valid data to export"}

        # Выполняем запросы на создание листов
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=file_id,
            body={"requests": requests}
        ).execute()

        # Выполняем запросы на заполнение данными
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=file_id,
            body={
                "valueInputOption": "RAW",
                "data": data_to_update
            }
        ).execute()

        # 4. Удалить стандартный Sheet1 (если остался) - ПЕРЕМЕЩЕНО СЮДА
        try:
            metadata = sheets_service.spreadsheets().get(spreadsheetId=file_id).execute()
            for sheet_info in metadata.get("sheets", []):
                if sheet_info["properties"]["title"] == "Sheet1":
                    default_sheet_id = sheet_info["properties"]["sheetId"]
                    sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=file_id,
                        body={"requests": [{"deleteSheet": {"sheetId": default_sheet_id}}]}
                    ).execute()
                    logging.info(f"Удален стандартный лист 'Sheet1' (ID: {default_sheet_id}).")
                    break # Выходим после удаления первого найденного "Sheet1"
        except Exception as e:
            logging.warning(f"Не удалось удалить стандартный лист 'Sheet1': {e}")

        # 🟣 НАКОНЕЦ — применяем стили и сортировку!
        finalize_google_sheet_formatting(file_id, delete_columns_by_header=["RecommendedSort"])

        return {
            "success": True,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{file_id}"
        }

    except Exception as e:
        logging.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
