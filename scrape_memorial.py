import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from io import BytesIO

# Constants
API_URL = "https://www.mandarinoriental.com/api/v1/booking/check-room-availability"
HOTEL_ID = 514  # Hardcoded hotel

# Streamlit UI
st.title("Mandarin Oriental Hotel Availability Checker")
st.write(f"Hotel ID: {HOTEL_ID}")

# Let user enter their cookie
cookie_input = st.text_input(
    "Enter your API cookie (from your browser session):", 
    type="password"
)

# Date picker
start_date = st.date_input("Select start date", datetime.today())

# Button to run
if st.button("Check Availability"):

    if not cookie_input:
        st.warning("Please enter a valid cookie to continue.")
    else:
        # Prepare headers with user-provided cookie
        HEADERS = {
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": cookie_input,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

        all_rows = []

        for day_offset in range(60):  # next 60 days
            check_date = start_date + timedelta(days=day_offset)
            st.text(f"Checking {check_date.strftime('%Y-%m-%d')}...")

            # Fetch availability
            payload = {
                "hotelCode": str(HOTEL_ID),
                "roomCodes": None,
                "roomName": None,
                "bedType": None,
                "rateCode": None,
                "adultGuestCount": "2",
                "childGuestCount": "0",
                "stayDateStart": check_date.strftime("%Y-%m-%d"),
                "stayDateEnd": (check_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "primaryLanguageId": "en"
            }

            response = requests.post(API_URL, headers=HEADERS, json=payload)
            if response.status_code == 200:
                data = response.json()
                room_stays = data.get("roomStays")
                if room_stays:
                    for room in room_stays:
                        for rate in room.get("rates", []):
                            all_rows.append({
                                "HotelID": HOTEL_ID,
                                "Date": check_date.strftime("%Y-%m-%d"),
                                "RoomType": room.get("title"),
                                "RoomCode": room.get("roomTypeCode"),
                                "RateTitle": rate.get("title"),
                                "Total": rate.get("total"),
                                "Taxes": rate.get("taxes"),
                                "Fees": rate.get("fees"),
                                "MaxGuests": room.get("maxGuests"),
                                "GuaranteeCode": rate.get("guaranteeCode"),
                                "ShortDescription": rate.get("shortDescription"),
                                "LongDescription": rate.get("longDescription"),
                                "Image": rate.get("image")
                            })
            else:
                st.error(f"HTTP {response.status_code} on {check_date.strftime('%Y-%m-%d')}")

        if all_rows:
            result_df = pd.DataFrame(all_rows)
            buffer = BytesIO()
            result_df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.success("Availability fetched successfully!")
            st.download_button(
                label="Download Results Excel",
                data=buffer,
                file_name="output_availability.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No availability found for the selected dates.")
