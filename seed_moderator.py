from database import SessionLocal
import models
db = SessionLocal()
mod = models.Moderator(name='Alice (Test)', max_capacity=5)
db.add(mod)
db.commit()
print('Test moderator Alice created!')