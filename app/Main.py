from fastapi import FastAPI, HTTPException
from Models.QueryPriceRequest import QueryPriceRequest
from Models.CompleteTransactionRequest import CompleteTransactionRequest
from Services.RenewalService import RenewalService
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import partial

app = FastAPI()
renewal_service_url = os.getenv("RENEWAL_SERVICE_URL")
# Create a thread pool for handling Selenium operations
thread_pool = ThreadPoolExecutor(max_workers=10)

logging.basicConfig(level=logging.INFO)

async def run_in_thread(func, *args, **kwargs):
    """Execute a function in a thread pool to prevent blocking"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(thread_pool, partial(func, *args, **kwargs))

def process_renewal_query(request: QueryPriceRequest):
    """Handle the renewal query process in a separate thread"""
    try:
        renewal_service = RenewalService(request)
        renewal_service.driver.get(renewal_service_url)
        
        renewal_service.beginning_county_selection()
        current_page = renewal_service.check_current_page()
        
        alert = renewal_service.fill_street_number_page()
        if alert:
            raise HTTPException(status_code=400, detail=f"{alert}")
        
        current_page = renewal_service.check_current_page()
        logging.info(f"current page {current_page}")


        if current_page == "price_page":
            logging.info("got price early")
            return renewal_service.collect_form_data()

        renewal_service.fill_form_page()

        renewal_service.county_selection_element()

        fee_summary = renewal_service.collect_form_data()
        
        if fee_summary:
            return fee_summary
        raise HTTPException(status_code=500, detail="Failed to retrieve fee summary")
    except Exception as e:
        raise e
    finally:
        # Clean up
        if 'renewal_service' in locals() and hasattr(renewal_service, 'driver'):
            renewal_service.driver.quit()

def process_renewal_completion(request: CompleteTransactionRequest):
    """Handle the renewal completion process in a separate thread"""
    try:
        renewal_service = RenewalService(request)
        renewal_service.driver.get(renewal_service_url)
        
        renewal_service.beginning_county_selection()
        renewal_service.save_screenshot()
        
        alert = renewal_service.fill_street_number_page()
        if alert:
            raise HTTPException(status_code=400, detail=f"{alert}")
        
        renewal_service.fill_form_page()
        renewal_service.county_selection_element()
        renewal_service.save_screenshot()
        fee_summary = renewal_service.collect_form_data()
        renewal_service.save_screenshot()

        payment_process = renewal_service.handle_payment_processing()
        
        current_page = renewal_service.check_current_page()
        renewal_service.save_screenshot()
        
        if current_page != "successful_payment":
            raise HTTPException(status_code=500, detail="Payment processing failed")
        return payment_process
    except Exception as e:
        raise e
    finally:
        # Clean up
        if 'renewal_service' in locals() and hasattr(renewal_service, 'driver'):
            renewal_service.driver.quit()

@app.post('/query/price/tennessee')
async def query_price(request: QueryPriceRequest):
    logging.info("Received request to query price")
    try:
        result = await run_in_thread(process_renewal_query, request)
        logging.info(result);
        return result
    except HTTPException as ex:
        logging.error(f"HTTPException: {ex.detail}")
        raise
    except Exception as ex:
        logging.error(f"Exception: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))

@app.post('/complete/tennessee')
async def complete_transaction(request: CompleteTransactionRequest):
    logging.info("Received request to complete transaction")
    try:
        result = await run_in_thread(process_renewal_completion, request)
        logging.info(result);
        return result
    except HTTPException as ex:
        logging.error(f"HTTPException: {ex.detail}")
        raise HTTPException(status_code=400, detail=ex.detail)
    except Exception as ex:
        logging.error(f"Exception: {ex}")
        raise HTTPException(status_code=400, detail=str(ex))

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup thread pool on application shutdown"""
    thread_pool.shutdown(wait=True)