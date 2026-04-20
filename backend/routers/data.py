from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any
import os
import json

router = APIRouter(prefix="/api", tags=["Data Simulation"])

# In-memory store (simulation)
# In production, this would be a real database.
DATA_FILE = "simulated_data.json"

def _load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "sops": [],
        "deviations": [],
        "capas": [],
        "audits": [],
        "decisions": []
    }

def _save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/{entity_type}")
async def get_entities(entity_type: str):
    data = _load_data()
    if entity_type not in data:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return {"results": data[entity_type]}

@router.post("/{entity_type}")
async def add_entity(entity_type: str, item: Dict[str, Any] = Body(...)):
    data = _load_data()
    if entity_type not in data:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    # Ensure ID
    if "id" not in item:
        item["id"] = len(data[entity_type]) + 1
        
    data[entity_type].append(item)
    _save_data(data)
    return {"status": "success", "item": item}

@router.delete("/{entity_type}/{item_id}")
async def delete_entity(entity_type: str, item_id: str):
    data = _load_data()
    if entity_type not in data:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    data[entity_type] = [i for i in data[entity_type] if str(i.get("id")) != item_id and str(i.get("sop_number")) != item_id]
    _save_data(data)
    return {"status": "deleted"}
