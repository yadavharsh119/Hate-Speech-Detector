from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    twitter_user_id = Column(String, unique=True, index=True)
    handle = Column(String)

    # Relationships
    tweets = relationship("Tweet", back_populates="author")
    warnings = relationship("Warning", back_populates="user")
    strikes = relationship("StrikeLog", back_populates="user")

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id_str = Column(String, unique=True, index=True)
    text = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String, default="twitter")
    
    # Classification data from Member 1 (AI)
    ai_category = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Lifecycle status: pending, classified, assigned, reviewed
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="tweets")
    assignments = relationship("ModeratorAssignment", back_populates="tweet")
    action_logs = relationship("ActionLog", back_populates="tweet")

class Moderator(Base):
    __tablename__ = "moderators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    active_load = Column(Integer, default=0)
    max_capacity = Column(Integer, default=5)
    role = Column(String, default="general") # general or senior
    languages = Column(String, nullable=True) # Used by Member 2 CSP logic

    # Relationships
    assignments = relationship("ModeratorAssignment", back_populates="moderator")
    actions_taken = relationship("ActionLog", back_populates="moderator")

class ModeratorAssignment(Base):
    __tablename__ = "moderator_assignments"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    moderator_id = Column(Integer, ForeignKey("moderators.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tweet = relationship("Tweet", back_populates="assignments")
    moderator = relationship("Moderator", back_populates="assignments")

class ActionLog(Base):
    __tablename__ = "actions_log"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    moderator_id = Column(Integer, ForeignKey("moderators.id"))
    verdict = Column(String) # clean, mild_hate, hate_speech, severe_threat
    action_taken = Column(String) # no_action, warning_reply, delete, delete_and_strike
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tweet = relationship("Tweet", back_populates="action_logs")
    moderator = relationship("Moderator", back_populates="actions_taken")

class Warning(Base):
    __tablename__ = "warnings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="warnings")
    tweet = relationship("Tweet")

class StrikeLog(Base):
    __tablename__ = "strike_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tweet_id = Column(Integer, ForeignKey("tweets.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="strikes")
    tweet = relationship("Tweet")