import requests

from environs import env
from terminaltables import AsciiTable

POPULAR_LANGUAGES = [
    "JavaScript",
    "Java",
    "Python",
    "Ruby",
    "PHP",
    "C++",
    "C#",
    "C",
]


def predict_rub_salary(salary_min, salary_max):
    if salary_min and salary_max:
        return int((salary_min + salary_max) / 2)
    elif salary_min:
        return int(salary_min) * 1.2
    elif salary_max:
        return int(salary_max) * 0.8


def predict_rub_salary_hh(vacancy):
    if vacancy and vacancy["currency"] == "RUR":
        return predict_rub_salary(vacancy["from"], vacancy["to"])


def predict_rub_salary_superjob(vacancy):
    if vacancy and vacancy["currency"] == "rub":
        return predict_rub_salary(vacancy["payment_from"], vacancy["payment_to"])


def get_salary_statistic_hh():
    url = "https://api.hh.ru/vacancies"
    salary_statistic = dict()
    moscow_area = 1
    count_days = 30
    vacancies_count = 100
    for language in POPULAR_LANGUAGES:
        payload = {
            "text": f"Программист {language}",
            "area": moscow_area,
            "period": count_days,
            "per_page": vacancies_count,
        }
        vacancies_processed = 0
        total_salary = 0
        page = 0
        total_pages = 1
        while page < total_pages:
            payload["page"] = page
            response = requests.get(url, params=payload)
            response.raise_for_status()
            vacancies = response.json()
            for vacancy in vacancies["items"]:
                salary = predict_rub_salary_hh(vacancy["salary"])
                if salary:
                    vacancies_processed += 1
                    total_salary += salary
            page += 1
            total_pages = vacancies["pages"]
        salary_statistic[language] = {
            "vacancies_found": vacancies["found"],
            "vacancies_processed": vacancies_processed,
            "average_salary": int(total_salary // vacancies_processed),
        }
    return salary_statistic


def get_salary_statistic_superjob(superjob_secret_key):
    url = "https://api.superjob.ru/2.0/vacancies/"
    salary_statistic = dict()
    vacancies_count = 100
    headers = {
        "X-Api-App-Id": superjob_secret_key,
    }
    for language in POPULAR_LANGUAGES:
        payload = {
            "keyword": f"Программист {language}",
            "town": "Москва",
            "count": vacancies_count,
        }
        vacancies_processed = 0
        total_salary = 0
        page = 0
        while True:
            payload["page"] = page
            response = requests.get(
                url,
                headers=headers,
                params=payload
            )
            response.raise_for_status()
            vacancies = response.json()
            for vacancy in vacancies["objects"]:
                salary = predict_rub_salary_superjob(vacancy)
                if salary:
                    vacancies_processed += 1
                    total_salary += salary
            page += 1
            if not vacancies["more"]:
                break
        if vacancies_processed:
            average_salary = int(total_salary // vacancies_processed)
        else:
            average_salary = 0
        salary_statistic[language] = {
            "vacancies_found": vacancies["total"],
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary,
        }
    return salary_statistic


def create_table(salary_statistic, title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language, vacancies in salary_statistic.items():
        language_info = list()
        language_info.append(language)
        language_info.extend(vacancies.values())
        table_data.append(language_info)
    table_instance = AsciiTable(table_data, title)
    return table_instance.table


def main():
    env.read_env()
    superjob_secret_key = env("SJ_SECRET_KEY")

    salaries_superJob = get_salary_statistic_superjob(superjob_secret_key)
    print(create_table(salaries_superJob, 'SuperJob Moscow'))
    print()

    salaries_hh = get_salary_statistic_hh()
    print(create_table(salaries_hh, 'HeadHunter Moscow'))
    print()

if __name__ == '__main__':
    main()
