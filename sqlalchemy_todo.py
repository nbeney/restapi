import os

from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_PATH = 'todo.db'
DATABASE_URI = 'sqlite:///' + DATABASE_PATH

# ======================================================================================================================
# Schema
# ======================================================================================================================

Base = declarative_base()


class Todo(Base):
    __tablename__ = 'todo'

    id = Column(Integer, primary_key=True)
    task = Column(String(250), nullable=False)

    def __repr__(self):
        return 'Todo(id={self.id}, task={self.task!r})'.format(self=self)


if not os.path.exists(DATABASE_PATH):
    # ==================================================================================================================
    # Create
    # ==================================================================================================================

    engine = create_engine(DATABASE_URI, echo=True)

    # Create all tables in the engine (idempotent). This is equivalent to "Create Table" statements in raw SQL.
    Base.metadata.create_all(engine)

    # ==================================================================================================================
    # Inserts
    # ==================================================================================================================

    engine = create_engine(DATABASE_URI, echo=True)
    session = sessionmaker(bind=engine)()

    for idx in range(1, 6):
        todo = Todo(task='Do this #{}'.format(idx))
        session.add(todo)
        session.commit()

# ======================================================================================================================
# Select
# ======================================================================================================================

engine = create_engine(DATABASE_URI, echo=True)
session = sessionmaker(bind=engine)()

for todo in session.query(Todo).all():
    print(todo)
print()
print(session.query(Todo).filter_by(id=1).one())
