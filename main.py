# Copyright (c) 2023 Manexware S.A.
from functools import lru_cache
from typing import Optional, List, Union

from fastapi import FastAPI, Depends
from odoo_rpc_client import Client
from pydantic import BaseModel, MissingError
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_201_CREATED

import config

app = FastAPI(title="FastAPI with Odoo Demo")


@lru_cache()
def get_client():
    settings = config.Settings()
    client = Client(settings.db_host, settings.db_name, settings.db_user, settings.db_password)
    return client


@app.on_event("startup")
def set_default_executor() -> None:
    from concurrent.futures import ThreadPoolExecutor
    import asyncio

    loop = asyncio.get_running_loop()
    # Tune this according to your requirements !
    loop.set_default_executor(ThreadPoolExecutor(max_workers=5))


class Partner(BaseModel):
    partner_id: int
    name: str
    email: str
    vat: str
    is_company: Union[bool, None] = None

    @classmethod
    def from_res_partner(cls, p):
        return Partner(partner_id=p.id, name=p.name, email=p.email, vat=p.ced_ruc, is_company=p.is_company)


@app.get("/partners", response_model=List[Partner])
def partners(is_company: Optional[bool] = None, client: Client = Depends(get_client)):
    domain = []
    if is_company is not None:
        domain.append(("is_company", "=", is_company))
    partner_ids = client["res.partner"].search_records(domain)
    return [Partner.from_res_partner(p) for p in partner_ids]


@app.get("/partners/{partner_id}", response_model=Partner)
def get_partner(partner_id: int, client: Client = Depends(get_client)):
    try:
        partner = client["res.partner"].browse(partner_id)
        return Partner.from_res_partner(partner)
    except MissingError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    except ConnectionRefusedError:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN)


@app.post("/partners", response_model=Partner, status_code=HTTP_201_CREATED)
def create_partner(partner: Partner, client: Client = Depends(get_client)):
    partner = client["res.partner"].create(
        {
            "name": partner.name,
            "email": partner.email,
            "ced_ruc": partner.vat,
            "is_company": partner.is_company,
        }
    )
    return Partner.from_res_partner(partner)


@app.get("/")
async def root():
    return {"message": "Odoo API"}

