from fastapi import APIRouter
from app.models import ReviewRateRequest
from app.services import review_service

router = APIRouter(prefix="/api")


@router.get("/review/queue")
def get_review_queue():
    cards = review_service.get_review_queue(1)
    return {"cards": cards}


@router.post("/review/{card_id}/rate")
def rate_card(card_id: int, req: ReviewRateRequest):
    return review_service.rate_card(1, card_id, req.quality)
