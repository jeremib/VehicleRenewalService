from fastapi import FastAPI, HTTPException
from Models.QueryPriceRequest import QueryPriceRequest
from Models.CompleteTransactionRequest import CompleteTransactionRequest
from Services.RenewalService import RenewalService
import os
import logging

app = FastAPI()
renewal_service_url = os.getenv("RENEWAL_SERVICE_URL")

logging.basicConfig(level=logging.INFO)

@app.post('/query/price/tennessee')
async def query_price(request: QueryPriceRequest):
    logging.info("Received request to query price")
    try:
        renewal_service = RenewalService(request)
        renewal_service.driver.get(renewal_service_url)
        logging.info("Navigated to renewal service URL")
        
        #start by selecting the county from the dropdown
        renewal_service.beginning_county_selection()
        current_page = renewal_service.check_current_page() 
   
        logging.info(f"Current page: {current_page}")    
        
        alert = renewal_service.fill_street_number_page() 
        if alert:
            logging.info(f"Alert: {alert}")
            raise HTTPException(status_code=400, detail=f"{alert}")
        
        
        logging.info(f"Current URL: {renewal_service.driver.current_url}")
        
        renewal_service.fill_form_page()
        renewal_service.county_selection_element() 
        fee_summary = renewal_service.collect_form_data()
        if fee_summary:
            logging.info("Fee summary retrieved successfully")
            return fee_summary
        
        raise HTTPException(status_code=500, detail="Failed to retrieve fee summary")
    except HTTPException as ex:
        logging.error(f"HTTPException: {ex.detail}")
        raise HTTPException(status_code=ex.status_code, detail=ex.detail)
    except Exception as ex:
        logging.error(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))

@app.post('/complete/tennessee')
async def complete_transaction(request: CompleteTransactionRequest):
    logging.info("Received request to complete transaction")
    try:
        renewal_service = RenewalService(request)
        renewal_service.driver.get(renewal_service_url)
        logging.info("Navigated to renewal service URL")
        
        #start by selecting the county from the dropdown
        renewal_service.beginning_county_selection()
        renewal_service.save_screenshot()
        current_page = renewal_service.check_current_page() 
   
        renewal_service.save_screenshot()
        logging.info(f"Current page: {current_page}")    
        
        renewal_service.save_screenshot()
        alert = renewal_service.fill_street_number_page() 
        if alert:
            logging.info(f"Alert: {alert}")
            raise HTTPException(status_code=400, detail=f"{alert}")
        
        
        logging.info(f"Current URL: {renewal_service.driver.current_url}")
        
        renewal_service.fill_form_page()
        renewal_service.county_selection_element() 
        renewal_service.save_screenshot()
        fee_summary = renewal_service.collect_form_data()
        renewal_service.save_screenshot()

        payment_process = renewal_service.handle_payment_processing()
        
        current_page = renewal_service.check_current_page()
        renewal_service.save_screenshot()
        
        logging.info(f"Current page: {current_page}") 
        if current_page != "successful_payment":
            raise HTTPException(status_code=500, detail="Payment processing failed")
        logging.info("Transaction completed successfully")
        return payment_process
    except HTTPException as ex:
        logging.error(f"HTTPException: {ex.detail}")
        raise HTTPException(status_code=400, detail=ex.detail)
    except Exception as ex:
        logging.error(f"Exception: {ex}")
        raise HTTPException(status_code=400, detail=str(ex))