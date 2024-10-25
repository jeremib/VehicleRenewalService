from Models.QueryPriceRequest import QueryPriceRequest


class CompleteTransactionRequest(QueryPriceRequest):
    account: str
    exp_month: str
    exp_year: str
    cv: str
