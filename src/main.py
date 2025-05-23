#!/bin/python
""" """

VERSION = "dev"

import argparse
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAYS_FULL = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
MONTHS_FULL = (
    "january",
    "febuary",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


@dataclass
class Configuration:
    day_worked: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri")
    pass


class Date(datetime.date):
    def __init__(self, *args, description: str = "", **kwargs):
        super().__init__()

        self.description = description

    def add_description(self, description: str):
        self.description = description
        return self

    def str_weekday(self):
        return WEEKDAYS[self.weekday()]


def parse_dates(str_: str, quiet: bool = False) -> list[Date]:

    # TODO: no errors by lines here?
    pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2})(?!:)(.*?)$",  # TODO
        re.MULTILINE,
    )
    dates: list[Date] = []
    # errors = {}
    for date_str, description in re.findall(pattern, str_):
        try:
            date = Date.fromisoformat(date_str)
        except ValueError as error:
            if not quiet:
                print(f"WARNING: {date_str} - {error}")
            # errors[date_str] = error.__str__()
            continue
        date.add_description(description.strip())
        dates.append(date)

    range_pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})(.*?)$",
        re.MULTILINE,
    )
    for start_date_str, end_date_str, description in re.findall(range_pattern, str_):
        try:
            start_date = Date.fromisoformat(start_date_str)
        except ValueError as error:
            if not quiet:
                print(f"WARNING: {start_date_str} - {error}")
            # errors[date_str] = error.__str__()
            continue
        try:
            end_date = Date.fromisoformat(end_date_str)
        except ValueError as error:
            if not quiet:
                print(f"WARNING: {end_date_str} - {error}")
            # errors[date_str] = error.__str__()
            continue
        date_range: list[Date] = [
            (start_date + datetime.timedelta(days=i)).add_description(description.strip())
            for i in range((end_date - start_date).days + 1)
        ]
        dates += date_range
    return dates


def load_date_file(input_file: Path, quiet: bool = False) -> list[Date]:
    assert input_file.is_file()

    with open(input_file, mode="rt", encoding="utf_8", errors="strict") as fh:
        str_ = fh.read()

    return parse_dates(str_, quiet=quiet)


def report(
    start_date: Date,
    end_date: Date,
    holidays: list[Date] | None = None,
    vacations: list[Date] | None = None,
    quiet: bool = False,
) -> dict[str, int]:

    delta: datetime.timedelta = (end_date - start_date) + datetime.timedelta(days=1)
    total_days: int = delta.days

    if holidays is None:
        holidays = []
    # TODO: if this part gets to long, use better search algorithms
    holidays_in_range: list[Date] = [
        date for date in holidays if date >= start_date and date <= end_date
    ]
    if vacations is None:
        vacations = []
    vacations_in_range: list[Date] = [
        date for date in vacations if date >= start_date and date <= end_date
    ]

    date_range: list[Date] = [start_date + datetime.timedelta(days=i) for i in range(total_days)]

    working_days: int = 0
    off_days: int = 0
    holidays_on_working_day: int = 0
    vacations_on_working_day: int = 0
    vacations_on_holiday: int = 0
    for date in date_range:
        if date in holidays_in_range:
            off_days += 1
            if date.str_weekday() in config.day_worked:
                holidays_on_working_day += 1
            if date in vacations_in_range:
                vacations_on_holiday += 1
        elif date in vacations_in_range:
            off_days += 1
            if date.str_weekday() in config.day_worked:
                vacations_on_working_day += 1
        elif date.str_weekday() in config.day_worked:
            working_days += 1
        else:
            off_days += 1

    results = {
        "total_days": total_days,
        "working_days": working_days,
        "off_days": off_days,
        "relevant_holidays": holidays_on_working_day,
        "total_holidays": len(holidays_in_range),
        "vacations_on_working_day": vacations_on_working_day,
        "vacations_on_holiday": vacations_on_holiday,
        "total_vacations": len(vacations_in_range),
    }
    return results


def date_iso_or_today(date_str):
    if date_str == "today":
        return Date.today()
    return Date.fromisoformat(date_str)


def parse_cli_args(args: list[str] | None = None):
    parser = argparse.ArgumentParser()

    # TODO: add config file args, wich would provide config + paths to files. Default in .config?
    parser.add_argument(
        "--report",
        action="store",
        nargs=2,
        required=False,
        type=date_iso_or_today,
        help="Produce a basic report of the period between two dates",
    )

    parser.add_argument(
        "--holidays-file",
        action="store",
        nargs=1,
        required=False,
        type=Path,
        help="File containing holidays dates",
    )

    parser.add_argument(
        "--vacations-file",
        action="store",
        nargs=1,
        required=False,
        type=Path,
        help="File containing vacations dates",
    )

    # TODO: use those arguments
    parser.add_argument("--verbose", "-v", action="count", default=0)
    parser.add_argument("--quiet", "-q", action="store_true")

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    return parser.parse_args() if args is None else parser.parse_args(args)


def main():
    global config

    config = Configuration()
    cli_args = parse_cli_args()
    test()

    if cli_args.report:
        holidays: list[Date]
        if cli_args.holidays_file:
            holidays_file: Path = cli_args.holidays_file.absolute()
            if not holidays_file.is_file():
                # TODO: proper error
                print("ERROR: holidays_file doesn't exist.", holidays_file.as_posix())
            holidays = load_date_file(holidays_file, quiet=False)
        else:
            print("No holidays file provided. Use --holidays-file to provide one")
            holidays = []

        vacations: list[Date]
        if cli_args.vacations_file:
            vacations_file: Path = cli_args.vacations_file.absolute()
            if not vacations_file.is_file():
                # TODO: proper error
                print("ERROR: vacations_file doesn't exist.", vacations_file.as_posix())
            vacations = load_date_file(vacations_file, quiet=False)
        else:
            print("No vacations file provided. Use --vacations-file to provide one")
            vacations = []

        start_date: Date = min(cli_args.report)
        end_date: Date = max(cli_args.report)
        res: dict[str, int] = report(
            start_date=start_date,
            end_date=end_date,
            holidays=holidays,
            vacations=vacations,
        )
        print(
            f"Report between {start_date.strftime("%A %Y-%m-%d")}"
            f" and {end_date.strftime("%A %Y-%m-%d")}\n"
            f" - total days: {res["total_days"]}  ({res["total_days"] / 7:.1f} weeks)\n"
            f" - working days: {res["working_days"]}\n"
            f" - total off days: {res["off_days"]}\n"
            f" - holidays: {res["relevant_holidays"]} falling on working weekdays\n"
            f" - vacations: {res["vacations_on_working_day"]} days\n"
        )


def test() -> int:
    global config
    config = Configuration()

    # Date parsing
    # ------------
    str_date: str = (
        "2025-04-12 test 1\n"
        "2025-04-14 test 2\n"
        "2024-12-24 test 3\n"
        "24-1-24 test missing\n"
        "2025-06-19 test 4\n"
        "2025-65-14 invalid month\n"
        "2024-12-32 invalid day\n"
        "2026-05-05\n"
        "2025-05-05:2025-07-05\n"
        "2025-02-20:2025-03-04 Spring break\n"
    )
    expected_dates = [
        Date(2025, 4, 12).add_description("test 1"),
        Date(2025, 4, 14).add_description("test 2"),
        Date(2024, 12, 24).add_description("test 3"),
        Date(2025, 6, 19).add_description("test 4"),
        Date(2026, 5, 5),
    ]
    expected_dates += [Date(2025, 5, d) for d in range(5, 32)]
    expected_dates += [Date(2025, 6, d) for d in range(1, 31)]
    expected_dates += [Date(2025, 7, d) for d in range(1, 6)]
    expected_dates += [Date(2025, 2, d).add_description("Spring break") for d in range(20, 29)]
    expected_dates += [Date(2025, 3, d).add_description("Spring break") for d in range(1, 5)]

    dates: list[Date] = parse_dates(str_date, quiet=True)
    assert dates == expected_dates, f"parse_date() return invalid object\n{dates}\n{expected_dates}"

    bank_holidays: list[Date] = parse_dates(
        # 2024
        "2024-01-01 New Year's Day\n"
        "2024-02-05 St Brigid's Day\n"
        "2024-03-18 Saint Patrick's Day\n"
        "2024-04-01 Easter Monday\n"
        "2024-05-06 May Day\n"
        "2024-06-03 June Bank Holiday\n"
        "2024-08-05 August Bank Holiday\n"
        "2024-10-28 October Bank Holiday\n"
        "2024-12-25 Christmas Day\n"
        "2024-12-26 St Stephens's Day\n"
        # 2025
        "2025-01-01 New Year's Day\n"
        "2025-02-03 St Brigid's Day\n"
        "2025-03-17 Saint Patrick's Day\n"
        "2025-04-21 Easter Monday\n"
        "2025-05-05 May Day\n"
        "2025-06-02 June Bank Holiday\n"
        "2025-08-04 August Bank Holiday\n"
        "2025-10-27 October Bank Holiday\n"
        "2025-12-25 Christmas Day\n"
        "2025-12-26 St Stephens's Day\n"
        # 2026
        "2026-01-01 New Year's Day\n"
        "2026-02-02 St Brigid's Day\n"
        "2026-03-17 Saint Patrick's Day\n"
        "2026-04-06 Easter Monday\n"
        "2026-05-04 May Day\n"
        "2026-06-01 June Bank Holiday\n"
        "2026-08-03 August Bank Holiday\n"
        "2026-10-26 October Bank Holiday\n"
        "2026-12-25 Christmas Day\n"
        "2026-12-26 St Stephens's Day\n"
    )

    vacations: list[Date] = parse_dates(
        "2025-04-22 4 days weekend\n" "2025-12-20:2026-01-01 Winter vacation\n"
    )

    # Report generation
    # -----------------
    results: dict[str, int]
    results = report(
        start_date=Date(2025, 4, 4),
        end_date=Date(2025, 4, 23),
        holidays=bank_holidays,
        vacations=vacations,
        quiet=True,
    )
    expected_results = {
        "total_days": 20,
        "working_days": 12,
        "off_days": 8,
        "relevant_holidays": 1,
        "total_holidays": 1,
        "vacations_on_working_day": 1,
        "vacations_on_holiday": 0,
        "total_vacations": 1,
    }
    assert (
        results == expected_results
    ), f"report() return invalid values\n{results}\n{expected_results}"

    results = report(
        start_date=Date(2025, 4, 7),
        end_date=Date(2025, 4, 20),
        holidays=bank_holidays,
        vacations=vacations,
        quiet=True,
    )
    expected_results = {
        "total_days": 14,
        "working_days": 10,
        "off_days": 4,
        "relevant_holidays": 0,
        "total_holidays": 0,
        "vacations_on_working_day": 0,
        "vacations_on_holiday": 0,
        "total_vacations": 0,
    }
    assert (
        results == expected_results
    ), f"report() return invalid values\n{results}\n{expected_results}"

    results = report(
        start_date=Date(2025, 4, 4),
        end_date=Date(2026, 4, 23),
        holidays=bank_holidays,
        vacations=vacations,
        quiet=True,
    )
    expected_results = {
        "total_days": 385,
        "working_days": 257,
        "off_days": 128,
        "relevant_holidays": 11,
        "total_holidays": 11,
        "vacations_on_working_day": 7,
        "vacations_on_holiday": 3,
        "total_vacations": 14,
    }
    assert (
        results == expected_results
    ), f"report() return invalid values\n{results}\n{expected_results}"

    return 0


if __name__ == "__main__":
    main()
