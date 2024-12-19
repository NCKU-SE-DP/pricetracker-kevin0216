from fastapi import APIRouter, Query, HTTPException
import requests
from requests.exceptions import JSONDecodeError
from sentry_sdk import capture_exception
import logging

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={418: {"description": "I'm a teapot, I can't brew coffee"}},
)

@router.get("/necessities-price")
def get_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    logging.debug(f"Accessed /api/v1/prices/necessities-price")
    try:
        return requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        ).json()
    except JSONDecodeError as e:
        logging.error(f"Failed to parse response: {e}")
        capture_exception(e)
        raise HTTPException(status_code=400, detail="Something went wrong while processing data")
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        capture_exception(e)
        raise HTTPException(status_code=400, detail="Failed to fetch data")