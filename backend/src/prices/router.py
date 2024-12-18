from fastapi import APIRouter, Query, HTTPException
import requests
from requests.exceptions import JSONDecodeError
from sentry_sdk import capture_exception
import logging

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"description": "Not found"}},
)

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    try:
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        ).json()
    except JSONDecodeError as e:
        logging.error(f"Failed to parse response: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Something went wrong while processing data")
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to fetch data")