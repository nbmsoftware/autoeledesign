offices = {
    1: {"office": "Alectra Patterson", "address": "55 Patterson Road", "city_postal": "Barrie, ON L4N 3V9", "phone": "1-833-253-2872"},
    2: {"office": "Alectra Cityview", "address": "161 Cityview Blvd", "city_postal": "Woodbridge, ON L4H 0A9", "phone": "1-833-253-2872"},
    3: {"office": "Alectra Kennedy", "address": "200 Kennedy Road South", "city_postal": "Brampton, ON L6W 3G6", "phone": "1-833-253-2872"},
    4: {"office": "Alectra Southgate", "address": "395 Southgate Drive", "city_postal": "Guelph, ON N1G 4Y1", "phone": "1-519-822-3010"},
    5: {"office": "Alectra John", "address": "55 John Street North", "city_postal": "Hamilton, Ontario L8R 3M8", "phone": "1-833-253-2872"}
}

municipality_to_office = {
    "Penetanguishene": 1,
    "Barrie": 1,
    "Thornton": 1,
    "Alliston": 1,
    "Beeton": 1,
    "Tottenham": 1,
    "Bradford West Gwillimbury": 1,
    "Aurora": 2,
    "Vaughan": 2,
    "Richmond Hill": 2,
    "Markham": 2,
    "Brampton": 3,
    "Mississauga": 3,
    "Rockwood": 4,
    "Guelph": 4,
    "Hamilton": 5,
    "St. Catharines": 5,
}

def get_office_info(municipality_name):
    """
    Retrieve the office info for a given municipality name.

    :param municipality_name: name of the municipality
    :return: office info
    """
    office_id = municipality_to_office.get(municipality_name.capitalize())
    if not office_id:
        raise Exception(f"No office info for municipality: {municipality_name}")

    office = offices.get(office_id)
    if not office:
        raise Exception(f"No office info for municipality: {municipality_name}, office ID: {office_id}")

    return office
