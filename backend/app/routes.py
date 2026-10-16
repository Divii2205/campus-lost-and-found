from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Item
from .schemas import ClaimIn, ItemCreate, ItemOut, ItemUpdate, StatsOut

# all item routes start with api items
router = APIRouter(prefix="/api/items", tags=["items"])


# find one item by id or send back a 404 not found error
def get_item_or_404(item_id: int, db: Session) -> Item:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


# list items with optional filters for status and category and a search word
@router.get("", response_model=list[ItemOut])
def list_items(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    q: str | None = Query(default=None, description="search in title, description and location"),
    db: Session = Depends(get_db),
):
    # newest items come first
    query = select(Item).order_by(Item.id.desc())
    if status_filter:
        query = query.where(Item.status == status_filter.upper())
    if category:
        query = query.where(Item.category == category.upper())
    # search the word in the title and description and location
    if q:
        like = f"%{q}%"
        query = query.where(or_(Item.title.ilike(like), Item.description.ilike(like), Item.location.ilike(like)))
    return list(db.scalars(query))


# count how many items are lost and found and claimed
# this route is above the item id route so stats is not read as an id
@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Item.status, func.count(Item.id)).group_by(Item.status)).all()
    counts = {row_status: count for row_status, count in rows}
    return StatsOut(
        total=sum(counts.values()),
        lost=counts.get("LOST", 0),
        found=counts.get("FOUND", 0),
        claimed=counts.get("CLAIMED", 0),
    )


# get one item
@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return get_item_or_404(item_id, db)


# report a new lost or found item
@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# change an item
@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    # only change the fields that were sent
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


# mark an item as claimed by its owner
@router.patch("/{item_id}/claim", response_model=ItemOut)
def claim_item(item_id: int, payload: ClaimIn, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    # an item can only be claimed one time
    if item.status == "CLAIMED":
        raise HTTPException(status_code=409, detail="Item is already claimed")
    item.status = "CLAIMED"
    item.claimed_by = payload.claimed_by
    db.commit()
    db.refresh(item)
    return item


# delete an item
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    db.delete(item)
    db.commit()
