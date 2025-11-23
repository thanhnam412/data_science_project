import random
import pandas as pd

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

MONTH_ABBR = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

ORDINAL = {
    1: "1st",
    2: "2nd",
    3: "3rd",
    # 4th–20th
}
for i in range(4, 32):
    ORDINAL[i] = f"{i}th"


def random_date_valid():
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = random.randint(1990, 2035)
    return day, month, year


def generate_formats(day, month, year):
    y2 = str(year)[2:]
    formats = [
        f"{day}/{month}/{year}",
        f"{day}-{month}-{year}",
        f"{day}.{month}.{year}",
        f"{month}/{day}/{year}",
        f"{year}-{month}-{day}",
        f"{year}/{month}/{day}",
        f"{day}/{month}-{year}",
        f"{day}/{month}/{y2}",
        f"{month}-{day}-{y2}",
        f"{day} {MONTH_NAMES[month-1]} {year}",
        f"{MONTH_NAMES[month-1]} {day}, {year}",
        f"{ORDINAL[day]} of {MONTH_NAMES[month-1]} {year}",
        f"{day} {MONTH_ABBR[month-1]} {year}",
        f"{MONTH_ABBR[month-1]} {ORDINAL[day]}, {year}",
        f"{MONTH_ABBR[month-1]} {day} {y2}",
        f"{day} tháng {month} năm {year}",
        f"ngày {day} tháng {month} năm {year}",
        f"{day}/{month}/{str(year)[-2:]}",
        f"{month}/{day}/{str(year)[-2:]}",
    ]
    return formats


def generate_noise(day, month, year):
    noise = [
        f"{day}/{month*2}-{year}",  # month nhân đôi = invalid
        f"{day}/{month}-{year}",  # mixed
        f"{day}/{month*3}/{year}",  # invalid month
        f"{day*2}-{month}-{year}",  # invalid day
        f"{str(day).zfill(2)}{str(month).zfill(2)}{year}",  # 08122025
        f"{day}-{month}",  # missing year
        f"{year}/{month}",  # missing day
        f"{day}:{month}:{year}",
        f"{day} {MONTH_NAMES[month-1][:2]} {year}",  # truncated month
        f"{day}{MONTH_ABBR[month-1]}{year}",  # no spaces
    ]
    return noise


def generate_dataset(N=100_000, outfile="dates_synthetic.csv"):
    rows = []
    for _ in range(N):
        day, month, year = random_date_valid()
        output = f"{year:04d}-{month:02d}-{day:02d}"

        all_inputs = generate_formats(day, month, year) + generate_noise(
            day, month, year
        )
        inp = random.choice(all_inputs)

        rows.append([inp, output])

    df = pd.DataFrame(rows, columns=["input_text", "target_text"])
    df.to_csv(outfile, index=False)
    print(f"Saved: {outfile} ({N} rows)")