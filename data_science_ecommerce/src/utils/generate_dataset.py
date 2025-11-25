import random
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
#  MONTH NAMES + MONTH ABBR + ORDINAL
# ============================================================

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

MONTH_ABBR_VARIANTS = [
    "Jan.", "Feb.", "Mar.", "Apr.", "May.", "Jun.",
    "Jul.", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."
]

# ORDINAL DAY (1st → 31st)
ORDINAL = {1:"1st", 2:"2nd", 3:"3rd"}
for i in range(4, 32):
    ORDINAL[i] = f"{i}th"


# ============================================================
#  HELPERS
# ============================================================

SEPARATORS = ["/", "-", ".", " ", "_", "|"]

def random_valid_date():
    """Pick a random date between 1990 and 2035"""
    start = datetime(1990, 1, 1)
    end = datetime(2035, 12, 31)
    delta = end - start
    offset = random.randint(0, delta.days)
    dt = start + timedelta(days=offset)
    return dt

def random_timezone():
    """Random timezone formats"""
    return random.choice([
        "Z", "+00:00", "+07:00", "-05:00", "+0500", "-0300",
        "+08", "-0330", "Z+3", "+2500", "+3"
    ])

def random_noise_number():
    return random.randint(0, 9999)


# ============================================================
#  GENERATE TIMESTAMP + DATE FORMATS
# ============================================================

def generate_formats_for(dt):
    day = dt.day
    month = dt.month
    year = dt.year

    d2 = f"{day:02d}"
    m2 = f"{month:02d}"
    y2 = str(year)[2:]
    y3 = str(year)[-3:]

    h = random.randint(0, 23)
    mi = random.randint(0, 59)
    s = random.randint(0, 59)
    ms = random.randint(0, 999)
    us = random.randint(0, 999999)
    ns = random.randint(0, 999999999)

    sep = random.choice(SEPARATORS)

    variants = [

        # ============================================================
        # BASIC DATE FORMATS
        # ============================================================
        f"{day}{sep}{month}{sep}{year}",
        f"{d2}{sep}{m2}{sep}{y2}",
        f"{m2}{sep}{d2}{sep}{year}",     # US style MM/DD/YYYY
        f"{day}-{month}-{year}",
        f"{year}{sep}{m2}{sep}{d2}",
        f"{day} {MONTH_NAMES[month-1]} {year}",
        f"{MONTH_NAMES[month-1]} {day}, {year}",
        f"{day} {MONTH_ABBR[month-1]} {year}",
        f"{ORDINAL[day]} of {MONTH_NAMES[month-1]}, {year}",

        # ============================================================
        # VIETNAMESE FORMS
        # ============================================================
        f"{day} tháng {month} năm {year}",
        f"ngày {day} tháng {month} năm {year}",
        f"Ngày {day}-{month}-{year}",
        f"{day}/{month}/{year} giờ {h}:{mi}:{s}",

        # ============================================================
        # ISO TIMESTAMP
        # ============================================================
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}",
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}{random_timezone()}",
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}.{ms:03d}Z",
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}.{us:06d}Z",
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}.{ns:09d}Z",

        # Custom ISO (requested)
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}+2500",
        f"{year}-{m2}-{d2}T{h:02d}:{mi:02d}:{s:02d}Z+3",

        # ============================================================
        # NO SEPARATORS
        # ============================================================
        f"{year}{m2}{d2}{h:02d}{mi:02d}{s:02d}",
        f"{year}{m2}{d2}{h:02d}{mi:02d}{s:02d}{ms:03d}",
        f"{year}{m2}{d2}{h:02d}{mi:02d}{s:02d}{us:06d}",
        f"{year}{m2}{d2}{h:02d}{mi:02d}{s:02d}{ns:09d}",

        # ============================================================
        # UNIX TIMESTAMPS (s, ms, µs, ns)
        # ============================================================
        str(int(dt.timestamp())),
        str(int(dt.timestamp() * 1000)),
        str(int(dt.timestamp() * 1_000_000)),
        str(int(dt.timestamp() * 1_000_000_000)),

        # ============================================================
        # MIXED / NOISY
        # ============================================================
        f"{day}/{month*2}-{year}",         # invalid month purposely
        f"{day*2}-{month}-{year}",         # invalid day purposely
        f"{year}/{month}/{day}T{h}{mi}{s}",
        f"{day}.{month}.{year}T{h}-{mi}-{s}",
        f"{year}_{m2}_{d2}T{h}_{mi}_{s}{random_timezone()}",

        # ============================================================
        # CONTAINED IN SENTENCES
        # ============================================================
        f"Event at {year}-{m2}-{d2}T{h}:{mi}:{s}",
        f"Sự kiện diễn ra vào {day}/{month}/{year} {h}:{mi}",
        f"The system recorded {year}{m2}{d2}{h:02d}{mi:02d}{s:02d}",
    ]

    return variants


# ============================================================
#  MAIN GENERATOR
# ============================================================

def generate_dataset(N=20_000, outfile="dates_mix_timestamp.csv"):
    rows = []
    for _ in range(N):
        dt = random_valid_date()
        target = dt.strftime("%Y-%m-%d")

        raw = random.choice(generate_formats_for(dt))

        rows.append([raw, target])

    df = pd.DataFrame(rows, columns=["input_text", "target_text"])
    df.to_csv(outfile, index=False)
    print(f"[OK] Saved {N} rows → {outfile}")


# ============================================================
#  RUN (for 3000 epochs small dataset)
# ============================================================

generate_dataset(25_000, "dates_advanced_25k.csv")
