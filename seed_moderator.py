from database import SessionLocal
import models

def seed():
    db = SessionLocal()
    
    # Idempotent check
    if db.query(models.Moderator).count() == 0:
        senior = models.Moderator(name='Alice (Senior)', max_capacity=5, role='senior', languages='en,es')
        general = models.Moderator(name='Bob (General)', max_capacity=5, role='general', languages='en')
        db.add(senior)
        db.add(general)
        db.commit()
        print('Moderators Alice (Senior) and Bob (General) created!')
    else:
        print('Moderators already exist. Skipping seed.')
    
    db.close()

if __name__ == "__main__":
    seed()