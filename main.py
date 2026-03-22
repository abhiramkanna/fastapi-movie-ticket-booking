from fastapi import FastAPI, Query, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ─────────────── Data Storage ───────────────
movies = [
    {"id": 1, "name": "RRR", "genre": "Action", "rating": 9.0, "price": 550, "language": "Telugu"},
    {"id": 2, "name": "KGF", "genre": "Action", "rating": 8.5, "price": 450, "language": "Kannada"},
]

shows = []
bookings = []

# ─────────────── Models ───────────────
class Movie(BaseModel):
    name: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=3)
    rating: float = Field(..., gt=0, le=10)
    price: float = Field(..., gt=0)
    language: str = Field(..., min_length=2)


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    genre: Optional[str] = Field(None, min_length=3)
    rating: Optional[float] = Field(None, gt=0, le=10)
    price: Optional[float] = Field(None, gt=0)
    language: Optional[str] = Field(None, min_length=2)


class Show(BaseModel):
    movie_id: int
    time: str
    available_seats: int = Field(..., gt=0)


class Booking(BaseModel):
    show_id: int
    seats: int = Field(..., gt=0)


# ─────────────── Helpers ───────────────
def find_movie(movie_id: int):
    for movie in movies:
        if movie["id"] == movie_id:
            return movie
    return None


def calculate_discount(price: float):
    if price > 500:
        return price * 0.85
    return price


def find_show(show_id: int):
    for show in shows:
        if show["id"] == show_id:
            return show
    return None


# ─────────────── Day 1: GET ───────────────
@app.get("/")
def home():
    return {"message": "Welcome to Movie Ticket Booking API 🎬"}


@app.get("/movies")
def get_movies():
    return {"movies": movies}


@app.get("/summary")
def summary():
    return {"total_movies": len(movies), "total_shows": len(shows), "total_bookings": len(bookings)}


# ─────────────── Day 3: Filter ───────────────
@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None
):
    result = movies

    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if min_rating is not None:
        result = [m for m in result if m["rating"] >= min_rating]

    if max_price is not None:
        result = [m for m in result if m["price"] <= max_price]

    return {"filtered_movies": result}


# ─────────────── Day 2 & 4: CRUD ───────────────
@app.post("/movies", status_code=status.HTTP_201_CREATED)
def add_movie(movie: Movie):

    for m in movies:
        if m["name"].lower() == movie.name.lower():
            raise HTTPException(status_code=400, detail="Movie already exists")

    new_movie = movie.dict()
    new_movie["id"] = len(movies) + 1
    new_movie["price"] = calculate_discount(movie.price)

    movies.append(new_movie)

    return {"message": "Movie added", "movie": new_movie}


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, updated_data: MovieUpdate):

    movie = find_movie(movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_dict = updated_data.dict(exclude_unset=True)

    for key, value in update_dict.items():
        if key == "price":
            movie[key] = calculate_discount(value)
        else:
            movie[key] = value

    return {"message": "Updated", "movie": movie}


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):

    movie = find_movie(movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["rating"] > 9:
        return {"error": "Highly rated movies cannot be deleted"}

    movies.remove(movie)

    return {"message": "Deleted"}


# ─────────────── Day 5: Workflow ───────────────
@app.post("/shows", status_code=status.HTTP_201_CREATED)
def create_show(show: Show):

    movie = find_movie(show.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_show = show.dict()
    new_show["id"] = len(shows) + 1

    shows.append(new_show)

    return {"message": "Show created", "show": new_show}


@app.post("/book", status_code=status.HTTP_201_CREATED)
def book_tickets(booking: Booking):

    show = find_show(booking.show_id)

    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    if booking.seats > show["available_seats"]:
        return {"error": "Not enough seats"}

    show["available_seats"] -= booking.seats

    new_booking = booking.dict()
    new_booking["id"] = len(bookings) + 1

    bookings.append(new_booking)

    return {"message": "Booking successful 🎉", "booking": new_booking}


@app.get("/bookings")
def get_bookings():
    return {"bookings": bookings}


# ─────────────── Day 6: Search ───────────────
@app.get("/movies/search")
def search_movies(keyword: str):
    result = [
        m for m in movies
        if keyword.lower() in m["name"].lower() or keyword.lower() in m["genre"].lower()
    ]

    if not result:
        return {"message": "No movies found"}

    return {"results": result}


# ─────────────── Sort ───────────────
@app.get("/movies/sort")
def sort_movies(sort_by: str = "price", order: str = "asc"):

    if sort_by not in ["price", "rating"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    reverse = True if order == "desc" else False

    sorted_movies = sorted(movies, key=lambda x: x[sort_by], reverse=reverse)

    return {"sorted_movies": sorted_movies}


# ─────────────── Pagination ───────────────
@app.get("/movies/page")
def paginate_movies(page: int = 1, limit: int = 2):

    start = (page - 1) * limit
    end = start + limit

    total = len(movies)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "movies": movies[start:end]
    }


# ─────────────── Combined Browse (Q20) ───────────────
@app.get("/movies/browse")
def browse_movies(
    keyword: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc",
    page: int = 1,
    limit: int = 2
):
    result = movies

    # Search
    if keyword:
        result = [
            m for m in result
            if keyword.lower() in m["name"].lower() or keyword.lower() in m["genre"].lower()
        ]

    # Sort
    if sort_by in ["price", "rating"]:
        reverse = True if order == "desc" else False
        result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    total_pages = (len(result) + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "results": result[start:end]
    }


# ─────────────── LAST: Get by ID ───────────────
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if movie:
        return movie
    raise HTTPException(status_code=404, detail="Movie not found")
