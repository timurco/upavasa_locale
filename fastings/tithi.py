import ephem

TITHI_SIZE = 12
TITHI_SIZE_DEG = ephem.degrees(f"{TITHI_SIZE}:00:00")

TITHI_ANGLES_LIST = [
    (ephem.degrees(str(x)), ephem.degrees(str(x + TITHI_SIZE)))
    for x in range(-6, 354, TITHI_SIZE)
]

local_copy = TITHI_ANGLES_LIST
TITHI_INFO = [
    ("Amavasya", local_copy[0][0], local_copy[0][1]),
    ("Pratipada", local_copy[1][0], local_copy[1][1]),
    ("Dwitiya", local_copy[2][0], local_copy[2][1]),
    ("Tritiya", local_copy[3][0], local_copy[3][1]),
    ("Chaturthi", local_copy[4][0], local_copy[4][1]),
    ("Panchami", local_copy[5][0], local_copy[5][1]),
    ("Shashti", local_copy[6][0], local_copy[6][1]),
    ("Saptami", local_copy[7][0], local_copy[7][1]),
    ("Ashtami", local_copy[8][0], local_copy[8][1]),
    ("Navami", local_copy[9][0], local_copy[9][1]),
    ("Dashami ", local_copy[10][0], local_copy[10][1]),
    ("Ekadashi", local_copy[11][0], local_copy[11][1]),
    ("Dwadashi", local_copy[12][0], local_copy[12][1]),
    ("Trayodashi ", local_copy[13][0], local_copy[13][1]),
    ("Chaturdashi ", local_copy[14][0], local_copy[14][1]),
    ("Purnima", local_copy[15][0], local_copy[15][1]),
    ("Pratipada", local_copy[16][0], local_copy[16][1]),
    ("Dwitiya", local_copy[17][0], local_copy[17][1]),
    ("Tritiya", local_copy[18][0], local_copy[18][1]),
    ("Chaturthi", local_copy[19][0], local_copy[19][1]),
    ("Panchami", local_copy[20][0], local_copy[20][1]),
    ("Shashti", local_copy[21][0], local_copy[21][1]),
    ("Saptami", local_copy[22][0], local_copy[22][1]),
    ("Ashtami", local_copy[23][0], local_copy[23][1]),
    ("Navami", local_copy[24][0], local_copy[24][1]),
    ("Dashami", local_copy[25][0], local_copy[25][1]),
    ("Ekadashi", local_copy[26][0], local_copy[26][1]),
    ("Dwadashi", local_copy[27][0], local_copy[27][1]),
    ("Trayodashi", local_copy[28][0], local_copy[28][1]),
    ("Chaturdashi", local_copy[29][0], local_copy[29][1]),
    ("Amavasya", local_copy[0][0], local_copy[0][1]),
]


def get_moon_sun_ra_difference(m, s):
    diff = ephem.degrees(m - s)
    if ephem.degrees("-6:00:00") <= diff < ephem.degrees("0:00:00"):
        result = diff
    elif diff < ephem.degrees("-6:00:00"):
        result = diff.norm
    else:
        result = diff
    return result


def calculate_tithi(moon_ra, sun_ra):
    diff = get_moon_sun_ra_difference(moon_ra, sun_ra)
    tithi = -1
    for tithi, j in enumerate(local_copy):
        if j[0] <= diff <= j[1]:
            break
    return tithi, diff
