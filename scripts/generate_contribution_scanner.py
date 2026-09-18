from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFilter


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "nabilsupardy4422"
)

OUTPUT = Path(
    "assets/github-cyber-scanner.gif"
)

PAGE_URL = (
    f"https://github.com/users/"
    f"{USERNAME}/contributions"
)


# Ukuran visual
WIDTH = 1200

CELL = 13
GAP = 4

LEFT = 72
TOP = 58

ROWS = 7
MAX_COLS = 53
BOTTOM = 78


# ============================================================
# CONTRIBUTION COLORS
# ============================================================

LEVEL_COLORS = {
    0: (20, 27, 36, 255),
    1: (19, 72, 82, 255),
    2: (18, 126, 142, 255),
    3: (28, 185, 202, 255),
    4: (91, 235, 255, 255),
}


# ============================================================
# FETCH GITHUB CONTRIBUTION DATA
# ============================================================

def fetch_contributions():

    headers = {
        "User-Agent": (
            "nabilsupardy4422-"
            "contribution-scanner/1.0"
        ),
        "Accept": (
            "text/html,"
            "application/xhtml+xml"
        ),
    }

    response = requests.get(
        PAGE_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    cells = []

    for node in soup.select(
        "[data-date][data-level]"
    ):

        raw_date = node.get(
            "data-date"
        )

        raw_level = node.get(
            "data-level"
        )

        if not raw_date or raw_level is None:
            continue

        try:

            day = date.fromisoformat(
                raw_date
            )

            level = max(
                0,
                min(
                    4,
                    int(raw_level)
                )
            )

        except ValueError:

            continue

        cells.append(
            (day, level)
        )

    # Jika tanggal yang sama muncul
    # lebih dari sekali, gunakan level tertinggi.
    merged = {}

    for day, level in cells:

        merged[day] = max(
            level,
            merged.get(day, 0)
        )

    if len(merged) < 300:

        raise RuntimeError(
            f"Contribution parser returned "
            f"only {len(merged)} days. "
            "GitHub's page format may have changed."
        )

    return sorted(
        merged.items()
    )


# ============================================================
# MONTH LABEL
# ============================================================

def month_label(day):

    return day.strftime(
        "%b"
    ).upper()


# ============================================================
# BUILD ANIMATION
# ============================================================

def build_frames(data):

    # GitHub contribution graph:
    #
    # Sunday
    # Monday
    # Tuesday
    # Wednesday
    # Thursday
    # Friday
    # Saturday

    first_day = data[0][0]

    start = first_day

    while start.weekday() != 6:

        start = start.fromordinal(
            start.toordinal() - 1
        )

    values = {
        day: level
        for day, level in data
    }

    weeks = []

    cursor = start

    while cursor <= data[-1][0]:

        week = []

        for row in range(ROWS):

            current_day = (
                cursor.fromordinal(
                    cursor.toordinal() + row
                )
            )

            week.append(
                (
                    current_day,
                    values.get(
                        current_day,
                        0
                    )
                )
            )

        weeks.append(
            week
        )

        cursor = cursor.fromordinal(
            cursor.toordinal() + 7
        )

    # Tampilkan maksimal 53 minggu
    weeks = weeks[-MAX_COLS:]


    grid_width = (
        MAX_COLS *
        (CELL + GAP)
    )

    height = (
        TOP
        + ROWS * (CELL + GAP)
        + BOTTOM
    )

    width = WIDTH


    x0 = max(
        LEFT,
        (width - grid_width) // 2
    )


    frames = []

    # Jumlah frame animasi
    FRAME_COUNT = 36


    for frame_no in range(
        FRAME_COUNT
    ):

        phase = (
            frame_no /
            (FRAME_COUNT - 1)
        )


        # Scanner bergerak:
        #
        # kiri → kanan
        # kanan → kiri

        if phase <= 0.5:

            t = phase * 2

        else:

            t = 2 - phase * 2


        scan_x = (
            x0
            + t *
            max(
                1,
                grid_width - CELL
            )
        )


        # ====================================================
        # BACKGROUND
        # ====================================================

        image = Image.new(
            "RGBA",
            (width, height),
            (8, 13, 20, 255)
        )

        draw = ImageDraw.Draw(
            image
        )


        # ====================================================
        # HEADER
        # ====================================================

        draw.text(
            (x0, 17),
            "CONTRIBUTION ACTIVITY",
            fill=(
                210,
                240,
                248,
                255
            )
        )

        draw.text(
            (
                width - 355,
                17
            ),
            (
                "CYBER SCANNER // "
                f"{USERNAME.upper()}"
            ),
            fill=(
                91,
                235,
                255,
                230
            )
        )


        # ====================================================
        # MONTH LABEL
        # ====================================================

        last_month = None

        for col, week in enumerate(
            weeks
        ):

            current_day = week[0][0]

            if current_day.month != last_month:

                draw.text(
                    (
                        x0
                        + col *
                        (CELL + GAP),
                        39
                    ),
                    month_label(
                        current_day
                    ),
                    fill=(
                        140,
                        165,
                        178,
                        255
                    )
                )

                last_month = (
                    current_day.month
                )


        # ====================================================
        # WEEKDAY LABEL
        # ====================================================

        labels = [
            "SUN",
            "",
            "TUE",
            "",
            "THU",
            "",
            "SAT"
        ]

        for row, label in enumerate(
            labels
        ):

            if label:

                draw.text(
                    (
                        x0 - 34,
                        TOP
                        + row *
                        (CELL + GAP)
                        + 1
                    ),
                    label,
                    fill=(
                        105,
                        130,
                        145,
                        255
                    )
                )


        # ====================================================
        # REAL CONTRIBUTION CELLS
        # ====================================================

        for col, week in enumerate(
            weeks
        ):

            for row, (
                current_day,
                level
            ) in enumerate(
                week
            ):

                x = (
                    x0
                    + col *
                    (CELL + GAP)
                )

                y = (
                    TOP
                    + row *
                    (CELL + GAP)
                )

                draw.rounded_rectangle(
                    (
                        x,
                        y,
                        x + CELL,
                        y + CELL
                    ),
                    radius=3,
                    fill=LEVEL_COLORS[
                        level
                    ]
                )


        # ====================================================
        # SCANNER GLOW
        # ====================================================

        glow = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0)
        )

        glow_draw = ImageDraw.Draw(
            glow
        )


        glow_draw.rectangle(
            (
                scan_x - 24,
                TOP - 7,
                scan_x + 24,
                (
                    TOP
                    + ROWS *
                    (CELL + GAP)
                    + 7
                )
            ),
            fill=(
                50,
                220,
                255,
                34
            )
        )


        glow_draw.line(
            (
                scan_x,
                TOP - 10,
                scan_x,
                (
                    TOP
                    + ROWS *
                    (CELL + GAP)
                    + 8
                )
            ),
            fill=(
                91,
                235,
                255,
                180
            ),
            width=2
        )


        glow = glow.filter(
            ImageFilter.GaussianBlur(
                8
            )
        )


        image = Image.alpha_composite(
            image,
            glow
        )

        draw = ImageDraw.Draw(
            image
        )


        # ====================================================
        # RETICLE
        # ====================================================

        ret_y = (
            TOP
            + 3 *
            (CELL + GAP)
            + CELL / 2
        )

        radius = 17
        arm = 7

        scanner_color = (
            130,
            245,
            255,
            245
        )


        # Top-left
        draw.line(
            (
                scan_x - radius,
                ret_y - radius,
                scan_x - radius + arm,
                ret_y - radius
            ),
            fill=scanner_color,
            width=2
        )

        draw.line(
            (
                scan_x - radius,
                ret_y - radius,
                scan_x - radius,
                ret_y - radius + arm
            ),
            fill=scanner_color,
            width=2
        )


        # Top-right
        draw.line(
            (
                scan_x + radius,
                ret_y - radius,
                scan_x + radius - arm,
                ret_y - radius
            ),
            fill=scanner_color,
            width=2
        )

        draw.line(
            (
                scan_x + radius,
                ret_y - radius,
                scan_x + radius,
                ret_y - radius + arm
            ),
            fill=scanner_color,
            width=2
        )


        # Bottom-left
        draw.line(
            (
                scan_x - radius,
                ret_y + radius,
                scan_x - radius + arm,
                ret_y + radius
            ),
            fill=scanner_color,
            width=2
        )

        draw.line(
            (
                scan_x - radius,
                ret_y + radius,
                scan_x - radius,
                ret_y + radius - arm
            ),
            fill=scanner_color,
            width=2
        )


        # Bottom-right
        draw.line(
            (
                scan_x + radius,
                ret_y + radius,
                scan_x + radius - arm,
                ret_y + radius
            ),
            fill=scanner_color,
            width=2
        )

        draw.line(
            (
                scan_x + radius,
                ret_y + radius,
                scan_x + radius,
                ret_y + radius - arm
            ),
            fill=scanner_color,
            width=2
        )


        # Center
        draw.ellipse(
            (
                scan_x - 3,
                ret_y - 3,
                scan_x + 3,
                ret_y + 3
            ),
            fill=(
                180,
                250,
                255,
                240
            )
        )


        # ====================================================
        # FOOTER
        # ====================================================

        draw.text(
            (
                x0,
                height - 30
            ),
            (
                "LIVE VISUALIZATION  •  "
                "BUILD  •  COMMIT  •  "
                "TEST  •  IMPROVE"
            ),
            fill=(
                105,
                140,
                155,
                255
            )
        )


        total_contributions = sum(
            level
            for _, level in data
        )


        draw.text(
            (
                width - 120,
                height - 30
            ),
            str(
                total_contributions
            ),
            fill=(
                91,
                235,
                255,
                255
            )
        )


        frames.append(
            image.convert(
                "P",
                palette=Image.Palette.ADAPTIVE
            )
        )


    return frames


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    print(
        f"Fetching: {PAGE_URL}"
    )


    data = fetch_contributions()


    print(
        f"Parsed {len(data)} contribution days."
    )


    frames = build_frames(
        data
    )


    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
        optimize=True,
        disposal=2
    )


    print(
        f"Generated: {OUTPUT}"
    )


if __name__ == "__main__":

    try:

        main()

    except Exception as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr
        )

        raise
