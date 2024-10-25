from fastapi import FastAPI, HTTPException, Request
from Models.models import QueryPriceRequest, CompleteTransactionRequest
from renewalService import RenewalService
from dotenv import load_dotenv
import os
import time


# FastAPI instance
app = FastAPI()
load_dotenv()
renewal_service_url = os.getenv("RENEWAL_SERVICE_URL")

@app.post('/query/price/tennessee')
async def query_price(request: QueryPriceRequest):
    renewal_service = RenewalService(request)

    renewal_service.driver.get(renewal_service_url)
    alert_text = renewal_service.search_plate_number()
    
    if renewal_service.driver.current_url==renewal_service_url:
        raise HTTPException(status_code=400, detail=f"{alert_text} Plate Number is not correct")
    
    # if alert_text:
    #     raise HTTPException(status_code=400, detail=alert_text)

    current_page = renewal_service.check_current_page()

    if current_page == "form_page":
        renewal_service.fill_form_page()                
        renewal_service.county_selection_element()
        # renewal_service.collect_form_data()
        
    elif current_page == "street_number_page":
        renewal_service.fill_street_number_page()
    


    # if current_page == "street_number_page":
    #     renewal_service.fill_street_number_page()
    
    fee_summary = renewal_service.collect_form_data()
    if fee_summary:
        return fee_summary
    raise HTTPException(status_code=500, detail="Unable to retrieve fee summary")


@app.post('/complete/tennessee')
async def complete_transaction(request: CompleteTransactionRequest):
    renewal_service = RenewalService(request)

    renewal_service.driver.get(renewal_service_url)
    alert_text = renewal_service.search_plate_number()
    
    if renewal_service.driver.current_url==renewal_service_url:
        raise HTTPException(status_code=400, detail=f"{alert_text} Plate Number is not correct")
    

    current_page = renewal_service.check_current_page()

    if current_page == "form_page":
        renewal_service.fill_form_page()                
        renewal_service.county_selection_element()
        # renewal_service.collect_form_data()


        
        
    elif current_page == "street_number_page":
        renewal_service.fill_street_number_page()

    # renewal_service.county_selection_element()  # Handle county selection if needed
    payment_process = renewal_service.handle_payment_processing()
    fee_summary=renewal_service.collect_form_data()
    if payment_process:
        return fee_summary
    raise HTTPException(status_code=400, detail="Payment processing failed")


# Run the FastAPI application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
