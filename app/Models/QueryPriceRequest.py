from pydantic import BaseModel


# Request Body Model for FastAPI
class QueryPriceRequest(BaseModel):
    plateNumber: str
    county: str
    name: str
    addressTwo: str
    city: str
    state: str
    zip: str
    homePhone0: str
    homePhone1: str
    homePhone2: str
    email: str
    confirmEmail: str
