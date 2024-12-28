from fastapi import APIRouter, Query, HTTPException
import requests
from requests.exceptions import JSONDecodeError
import logging

from backend.src.utils import log_exception, ExceptionLevel

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
        request = requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        )
        request.raise_for_status()
        return request.json()
    except JSONDecodeError as e:
        log_exception(e, ExceptionLevel.ERROR, "Failed to parse response")
        raise HTTPException(status_code=400, detail="Something went wrong while processing data")
    except requests.exceptions.RequestException as e:
        log_exception(e, ExceptionLevel.ERROR, "Failed to fetch data")
        raise HTTPException(status_code=400, detail="Failed to fetch data")