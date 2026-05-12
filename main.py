from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from config import TRACK_STATUS_NEW, TRACK_STATUS_MODIFIED
import bot
from Yoku.yoku.scrape import prettify_timestamp
from Yoku.yoku.consts import KEY_START_TIMESTAMP, KEY_END_TIMESTAMP, KEY_POST_TIMESTAMP
import uvicorn
import json

from mercapi import Mercapi
from mercapi.requests.search import SearchRequestData

app = FastAPI(title="Yambot Tracking API")
m = Mercapi()

class TrackItem(BaseModel):
    site: str # 'mercari' or 'yahoo_auctions'
    keyword: str
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    exclude_keyword: Optional[str] = None
    category_id: Optional[List[int]] = None
    item_condition_id: Optional[List[int]] = None
    level: Optional[int] = None
    supplement: Optional[str] = None

class ExcludeRequest(BaseModel):
    item_id: str

class InputItem(BaseModel):
    url: str
    row_number: int
    item: str
    facebook: str

class OutputItem(BaseModel):
    url: str
    row_number: int
    item: str
    facebook: str
    status: str

class SearchItemResult(BaseModel):
    name: str
    price: str
    url: str

class SearchResponse(BaseModel):
    num_found: int
    items: List[SearchItemResult]

@app.get("/track")
def trigger_tracking():
    # Run the tracking function but do not send the email
    # It returns a list of tuples: (entry_dict, list_of_modified_items)
    updates = bot.track(send_email=False)
    
    response_data = []
    
    # Process the updates into a clean JSON format for n8n
    for entry, items in updates:
        entry_res = {
            "keyword": entry.get("keyword") or entry.get("va"),
            "site": entry.get("site"),
            "changes": []
        }
        
        for item, status in items:
            # Mercari items are custom objects (Item), Yahoo ones are standard dicts
            item_data = dict(item.__dict__) if hasattr(item, "__dict__") else dict(item)
            
            for ts_key in [KEY_START_TIMESTAMP, KEY_END_TIMESTAMP, KEY_POST_TIMESTAMP, "created", "updated"]:
                if ts_key in item_data and isinstance(item_data[ts_key], int):
                    item_data[f"{ts_key}_formatted"] = prettify_timestamp(item_data[ts_key])
            
            entry_res["changes"].append({
                "status": status,
                "item": item_data,
                "site": entry.get("site", "UNKNOWN"),
                "keyword": entry.get("keyword") or entry.get("va") or "UNKNOWN"
            })
            
        response_data.append(entry_res)
        
    return {"success": True, "new_or_modified_items": response_data}

@app.get("/configs")
def get_configs():
    """Get the list of currently tracked keywords"""
    track_json = bot.load_file_to_json(file_path=bot.RESULT_PATH) or []
    return {"success": True, "configs": track_json}

@app.post("/configs")
def add_config(item: TrackItem):
    """Add a new keyword to the tracking list"""
    track_json = bot.load_file_to_json(file_path=bot.RESULT_PATH) or []
    
    max_entry_id = 0
    for track_entry in track_json:
        max_entry_id = max(max_entry_id, track_entry.get("id", 0))
        
    new_entry = {"id": max_entry_id + 1, "site": item.site}
    
    if item.site == bot.SITE_MERCARI:
        new_entry["keyword"] = item.keyword
        new_entry["level"] = item.level if item.level else bot.LEVEL_ABSOLUTELY_UNIQUE
        if item.supplement: new_entry["supplement"] = item.supplement
        if item.min_price: new_entry["price_min"] = item.min_price
        if item.max_price: new_entry["price_max"] = item.max_price
        if item.exclude_keyword: new_entry["exclude_keyword"] = item.exclude_keyword
        if item.category_id: new_entry["category_id"] = item.category_id
        if item.item_condition_id: new_entry["item_condition_id"] = item.item_condition_id
    elif item.site == bot.SITE_YAHOO_AUCTIONS:
        new_entry["va"] = item.keyword
        if item.min_price: new_entry["min"] = item.min_price
        if item.max_price: new_entry["max"] = item.max_price
        if item.exclude_keyword: new_entry["ve"] = item.exclude_keyword
        if item.category_id and len(item.category_id) > 0: new_entry["auccat"] = item.category_id[0]
        if item.item_condition_id: new_entry["istatus"] = item.item_condition_id
    else:
        raise HTTPException(status_code=400, detail="Site must be 'mercari' or 'yahoo_auctions'")
        
    new_entry["last_result"] = {}
    track_json.append(new_entry)
    bot.save_json_to_file(track_json, bot.RESULT_PATH)
    return {"success": True, "message": "Added successfully", "entry": new_entry}

@app.delete("/configs/{entry_id}")
def remove_config(entry_id: int):
    """Remove a currently tracked keyword"""
    track_json = bot.load_file_to_json(file_path=bot.RESULT_PATH) or []
    initial_len = len(track_json)
    track_json = [entry for entry in track_json if entry.get("id") != entry_id]
    
    if len(track_json) == initial_len:
        raise HTTPException(status_code=404, detail="Entry ID not found")
        
    bot.save_json_to_file(track_json, bot.RESULT_PATH)
    return {"success": True, "message": f"Removed entry {entry_id}"}

@app.post("/exclude")
def exclude_item(req: ExcludeRequest):
    """Exclude a specific item ID from future results"""
    track_json = bot.load_file_to_json(file_path=bot.RESULT_PATH) or []
    found = False
    for entry in track_json:
        if "exclude_items" not in entry:
            entry["exclude_items"] = []
        if req.item_id not in entry["exclude_items"]:
            entry["exclude_items"].append(req.item_id)
            found = True
            
    bot.save_json_to_file(track_json, bot.RESULT_PATH)
    return {"success": True, "message": f"Item {req.item_id} excluded from future results."}


@app.post("/item", response_model=List[OutputItem])
async def get_status(data: List[InputItem]):
    results = []
    for item in data:
        try:
            item_id = item.url.strip().split("/")[-1]
            details = await m.item(item_id)
            status = details.status  # <-- dùng property status của Item object

            results.append({
                "url": item.url,
                "row_number": item.row_number,
                "item": item.item,
                "facebook": item.facebook,
                "status": status
            })
        except Exception as e:
            results.append({
                "url": item.url,
                "row_number": item.row_number,
                "item": item.item,
                "facebook": item.facebook,
                "status": f"error: {str(e)}"
            })
    return results

@app.get("/search", response_model=SearchResponse)
async def search_items(query: str, on_sale: bool = False):
    try:
        status_list = [SearchRequestData.Status.STATUS_ON_SALE] if on_sale else []
        results = await m.search(query, status=status_list)
        
        items = []
        for item in results.items:
            items.append({
                "name": item.name,
                "price": str(item.price),
                "url": f"https://jp.mercari.com/item/{item.id_}"
            })
            
        return {
            "num_found": results.meta.num_found,
            "items": items
        }
    except Exception as e:
        return {"num_found": 0, "items": []}

if __name__ == "__main__":
    print("Starting combined Yambot/Mercapi API on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
