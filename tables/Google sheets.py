import os.path
import pickle
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
#БИ 1VtfOS3n9kus2O_8dm7D85ktvlS4vA9hV_RCICo2v5v4
# The ID and range of a sample spreadsheet.
# МББЭ 1305APD5kjZsE87yNSbORMDuDWF3QFjtDBqswHYD1dc0
# КНТ 1bNCPfD6I_81VrTs6Jgm922pg1ASvKtQnK4igOOsulfM
SAMPLE_SPREADSHEET_ID = "1VtfOS3n9kus2O_8dm7D85ktvlS4vA9hV_RCICo2v5v4"
SAMPLE_RANGE_NAME = "B18:AD69"  # придется парсить название листа


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

    def __str__(self):
        return self.group_name


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

def main():
    """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

    except HttpError as err:
        print(err)
    return values


def table_parsing() -> list:
    """
    Функция для получения массива из множества вложенных словарей

    :return: список, который имеет формат {"номер группы": {день недели: {"lessons":[]}}}
    """
    values = main()
    print(values)
    pattern = r'^[12].*\d$'
    students_groups = []
    flag_of_group_arr = False
    for elem in values:
        if flag_of_group_arr:
            break
        for i in range(len(elem)):
            if re.fullmatch(pattern, elem[i]):
                students_groups.append(elem[i])
                flag_of_group_arr = True
    print(students_groups)
    schedule_res = []
    for i in range(len(students_groups)):
        schedule_res.append({students_groups[i]: dict()})
    #print("----------------------------------")
    #print(schedule_res)
    #print("----------------------------------")

    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    for i in range(len(students_groups)):
        schedule_res[i][students_groups[i]] = {"понедельник": {"lessons": []}, "вторник": {"lessons": []},
                                               "среда": {"lessons": []},
                                               "четверг": {"lessons": []}, "пятница": {"lessons": []},
                                               "суббота": {"lessons": []}, "воскресенье": {"lessons": []}}

    #print(schedule_res)
   # print(values)

    pattern_for_classroom = r'\d{3}'
    pattern_for_time = r"\d{2}:\d{2} \d{2}:\d{2}"
    number_of_cur_group = 0

    empty_string_counter = 0
    cur_week_day = ""
    cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    #pattern_of_auditorium = r"\d{3}|\d{3}(\s*\d*)*"
    pattern_of_auditorium = r'\d{3}|(\s*\d*\w*)\d{3}(\s*\d*\w*)|online'
    pattern_of_lecturer = r"\w+\s\w\.\w\."
    #print("-------------------------------------")
    #print(schedule_res[0]["22БИ1"]["понедельник"]["lessons"].append(cur_lesson_dict))
    #print(schedule_res)
    schedule_res_classes_version = []
    #print("-------------------------------------")
    cur_lesson_class = Lesson()
    # вставляем предобработку строк, которая убирает дефисы и переводы строки
    for i in range(len(values)):
        for j in range(len(values[i])):
            values[i][j] = values[i][j].replace("\n", " ")
            values[i][j] = values[i][j].replace("-", " ")
    for elem in values:
        cur_lesson_time = ""
        number_of_cur_group = 0
        for i in range(0, len(elem)):

            if empty_string_counter == 3:
                number_of_cur_group += 1
                empty_string_counter = 0
            if elem[i] in week_days:
                cur_week_day = elem[i]

                #append cur lesson dict
            if re.fullmatch(pattern_for_time, elem[i]):
                cur_lesson_time = elem[i]

            cur_group = students_groups[number_of_cur_group]
            cur_group_class = Group(students_groups[number_of_cur_group])

            if elem[i] == "":
                empty_string_counter += 1
            elif elem[i] != "":  #потенциальные проблемы
                empty_string_counter = 0
                cur_lesson_dict["time"] = cur_lesson_time.strip() #добавил
                cur_lesson_class.time = cur_lesson_time
                if not re.fullmatch(pattern_of_auditorium, elem[i]):
                    cur_lesson_dict["name"] = elem[i].strip()  #нужно довавить после обрезки в конце
                    cur_lesson_class.lesson_name = elem[i]
                if re.fullmatch(pattern_of_auditorium, elem[i]):
                    cur_lesson_dict["auditorium"] = elem[i].strip()
                    cur_lesson_class.auditorium = elem[i]

                    schedule_res[number_of_cur_group][cur_group][cur_week_day]["lessons"].append(cur_lesson_dict)
                    if cur_week_day == "понедельник":
                        cur_group_class.monday.append(cur_lesson_class)

                    if cur_week_day == "вторник":
                        cur_group_class.tuesday.append(cur_lesson_class)

                    if cur_week_day == "среда":
                        cur_group_class.wednesday.append(cur_lesson_class)

                    if cur_week_day == "четверг":
                        cur_group_class.thursday.append(cur_lesson_class)

                    if cur_week_day == "пятница":
                        cur_group_class.friday.append(cur_lesson_class)

                    if cur_week_day == "суббота":
                        cur_group_class.saturday.append(cur_lesson_class)

                    if cur_week_day == "воскресенье":
                        cur_group_class.sunday.append(cur_lesson_class)

                    schedule_res_classes_version.append(cur_group_class)
                    cur_lesson_class = Lesson()
                    number_of_cur_group += 1
                    cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    return schedule_res


def lessons_split(schedule_res: list, students_groups: list):  #функция для разделения нескольких пар, не допилил
    #включить strip для пробелов
    week_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
    pattern_of_lecturer = r"\w+\s\w\.\w\.|\w+\s\w\.\w"
    pattern_of_lesson_name = r'\w{3,}'

    cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    pattern_of_lesson_type = r"лекция|семинар|НИС"  #возможно расширить число паттернов
    for i in range(len(students_groups)):
        cur_group_num = i
        cur_group = students_groups[i]
        for cur_week_day in week_days:
            len_of_lessons_arr = len(schedule_res[i][cur_group][cur_week_day]["lessons"])
            for j in range(len_of_lessons_arr): #пробуем изменить длину и взять как переменную тут гле-то ошибка
                if len((schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"]).split()) != 1:
                    cur_auditorium_list = (schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"]).split()
                    cur_lecturers_list = re.findall(pattern_of_lecturer, schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    cur_lessons_name_list = re.split(pattern_of_lecturer, schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"])
                    cur_time = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["time"]
                    del schedule_res[i][cur_group][cur_week_day]["lessons"][j]
                    for k in range(len(cur_auditorium_list)): # мб сделать для нескольких аудиторий и для 1 
                        cur_lecturer = cur_lecturers_list[k]
                        cur_lesson_type_match = re.search(pattern_of_lesson_type, cur_lessons_name_list[k])
                        cur_lesson_name_str = cur_lessons_name_list[k]
                        if cur_lecturer is not None:
                            cur_lesson_dict["lecturer"] = cur_lecturer
                        if cur_lesson_type_match is not None:
                            cur_lesson_dict["lesson_type"] = cur_lesson_type_match[0]
                            cur_lesson_name_str = cur_lesson_name_str.replace(cur_lesson_type_match[0], "")
                        cur_lesson_dict["name"] = cur_lesson_name_str  #добавляем после преобразования
                        #нужно преобразовать строку, чтобы она не содеражала пробелов, тире и тп
                        cur_lesson_dict["time"] = cur_time
                        cur_lesson_dict["auditorium"] = cur_auditorium_list[k]
                        schedule_res[cur_group_num][cur_group][cur_week_day]["lessons"].append(cur_lesson_dict)
                        cur_lesson_dict = {"name": "", "time": "", "auditorium": "", "lecturer": "", "lesson_type": ""}
    for i in range(len(students_groups)): #разбиваем на преподов и типы предметов те ячейки, где один предмет
        cur_group_num = i
        cur_group = students_groups[i]
        for cur_week_day in week_days:
            for j in range(len(schedule_res[i][cur_group][cur_week_day]["lessons"])):
                if len((schedule_res[i][cur_group][cur_week_day]["lessons"][j]["auditorium"]).split()) == 1:
                    cur_lesson_name_str = schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"]
                    cur_lecturer_match = re.search(pattern_of_lecturer, cur_lesson_name_str)
                    cur_lesson_type_match = re.search(pattern_of_lesson_type, cur_lesson_name_str)
                    if cur_lesson_type_match is not None:
                        cur_lesson_name_str = cur_lesson_name_str.replace(cur_lesson_type_match[0], "")
                        schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lesson_type"] = cur_lesson_type_match[0].strip()
                    if cur_lecturer_match is not None:
                        cur_lesson_name_str = cur_lesson_name_str.replace(cur_lecturer_match[0], "")
                        schedule_res[i][cur_group][cur_week_day]["lessons"][j]["lecturer"] = cur_lecturer_match[0].strip()
                    #сделать проверку на то, что нет названия предмета
                    #попробовать взять имя предыдущего

                    if re.search(pattern_of_lesson_name, cur_lesson_name_str) is None:
                        prev_lesson_name = schedule_res[i][cur_group][cur_week_day]["lessons"][j - 1]["name"].strip()

                        if re.search(pattern_of_lesson_name, prev_lesson_name) is not None:
                            prev_lesson_name = re.sub(r'[^а-яА-Я ]', "", prev_lesson_name)
                            cur_lesson_name_str = cur_lesson_name_str.strip() + prev_lesson_name.strip()
                            #print(cur_lesson_name_str, "-----------------")
                    schedule_res[i][cur_group][cur_week_day]["lessons"][j]["name"] = cur_lesson_name_str.strip()

    return schedule_res


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




def get_group_names(schedule_res: list):  #использовал для отладки
    groups = []

    for elem in schedule_res:
        groups.extend(list(elem.keys()))
    return groups


schedule_res = table_parsing()
students_groups = get_group_names(schedule_res)
schedule_res = lessons_split(schedule_res, students_groups)
print(schedule_res)

