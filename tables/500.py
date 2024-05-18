import datetime
from typing import Tuple, List, Dict, Any
import time
from bs4 import BeautifulSoup
import urllib.request
import os.path
import pickle
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

curs = ' ',
napravlenie = ' ',
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class NoValuesExeption(Exception):
    pass


class No_such_sheet_exeption(Exception):
    pass


class Group():
    def __init__(self, group_name):
        self.group_name = group_name
        self.monday = []
        self.tuesday = []
        self.wednesday = []
        self.thursday = []
        self.friday = []
        self.saturday = []
        self.sunday = []


class Lesson():
    def __init__(self):
        self.lesson_name = None
        self.time = None
        self.lecturer = None
        self.auditorium = None
        self.lesson_type = None

    def __str__(self):
        return (f"name: {self.lesson_name}, auditorium: {self.auditorium}, lecturer: {self.lecturer}"
                f"time: {self.time}, lesson_type {self.lesson_type}")


def get_group_names(schedule_res: list):
    groups = []

    for elem in schedule_res:
        groups.extend(list(elem.keys()))
    return groups


# ФУНКЦИЯ ДЛЯ ПАРСИНГА ТАБЛИЦЫ ПО ССЫЛКЕ БАКАЛАВРИАТА И МАГИСТРАТУРЫ ОЧНОЙ ФОРМЫ ОБУЧЕНИЯ
def transform_to_classes(schedule_res):
    groups = get_group_names(schedule_res)
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    res = []
    for i in range(len(groups)):
        cur_group = Group(groups[i])
        for j in week_days:
            for k in range(len(schedule_res[i][groups[i]][j]["lessons"])):
                cur_lesson = Lesson()
                cur_lesson.lesson_name = schedule_res[i][groups[i]][j]["lessons"][k]["name"]
                cur_lesson.time = schedule_res[i][groups[i]][j]["lessons"][k]["time"]
                cur_lesson.auditorium = schedule_res[i][groups[i]][j]["lessons"][k]["auditorium"]
                cur_lesson.lecturer = schedule_res[i][groups[i]][j]["lessons"][k]["lecturer"]
                cur_lesson.lesson_type = schedule_res[i][groups[i]][j]["lessons"][k]["lesson_type"]
                if j == "понедельник":
                    cur_group.monday.append(cur_lesson)
                if j == "вторник":
                    cur_group.tuesday.append(cur_lesson)
                if j == "среда":
                    cur_group.wednesday.append(cur_lesson)
                if j == "четверг":
                    cur_group.thursday.append(cur_lesson)
                if j == "пятница":
                    cur_group.friday.append(cur_lesson)
                if j == "суббота":
                    cur_group.saturday.append(cur_lesson)
                if j == "воскресенье":
                    cur_group.sunday.append(cur_lesson)
        res.append(cur_group)
    return res


# ФУНКЦИЯ ДЛЯ ПАРСИНГА ТАБЛИЦЫ ПО ССЫЛКЕ БАКАЛАВРИАТА И МАГИСТРАТУРЫ ОЧНОЙ ФОРМЫ ОБУЧЕНИЯ
def connect_to_tables(link, SAMPLE_RANGE_NAME, course):
    """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
    if course == "first":
        course = "1"
    if course == "second":
        course = "2"
    if course == "third":
        course = "3"
    if course == "fourth":
        course = "4"

    sheet_name = [course + " курс", course + " курс обновление ", course + " курс обновление"]
    SAMPLE_SPREADSHEET_ID = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", link).group(1)
    creds = None
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    try:
        service = build("sheets", "v4", credentials=creds)
        sheet_name = [course + " курс", course + " курс обновление ", course + " курс обновление"]

        # Запрос на получение информации о листах в таблице
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        needed_vers = 9
        # Проверка наличия конкретного листа по его имени
        sheet_found = False
        for sheet in sheets:
            # print(sheet['properties']['title'])
            if sheet['properties']['title'] == sheet_name[0]:
                sheet_found = True
                needed_vers = 0
                break
            elif sheet['properties']['title'] == sheet_name[1]:
                sheet_found = True
                needed_vers = 1
                break
            elif sheet['properties']['title'] == sheet_name[2]:
                sheet_found = True
                needed_vers = 2
                break

        if sheet_found:
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=sheet_name[needed_vers] + "!" + SAMPLE_RANGE_NAME)
                .execute()
            )
            values = result.get("values", [])

            if not values:
                raise NoValuesExeption("values was not found")

            return values
        else:
            raise No_such_sheet_exeption("Sheet was not found")
    except HttpError as err:
        print(err)


week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
dt_now = datetime.datetime.now()
months_of_year = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"}


# ФУНКЦИЯ ДЛЯ ПОИСКА ПО ПРЕДМЕТУ ДЛЯ ОЧНО-ЗАОЧНОЙ ФОРМЫ
def poisk_subject_OZ(spisok_, param_):
    for j in range(len(spisok_)):
        if spisok_[j][5].lower().find(param_.lower()) >= 0:
            answer = week_days[spisok_[j][1]] + " " + spisok_[j][2] + "\n"
            answer += spisok_[j][3] + " аудитория " + spisok_[j][4] + "\n"
            answer += spisok_[j][5].replace("\n", " ") + " (" + spisok_[j][6] + ")\n"
            answer += "преподаватель " + spisok_[j][7]
            lines = answer.split("\n")
            line1 = lines[0]
            line2 = lines[1]
            line3 = lines[2]
            line4 = lines[3]
            return (f"{line3} у вас в {line1} на {line2}, {line4}")
    return "Такой предмет не найден или он у вас уже был"


# ФУНКЦИЯ ДЛЯ ПОИСКА ПО ФАМИЛИИ ПРЕПОДАВАТЕЛЯ ДЛЯ ОЧНО-ЗАОЧНОЙ ФОРМЫ
def poisk_lector_OZ(spisok_, param_):
    for j in range(len(spisok_)):
        if spisok_[j][7].lower().find(param_.lower()) >= 0:
            answer = week_days[spisok_[j][1]] + " " + spisok_[j][2] + "\n"
            answer += spisok_[j][3] + " аудитория " + spisok_[j][4] + "\n"
            answer += spisok_[j][5].replace("\n", " ") + " (" + spisok_[j][6] + ")\n"
            answer += "преподаватель " + spisok_[j][7]
            lines = answer.split("\n")
            line1 = lines[0]
            line2 = lines[1]
            line3 = lines[2]
            line4 = lines[3]
            return (f"{line3} у вас в {line1} на {line2}, {line4}")
    return "Такой преподаватель не найден или пара с ним уже была"


# ФУНКЦИЯ ДЛЯ ПОИСКА ПО ДНЮ НЕДЕЛИ ДЛЯ ОЧНО-ЗАОЧНОЙ ФОРМЫ
def poisk_day_week_OZ(spisok_, param_):
    if param_ < 7:
        answer = ""
        flag = True
        for j in range(len(spisok_)):
            if flag:
                dat_tek = spisok_[j][0]
            else:
                if dat_tek == spisok_[j][0]:
                    answer += "\n\n"
                else:
                    lessons = answer.split("\n\n")
                    info = [week_days[param_], " у вас"]
                    for i in range(len(lessons)):
                        mass = lessons[i].split('\n')
                        info.append(mass[2])
                        info.append(mass[3])
                        if i != len(lessons) - 1:
                            info.append('потом')
                    return (' '.join(info))
            if spisok_[j][1] == param_:
                flag = False
                answer += week_days[spisok_[j][1]] + " (" + spisok_[j][0] + ") " + spisok_[j][2] + "\n"
                answer += spisok_[j][3] + " аудитория " + spisok_[j][4] + "\n"
                answer += spisok_[j][5].replace("\n", " ") + " (" + spisok_[j][6] + ")\n"
                answer += "преподаватель " + spisok_[j][7]
        return "В " + week_days[param_] + " у вас пар нет"
    else:
        return "В этот день у вас пар нет."


# ФУНКЦИЯ ДЛЯ ПОИСКА ПО ДАТЕ ДЛЯ ОЧНО-ЗАОЧНОЙ ФОРМЫ
def poisk_data_OZ(spisok_, data_z):
    answer = ""
    flag = True
    for j in range(len(spisok_)):
        if flag:
            dat_tek = spisok_[j][0]
        else:
            if dat_tek == spisok_[j][0]:
                answer += "\n\n"
            else:
                info = []
                lessons = answer.split("\n\n")
                info.append(str(data_z.day))
                info.append(months_of_year[data_z.month])
                info.append("у вас")
                for i in range(len(lessons)):
                    mass = lessons[i].split('\n')
                    info.append(mass[2])
                    info.append(mass[3])
                    if i != len(lessons) - 1:
                        info.append('потом')
                return ' '.join(info)
        if datetime.datetime.strptime(spisok_[j][0], "%Y-%m-%d %H:%M:%S") == data_z:
            flag = False
            answer += week_days[spisok_[j][1]] + " (" + spisok_[j][0] + ") " + spisok_[j][2] + "\n"
            answer += spisok_[j][3] + " аудитория " + spisok_[j][4] + "\n"
            answer += spisok_[j][5].replace("\n", " ") + " (" + spisok_[j][6] + ")\n"
            answer += "преподаватель " + spisok_[j][7]
        elif datetime.datetime.strptime(spisok_[j][0], "%Y-%m-%d %H:%M:%S") > data_z:
            answer += data_z.strftime('%d.%m.%Y') + " у вас пар нет\n"
            answer += "Следующий учебный день " + spisok_[j][0][0] + spisok_[j][0][1] + spisok_[j][0][2] + \
                      spisok_[j][0][3] + spisok_[j][0][4]
            return answer
    if len(answer) > 0:
        info = []
        lessons = answer.split("\n\n")
        info.append(str(data_z.day))
        info.append(months_of_year[data_z.month])
        info.append("у вас")
        for i in range(len(lessons)):
            mass = lessons[i].split('\n')
            info.append(mass[2])
            info.append(mass[3])
            if i != len(lessons) - 1:
                info.append('потом')
        return ' '.join(info)
    else:
        return data_z.strftime('%d.%m.%Y') + " у вас пар нет"


# ФУНКЦИЯ ДЛЯ ПОИСКА ДАТЫ(ИСПОЛЬЗУЕТСЯ ДЛЯ ПОИСКА ПО ДАТЕ)
def poisk_dat(i, values):
    if values[i][0] in week_days:
        return datetime.datetime.strptime(values[i + 1][0], "%d.%m.%Y")
    elif values[i - 1][0] in week_days:
        return datetime.datetime.strptime(values[i][0], "%d.%m.%Y")
    elif values[i + 1][0] in week_days:
        return datetime.datetime.strptime(values[i + 2][0], "%d.%m.%Y")
    elif values[i - 2][0] in week_days:
        return datetime.datetime.strptime(values[i - 1][0], "%d.%m.%Y")


# ФУНКЦИЯ ДЛЯ ПАРСИНГА ТАБЛИЦЫ ПО ССЫЛКЕ ДЛЯ ОЧНО-ЗАОЧНОЙ ФОРМЫ
def table_parsing_OZ(link, course) -> list:
    SAMPLE_RANGE_NAME = "A11:H1000"
    values = connect_to_tables(link, SAMPLE_RANGE_NAME, course)
    group_names = values[0][0][9:]
    pattern_for_date = r"\d{2}.\d{2}.\d{4}"
    b = 0
    for i in range(len(values)):
        if len(values[i]) != 8:
            continue
        if re.fullmatch(pattern_for_date, values[i][0]):
            if datetime.datetime.strptime(values[i][0], "%d.%m.%Y") < dt_now:
                continue
        else:
            continue
        b = i
        break
    if (values[b - 1][0] in week_days) and len(values[b - 1]) == 8:
        if len(values[b - 2]) == 8 and values[b - 2][0] == '':
            nn = b - 2
        else:
            nn = b - 1
    else:
        nn = b
    spisok = []
    for i in range(nn, len(values)):
        # дата, день недели, время, место, аудитория, наименование, вид занятий, преподаватель
        if len(values[i]) == 8:
            # установка даты занятий
            dat_ = poisk_dat(i, values)
            sp_ = [dat_, dat_.weekday(), values[i][1], values[i][3], values[i][4], values[i][5], values[i][6],
                   values[i][7]]
            spisok.append(sp_)
    return spisok


# ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ МОДУЛЯ
def quarter():
    today = datetime.date.today()

    if datetime.date(2024, 3, 25) <= today <= datetime.date(2024, 6, 20):
        return 4
    elif datetime.date(2023, 12, 21) <= today <= datetime.date(2024, 3, 24):
        return 3
    elif datetime.date(2023, 10, 25) <= today <= datetime.date(2023, 12, 20):
        return 2
    else:
        return 1


# ФУНКЦИЯ ДЛЯ ПАРСИНГА РАСПИСАНИЯ ПО ССЫЛКЕ ДЛЯ БАКАЛАВРИАТА И МАГИСТРАТУРЫ ОЧНОЙ ФОРМЫ
def table_parsing(link, course) -> tuple[list[dict[Any, dict[Any, Any]]], list[Any]]:
    if link is None:
        return None, None
    """
    Функция для получения массива из множества вложенных словарей

    :return: список, который имеет формат {"номер группы": {день недели: {"lessons":[]}}}
    """
    SAMPLE_RANGE_NAME = "B18:AD69"
    values = connect_to_tables(link, SAMPLE_RANGE_NAME, course)
    pattern = r'^[12].*$|2\dФМ'
    students_groups = []
    flag_of_group_arr = False
    for elem in values:
        if flag_of_group_arr:
            break
        for i in range(len(elem)):
            if re.fullmatch(pattern, elem[i]):
                students_groups.append(elem[i])
                flag_of_group_arr = True
    # print(students_groups)
    schedule_res = []
    for i in range(len(students_groups)):
        schedule_res.append({students_groups[i]: dict()})
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    # создаем основу для списка
    for i in range(len(students_groups)):
        schedule_res[i][students_groups[i]] = {"понедельник": {"lessons": []}, "вторник": {"lessons": []},
                                               "среда": {"lessons": []},
                                               "четверг": {"lessons": []}, "пятница": {"lessons": []},
                                               "суббота": {"lessons": []}, "воскресенье": {"lessons": []}}
    pattern_for_time = r"\d{2}:\d{2} \d{2}:\d{2}"
    empty_string_counter = 0
    cur_week_day = ""
    cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}

    pattern_of_auditorium = r'\d{3}|(\s*\d*\w*)\d{3}(\s*\d*\w*)|online|\d{3}[\d\s]*\d{3}|^\d{3}\s(?:Львов|Сорм|Кост)$'
    # вставляем предобработку строк, которая убирает дефисы и переводы строки
    for i in range(len(values)):
        for j in range(len(values[i])):
            values[i][j] = values[i][j].replace("\n", " ")
            values[i][j] = values[i][j].replace("-", " ")
    # print(values)
    for elem in values:
        cur_lesson_time = ""
        number_of_cur_group = 0
        for i in range(0, len(elem)):
            if empty_string_counter == 3:
                number_of_cur_group += 1
                empty_string_counter = 0
            if elem[i] in week_days:
                cur_week_day = elem[i]
            if re.fullmatch(pattern_for_time, elem[i]):
                cur_lesson_time = elem[i]
            if len(students_groups) == 1:
                cur_group = students_groups[0]
            if len(students_groups) != 1:
                # print(cur_week_day, cur_lesson_time)
                cur_group = students_groups[number_of_cur_group]
            if elem[i] == "" and i > 2:
                empty_string_counter += 1
            elif elem[i] != "":
                empty_string_counter = 0
                cur_lesson_dict["time"] = cur_lesson_time.strip()  # добавил
                if not re.fullmatch(pattern_of_auditorium, elem[i]):
                    cur_lesson_dict["name"] = elem[i].strip()
                if re.fullmatch(pattern_of_auditorium,
                                elem[i]):  # прописываем условие для ПИ, если идут 2 аудитории подряд
                    if i - 1 != -1 and re.fullmatch(pattern_of_auditorium, elem[i - 1]):
                        print("Ура баг")
                    else:
                        cur_lesson_dict["auditorium"] = elem[i].strip()

                        schedule_res[number_of_cur_group][cur_group][cur_week_day]["lessons"].append(cur_lesson_dict)
                        number_of_cur_group += 1
                        cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    groups = []
    for elem in schedule_res:
        groups.extend(list(elem.keys()))
    return schedule_res, groups


# ФУНКЦИЯ ДЛЯ ПАРСИНГА РАСПИСАНИЯ БАКАЛАВРИАТА И МАГИСТРАТУРЫ ОЧНОЙ ФОРМЫ ОБУЧЕНИЯ
def lessons_split(schedule_res: list, students_groups: list):
    if (schedule_res is None):
        return None
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    pattern_of_lecturer = r"\w+\s\w\.\w\.|\w+\s\w\.\w|\w+\s\w\.|\w\.\w\.\s\w+"
    pattern_of_lesson_name = r'\w{3,}'
    cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    pattern_of_lesson_type = r"лекция|семинар|НИС"
    for i in range(len(students_groups)):
        cur_group_num = i
        cur_group = students_groups[i]
        for cur_week_day in week_days:
            len_of_lessons_arr = len(schedule_res[i][cur_group][cur_week_day]["lessons"])
            for j in range(len_of_lessons_arr):

                if len((schedule_res[i][cur_group][cur_week_day]["lessons"][j][
                    "auditorium"]).split()) != 1:

                    cur_auditorium_list = (schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"]).split()

                    cur_lecturers_list = re.findall(pattern_of_lecturer,
                                                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    cur_lessons_name_list = re.split(pattern_of_lecturer,
                                                     schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    cur_time = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["time"]
                    del schedule_res[i][cur_group][cur_week_day]["lessons"][j]
                    for k in range(len(cur_auditorium_list)):  # сделать мб для одного тоже

                        if len(cur_lecturers_list) == 1:
                            cur_lecturer = cur_lecturers_list[0]
                        else:

                            if k < len(cur_lecturers_list):
                                cur_lecturer = cur_lecturers_list[k]
                            else:
                                cur_lecturer = ""

                        cur_lesson_type_match = re.search(pattern_of_lesson_type, cur_lessons_name_list[k])
                        cur_lesson_name_str = cur_lessons_name_list[k]
                        if cur_lecturer is not None:
                            cur_lesson_dict["lecturer"] = cur_lecturer
                        if cur_lesson_type_match is not None:
                            cur_lesson_dict["lesson_type"] = cur_lesson_type_match[0]
                            cur_lesson_name_str = cur_lesson_name_str.replace(cur_lesson_type_match[0], "")
                        cur_lesson_dict["name"] = cur_lesson_name_str

                        cur_lesson_dict["time"] = cur_time
                        cur_lesson_dict["auditorium"] = cur_auditorium_list[k]
                        schedule_res[cur_group_num][cur_group][cur_week_day]["lessons"].append(cur_lesson_dict)
                        cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    # print("-------------------", schedule_res)
    for i in range(len(students_groups)):  # разбиваем, если есть одна аудитория и несколько предметов
        cur_group = students_groups[i]
        for cur_week_day in week_days:
            for j in range(len(schedule_res[i][cur_group][cur_week_day]["lessons"])):
                name_l = re.split(pattern_of_lecturer, schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                name_l_without_emp_str = []
                for elem in name_l:
                    if len(elem) > 5 and elem[0:2] != " (" and elem[0:2] != " К" and not re.fullmatch(r' \d', elem[
                                                                                                              :2]):  # Заменил elem != ""
                        name_l_without_emp_str.append(elem)
                    # print(name_l_without_emp_str)
                if len(name_l_without_emp_str) == 2 and len((schedule_res[i][cur_group][cur_week_day]["lessons"][j][
                    "auditorium"]).split()) == 1:
                    # print(cur_group, cur_week_day, schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    cur_lecturers_list = re.findall(pattern_of_lecturer,
                                                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    for m in range(len(name_l_without_emp_str)):
                        cur_lesson_name_str = name_l_without_emp_str[m]
                        # print(cur_group, cur_week_day, cur_time)
                        if m < len(cur_lecturers_list):
                            cur_lecturer = cur_lecturers_list[m]
                        elif m == len(cur_lecturers_list):
                            cur_lecturer = cur_lecturers_list[m - 1]
                        cur_auditorium = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"]
                        cur_time = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["time"]
                        cur_lesson_dict = {"name": cur_lesson_name_str, "time": cur_time, "auditorium": cur_auditorium,
                                           "lecturer": cur_lecturer, "lesson_type": ""}
                        schedule_res[i][cur_group][cur_week_day]["lessons"].append(cur_lesson_dict)
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"] = ""
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["time"] = ""
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"] = ""
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lecturer"] = ""
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lesson_type"] = ""

    for i in range(len(students_groups)):  # разбиваем на преподов и типы предметов те ячейки, где один предмет
        cur_group_num = i
        cur_group = students_groups[i]
        for cur_week_day in week_days:
            for j in range(len(schedule_res[i][cur_group][cur_week_day]["lessons"])):
                if len((schedule_res[i][cur_group][cur_week_day]["lessons"][j][
                    "auditorium"]).split()) == 1:
                    cur_lesson_name_str = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"]
                    cur_lecturer_match = re.search(pattern_of_lecturer, cur_lesson_name_str)
                    cur_lesson_type_match = re.search(pattern_of_lesson_type, cur_lesson_name_str)
                    if cur_lesson_type_match is not None:
                        cur_lesson_name_str = cur_lesson_name_str.replace(cur_lesson_type_match[0], "")
                        schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lesson_type"] = cur_lesson_type_match[
                            0].strip()
                    if cur_lecturer_match is not None:
                        cur_lesson_name_str = cur_lesson_name_str.replace(cur_lecturer_match[0], "")
                        schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lecturer"] = cur_lecturer_match[
                            0].strip()
                    # сделать проверку на то, что нет названия предмета
                    # попробовать взять имя предыдущего

                    if re.search(pattern_of_lesson_name, cur_lesson_name_str) is None:
                        prev_lesson_name = schedule_res[i][cur_group][cur_week_day]["lessons"][j - 1]["name"].strip()

                        if re.search(pattern_of_lesson_name, prev_lesson_name) is not None:
                            prev_lesson_name = re.sub(r'[^а-яА-Я ]', "", prev_lesson_name)
                            cur_lesson_name_str = cur_lesson_name_str.strip() + prev_lesson_name.strip()
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"] = cur_lesson_name_str.strip()
    return schedule_res


# ФУНКЦИЯ ДЛЯ ИЗВЛЕЧЕНИЯ ССЫЛКИ
def take_a_link(module, direction, format_, level, course):
    if (direction is None or format_ is None or level is None or course is None):
        return None  # потенциальная ошибка, почему-то соблюдается условие
    html_page0 = urllib.request.urlopen("https://nnov.hse.ru/uch/schedule")
    soup0 = BeautifulSoup(html_page0, "lxml")
    make_response(text='Работаю')
    modules = []
    for link0 in soup0.select('.wdj-plashka a'):
        if 'занятий' in link0.get_text():
            href = link0.get('href')
            modules.append(href)

    html_page = urllib.request.urlopen(modules[module - 1])
    soup = BeautifulSoup(html_page, "lxml")

    timetables = []
    subjects = ['Design', 'InYas', 'Filology', 'FundLing', 'BI', 'CompNauki', 'Math', 'MathAndInf', 'PI', 'MBBE',
                'Business', 'Digital_marketing', 'Jurisprudence',
                'MBBE', 'Economics', '-', '-', '-', '-', '-', 'PriclAndTextLinguistics', 'FilologyPractics',
                'BusinessInf', 'IntAnalysis', 'MagMath', 'MagMarketing',
                'UprBusiness', 'UprOrg', 'UprRasvitiem', 'PravObespetch', 'BusAnalytics', 'Finances']
    for link in soup.select('.foldable_block__item a'):
        if 'курс' not in link.get_text():
            href = link.get('href')
            timetables.append(href)

    if format_ != 'ochno':
        groups = []
        sub = ['PI', 'Business', 'Jurisprudence', 'Business_Economics', 'Business_analiz']

        for i in range(15, 20):
            if direction == sub[i - 15]:
                html_page2 = urllib.request.urlopen(timetables[i])
                soup2 = BeautifulSoup(html_page2, "lxml")

                for link in soup2.select('[href*="spreadsheets"]'):
                    if 'график' not in link.get_text():
                        href = link.get('href')
                        groups.append(href)
        print(groups)

        if direction == sub[0]:
            groups.insert(1, groups.pop(3))
            groups.insert(2, groups.pop(3))
        elif direction == sub[2] or direction == sub[4]:
            groups.insert(0, '-')
            groups.insert(0, "-")
        courses = ['first', 'second', 'third', 'fourth']

        if (groups == []):
            return None

        for i in range(4):
            if courses[i] == course:
                return groups[i]  # выводим нужную ссылку

    # печатаем необходимую ссылку, если очка
    elif level == "bacalavriat":
        for i in range(0, 15):
            if direction == subjects[i]:
                return timetables[i]
    else:
        for i in range(20, 32):
            if direction == subjects[i]:
                return timetables[i]


# ФУНКЦИЯ ВОЗВРАЩЕНИЯ ОТВЕТА ПОЛЬЗОВАТЕЛЮ
def make_response(text, tts=None, session_state=None, user_state_update=None, end_session=None):
    response = {
        'text': text,
        'tts': tts if tts is not None else text

    }

    webhook_response = {
        'response': response,
        'version': '1.0',

    }
    if session_state is not None:
        webhook_response['session'] = state

    if end_session is not None:
        webhook_response['end_session'] = end_session  # заполняется, если был задан, по ключу

    if user_state_update is not None:  # заполняется если был задан
        webhook_response['user_state_update'] = user_state_update

    return webhook_response


# ФУНКЦИЯ ДЛЯ НАЧАЛА РЕГИСТРАЦИИ
def what_curs(event):
    text = "Я ещё не знаю, на каком курсе вы учитесь. Подскажете мне?"
    return make_response(text)


# ФУНКЦИЯ ДЛЯ ЗАВЕРШЕНИЯ СЕССИИ
def end_event(event):
    text = "Очень жаль! Увидимся в следующий раз"
    return make_response(text, end_session=True)


# ФАЛБЭК ФУНКЦИЯ
def fallback(event):
    return make_response(
        "Извините, я не поняла! Переформулируйте запрос, пожалуйста")


# ПЕРВАЯ ФУНКЦИЯ ДЛЯ РЕГИСТРАЦИИ
def what_level(event):
    intent = event['request']['nlu']['intents']
    curs = intent['course']['slots']['course']['value']
    curs_text = event['request']['original_utterance']
    event['user_state_update']: {'curs_for_search': curs}  # обновление состояния пользователя - был указан курс
    return make_response(text='Замечательно! Подскажите, вы учитесь на бакалавриате или магистратуре?',
                         user_state_update={'curs_for_search': curs, 'curs_text': curs_text})


# ВТОРАЯ ФУНКЦИЯ ДЛЯ РЕГИСТРАЦИИ
def what_direction(event):
    intent = event['request']['nlu']['intents']
    curs = intent['course']['slots']['course']['value']
    curs_text = event['request']['original_utterance']
    return make_response(
        text='Отлично! Теперь скажите направление и формат, на котором учитесь. Например, скажите: бакалавриат, бизнес-информатика, очно',
        user_state_update={'curs_for_search': curs, 'curs_text': curs_text})


# ФУНКЦИЯ ВЫЗОВА СПРАВКИ
def spravka(event):
    return make_response(
        "Привет, я помогу  узнать расписание основных дисциплин, если вы - студент Нижегородской Вышки. Например, вы хотите узнать расписание по философии. Скажите: Алиса, когда у меня философия? Или: Алиса, что у меня во вторник? Если хотите узнать, когда у вас пара с преподавателем, скажите, когда у меня пара с Владимиром Владимировым? Главное, чтобы фамилия была правильной. Также могу подсказать расписание по названию предмета. Чтобы поменять данные, скажи: хочу поменять данные.")


# ФУНКЦИЯ ДЛЯ СМЕНЫ ДАННЫХ
def change_data(event):
    return make_response(text="Данные обнулены. Назовите курс, на котором учитесь",
                         user_state_update={'curs_for_search': None, 'napravlenie_for_search': None,
                                            'level_for_search': None, 'group_for_search': None, 'day_today': None,
                                            'month_today': None, 'quater_today': None, 'format_for_search': None,
                                            'link': None})


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ПРЕДМЕТУ МАГИСТРАТУРЫ И БАКАЛАВРИАТА ОЧНЫХ ФОРМ ОБУЧЕНИЯ
def poisk_subject_M_B(schedule_, param_):
    day_d = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday"}
    # day_d = {0: "понедельник", 1: "вторник", 2: "среда", 3: "четверг", 4: "пятница", 5: "суббота"}
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    # Определяем текущую дату
    dt_now = datetime.datetime.now()
    # День недели
    dt_week = dt_now.weekday()
    dt_m = dt_now.month
    dt_d = dt_now.day

    for i in range(6):
        str_poisk = "schedule_." + day_d[(dt_week + i) % 6]
        for j in range(len(eval(str_poisk))):
            str_poisk_l = str_poisk + "[" + str(j) + "].lesson_name"
            if eval(str_poisk_l).lower().find(param_.lower()) >= 0:
                answer = week_days[(dt_week + i) % 6] + " " + eval(str_poisk + "[" + str(j) + "].time") + "\n"
                answer += eval(str_poisk_l).replace("\n", " ")
                return answer
    return "Такой предмет не найден"


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ДНЮ НЕДЕЛИ ДЛЯ МАГИСТРАТУРЫ И БАКАЛАВРИАТА ОЧНЫХ ФОРМ ОБУЧЕНИЯ
def poisk_day_week_M_B(schedule_, param_):
    day_d = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday"}
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    # Определяем текущую дату
    dt_now = datetime.datetime.now()
    # День недели
    dt_week = dt_now.weekday()
    dt_m = dt_now.month
    dt_d = dt_now.day

    if param_ < 6:
        str_poisk = "schedule_." + day_d[param_]
        if len(eval(str_poisk)) > 0:
            str_rez = week_days[param_] + "\n"
            for j in range(len(eval(str_poisk))):
                str_rez += str(j + 1) + " " + eval(str_poisk + "[" + str(j) + "].time") + " " + \
                           eval(str_poisk + "[" + str(j) + "].lesson_name").replace("\n", ' ') + "\n"
            return str_rez
        else:
            return "В этот день у вас пар нет"
    else:
        return "В этот день у вас пар нет"


# ФУНКЦИЯ ДЛЯ НАЧАЛА РАБОТЫ ФУНКЦИИ
def start_raspisanie(event):
    intent = event['request']['nlu']['intents']
    group = intent['what_group']['slots']['groups']['value']
    group_text = event['request']['original_utterance']
    return make_response(text='Отлично! Теперь можем начать. Что ты хочешь узнать?',
                         user_state_update={'group_for_search': group, 'group_text': group_text})


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ДАТЕ ДЛЯ МАГИСТРАТУРЫ И БАКАЛАВРИАТА ОБЧНЫХ ФОРМ ОБУЧЕНИЯ
def poisk_data_M_B(schedule_, d_n, data_z):
    day_d = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday"}
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    # Определяем текущую дату
    dt_now = datetime.datetime.now()
    # День недели
    dt_week = dt_now.weekday()
    dt_m = dt_now.month
    dt_d = dt_now.day

    if d_n < 6:
        str_poisk = "schedule_." + day_d[d_n]
        if len(eval(str_poisk)) > 0:
            str_rez = data_z.strftime('%d.%m.%y') + " " + week_days[d_n] + "\n"
            for j in range(len(eval(str_poisk))):
                str_rez += str(j + 1) + " " + eval(str_poisk + "[" + str(j) + "].time") + " " + \
                           eval(str_poisk + "[" + str(j) + "].lesson_name").replace("\n", ' ') + "\n"
            return str_rez
        else:
            return "В этот день у вас пар нет"
    else:
        return "В этот день у вас пар нет"


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ФАМИЛИИ ПРЕПОДАВАТЕЛЯ ДЛЯ МАГИСТРАТУРЫ И БАКАЛАВРИАТА ОЧНЫХ ФОРМ ОБУЧЕНИЯ
def poisk_lector_M_B(schedule_, param_):
    day_d = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday"}
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    # Определяем текущую дату
    dt_now = datetime.datetime.now()
    # День недели
    dt_week = dt_now.weekday()
    dt_m = dt_now.month
    dt_d = dt_now.day

    for i in range(6):
        str_poisk = "schedule_." + day_d[(dt_week + i) % 6]
        for j in range(len(eval(str_poisk))):
            # str_poisk_l = str_poisk + "." + str(j) + ".lecturer"
            str_poisk_l = str_poisk + "[" + str(j) + "].lecturer"  # переписал lesson_name
            if eval(str_poisk_l).lower().find(
                    param_.lower()) != -1:  # поменял if eval(str_poisk_l).lower().find(param_.lower()) > 0:
                answer = week_days[(dt_week + i) % 6] + " " + eval(str_poisk + "[" + str(j) + "].time") + "\n"
                answer += eval(str_poisk_l).replace("\n", " ")
                return answer
    return "Такой преподаватель не найден"


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ДНЮ НЕДЕЛИ
def start_rasp_with_weekday(event):
    group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
    weekday = event['request']['nlu']['intents']['when_weekday']['slots']['weekday']['value']
    zapros = "Запрос на расписание по дню недели. Код дня недели: " + str(weekday)
    intents = event['request'].get('nlu', {}).get('intents')  # интенты
    link = event.get('state').get('user', {}).get('link')
    form = event.get('state').get('user', {}).get('format_for_search')
    curs = event.get('state').get('user', {}).get('curs_for_search')

    schedule_arr_OZ = event.get('state').get('user', {}).get('schedule_arr_OZ')

    if form == "ochnozaochno":
        day_week = int(zapros[-1]) - 1
        spisok = schedule_arr_OZ
        answer = poisk_day_week_OZ(spisok, day_week)

    elif form == "ochno":
        schedule_arr = transform_to_classes(lessons_split(table_parsing(link, curs)[0],
                                                          table_parsing(link, curs)[1]))
        cur_group_schedule = schedule_arr[int(group) - 1]
        day_week = int(zapros[-1]) - 1
        answer = poisk_day_week_M_B(cur_group_schedule, day_week)

    return make_response(text=answer)


# ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ПРАЗДНИКОВ ПО ДАТЕ
def is_holidays(month, date):
    arr = ["0803", "2302", "3112", "0101", "0201", "0301", "0401", "0501", "0601", "0701", "0801", "0901", "0905"]
    for a in arr:
        if (date == a):
            return 1
    if (month == "07" or month == "08"):
        return 1

    return 0


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ДАТЕ
def start_rasp_with_date(event):
    group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
    day = event['request']['nlu']['intents']['when_date']['slots']['date']['value']['day']
    form = event.get('state').get('user', {}).get('format_for_search')
    day_relative = event['request']['nlu']['intents']['when_date']['slots']['date']['value']['day_is_relative']
    schedule_arr_OZ = event.get('state').get('user', {}).get('schedule_arr_OZ')
    curs = event.get('state').get('user', {}).get('curs_for_search')
    date_today = "ddmm"
    date_for_search = "ddmm"
    day_for_search = "dd"
    month_for_search = "mm"

    # нужно привести все данные к формату DDMM:

    if (day_relative is True):  # если запрос формата завтра/послезавтра
        date_today = datetime.datetime.now()
        relative_days = datetime.timedelta(day)
        date_for_search = date_today + relative_days

        day_today = str(date_today.day)
        month_today = str(date_today.month)
        day_for_search = str(date_for_search.day)
        month_for_search = str(date_for_search.month)

        if (len(day_today) is 1):
            day_today = "0" + day_today
        if (len(month_today) is 1):
            month_today = "0" + month_today
        if (len(day_for_search) is 1):
            day_for_search = "0" + day_for_search
        if (len(month_for_search) is 1):
            month_for_search = "0" + month_for_search

        date_today = day_today + month_today
        date_for_search = day_for_search + month_for_search

    elif (day_relative is False):  # если запрос формата "что будет пятого марта"
        month = event['request']['nlu']['intents']['when_date']['slots']['date']['value']['month']
        day = str(day)
        month = str(month)
        if (len(day) is 1):
            day = "0" + day
        if (len(month) is 1):
            month = "0" + month

        day_for_search = day
        month_for_search = month
        date_for_search = day + month

    a = is_holidays(month_for_search, date_for_search)  # проверяем, является ли указанная дата праздником

    if (a is 1):
        text = "В этот день точно нет пар!"
        return make_response(text)

    else:
        if form == "ochnozaochno":
            zapros = str(day) + " - запрос на получение расписания по дате, " + str(
                date_today) + " - день сегодня, " + str(
                date_for_search) + " - искомая дата"
            data_zapros = zapros[(zapros.find(" - искомая дата") - 4):(zapros.find(" - искомая дата"))]
            zapros_d = int(data_zapros[:2])
            zapros_m = int(data_zapros[2:])
            zapros_y = dt_now.year
            zapros_data = (datetime.datetime(zapros_y, zapros_m, zapros_d, 0, 0))
            spisok = schedule_arr_OZ
            text = poisk_data_OZ(spisok, zapros_data)

        elif form == "ochno":

            intents = event['request'].get('nlu', {}).get('intents')  # интенты
            group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
            level = event.get('state').get('user', {}).get(
                'level_for_search')  # какой уровень образования у пользователя
            napravlenie = event.get('state').get('user', {}).get('napravlenie_for_search')
            link = event.get('state').get('user', {}).get('link')
            form = event.get('state').get('user', {}).get('format_for_search')

            schedule_arr = transform_to_classes(lessons_split(table_parsing(link, curs)[0],
                                                              table_parsing(link, curs)[1]))

            cur_group_schedule = schedule_arr[int(group) - 1]

            zapros = str(day) + " - запрос на получение расписания по дате, " + str(
                date_today) + " - день сегодня, " + str(
                date_for_search) + " - искомая дата"
            data_zapros = zapros[(zapros.find(" - искомая дата") - 4):(zapros.find(" - искомая дата"))]
            zapros_d = int(data_zapros[:2])
            zapros_m = int(data_zapros[2:])
            zapros_y = dt_now.year
            zapros_data = datetime.date(zapros_y, zapros_m, zapros_d)
            zapros_d_w = zapros_data.weekday()

            text = poisk_data_M_B(cur_group_schedule, zapros_d_w, zapros_data)

        return make_response(text)


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО ФАМИЛИИ ПРЕПОДАВАТЕЛЯ
def start_rasp_with_master(event):
    group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
    form = event.get('state').get('user', {}).get('format_for_search')
    intent = event['request']['nlu']['intents']
    master_surname = intent['when_master']['slots']['surname']['value']['last_name']
    schedule_arr_OZ = event.get('state').get('user', {}).get('schedule_arr_OZ')
    zapros = master_surname + " - запрос на получение расписания по фамилии преподавателя"
    curs = event.get('state').get('user', {}).get('curs_for_search')
    lector = zapros[:zapros.find(" -")]

    if form == "ochnozaochno":
        lector = zapros[:zapros.find(" -")]
        spisok = schedule_arr_OZ
        answer = poisk_lector_OZ(spisok, lector)
    elif form == "ochno":

        intents = event['request'].get('nlu', {}).get('intents')  # интенты
        group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
        level = event.get('state').get('user', {}).get('level_for_search')  # какой уровень образования у пользователя
        napravlenie = event.get('state').get('user', {}).get('napravlenie_for_search')
        link = event.get('state').get('user', {}).get('link')
        form = event.get('state').get('user', {}).get('format_for_search')

        schedule_arr = transform_to_classes(lessons_split(table_parsing(link, curs)[0],
                                                          table_parsing(link, curs)[1]))

        cur_group_schedule = schedule_arr[int(group) - 1]
        answer = poisk_lector_M_B(cur_group_schedule, lector)

    return make_response(text=answer)


# ФУНКЦИЯ ДЛЯ ПОИСКА РАСПИСАНИЯ ПО НАЗВАНИЮ ПРЕДМЕТА
def start_rasp_sub(event):
    group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
    sub = event['request'].get('nlu', {}).get('tokens')[-1]
    zapros = sub + " -  запрос на расписание по названию предмета"
    subject = zapros[:zapros.find(" -")]
    intents = event['request'].get('nlu', {}).get('intents')  # интенты
    form = event.get('state').get('user', {}).get('format_for_search')
    schedule_arr_OZ = event.get('state').get('user', {}).get('schedule_arr_OZ')
    curs = event.get('state').get('user', {}).get('curs_for_search')
    link = event.get('state').get('user', {}).get('link')
    if form == "ochnozaochno":
        subject = zapros[:zapros.find(" -")]
        spisok = schedule_arr_OZ
        answer = poisk_subject_OZ(spisok, subject)

    elif form == "ochno":
        schedule_arr = transform_to_classes(lessons_split(table_parsing(link, curs)[0],
                                                          table_parsing(link, curs)[1]))
        cur_group_schedule = schedule_arr[int(group) - 1]
        answer = poisk_subject_M_B(cur_group_schedule, subject)

    return make_response(text=answer)


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ
def news_title(type_chose):  # когда скажет какую-нибудь из рубрик
    if type_chose != 'Postupaushim' and type_chose != 'Obrazovsnie' and type_chose != 'Nauka' and type_chose != 'Expertiza' and type_chose != 'Obshestvo' and type_chose != 'SvobodnoeObshenie' and type_chose != 'UniversitetZizn' and type_chose != 'Prioritet2030' and type_chose != 'ProgRasv2030' and type_chose != 'VseNovosti':
        return make_response(text='Такой рубрики нет. Попробуй, пожалуйста, еще раз.')

    types_t = ['Postupaushim', 'Obrazovsnie', 'Nauka', 'Expertiza', 'Obshestvo', 'SvobodnoeObshenie', 'UniversitetZizn',
               'Prioritet2030', 'ProgRasv2030']
    types_tt = ['Поступающим', 'Образование', 'Наука', 'Экспертиза', 'Общество', 'Свободное общение',
                'Университетская жизнь',
                'Приоритет 2030', 'Программа развития 2030']
    # type_chose = input() #(эта переменная дальше нужна для работы, сохраняем ее) тут будет одна из рубрик
    for i in range(len(types_t)):
        if types_t[i] == type_chose:
            type_chose_ = i + 1
            break
        elif type_chose == 'VseNovosti':
            type_chose_ = 10
            break
    if type_chose == 8:
        amount_news = 1
    elif type_chose == 9:
        amount_news = 2
    else:
        amount_news = 7

    html_page_news = urllib.request.urlopen("https://nnov.hse.ru/news/")
    soup = BeautifulSoup(html_page_news, "lxml")
    types_l = []  # переменная для ссылок на рубрики новостей

    for link in soup.find_all('a'):
        if link.get_text() in types_tt and len(types_l) < 9:
            href = link.get('href')

            types_l.append(href)  # заполнили список ссылками на стр с разными рубриками новостей

    if type_chose_ < 10:
        html_page_news1 = urllib.request.urlopen(types_l[type_chose_ - 1])
        soup2 = BeautifulSoup(html_page_news1, "lxml")
    else:  # создаем объект под опред страничку с новостями
        html_page_news1 = html_page_news
        soup2 = soup

    headings_l = []  # для заголовков ссылок на опред новость конкретной рубрики
    headings_t = []  # для заголовков названий опред новостей конкретной рубрики
    subs = []  # для краткого содержания новости
    for link in soup2.select('h2.first_child'):
        if len(headings_t) < amount_news:
            text = link.get_text()
            headings_t.append(text)  # заполнили названиями заголовков

    for link in soup2.find_all('a'):
        if link.get_text() in headings_t and len(headings_l) < amount_news:
            href = link.get('href')
            headings_l.append(href)  # заполнили список ссылками на стр с конкретными новостей

    for link in soup2.select('div.post__text'):
        text = link.get_text()
        if text != '' and len(subs) < amount_news:
            subs.append(text)  # заполнили кратким содержанием выбранных новостей

    return headings_t, headings_l, subs, len(headings_t)


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ - НАЧАЛО НОВОСТЕЙ
def start_news(event):
    TEXT1 = "Привет! Я расскажу тебе о последних новостях Высшей Школы Экономики. Если готов начать, скажи 'Покажи рубрики/Рубрики'"
    return make_response(TEXT1)  # выводим пользователю


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ - ПОКАЗ РУБРИК
def sh_rubrics(event):
    # принимаем 'покажи рубрики' и запускаем эту функцию (эта переменная не нужна дальше для работы)
    one = "Давай определимся по какой рубрике ты хочешь узнать новость."
    two = "1.Поступающим, 2.Образование, 3.Наука, 4.Экспертиза, 5.Общество, 6.Свободное общение, 7.Университетская жизнь, 8.Приоритет 2030, 9.Программа развития 2030, 10.Все новости"
    three = "Скажи, пожалуйста, название выбранной рубрики:"
    TEXT2 = f'{one} \n{two} \n{three}'
    return make_response(TEXT2)  # выводим пользователю


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ - ПОКАЗ ЗАГОЛОВКОЙ ПО ВЫБРАННОЙ РУБРИКЕ
def headings(event):
    intent = event['request']['nlu']['intents']
    if ('news_title' in intent):
        type_chose = intent['news_title']['slots']['rubrics']['value']
    else:
        type_chose = event.get('state').get('user', {}).get('type_chose')

    headings_t, headings_l, subs, number_of_news = news_title(type_chose)  # сказал название конкретной рубрики

    TEXT4 = "Отлично! Показываю тебе названия последних заголовков новостей по выбранной рубрике:"
    headings = ''

    for i in range(len(headings_t)):
        headings += str(i + 1) + '. ' + str(headings_t[i]) + '\n'
    TEXT4 += '\n' + headings + "\n" + 'Назови цифру новости, которую хочешь прочитать: '  # выводим пользователю (Тут в интентах надо добавить цифру от 1 до 7)
    return make_response(text=TEXT4,
                         user_state_update={'headings_t': headings_t, 'headings_l': headings_l, 'subs': subs,
                                            'type_chose': type_chose,
                                            'number_of_news': number_of_news})  # выводим пользователю


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ - ПОКАЗ НОВОСТИ
def res_news(event):  # когда пользователь называет цифру

    intent = event['request']['nlu']['intents']
    title_chose = intent['res_news']['slots']['number']['value']
    headings_t = event.get('state').get('user', {}).get('headings_t')
    headings_l = event.get('state').get('user', {}).get('headings_l')
    subs = event.get('state').get('user', {}).get('subs')
    number_of_news = event.get('state').get('user', {}).get('number_of_news')

    if title_chose < 1 or title_chose > number_of_news:
        return make_response("Новости под такой цифрой нет. Назови, пожалуйста, цифру из тех, которые есть.")

    res_link = headings_l[title_chose - 1]
    title = headings_t[title_chose - 1]
    sub = subs[title_chose - 1]
    TEXT5 = f'Отлично! Показываю новость: \n{title}: \n{sub} \nТакже даю ссылку, если хочешь ознакомиться с новостью подробнее и посмотреть картинки: {res_link} \nЕсли хочешь посмотреть еще другую новость, скажи "Хочу посмотреть другую новость"'
    return make_response(TEXT5)  # выводим пользователю


# ФУНКЦИЯ ДЛЯ НОВОСТЕЙ - ПРОДОЛЖЕНИЕ НОВОСТЕЙ
def contin_news(event):
    TEXT9 = "Супер! Если хочешь посмотреть новость из этой рубрики, скажи 'Эта', если нет, то 'Другая'"
    return make_response(TEXT9)  # выводим пользователю


# ОСНОВНАЯ ФУНКЦИЯ ДЛЯ РАБОТЫ НАВЫКА
def handler(event, context):
    intents = event['request'].get('nlu', {}).get('intents')  # интенты
    form = event.get('state').get('user', {}).get('format_for_search')
    curs = event.get('state').get('user', {}).get('curs_for_search')  # какой курс у пользователя
    group = event.get('state').get('user', {}).get('group_for_search')  # какая группа у пользователя
    level = event.get('state').get('user', {}).get('level_for_search')  # какой уровень образования у пользователя
    level_text = event.get('state').get('user', {}).get('level_text')
    group_text = event.get('state').get('user', {}).get('group_text')
    curs_text = event.get('state').get('user', {}).get('curs_text')
    napravlenie = event.get('state').get('user', {}).get('napravlenie_for_search')
    napr_text = event.get('state').get('user', {}).get('napr_text')

    if event['session']['new']:

        if (napravlenie is not None and curs is not None and level is not None and form is not None):
            link = take_a_link(quarter(), napravlenie, form, level, curs)
            schedule_arr = []
            if form == "ochnozaochno":
                schedule_arr_OZ = table_parsing_OZ(link, curs)
            elif form == "ochno":
                schedule_arr_OZ = []


        else:
            link = []
            schedule_arr_OZ = []

        txt = "Привет! Я подскажу расписание ВШЭ. Чтобы подробнее узнать о том, что я умею, ты можешь попросить меня показать справку."

        return make_response(
            text=txt,
            tts="Привет! <speaker audio='dialogs-upload/05d0273d-97bb-45de-a2c5-52b00fa2ec70/54db7e77-f45c-457e-9b8a-143a0515d47c.opus'> sil <[1500]> Я подскажу расписание Высшей Школы Экономики. Чтобы подробнее узнать о том, что я умею, ты можешь попросить меня показать справку.",
            user_state_update={'link': link, 'schedule_arr_OZ': schedule_arr_OZ})



    elif 'when_master' in intents and 'when_subject' in intents:  # путает преподавателя с назанием предмета - вызываются обе функции, если не сделать такое условие
        if (napravlenie is None or curs is None or group is None or level is None):
            return make_response(text="Стой, мы же пока не знакомы! Для начала скажи, на каком курсе ты учишься?");
        else:
            return start_rasp_with_master(event)

    elif 'when_subject' in intents:

        if (napravlenie is None or curs is None or group is None or level is None):
            return make_response(text="Стой, мы же пока не знакомы! Для начала скажи, на каком курсе ты учишься?");
        else:
            return start_rasp_sub(event)  # запускается Настина функция добавил make_response

    elif 'when_date' in intents:
        if (napravlenie is None or curs is None or group is None or level is None):
            return make_response(text="Стой, мы же пока не знакомы! Для начала скажи, на каком курсе ты учишься?");
        else:
            return start_rasp_with_date(event)

    elif 'when_weekday' in intents:
        if (napravlenie is None or curs is None or group is None or level is None):
            return make_response(text="Стой, мы же пока не знакомы! Для начала скажи, на каком курсе ты учишься?");
        else:
            return start_rasp_with_weekday(event)



    elif 'course' in intents and curs is None:  # если в запросе пользователя есть номер курса
        return what_direction(event)


    elif 'direction' in intents and napravlenie is None:
        intent = event['request']['nlu']['intents']
        napravlenie = intent['direction']['slots']['direction']['value']
        napr_text = event['request']['original_utterance']
        form = intent['direction']['slots']['format']['value']
        level = intent['direction']['slots']['level']['value']
        curs = event.get('state').get('user', {}).get('curs_for_search')
        if (form == 'ochno'):
            link = take_a_link(quarter(), napravlenie, form, level, curs)
            if (link is None):
                return make_response(text="Упс! Я не нашла нужную ссылку на сайте. Давай попробуем ещё раз!")
            schedule_arr_OZ = []

        elif (form == 'ochnozaochno'):
            link = take_a_link(quarter(), napravlenie, form, level, curs)
            if (link is None):
                return make_response(text="Упс! Я не нашла нужную ссылку на сайте. Давай попробуем ещё раз!")
            schedule_arr_OZ = table_parsing_OZ(link, curs)

        if (form == 'zaochno'):
            return make_response(
                text="Ой! Я пока не умею работать с заочным форматом обучения. Я не могу подсказать расписание, но зато могу рассказать интересные новости! Чтобы послушать новость, скажи: Покажи новости")

        return make_response(text='Внимательно запоминаю информацию. Последний вопрос - в какой группе ты учишься?',
                             user_state_update={'napravlenie_for_search': napravlenie, 'napr_text': napr_text,
                                                'format_for_search': form, 'level_for_search': level,
                                                'link': link,
                                                'schedule_arr_OZ': schedule_arr_OZ})  # если в запросе есть направление


    elif 'what_group' in intents and group is None:
        return start_raspisanie(event)




    elif ('course' in intents and curs is not None) or ('direction' in intents and napravlenie is not None) or (
            'what_group' in intents and group is not None) or ('what_level' in intents and level is not None) or (
            'what_format' in intents and form is not None):  # если пользователь называет данные, которые уже есть
        if (curs is None):
            c = ' '
        else:
            c = curs_text

        if (napravlenie is None):
            n = ' '
        else:
            n = napr_text

        if (group is None):
            g = ' '
        else:
            g = group_text

        return make_response("Кажется, вы уже рассказали мне о себе! Вы учитесь " +
                             c + " курсе,  " + n + " " +
                             g + " группе? Если хотите поменять данные или данные заполнены не полностью, скажите: поменять данные")



    elif 'change_data' in intents:  # запрос на смену данных
        return change_data(event)

    elif 'end_rasp' in intents:  # выход из функции
        return end_event(event)

    elif 'what_you_can' in intents:  # справка
        return spravka(event)

    elif 'start_news' in intents:
        return start_news(event)

    elif 'sh_rubrics' in intents:
        return sh_rubrics(event)

    elif 'news_title' in intents or 'headings' in intents:
        return headings(event)

    elif 'res_news' in intents:
        return res_news(event)

    elif 'contin_news' in intents:
        return contin_news(event)

    else:  # если непонятно, что сказал пользователь
        return fallback(event)

    return {
        'response': {
            'text': text,

        },
        'version': '1.0',
    }


"""s = lessons_split(table_parsing("https://docs.google.com/spreadsheets/d/15usRviduMkviOrNBhEla4e8AcT843fQUsMExQRD3KIE/edit#gid=1914181397")[0],
                                         table_parsing("https://docs.google.com/spreadsheets/d/15usRviduMkviOrNBhEla4e8AcT843fQUsMExQRD3KIE/edit#gid=1914181397")[1])
print(s)"""
