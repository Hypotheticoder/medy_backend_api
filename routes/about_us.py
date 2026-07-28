from fastapi import APIRouter

router = APIRouter(prefix="/api/rest/about-us", tags=["REST - About Us"])

@router.get("/get-all")
def get_about_us():
    """Static About Us data since it's global to the platform"""
    return [
        {
            "id": 1,
            "title": "About Medy Lab Services",
            "content": "Medy connects patients with top-tier pathology labs across the country, providing fast, accurate, and reliable diagnostic services directly to your doorstep."
        },
        {
            "id": 2,
            "title": "Our Mission",
            "content": "To make healthcare accessible and affordable for everyone by digitizing and streamlining lab test bookings."
        }
    ]

@router.get("/get-by/{id}")
def get_about_us_by_id(id: int):
    all_content = get_about_us()
    for item in all_content:
        if item["id"] == id:
            return item
    return {"id": id, "title": "Not Found", "content": "The requested about us section was not found."}
