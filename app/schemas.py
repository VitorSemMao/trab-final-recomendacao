from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    preferences: list[str] = Field(default_factory=list)


class MovieCreate(BaseModel):
    title: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class PreferenceUpdate(BaseModel):
    preferences: list[str] = Field(default_factory=list)


class RatingCreate(BaseModel):
    movie_id: int = Field(ge=1)
    rating: float = Field(ge=0, le=5)


class UserRead(BaseModel):
    id: int
    name: str
    preferences: list[str]


class MovieRead(BaseModel):
    id: int
    title: str
    tags: list[str]
    average_rating: float
    rating_count: int


class RecommendationRead(BaseModel):
    movie_id: int
    title: str
    tags: list[str]
    score: float
    source: str


class RatingRead(BaseModel):
    user_id: int
    movie_id: int
    rating: float


class UserMovieRatingRead(BaseModel):
    movie_id: int
    title: str
    tags: list[str]
    rating: float
    average_rating: float
    rating_count: int


class DatasetRead(BaseModel):
    source: str
    movies: int
    registered_users: int
