# create a tip
# get all tips
# get all tips for a user
# get all tips from a user
# tip events from Breez

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.tip import Tip
from schemas.tip import TipCreate, TipOut
from models.user import User
