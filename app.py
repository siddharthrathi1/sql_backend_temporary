from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Spanda%40123@localhost/dissertation_data"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    degree = Column(String(255))
    topic = Column(String(255))
    total_score = Column(Integer)

    scores = relationship("UserScore", back_populates="user")

    __table_args__ = (
        UniqueConstraint('name', 'degree', 'topic', name='unique_user'),  # Ensure unique combination
    )

class UserScore(Base):
    __tablename__ = 'UserScores'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'))
    dimension_name = Column(String(255))
    score = Column(Integer)

    user = relationship("User", back_populates="scores")

class Feedback(Base):
    __tablename__ = 'Feedbacks'
    id = Column(Integer, primary_key=True, index=True)
    selected_text = Column(Text, nullable=False)  # Allow longer text
    feedback = Column(Text, nullable=False)        # Allow longer feedback

# Initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)

# FastAPI setup
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4000",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserData(BaseModel):
    name: str
    degree: str
    topic: str
    total_score: float

class UserScoreData(BaseModel):
    dimension_name: str
    score: float

class PostData(BaseModel):
    userData: UserData
    userScores: List[UserScoreData]

class FeedbackData(BaseModel):
    selectedText: str
    feedback: str

init_db()

@app.post("/api/postUserData")
def post_user_data(postData: PostData, db: Session = Depends(get_db)):
    # Check if user exists based on unique combination of name, degree, and topic
    db_user = db.query(User).filter_by(
        name=postData.userData.name,
        degree=postData.userData.degree,
        topic=postData.userData.topic
    ).first()

    if db_user:
        # Update user total score
        db_user.total_score = postData.userData.total_score
    else:
        # Insert new user data if not exists
        db_user = User(
            name=postData.userData.name,
            degree=postData.userData.degree,
            topic=postData.userData.topic,
            total_score=postData.userData.total_score
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Update or insert user score data
    existing_scores = {score.dimension_name: score for score in db_user.scores}
    
    for score_data in postData.userScores:
        if score_data.dimension_name in existing_scores:
            # Update existing score
            existing_scores[score_data.dimension_name].score = score_data.score
        else:
            # Insert new score
            db_score = UserScore(
                user_id=db_user.id,
                dimension_name=score_data.dimension_name,
                score=score_data.score
            )
            db.add(db_score)
    
    db.commit()

    return {"message": "Data successfully stored", "user_id": db_user.id}


@app.post("/api/submitFeedback")
def submit_feedback(feedback_data: FeedbackData, db: Session = Depends(get_db)):
    # Insert the feedback into the database
    feedback_entry = Feedback(
        selected_text=feedback_data.selectedText,
        feedback=feedback_data.feedback
    )
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)

    return {"message": "Feedback stored successfully", "feedback_id": feedback_entry.id}
